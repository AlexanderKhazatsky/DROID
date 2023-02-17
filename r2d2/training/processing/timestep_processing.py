from r2d2.training.processing.data_transforms import ImageTransformer
from r2d2.camera_utils.info import camera_type_to_string_dict
from collections import defaultdict
from itertools import chain
from copy import deepcopy
import numpy as np

class TimestepProcesser:

	def __init__(self,
			ignore_action=False,
			action_space='cartesian_velocity',
			
			robot_state_keys=['cartesian_position', 'gripper_position', 'joint_positions', 'joint_velocities'],
			camera_extrinsics=['hand_camera', 'varied_camera', 'fixed_camera'],
			
			state_dtype=np.float32,
			action_dtype=np.float32,
			
			image_transform_kwargs={}
		):

		assert action_space in ['cartesian_position', 'joint_position', 'cartesian_velocity', 'joint_velocity']
		
		self.action_space = action_space
		self.gripper_key = 'gripper_velocity' if 'velocity' in action_space else 'gripper_position'
		self.ignore_action = ignore_action
		
		self.robot_state_keys = robot_state_keys
		self.camera_extrinsics = camera_extrinsics
		
		self.state_dtype = state_dtype
		self.action_dtype = action_dtype
		
		self.image_transformer = ImageTransformer(**image_transform_kwargs)

	def forward(self, timestep):
		# Make Deep Copy #
		timestep = deepcopy(timestep)

		# Get Relevant Camera Info #
		camera_type_dict = {k: camera_type_to_string_dict[v] for k, v in
			timestep['observation']['camera_type'].items()}
		sorted_camera_ids = sorted(camera_type_dict.keys())

		### Get Robot State Info ###
		sorted_state_keys = sorted(self.robot_state_keys)
		full_robot_state = timestep['observation']['robot_state']
		robot_state = [np.array(full_robot_state[key]).flatten() for key in sorted_state_keys]
		if len(robot_state):
			robot_state = np.concatenate(robot_state)

		### Get Extrinsics ###
		calibration_dict = timestep['observation']['camera_extrinsics']
		sorted_calibrated_ids = sorted(calibration_dict.keys())
		extrinsics_dict = defaultdict(list)

		for serial_number in sorted_camera_ids:
			cam_type = camera_type_dict[serial_number]
			if cam_type not in self.camera_extrinsics: continue

			for full_cam_id in sorted_calibrated_ids:
				if serial_number in full_cam_id:
					cam2base = calibration_dict[full_cam_id]
					extrinsics_dict[cam_type].append(cam2base)

		sorted_extrinsics_keys = sorted(extrinsics_dict.keys())
		extrinsics_state =  list(chain(*[extrinsics_dict[cam_type] for 
				cam_type in sorted_extrinsics_keys]))
		if len(extrinsics_state):
			extrinsics_state = np.concatenate(extrinsics_state)

		### Get High Dimensional State Info ###
		high_dim_state_dict = defaultdict(lambda: defaultdict(list))

		for obs_type in ['image', 'depth', 'pointcloud']:
			obs_type_dict = timestep['observation'].get(obs_type, {})
			sorted_obs_ids = sorted(obs_type_dict.keys())

			for serial_number in sorted_camera_ids:
				cam_type = camera_type_dict[serial_number]

				for full_obs_id in sorted_obs_ids:
					if serial_number in full_obs_id:
						data = obs_type_dict[full_obs_id]
						high_dim_state_dict[obs_type][cam_type].append(data)

		### Finish Observation Portion ### 
		low_level_state = np.concatenate([robot_state, extrinsics_state], dtype=self.state_dtype) 
		processed_timestep = {'observation': {'state': low_level_state, 'camera': high_dim_state_dict}}
		self.image_transformer.forward(processed_timestep)

		### Add Proper Action ###
		if not self.ignore_action:
			arm_action = timestep['action'][self.action_space]
			gripper_action = timestep['action'][self.gripper_key]
			action = np.concatenate([arm_action, [gripper_action]], dtype=self.action_dtype)
			processed_timestep['action'] = action
			
		return processed_timestep


# class TimestepProcesser:

# 	def __init__(self,
# 			ignore_action=False,
# 			action_space='cartesian_velocity',
			
# 			robot_state_keys=['cartesian_position', 'gripper_position', 'joint_positions', 'joint_velocities'],
# 			image_views=['hand_camera', 'varied_camera', 'fixed_camera'], depth_views=[], pointcloud_views=[],
# 			camera_extrinsics=['hand_camera', 'varied_camera', 'fixed_camera'],
			
