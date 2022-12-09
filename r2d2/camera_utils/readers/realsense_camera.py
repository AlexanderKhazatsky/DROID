import pyrealsense2 as rs
import numpy as np
import time
import cv2

from copy import deepcopy

def gather_realsense_cameras():
	context = rs.context()
	all_devices = list(context.devices)
	all_rs_cameras = []

	for device in all_devices:
		#device.hardware_reset()
		rs_camera = RealSenseCamera(device)
		all_rs_cameras.append(rs_camera)

	return all_rs_cameras

class RealSenseCamera:
	def __init__(self, device):
		self._pipeline = rs.pipeline()
		self._serial_number = str(device.get_info(rs.camera_info.serial_number))
		config = rs.config()

		print('Opening RS: ', self._serial_number)
		config.enable_device(self._serial_number)
		# config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 15)
		# config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 15)
		config.enable_stream(rs.stream.depth, 848, 480, rs.format.z16, 15)
		config.enable_stream(rs.stream.color, 848, 480, rs.format.bgr8, 15)
		self._aligner = rs.align(rs.stream.color)
		self._pipeline.start(config)

	def get_info(self):
		return {'serial_number': self._serial_number}
		#serial number, camera intrinsics

	def set_calibration(self, camera2robot):
		self._camera2robot = camera2robot

	def read_camera(self):
		# Wait for a coherent pair of frames: depth and color
		read_time = time.time()
		frames = self._pipeline.wait_for_frames()
		frames = self._aligner.process(frames)
		depth_frame = frames.get_depth_frame()
		color_frame = frames.get_color_frame()
		if not depth_frame or not color_frame: return None

		# Convert images to numpy arrays
		depth_image = np.asanyarray(depth_frame.get_data()).copy()
		color_image = np.asanyarray(color_frame.get_data()).copy()

		img_dict = {'rgb': color_image, 'depth': depth_image}

		return img_dict, read_time

	# def read_camera(self):
	# 	# Wait for a coherent pair of frames: depth and color
	# 	frames = self._pipeline.wait_for_frames()
	# 	depth_frame = frames.get_depth_frame()
	# 	color_frame = frames.get_color_frame()
	# 	if not depth_frame or not color_frame: return None
	# 	read_time = time.time()

	# 	# Convert images to numpy arrays
	# 	depth_image = np.asanyarray(depth_frame.get_data()).copy()
	# 	color_image = np.asanyarray(color_frame.get_data()).copy()

	# 	# Apply colormap on depth image (image must be converted to 8-bit per pixel first)
	# 	#depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)

	# 	#color_image = cv2.resize(color_image, dsize=(128, 96), interpolation=cv2.INTER_AREA)
	# 	#depth_image= cv2.resize(depth_image, dsize=(128, 96), interpolation=cv2.INTER_AREA)

	# 	#color_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2RGB)
	# 	#depth_colormap = cv2.cvtColor(depth_colormap, cv2.COLOR_BGR2RGB)

	# 	dict_1 = {'array': color_image, 'shape': color_image.shape, 'type': 'rgb',
	# 		'read_time': read_time, 'serial_number': self._serial_number + '_rgb'}
	# 	dict_2 = {'array': depth_image, 'shape': depth_image.shape, 'type': 'depth',
	# 		'read_time': read_time, 'serial_number': self._serial_number + '_depth'}

	# 	fake_dict = deepcopy(dict_1)
	# 	fake_dict['serial_number'] += '_copy'

	# 	return [dict_1, fake_dict]
		
	def disable_camera(self):
		self._pipeline.stop()
