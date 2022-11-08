from r2d2.misc.compression_utils import *
from collections import defaultdict
from copy import deepcopy
import numpy as np
import time

def collect_trajectory(env, controller=None, policy=None, horizon=None, obs_pointer=None, wait_for_controller=False):
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
	traj_data = defaultdict(list)
	num_steps = 0

	while True:

		# Collect Miscellaneous Info #
		info = {'controller': {} if (controller is None) else controller.get_info(),
				'timestamps': {}}

		# Get Observation #
		info['timestamps']['step_start'] = time.time()
		obs = env.get_observation()
		if obs_pointer is not None: obs_pointer.update(obs)

		# Get Action #
		info['timestamps']['policy_start'] = time.time()
		if policy is None: action = controller.forward(obs)
		else: action = policy.forward(obs)

		# Regularize Control Frequency #
		info['timestamps']['sleep_start'] = time.time()
		comp_time = time.time() - info['timestamps']['step_start']
		sleep_left = (1 / env.hz) - comp_time
		if sleep_left > 0: time.sleep(sleep_left)

		# Skip If Necessary #
		skip_step = wait_for_controller and (not info['controller']['movement_enabled'])
		if skip_step: continue

		# Step Environment #
		info['timestamps']['control_start'] = time.time()
		action_info = env.step(action)

		# Save Data #
		info['timestamps']['step_end'] = time.time()
		traj_data['observations'].append(obs)
		traj_data['actions'].append(action_info)
		traj_data['info'].append(info)
		num_steps += 1

		# Check Termination #
		if horizon is not None: end_traj = (horizon == num_steps)
		else: end_traj = info['controller']['save_episode'] or info['controller']['delete_episode']
		if end_traj: return traj_data

	return traj_data

	
def save_trajectory(filepath, traj_data, compression_type=''):
	'''Saves a trajectory with the desired compression technique'''
	assert compression_type in ['', 'png', 'jpeg', 'mp4']
	
	traj_data = deepcopy(traj_data)
	traj_data['compression_type'] = compression_type

	if compression_type in ['png', 'jpeg']:
		apply_img_compression(traj_data, compression_type=compression_type)
	elif compression_type == 'mp4':
		apply_video_compression(traj_data)

	np.savez_compressed(filepath + '.npz', compressed_traj)
	
def load_trajectory(filepath):
	'''Loads a trajectory file into a numpy array'''
	traj_data = np.load(filepath, allow_pickle=True)['arr_0']
	compression_type = traj_data['compression_type']

	if compression_type in ['png', 'jpeg']:
		invert_img_compression(traj_data)
	elif compression_type == 'mp4':
		invert_video_compression(traj_data)

	return traj_data
