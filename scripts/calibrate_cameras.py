from r2d2.robot_env import RobotEnv
from r2d2.controllers.oculus_controller import VRPolicy
import numpy as np
import time
from r2d2.calibration_utils.calibration import *

# Test Parameters #
server_is_client = False
server_ip_address = '172.16.0.1'
use_oculus = True
max_steps = 10000
# Test Parameters #

get_action = lambda a: np.concatenate([a['joint'], [a['gripper']]])

ip_address = None if server_is_client else server_ip_address
env = RobotEnv(ip_address=ip_address)
#env.reset()
if use_oculus:
    controller = VRPolicy()
    controller.reset_state()
else:
    controller = lambda obs: np.array([0.001, 0, 0, 0, 0, 0, 0])

from collections import defaultdict
sols = defaultdict(list)
actions = []
save_episodes = []
delete_episodes = []
for i in range(10):
	env.reset()
	images, robot_poses = [], []


	camera_dict = defaultdict(list)
	calibration_dict = {}
	robot_states = []
	k = 0
	while True:
		obs, info = env.get_observation()
		info = controller.get_info()
		if i == 0:
			a = controller.forward(obs)
			a_dict = env.step(a)
			a = get_action(a_dict)
			actions.append(a)
		else:
			a = actions[k]
			env.update_robot(a, action_space='joint', delta=False)
		
		time.sleep(1/15)

		# img = obs['images'][0]['array']
		# pose = obs['ee_state'][:6]
		# try: visualize_chessboard(img)
		# except: pass

		if i == 0:
			save_ep = info['save_episode']
			delete_ep = info['delete_episode']
			save_episodes.append(save_ep)
			delete_episodes.append(delete_ep)
		else:
			save_ep = save_episodes[k]
			delete_ep = delete_episodes[k]
			k += 1

		if save_ep:
			curr_state = obs['state_dict']['ee_state']
			robot_states.append(curr_state)

			for cam_id in obs['camera_dict']:
				img_dict = obs['camera_dict'][cam_id]
				for img_id in img_dict:
					if 'rgb' in img_id:
						view_id = '{0}_{1}'.format(cam_id, img_id)
						camera_dict[view_id].append(img_dict[img_id])

		if delete_ep:
			for view_id in camera_dict:
				try:
					print('Calibrating: ', view_id)
					cam2base = calibrate_cam_to_base(camera_dict[view_id], robot_states)
					estimated_accuracy = estimate_3rd_person_accuracy(camera_dict[view_id], robot_states)
					calibration_dict[view_id] = cam2base
					print('Accuracy:', estimated_accuracy)
					sols[view_id].append(cam2base[:3].tolist() + [d * 180 / np.pi for d in cam2base[3:]])
				except:
					continue



			for key in sols:
				x = np.array(sols[key])
				print('{0}: {1}'.format(key, x.std(axis=0)))
			
			break


			#visualize_calibration(calibration_dict)


# images, robot_poses = [], []


# camera_dict = defaultdict(list)
# calibration_dict = {}
# robot_states = []

# while True:
# 	obs, info = env.get_observation()
# 	info = controller.get_info()
# 	a = controller.forward(obs)
# 	time.sleep(1/15)
# 	env.step(a)

# 	# img = obs['images'][0]['array']
# 	# pose = obs['ee_state'][:6]
# 	# try: visualize_chessboard(img)
# 	# except: pass

# 	if info['save_episode']:
# 		curr_state = obs['state_dict']['ee_state']
# 		robot_states.append(curr_state)

# 		for cam_id in obs['camera_dict']:
# 			img_dict = obs['camera_dict'][cam_id]
# 			for img_id in img_dict:
# 				if 'rgb' in img_id:
# 					view_id = '{0}_{1}'.format(cam_id, img_id)
# 					camera_dict[view_id].append(img_dict[img_id])

# 	if info['delete_episode']:
# 		for view_id in camera_dict:
# 			try:
# 				print('Calibrating: ', view_id)
# 				cam2base = calibrate_cam_to_base(camera_dict[view_id], robot_states)
# 				estimated_accuracy = estimate_3rd_person_accuracy(camera_dict[view_id], robot_states)
# 				calibration_dict[view_id] = cam2base
# 				print('Accuracy:', estimated_accuracy)

# 				print(cam2base)
# 			except:
# 				continue

# 		visualize_calibration(calibration_dict)
