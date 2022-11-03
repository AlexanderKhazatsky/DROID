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
	def __init__(self, device):
		self._pipeline = rs.pipeline()
		self._serial_number = str(device.get_info(rs.camera_info.serial_number))
		config = rs.config()

		config.enable_device(self._serial_number)
		config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
		config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

		self._pipeline.start(config)

	def read_camera(self):
		# Wait for a coherent pair of frames: depth and color
		frames = self._pipeline.wait_for_frames()
		depth_frame = frames.get_depth_frame()
		color_frame = frames.get_color_frame()
		if not depth_frame or not color_frame: return None
		read_time = time.time()

		# Convert images to numpy arrays
		depth_image = np.asanyarray(depth_frame.get_data()).copy()
		color_image = np.asanyarray(color_frame.get_data()).copy()

		# Apply colormap on depth image (image must be converted to 8-bit per pixel first)
		#depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)

		#color_image = cv2.resize(color_image, dsize=(128, 96), interpolation=cv2.INTER_AREA)
		#depth_image= cv2.resize(depth_image, dsize=(128, 96), interpolation=cv2.INTER_AREA)

		#color_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2RGB)
		#depth_colormap = cv2.cvtColor(depth_colormap, cv2.COLOR_BGR2RGB)

		dict_1 = {'array': color_image, 'shape': color_image.shape, 'type': 'rgb',
			'read_time': read_time, 'serial_number': self._serial_number + '/rgb'}
		dict_2 = {'array': depth_image, 'shape': depth_image.shape, 'type': 'depth',
			'read_time': read_time, 'serial_number': self._serial_number + '/depth'}

		return [dict_1, dict_2]
		
	def disable_camera(self):
		self._pipeline.stop()
