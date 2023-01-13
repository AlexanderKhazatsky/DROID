from r2d2.camera_utils.wrappers.camera_thread import CameraThread
from r2d2.camera_utils.readers.zed_camera import gather_zed_cameras
from collections import defaultdict
import random
import time

class MultiCameraWrapper:

	def __init__(self):
		zed_cameras = gather_zed_cameras()
		self.camera_dict = {cam.serial_number: cam for cam in zed_cameras}

	### Calibration Functions ###
	def get_camera(self, camera_id):
		return self.camera_dict[camera_id]

	def set_calibration_mode(self, cam_id):
		for curr_cam_id in self.camera_dict.keys():
			if curr_cam_id != cam_id:
				self.camera_dict[curr_cam_id].disable_camera()
			else:
				self.camera_dict[curr_cam_id].set_calibration_mode()

	def set_trajectory_mode(self):
		for cam in self.camera_dict.values():
			cam.set_trajectory_mode()

	### Data Storing Functions ###
	def start_recording(self, file_generator):
		for cam in self.camera_dict.values():
			filename = file_generator(cam.serial_number)
			cam.start_recording(filename)

	def stop_recording(self):
		for cam in self.camera_dict.values():
			cam.stop_recording()
	
	### Basic Camera Functions ###
	def read_cameras(self, image=True, depth=False, pointcloud=False):
		read_camera = any([image, depth, pointcloud])
		if not read_camera: return full_obs_dict
		full_obs_dict = defaultdict(dict)
		full_timestamp_dict = {}

		# Read Cameras In Randomized Order #
		all_cam_ids = list(self.camera_dict.keys())
		random.shuffle(all_cam_ids)

		for cam_id in all_cam_ids:
			if not self.camera_dict[cam_id].is_running(): continue
			data_dict, timestamp_dict = self.camera_dict[cam_id].read_camera(
				image=image, depth=depth, pointcloud=pointcloud)
			for key in data_dict:
				full_obs_dict[key].update(data_dict[key])
			full_timestamp_dict.update(timestamp_dict)

		return full_obs_dict, full_timestamp_dict

	def disable_cameras(self):
		for camera in self.camera_dict.values():
			camera.disable_camera()
