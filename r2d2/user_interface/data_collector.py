from r2d2.misc import trajectory_utils
from r2d2.misc.parameters import data_logdir
from collections import defaultdict
from datetime import date
from copy import deepcopy
import numpy as np
import time
import cv2
import os

class DataCollecter:

	def __init__(self, env, controller, policy=None):
		self.env = env
		self.traj_running = False
		self.action_noise = None
		self.controller = controller
		self.policy = policy
		self.traj_num = 0
		self.log_dir = '{0}/{1}/'.format(data_logdir, date.today())
		self.num_cameras = len(self.get_camera_feed())

		# Data Variables #
		self.traj_name = None
		self.traj_info = None
		self.traj_data = None
		self.traj_saved = None

		return None

	def reset_robot(self):
		self.env._robot.establish_connection()
		self.env.reset()
		self.controller.reset_state()

	# def is_robot_reset(self):
	# 	return self.env.is_robot_reset()

	def get_user_feedback(self):
		info = self.controller.get_info()
		return deepcopy(info)

	def save_trajectory(self):
		if self.traj_saved: return
		print('Saving Trajectory #{0}'.format(self.traj_num))

		filepath = os.path.join(self.log_dir + self.traj_name)
		os.makedirs(self.log_dir, exist_ok=True)

		trajectory_utils.save_trajectory(filepath, self.traj_data)

		self.traj_saved = True
		self.traj_num += 1

	def delete_trajectory(self):
		if not self.traj_saved: return
		print('Deleting Trajectory #{0}'.format(self.traj_num - 1))

		filepath = os.path.join(self.log_dir + self.traj_name)
		os.remove(filepath)

		self.traj_saved = False
		self.traj_num -= 1

	def collect_trajectory(self, info={}, practice=False):
		self.traj_running = True
		self.traj_name = time.asctime().replace(" ", "_")
		self.obs_pointer = {}
		self.traj_saved = False

		self.env._robot.establish_connection()
		self.traj_data = trajectory_utils.collect_trajectory(self.env, controller=self.controller,
			policy=self.policy, obs_pointer=self.obs_pointer, wait_for_controller=True)
		self.traj_data['metadata'] = info.copy()
		
		self.traj_running = False
		save = self.traj_data['info'][-1]['controller']['save_episode']
		if save and (not practice): self.save_trajectory()

	def get_gui_imgs(self, camera_feed):
		camera_feed = list(filter(lambda feed: ('rgb' in feed['type']) and \
			('right' not in feed['serial_number']), camera_feed))
		camera_feed.sort(key=lambda feed: feed['serial_number'])
		camera_feed = [cv2.cvtColor(feed['array'][:,:,:3], cv2.COLOR_BGR2RGB) for feed in camera_feed]
		return camera_feed

	def get_camera_feed(self):
		if self.traj_running and ('images' in self.obs_pointer):
			camera_feed = deepcopy(self.obs_pointer['images'])
		else:
			camera_feed = self.env.get_images()

		return self.get_gui_imgs(camera_feed)

	def get_last_trajectory(self):
		last_traj = []
		for obs in self.traj_data['observations']:
			camera_feed = deepcopy(obs['images'])
			gui_imgs = self.get_gui_imgs(camera_feed)
			last_traj.append(gui_imgs)

		return last_traj

	def set_action_noise(self, noise_percentage, low=0, high=0.1):
		self.action_noise = noise_percentage * (high - low) + low



# from datetime import date
# from copy import deepcopy
# import numpy as np
# import time
# import os

# import cv2

# class DataCollecter:

# 	def __init__(self, env, controller, policy=None):
# 		self.env = env
# 		self.traj_running = False
# 		self.action_noise = None
# 		self.controller = controller
# 		self.policy = policy
# 		self.traj_num = 0
# 		self.log_dir = '/home/sasha/Desktop/irisnet/{0}/'.format(date.today())
# 		self.num_cameras = len(self.get_camera_feed())

# 		# Data Variables #
# 		self.traj_name = None
# 		self.traj_info = None
# 		self.traj_data = None
# 		self.traj_saved = None

