from copy import deepcopy
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
		self.fps = 30
		self.latency = int(2.5 * (1e3 / self.fps)) # in milliseconds
		self._config = rs.config()
		self._current_mode = None
		self.recording_video = False

	def set_reading_parameters(self, image=True, depth=True, pointcloud=False, concatenate_images=False, resolution=(0,0)):
		"""Sets the camera reading parameters."""
		# Non-Permenant Values #
		self.image = image
		# Permenant Values #
		self.depth = depth

	def set_calibration_mode(self):
		"""Sets the camera mode for camera calibration."""
		self._configure_camera(image_width=1920, image_height=1080) # use high-resolution images for camera calibration
		self._current_mode = 'calibration'

	def set_trajectory_mode(self):
		"""Sets the camera mode for normal trajectory recording."""
		self._configure_camera(image_width=640, image_height=480)
		self._current_mode = 'trajectory'

	def _configure_camera(self, image_width, image_height):
		# Close Existing Camera #
		self.disable_camera()
		# Start Camera #
		self._config.enable_device(self.serial_number)
		self._config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, self.fps) # enable depth camera
		self._config.enable_stream(rs.stream.color, image_width, image_height, rs.format.bgr8, self.fps) # enable RGB camera
		cfg = self._pipeline.start(self._config)
		# Save Intrinsics #
		profile = cfg.get_stream(rs.stream.color)
		intrinsics_params = profile.as_video_stream_profile().get_intrinsics()
		self._intrinsics = {self.serial_number: self._process_intrinsics(intrinsics_params)}

	### Calibration Utilities ###
	def _process_intrinsics(self, intrinsics_params):
		intrinsics = {}
		intrinsics['cameraMatrix'] = np.array([
				[intrinsics_params.fx, 0, intrinsics_params.ppx],
				[0, intrinsics_params.fy, intrinsics_params.ppy],
				[0, 0, 1]])
		intrinsics['distCoeffs'] = np.array(list(intrinsics_params.coeffs))
		return intrinsics

	def get_intrinsics(self):
		return deepcopy(self._intrinsics)

	### Recording Utilities ###
	def start_recording(self, filename):
		assert filename.endswith(".mp4")
		# Create/Open the RGB and depth MP4 files we will write to.
		video_codec = cv2.VideoWriter_fourcc(*"mp4v")
		self.video_writer = cv2.VideoWriter(filename, fourcc=video_codec, fps=15, frameSize=(640, 480))
		depth_filename = filename.split('.mp4')[0] + '_depth.mp4'
		self.depth_video_writer = cv2.VideoWriter(depth_filename, fourcc=video_codec, fps=15, frameSize=(640, 480), isColor=False)
		self.recording_video = True

	def stop_recording(self):
		# Close and save the RGB and depth MP4 files we wrote to.
		if self.recording_video:
			self.video_writer.release()
			self.depth_video_writer.release()
			self.recording_video = False

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
			if self.recording_video:
				self.video_writer.write(color_image)
		if self.depth:
			depth_frame = frames.get_depth_frame()
			depth_image = np.asanyarray(depth_frame.get_data())
			# The original depth values are 16-bit unsigned integers between 0 and 65535, inclusive.
			# We convert depth values to 8-bit unsigned integers between 0 and 255, inclusive, as follows:
			#   Say we only care about depth values 0 to 1000 and want to clip values larger than 1000 (assuming
			#   that 1000 is usually the max value we observe in our application).
			#   Then we can use the calculation y = (x * 255.0 / 1000.0).clip(0, 255).
			#   To see how this works, plug in x = 0 and x = 1000. Then y = 0 and y = 255. Any x > 1000 gets clipped.
			depth_image = (depth_image * 255.0 / 1000.0).clip(0, 255).astype(np.uint8) # 1000 is a magic number
			data_dict['depth'] = {self.serial_number: depth_image}
			if self.recording_video:
				self.depth_video_writer.write(depth_image)
		return data_dict, timestamp_dict

	def disable_camera(self):
		"""Turns off the camera."""
		if self._current_mode in ['calibration', 'trajectory']:
			self._pipeline.stop()
			self._config.disable_all_streams()
			self._current_mode = 'disabled'

	def is_running(self):
		"""Checks whether the camera is enabled."""
		return self._current_mode != 'disabled'