# 			state_dtype=np.float32,
# 			action_dtype=np.float32,
			
# 			image_transform_kwargs={}
# 		):

# 		assert action_space in ['cartesian_position', 'joint_position', 'cartesian_velocity', 'joint_velocity']
		
# 		self.action_space = action_space
# 		self.gripper_key = 'gripper_velocity' if 'velocity' in action_space else 'gripper_position'
# 		self.ignore_action = ignore_action
		
# 		self.robot_state_keys = robot_state_keys
# 		self.image_views = image_views
# 		self.depth_views = depth_views
# 		self.pointcloud_views = pointcloud_views
# 		self.camera_extrinsics = camera_extrinsics
		
# 		self.state_dtype = state_dtype
# 		self.action_dtype = action_dtype
		
# 		self.image_transformer = ImageTransformer(**image_transform_kwargs)

# 	def are_cameras_used(self):
# 		num_used = len(self.image_views) + len(self.depth_views) + len(self.pointcloud_views)
# 		return num_used  > 0

# 	def forward(self, timestep):
# 		# Make Deep Copy #
# 		timestep = deepcopy(timestep)

# 		# Get Relevant Camera Info #
# 		camera_type_dict = {k: camera_type_to_string_dict[v] for k, v in
# 			timestep['observation']['camera_type'].items()}
# 		sorted_camera_ids = sorted(camera_type_dict.keys())

# 		### Get Robot State Info ###
# 		sorted_state_keys = sorted(self.robot_state_keys)
# 		full_robot_state = timestep['observation']['robot_state']
# 		robot_state = [np.array(full_robot_state[key]).flatten() for key in sorted_state_keys]
# 		if len(robot_state):
# 			robot_state = np.concatenate(robot_state)

# 		### Get Extrinsics ###
# 		calibration_dict = timestep['observation']['camera_extrinsics']
# 		sorted_calibrated_ids = sorted(calibration_dict.keys())
# 		extrinsics_dict = defaultdict(list)

# 		for serial_number in sorted_camera_ids:
# 			cam_type = camera_type_dict[serial_number]
# 			if cam_type not in self.camera_extrinsics: continue

# 			for full_cam_id in sorted_calibrated_ids:
# 				if serial_number in full_cam_id:
# 					cam2base = calibration_dict[full_cam_id]
# 					extrinsics_dict[cam_type].append(cam2base)

# 		sorted_extrinsics_keys = sorted(extrinsics_dict.keys())
# 		extrinsics_state =  list(chain(*[extrinsics_dict[cam_type] for 
# 				cam_type in sorted_extrinsics_keys]))
# 		if len(extrinsics_state):
# 			extrinsics_state = np.concatenate(extrinsics_state)

# 		### Get High Dimensional State Info ###
# 		high_dim_state_dict = defaultdict(lambda: defaultdict(list))

# 		for obs_type in ['image', 'depth', 'pointcloud']:
# 			if obs_type == 'image': curr_cam_types = self.image_views
# 			elif obs_type == 'depth': curr_cam_types = self.depth_views
# 			elif obs_type == 'pointcloud': curr_cam_types = self.pointcloud_views

# 			for serial_number in sorted_camera_ids:
# 				cam_type = camera_type_dict[serial_number]
# 				if cam_type not in curr_cam_types: continue

# 				obs_type_dict = timestep['observation'][obs_type]
# 				sorted_obs_ids = sorted(obs_type_dict.keys())

# 				for full_obs_id in sorted_obs_ids:
# 					if serial_number in full_obs_id:
# 						data = obs_type_dict[full_obs_id]
# 						high_dim_state_dict[obs_type][cam_type].append(data)

# 		### Finish Observation Portion ### 
# 		low_level_state = np.concatenate([robot_state, extrinsics_state], dtype=self.state_dtype) 
# 		processed_timestep = {'observation': {'state': low_level_state, 'camera': high_dim_state_dict}}
# 		self.image_transformer.forward(processed_timestep)

# 		### Add Proper Action ###
# 		if not self.ignore_action:
# 			arm_action = timestep['action'][self.action_space]
# 			gripper_action = timestep['action'][self.gripper_key]
# 			action = np.concatenate([arm_action, [gripper_action]], dtype=self.action_dtype)
# 			processed_timestep['action'] = action
			
# 		return processed_timestep
