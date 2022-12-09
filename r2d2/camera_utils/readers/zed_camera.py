import numpy
import time
import cv2
from copy import deepcopy

try:
	import pyzed.sl as sl
except ModuleNotFoundError:
	print('WARNING: You have not setup the ZED cameras, and currently cannot use them')

def gather_zed_cameras():
	all_zed_cameras = []
    
	try: cameras = sl.Camera.get_device_list()
	except NameError: return []

	for cam in cameras:
		cam = ZedCamera(cam)
		all_zed_cameras.append(cam)

	return all_zed_cameras

class ZedCamera:
	def __init__(self, camera):
		init = sl.InitParameters()
		# init.sdk_verbose = True
		# init.depth_minimum_distance = 0.1
		# init.depth_maximum_distance = 5
		# init.depth_mode = sl.DEPTH_MODE.ULTRA
		init.camera_resolution = sl.RESOLUTION.HD720
		init.camera_fps = 15
		init.set_from_serial_number(camera.serial_number)

		self._cam = sl.Camera()
		self._left_view = sl.Mat()
		self._right_view = sl.Mat()
		self._depth_view = sl.Mat()
		self._serial_number = str(camera.serial_number)

		print('Opening ZED: ', self._serial_number)

		status = self._cam.open(init)
		self._runtime = sl.RuntimeParameters()

	def get_info(self):
		return {'serial_number': self._serial_number}

	def read_camera(self):
		err = self._cam.grab(self._runtime)
		if err != sl.ERROR_CODE.SUCCESS: return None

		read_time = time.time()
		self._cam.retrieve_image(self._left_view, sl.VIEW.LEFT)
		self._cam.retrieve_image(self._right_view, sl.VIEW.RIGHT)
		self._cam.retrieve_measure(self._depth_view, sl.MEASURE.DEPTH)

		left_img = self._left_view.get_data().copy()
		#left_img = cv2.cvtColor(left_img, cv2.COLOR_BGRA2BGR)

		right_img = self._right_view.get_data().copy()
		#right_img = cv2.cvtColor(right_img, cv2.COLOR_BGRA2BGR)

		depth_img = self._depth_view.get_data().copy()

		img_dict = {'rgb': left_img, 'depth': right_img, 'stereo_rgb': right_img}
		
		return img_dict, read_time

	# def read_camera(self):
	# 	err = self._cam.grab(self._runtime)
	# 	if err != sl.ERROR_CODE.SUCCESS: return None

	# 	read_time = time.time()
	# 	self._cam.retrieve_image(self._left_view, sl.VIEW.LEFT)
	# 	self._cam.retrieve_image(self._right_view, sl.VIEW.RIGHT)
	# 	self._cam.retrieve_measure(self._depth_view, sl.MEASURE.DEPTH)

	# 	left_img = self._left_view.get_data().copy()[:,:,:3]
	# 	#left_img = cv2.resize(left_img, dsize=(128, 96), interpolation=cv2.INTER_AREA)
	# 	#left_img = cv2.cvtColor(left_img, cv2.COLOR_BGR2RGB)

	# 	right_img = self._right_view.get_data().copy()[:,:,:3]
	# 	#right_img = cv2.resize(right_img, dsize=(128, 96), interpolation=cv2.INTER_AREA)
	# 	#right_img = cv2.cvtColor(right_img, cv2.COLOR_BGR2RGB)

	# 	depth_img = self._depth_view.get_data().copy()
	# 	#depth_img = cv2.applyColorMap(cv2.convertScaleAbs(depth_img, alpha=0.03), cv2.COLORMAP_JET)
	# 	#depth_img = cv2.resize(depth_img, dsize=(128, 96), interpolation=cv2.INTER_AREA)
	# 	#depth_img = cv2.cvtColor(depth_img, cv2.COLOR_BGR2RGB)

	# 	dict_1 = {'array': left_img, 'shape': left_img.shape, 'type': 'rgb',
	# 		'read_time': read_time, 'serial_number': self._serial_number + '_left'}
	# 	dict_2 = {'array': right_img,  'shape': right_img.shape, 'type': 'rgb',
	# 		'read_time': read_time, 'serial_number': self._serial_number + '_right'}
	# 	dict_3 = {'array': depth_img,  'shape': depth_img.shape, 'type': 'depth',
	# 		'read_time': read_time, 'serial_number': self._serial_number + '_depth'}

	# 	fake_dict = deepcopy(dict_1)
	# 	fake_dict['serial_number'] += '_copy'
		
	# 	return [dict_1, dict_2, fake_dict]

	def disable_camera(self):
		self._cam.close()
