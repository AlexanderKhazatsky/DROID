from r2d2.misc.parameters import hand_camera_id
from r2d2.misc.time import time_ms
from copy import deepcopy
import numpy as np
import time
import cv2
import os

try:
	import pyzed.sl as sl
except ModuleNotFoundError:
	print('WARNING: You have not setup the ZED cameras, and currently cannot use them')

class RecordedZedCamera:
	def __init__(self, filepath, serial_number):
		# Save Parameters #
		self.filepath = filepath
		self.serial_number = serial_number
		self._index = 0

		# Initialize Readers #
		self._sbs_img = sl.Mat()
		self._left_img = sl.Mat()
		self._right_img = sl.Mat()
		self._left_depth = sl.Mat()
		self._right_depth = sl.Mat()
		self._left_pointcloud = sl.Mat()
		self._right_pointcloud = sl.Mat()

	def set_reading_parameters(self,
			image=True, depth=False, pointcloud=False,
			concatenate_images=False, resolution=(0,0)
		):

		# Save Parameters #
		self.image = image
		self.depth = depth
		self.pointcloud = pointcloud
		self.concatenate_images = concatenate_images
		self.resolution = sl.Resolution(*resolution)
		self.skip_reading = not any([image, depth, pointcloud])
		if self.skip_reading: return

		# Set SVO path for playback
		init_parameters = sl.InitParameters()
		init_parameters.set_from_svo_file(self.filepath)

		# Open the ZED
		self._cam = sl.Camera()
		status = self._cam.open(init_parameters)
		if status != sl.ERROR_CODE.SUCCESS:
			print('Zed Error: ' + repr(status))

	def get_frame_count(self):
		if self.skip_reading: return 0
		return self._cam.get_svo_number_of_frames()

	def set_frame_index(self, index):
		if self.skip_reading: return

		if index < self._index:
			self._cam.set_svo_position(index)
			self._index = index

		while self._index < index:
			self.read_camera(ignore_data=True)

	def read_camera(self, ignore_data=False, timestamp=None):
		# Skip if Read Unnecesary #
		if self.skip_reading: return {} 
		
		# Read Camera #
		self._index += 1
		err = self._cam.grab()
		if err != sl.ERROR_CODE.SUCCESS: return None
		if ignore_data: return None

		# Check Image Timestamp #
		received_time = self._cam.get_timestamp(sl.TIME_REFERENCE.IMAGE).get_milliseconds()
		timestamp_error = (timestamp is not None) and (timestamp != received_time)

		if timestamp_error:
			print('Timestamps did not match...')
			return None

		# Return Data #
		data_dict = {}
		
		if self.image:
			if self.concatenate_images:
				self._cam.retrieve_image(svo_image, sl.VIEW.SIDE_BY_SIDE, resolution=self.resolution)
				data_dict['image'] = {self.serial_number: self._sbs_img.get_data().copy()}
			else:
				self._cam.retrieve_image(self._left_img, sl.VIEW.LEFT, resolution=self.resolution)
				self._cam.retrieve_image(self._right_img, sl.VIEW.RIGHT, resolution=self.resolution)
				data_dict['image'] = {
					self.serial_number + '_left': self._left_img.get_data().copy(),
					self.serial_number + '_right': self._right_img.get_data().copy()}
		if self.depth:
			self._cam.retrieve_measure(self._left_depth, sl.MEASURE.DEPTH, resolution=self.resolution)
			self._cam.retrieve_measure(self._right_depth, sl.MEASURE.DEPTH_RIGHT, resolution=self.resolution)
			data_dict['depth'] = {
				self.serial_number + '_left': self._left_depth.get_data().copy(),
				self.serial_number + '_right': self._right_depth.get_data().copy()}
		if self.pointcloud:
			self._cam.retrieve_measure(self._left_pointcloud, sl.MEASURE.XYZRGBA, resolution=self.resolution)
			self._cam.retrieve_measure(self._right_pointcloud, sl.MEASURE.XYZRGBA_RIGHT, resolution=self.resolution)
			data_dict['pointcloud'] = {
				self.serial_number + '_left': self._left_pointcloud.get_data().copy(),
				self.serial_number + '_right': self._right_pointcloud.get_data().copy()}
		
		return data_dict

	def disable_camera(self):		
		if hasattr(self, '_cam'):
			self._cam.close()
