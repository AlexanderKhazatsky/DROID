from r2d2.misc.trajectory_writer import TrajectoryWriter
from r2d2.misc.compression_utils import *
from collections import defaultdict
from copy import deepcopy
import numpy as np
import time
import h5py
import cv2

def collect_trajectory(env, controller=None, policy=None, horizon=None, save_filepath=None,
		metadata=None, wait_for_controller=False, obs_pointer=None):
	'''
	Collects a robot trajectory.
	- If policy is None, actions will come from the controller
	- If a horizon is given, we will step the environment accordingly
	- Otherwise, we will end the trajectory when the controller tells us to
	- If you need a pointer to the current observation, pass a dictionary in for obs_pointer
	'''

	# Check Parameters #
	assert (controller is not None) or (policy is not None)
	assert (controller is not None) or (horizon is not None)
	if wait_for_controller: assert (controller is not None)
	if obs_pointer is not None: assert isinstance(obs_pointer, dict)

	# Reset States #
	if controller is not None: controller.reset_state()
	env.reset()

	# Step Environment Until Termination #
	traj_writer = TrajectoryWriter(save_filepath, metadata=metadata)
	num_steps = 0

	while True:

		# Collect Miscellaneous Info #
		controller_info = {} if (controller is None) else controller.get_info()
		control_timestamps = {'step_start': time.time()}

		# Get Observation #
		obs, timestamp_dict = env.get_observation()
		if obs_pointer is not None: obs_pointer.update(obs)

		# Get Action #
		control_timestamps['policy_start'] = time.time()
		if policy is None: action = controller.forward(obs)
		else: action = policy.forward(obs)

		# Regularize Control Frequency #
		control_timestamps['sleep_start'] = time.time()
		comp_time = time.time() - control_timestamps['step_start']
		print('Potential HZ: ', 1 / comp_time)
		sleep_left = (1 / env.hz) - comp_time
		if sleep_left > 0: time.sleep(sleep_left)

		# Skip If Necessary #
		skip_step = wait_for_controller and (not controller_info['movement_enabled'])
		if skip_step: continue

		# Step Environment #
		control_timestamps['control_start'] = time.time()
		action_info = env.step(action)

		# Save Data #
		# Info


		control_timestamps['step_end'] = time.time()
		timestamp_dict['control'] = control_timestamps
		timestep = {
			'observations': obs,
			'actions': action_info,
			'timestamps': timestamp_dict}
		traj_writer.write_timestep(timestep)

		# Check Termination #
		num_steps += 1
		if horizon is not None: end_traj = (horizon == num_steps)
		else: end_traj = controller_info['save_episode'] or controller_info['delete_episode']
		
		start_close = time.time()
		if end_traj:
			traj_writer.close()
			print('Close Time: ', time.time() - start_close)
			return traj_data

# def save_transition(logdir, step_dict, compression_type='jpeg'):
# 	'''Saves a transition with the desired compression technique'''
# 	assert compression_type in ['', 'png', 'jpeg']
	
# 	step_dict = deepcopy(step_dict)

# 	filepath = os.path.join(self.log_dir + self.traj_name) + '.npz'

# 	filepath = logdir + step_dict
# 	step_dict['compression_type'] = compression_type

# 	if compression_type in ['png', 'jpeg']:
# 		apply_img_compression(step_dict, compression_type=compression_type)

# 	np.savez_compressed(filepath, step_dict)
	
def save_trajectory(filepath, traj_data, compression_type=''):
	'''Saves a trajectory with the desired compression technique'''
	assert compression_type in ['', 'png', 'jpeg', 'mp4']
	assert filepath[-4:] == '.npz'
	
	traj_data = deepcopy(traj_data)
	traj_data['compression_type'] = compression_type

	if compression_type in ['png', 'jpeg']:
		apply_img_compression(traj_data, compression_type=compression_type)
	elif compression_type == 'mp4':
		apply_video_compression(traj_data)

	np.savez_compressed(filepath, traj_data)
	
def load_trajectory(filepath):
	'''Loads a trajectory file into a numpy array'''
	traj_data = np.load(filepath, allow_pickle=True)['arr_0'].item()
	compression_type = traj_data['compression_type']

	if compression_type in ['png', 'jpeg']:
		invert_img_compression(traj_data)
	elif compression_type == 'mp4':
		invert_video_compression(traj_data)

	return traj_data

def compress_trajectory(filepath, compression_type='jpeg'):
	'''Compresses a trajectory filepath with the desired compression technique'''
	assert compression_type in ['', 'png', 'jpeg', 'mp4']
	traj_data = load_trajectory(filepath)
	save_trajectory(filepath, compression_type=compression_type)