import numpy
import time
import cv2

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
		init.camera_resolution = sl.RESOLUTION.HD720
		init.camera_fps = 30
		init.set_from_serial_number(camera.serial_number)

		self._cam = sl.Camera()
		self._left_view = sl.Mat()
		self._right_view = sl.Mat()
		self._depth_view = sl.Mat()
		self._serial_number = str(camera.serial_number)
		status = self._cam.open(init)
		self._runtime = sl.RuntimeParameters()

	def read_camera(self):
		err = self._cam.grab(self._runtime) # i may need to update this?
		if err != sl.ERROR_CODE.SUCCESS: return None

		read_time = time.time()
		self._cam.retrieve_image(self._left_view, sl.VIEW.LEFT)
		self._cam.retrieve_image(self._right_view, sl.VIEW.RIGHT)
		self._cam.retrieve_measure(self._depth_view, sl.MEASURE.DEPTH)

		left_img = self._left_view.get_data()
		#left_img = cv2.resize(left_img, dsize=(128, 96), interpolation=cv2.INTER_AREA)
		#left_img = cv2.cvtColor(left_img, cv2.COLOR_BGR2RGB)

		right_img = self._right_view.get_data()
		#right_img = cv2.resize(right_img, dsize=(128, 96), interpolation=cv2.INTER_AREA)
		#right_img = cv2.cvtColor(right_img, cv2.COLOR_BGR2RGB)

		depth_img = self._depth_view.get_data()
		#depth_img = cv2.applyColorMap(cv2.convertScaleAbs(depth_img, alpha=0.03), cv2.COLORMAP_JET)
		#depth_img = cv2.resize(depth_img, dsize=(128, 96), interpolation=cv2.INTER_AREA)
		#depth_img = cv2.cvtColor(depth_img, cv2.COLOR_BGR2RGB)

		dict_1 = {'array': left_img, 'shape': left_img.shape, 'type': 'rgb',
			'read_time': read_time, 'serial_number': self._serial_number + '/left'}
		dict_2 = {'array': right_img,  'shape': right_img.shape, 'type': 'rgb',
			'read_time': read_time, 'serial_number': self._serial_number + '/right'}
		dict_3 = {'array': depth_img,  'shape': depth_img.shape, 'type': 'depth',
			'read_time': read_time, 'serial_number': self._serial_number + '/depth'}
		
		return [dict_1, dict_2, dict_3]

	def disable_camera(self):
		self._cam.close()
