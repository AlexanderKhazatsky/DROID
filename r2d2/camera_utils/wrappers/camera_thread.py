from copy import deepcopy
import threading

import time

class CameraThread:
	def __init__(self, camera, hz=50):
		self._camera = camera
		self._latest_feed = None
		self._hz = hz

		camera_thread = threading.Thread(target=self.update_camera_feed)
		camera_thread.daemon = True
		camera_thread.start()

	def read_camera(self):
		return deepcopy(self._latest_feed)

	def update_camera_feed(self):
		while True:
			feed = self._camera.read_camera()
			if feed is not None:
				self._latest_feed = self._camera.read_camera()
			time.sleep(1 / self._hz)

	def disable_camera(self):
		self._camera.disable_camera()