# 		return None

# 	def reset_robot(self):
# 		self.env._robot.establish_connection()
# 		self.env.reset()
# 		self.controller.reset_state()

# 	# def is_robot_reset(self):
# 	# 	return self.env.is_robot_reset()

# 	def get_user_feedback(self):
# 		info = self.controller.get_info()
# 		return deepcopy(info)

# 	def save_trajectory(self):
# 		if self.traj_saved: return
# 		print('Saving Trajectory #{0}'.format(self.traj_num))

# 		filepath = os.path.join(self.log_dir + self.traj_name + '.npy')
# 		os.makedirs(self.log_dir, exist_ok=True)
# 		np.save(filepath, self.traj_data)

# 		self.traj_saved = True
# 		self.traj_num += 1

# 	def delete_trajectory(self):
# 		if not self.traj_saved: return
# 		print('Deleting Trajectory #{0}'.format(self.traj_num - 1))

# 		filepath = os.path.join(self.log_dir + self.traj_name + '.npy')
# 		os.remove(filepath)

# 		self.traj_saved = False
# 		self.traj_num -= 1

# 	def collect_trajectory(self, info={}, practice=False):
# 		"""
# 		Collect trajectory until we end

# 		Notes: Save last trajectory, and whether or not we kept it
# 		"""
# 		self.reset_robot()
# 		self.traj_running = True
# 		self.traj_name = time.asctime().replace(" ", "_")
# 		self.traj_data = dict(observations=[], actions=[], info=info)
# 		self.traj_saved = False
# 		delays = []

# 		while True:

# 			# Determine If User Ended Episode #
# 			feedback = self.get_user_feedback()
# 			end_traj = feedback['save_episode'] or feedback['delete_episode']
# 			save = feedback['save_episode'] and (not practice) and (self.policy is None)

# 			# End Episode Appropriately #
# 			if end_traj:
# 				self.traj_running = False
# 				if save: self.save_trajectory()
# 				return

# 			# Get Latest Observation And Action #
# 			#act = np.random.normal(loc=act, scale=self.action_noise)
# 			obs = self.env.get_observation()
# 			act = self.controller.get_action(obs)

# 			# if self.policy is None:
# 			# 	act = self.controller.get_action(obs)
# 			# # else:
# 			# 	act = self.policy(process_observation(obs), None).flatten().detach().numpy()

# 			# Add Relevant Info To Obs #
# 			obs['movement_enabled'] = feedback['movement_enabled']
# 			obs['step_time'] = time.time()

# 			# Step Environment #
# 			self.env.step(act)

# 			for feed_dict in obs['images']:
# 				delays.append(obs['step_time'] - feed_dict['read_time'])

# 			# Save Data #
# 			#if obs['movement_enabled']:
# 			self.last_obs = deepcopy(obs)
# 			self.traj_data['observations'].append(obs)
# 			self.traj_data['actions'].append(act)

# 	def get_gui_imgs(self, camera_feed):
# 		camera_feed = list(filter(lambda feed: ('rgb' in feed['type']) and \
# 			('right' not in feed['serial_number']), camera_feed))
# 		camera_feed.sort(key=lambda feed: feed['serial_number'])
# 		camera_feed = [cv2.cvtColor(feed['array'][:,:,:3], cv2.COLOR_BGR2RGB) for feed in camera_feed]
# 		return camera_feed


# 	def get_camera_feed(self):
# 		if self.traj_running and len(self.traj_data['observations']) > 0:
# 			camera_feed = self.last_obs['images']
# 		else:
# 			camera_feed = self.env.get_images()

# 		return self.get_gui_imgs(camera_feed)

# 	def get_last_trajectory(self):
# 		last_traj = []
# 		for obs in self.traj_data['observations']:
# 			camera_feed = deepcopy(obs['images'])
# 			gui_imgs = self.get_gui_imgs(camera_feed)
# 			last_traj.append(gui_imgs)

# 		return last_traj

# 	def set_action_noise(self, noise_percentage, low=0, high=0.1):
# 		self.action_noise = noise_percentage * (high - low) + low
