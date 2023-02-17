from r2d2.camera_utils.readers.zed_camera import gather_zed_cameras
from r2d2.camera_utils.info import get_camera_type
from collections import defaultdict
import random
import os

class MultiCameraWrapper:

	def __init__(self, camera_kwargs={}):

		# Open Cameras #
		zed_cameras = gather_zed_cameras()
		self.camera_dict = {cam.serial_number: cam for cam in zed_cameras}

		# Set Correct Parameters #
		for cam_id in self.camera_dict.keys():
			cam_type = get_camera_type(cam_id)
			curr_cam_kwargs = camera_kwargs.get(cam_type, {})
			self.camera_dict[cam_id].set_reading_parameters(**curr_cam_kwargs)

		# Launch Camera #
		self.set_trajectory_mode()

	### Calibration Functions ###
	def get_camera(self, camera_id):
		return self.camera_dict[camera_id]

	def set_calibration_mode(self, cam_id):
		for cam in self.camera_dict.values():
			cam.disable_camera()
		self.camera_dict[cam_id].set_calibration_mode()

	def set_trajectory_mode(self):
		for cam in self.camera_dict.values():
			cam.set_trajectory_mode()

	### Data Storing Functions ###
	def start_recording(self, recording_folderpath):
		for cam in self.camera_dict.values():
			filepath = os.path.join(recording_folderpath, cam.serial_number + '.svo')
			cam.start_recording(filepath)

	def stop_recording(self):
		for cam in self.camera_dict.values():
			cam.stop_recording()
	
	### Basic Camera Functions ###
	def read_cameras(self):
		full_obs_dict = defaultdict(dict)
		full_timestamp_dict = {}

		# Read Cameras In Randomized Order #
		all_cam_ids = list(self.camera_dict.keys())
		random.shuffle(all_cam_ids)

		for cam_id in all_cam_ids:
			if not self.camera_dict[cam_id].is_running(): continue
			data_dict, timestamp_dict = self.camera_dict[cam_id].read_camera()
			
			for key in data_dict:
				full_obs_dict[key].update(data_dict[key])
			full_timestamp_dict.update(timestamp_dict)

		return full_obs_dict, full_timestamp_dict

	def disable_cameras(self):
		for camera in self.camera_dict.values():
			camera.disable_camera()
