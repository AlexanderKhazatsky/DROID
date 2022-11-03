from r2d2.camera_utils.wrappers.camera_thread import CameraThread
from r2d2.camera_utils.readers.realsense_camera import gather_realsense_cameras
from r2d2.camera_utils.readers.zed_camera import gather_zed_cameras
import numpy as np
import time

class MultiCameraWrapper:

	def __init__(self, camera_types=['realsense', 'zed'], specific_cameras=None, use_threads=False):
		self._all_cameras = []

		if specific_cameras is not None:
			self._all_cameras.extend(specific_cameras)

		if 'realsense' in camera_types:
			realsense_cameras = gather_realsense_cameras()
			self._all_cameras.extend(realsense_cameras)

		if 'zed' in camera_types:
			zed_cameras = gather_zed_cameras()
			self._all_cameras.extend(zed_cameras)

		if use_threads:
			for i in range(len(self._all_cameras)):
				self._all_cameras[i] = CameraThread(self._all_cameras[i])
			time.sleep(1)
	
	def read_cameras(self):
		all_frames = []
		order_id = np.random.permutation(len(self._all_cameras))

		for i in order_id:
			curr_feed = self._all_cameras[i].read_camera()
			if curr_feed is not None:
				all_frames.extend(curr_feed)

		return all_frames

	def disable_cameras(self):
		for camera in self._all_cameras:
			camera.disable_camera()
