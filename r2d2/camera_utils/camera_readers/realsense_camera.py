from r2d2.misc.time import time_ms
import pyrealsense2 as rs
import numpy as np
import time
import cv2

def gather_realsense_cameras():
	context = rs.context()
	all_devices = list(context.devices)
	all_rs_cameras = []
	for device in all_devices:
		rs_camera = RealSenseCamera(device)
		all_rs_cameras.append(rs_camera)
	return all_rs_cameras

class RealSenseCamera:
	# Some code in this class is adapted from: https://github.com/IntelRealSense/librealsense/blob/master/wrappers/python/examples/opencv_viewer_example.py
	def __init__(self, device):
		self._pipeline = rs.pipeline()
		self.serial_number = str(device.get_info(rs.camera_info.serial_number))
		config = rs.config()
		config.enable_device(self.serial_number)
		config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
		device_product_line = str(device.get_info(rs.camera_info.product_line))
		if device_product_line == 'L500': config.enable_stream(rs.stream.color, 960, 540, rs.format.bgr8, 30)
		else: config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
		self._pipeline.start(config)

	def set_reading_parameters(self, image=True, depth=True, pointcloud=False, concatenate_images=False, resolution=(0,0)):
		"""Sets the camera reading parameters."""
		# Non-Permenant Values #
		self.image = image
		# Permenant Values #
		self.depth = depth

	def set_calibration_mode(self):
		"""Sets the camera mode for camera calibration."""
		self._current_mode = 'calibration'

	def set_trajectory_mode(self):
		"""Sets the camera mode for normal trajectory recording."""
		self._current_mode = 'trajectory'

	def read_camera(self, enforce_same_dim=False):
		"""Captures color and/or depth images. Returns the image data as well as read timestamps."""
		data_dict = {}
		timestamp_dict = {self.serial_number +'_read_start': time_ms()}
		frames = self._pipeline.wait_for_frames()
		timestamp_dict[self.serial_number + '_read_end'] = time_ms()
		if self.image:
			color_frame = frames.get_color_frame()
			color_image = np.asanyarray(color_frame.get_data())
			data_dict['image'] = {self.serial_number: color_image}
		if self.depth:
			depth_frame = frames.get_depth_frame()
			depth_image = np.asanyarray(depth_frame.get_data())
			# Apply colormap on depth image (image must be converted to 8-bit per pixel first)
			depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)
			data_dict['depth'] = {self.serial_number: depth_colormap}
		return data_dict, timestamp_dict

	def disable_camera(self):
		"""Turns off the camera."""
		self._pipeline.stop()

	def is_running(self):
		"""Checks whether the camera is enabled."""
		return self._current_mode != 'disabled'
