from r2d2.misc.trajectory_writer import TrajectoryWriter
from r2d2.misc.transformations import change_pose_frame
from r2d2.calibration.calibration_utils import *
from r2d2.misc.time import time_ms
from r2d2.misc.parameters import *
from collections import defaultdict
from copy import deepcopy
import numpy as np
import time
import cv2
import os

def collect_trajectory(env, controller=None, policy=None, horizon=None, save_filename=None, metadata=None,
		wait_for_controller=False, obs_pointer=None, save_images=False, use_recording=False):
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
	if use_recording: assert (save_filename is not None) and save_images
	if obs_pointer is not None: assert isinstance(obs_pointer, dict)

	# Reset States #
	if controller is not None: controller.reset_state()
	env.camera_reader.set_trajectory_mode()
	env.reset()

	# Prepare Data Writers If Necesary #
	if save_filename is not None:
		save_images_internally = save_images and (not use_recording)
		traj_writer = TrajectoryWriter(save_filename, metadata=metadata,
			save_images=save_images_internally)
		if use_recording:
			file_generator = lambda sn: traj_writer.create_video_file(sn, '.svo')
			env.camera_reader.start_recording(file_generator)

	num_steps = 0
	while True:

		# Collect Miscellaneous Info #
		controller_info = {} if (controller is None) else controller.get_info()
		control_timestamps = {'step_start': time_ms()}

		# Get Observation #
		obs = env.get_observation()
		if obs_pointer is not None: obs_pointer.update(obs)

		# Get Action #
		control_timestamps['policy_start'] = time_ms()
		if policy is None: action = controller.forward(obs)
		else: action = policy.forward(obs)

		# Regularize Control Frequency #
		control_timestamps['sleep_start'] = time_ms()
		comp_time = time_ms() - control_timestamps['step_start']
		sleep_left = (1 / env.hz) - (comp_time / 1000)
		if sleep_left > 0: time.sleep(sleep_left)

		# Skip If Necessary #
		skip_step = wait_for_controller and (not controller_info['movement_enabled'])
		if skip_step: continue

		# Step Environment #
		control_timestamps['control_start'] = time_ms()
		action_info = env.step(action)

		# Save Data #
		control_timestamps['step_end'] = time_ms()
		obs['timestamp']['control'] = control_timestamps
		timestep = {'observations': obs, 'actions': action_info}
		if save_filename: traj_writer.write_timestep(timestep)

		# Check Termination #
		num_steps += 1
		if horizon is not None: end_traj = (horizon == num_steps)
		else: end_traj = controller_info['success'] or controller_info['failure']
		
		# Close Files And Return #
		if end_traj:
			if use_recording: env.camera_reader.stop_recording()
			if save_filename: traj_writer.close(metadata=controller_info)
			return controller_info

def calibrate_camera(env, camera_id, controller, step_size=0.01, pause_time=0.5, image_freq=10, obs_pointer=None, wait_for_controller=True):
	'''Returns true if calibration was successful, otherwise returns False
	   3rd Person Calibration Instructions: Press A when board in aligned with the camera from 1 foot away.
	   Hand Calibration Instructions: Press A when the hand camera is aligned with the board from 1 foot away.'''
	if obs_pointer is not None: assert isinstance(obs_pointer, dict)

	# Get Camera + Set Calibration Mode #
	camera = env.camera_reader.get_camera(camera_id)
	env.camera_reader.set_calibration_mode(camera_id)

	# Select Proper Calibration Procedure #
	hand_camera = camera.serial_number == hand_camera_id
	intrinsics_dict = camera.get_intrinsics()
	if hand_camera: calibrator = HandCameraCalibrator(intrinsics_dict)
	else: calibrator = ThirdPersonCameraCalibrator(intrinsics_dict)

	env.reset()
	controller.reset_state()

	while True:
		# Collect Controller Info #
		controller_info = controller.get_info()
		start_time = time.time()

		# Get Observation #
		state, _ = env.get_state()
		cam_obs, _ = camera.read_camera()

		for cam_id in cam_obs['image']:
			cam_obs['image'][cam_id] = calibrator.augment_image(cam_id, cam_obs['image'][cam_id])
		if obs_pointer is not None: obs_pointer.update(cam_obs)

		# Get Action #
		action = controller.forward({'robot_state': state})
		action[-1] = 0 # Keep gripper open

		# Regularize Control Frequency #
		comp_time = time.time() - start_time
		sleep_left = (1 / env.hz) - comp_time
		if sleep_left > 0: time.sleep(sleep_left)

		# Skip If Necessary #
		skip_step = wait_for_controller and (not controller_info['movement_enabled'])
		if skip_step: continue

		# Step Environment #
		action_info = env.step(action)

		# Check Termination #
		start_calibration = controller_info['success']
		end_calibration = controller_info['failure']
		
		# Close Files And Return #
		if start_calibration: break
		if end_calibration: return False

	# Collect Data #
	calib_start = time.time()
	pose_origin = state['ee_state'][:6]
	i = 0

	while True:
		# Check For Termination #
		controller_info = controller.get_info()
		if controller_info['failure']: return False

		# Start #
		start_time = time.time()
		take_picture = (i % image_freq) == 0

		# Collect Observations #
		if take_picture: time.sleep(pause_time)
		state, _ = env.get_state()
		cam_obs, _ = camera.read_camera()

		# Add Sample + Augment Images #
		for cam_id in cam_obs['image']:
			cam_obs['image'][cam_id] = calibrator.augment_image(cam_id, cam_obs['image'][cam_id])
			if not take_picture: continue
			img = deepcopy(cam_obs['image'][cam_id])
			pose = state['ee_state'][:6].copy()
			calibrator.add_sample(cam_id, img, pose)

		# Update Obs Pointer #
		if obs_pointer is not None: obs_pointer.update(cam_obs)

		# Move To Desired Next Pose #
		calib_pose = calibration_traj(i * step_size, hand_camera=hand_camera)
		desired_pose = change_pose_frame(calib_pose, pose_origin)
		action = np.concatenate([desired_pose, [0]])
		env.update_robot(action, action_space='cartesian', delta=False, blocking=False)
		i += 1

		# Regularize Control Frequency #
		comp_time = time.time() - start_time
		sleep_left = (1 / env.hz) - comp_time
		if sleep_left > 0: time.sleep(sleep_left)

		# Check If Cycle Complete #
		cycle_complete = (i * step_size) >= (2 * np.pi)
		if cycle_complete: break

	# SAVE INTO A JSON
	for cam_id in cam_obs['image']:
		success = calibrator.is_calibration_accurate(cam_id)
		if not success: return False
		transformation = calibrator.calibrate(cam_id)
		update_calibration_info(cam_id, transformation)

	return True
