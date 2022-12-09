from r2d2.camera_utils.wrappers.camera_thread import CameraThread
from r2d2.camera_utils.readers.realsense_camera import gather_realsense_cameras
from r2d2.camera_utils.readers.zed_camera import gather_zed_cameras
import random
import time

class MultiCameraWrapper:

	def __init__(self, camera_types=['realsense', 'zed'], use_threads=False):
		self._camera_dict = {}

		if 'realsense' in camera_types:
			realsense_cameras = gather_realsense_cameras()
			new_cameras = {cam.get_info()['serial_number']: cam
				for cam in realsense_cameras}
			self._camera_dict.update(new_cameras)

		if 'zed' in camera_types:
			zed_cameras = gather_zed_cameras()
			new_cameras = {cam.get_info()['serial_number']: cam
				for cam in zed_cameras}
			self._camera_dict.update(new_cameras)

		if use_threads:
			for cam_id in self._camera_dict:
				threaded_cam = CameraThread(self._camera_dict[cam_id])
				self._camera_dict[cam_id] = threaded_cam
			time.sleep(1)

	def calibrate_cameras(self, calibration_dict):
		for cam_id in calibration_dict:
			camera2robot = calibration_dict[cam_id]
			self._camera_dict[cam_id].set_calibration(camera2robot)
	
	def read_cameras(self, include_rgb=True, include_depth=True, include_pointcloud=True):
		all_cam_ids = list(self._camera_dict.keys())
		random.shuffle(all_cam_ids) # Randomize reading order
		camera_dict = {}
		timestamp_dict = {}

		for cam_id in all_cam_ids:
			img_dict, read_time = self._camera_dict[cam_id].read_camera()
			camera_dict[cam_id] = img_dict
			timestamp_dict[cam_id] = read_time

		return camera_dict, timestamp_dict

	def get_camera_infos(self):
		return {cam_id: cam.get_info() for cam_id, cam
			in self._camera_dict.items()}

	def disable_cameras(self):
		for camera in self._camera_dict.values():
			camera.disable_camera()
