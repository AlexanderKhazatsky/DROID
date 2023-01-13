from r2d2.calibration.calibration_utils import check_calibration_info, load_calibration_info
from r2d2.misc import trajectory_utils
from datetime import date
from copy import deepcopy
import time
import cv2
import os

# Prepare Data Folder #
dir_path = os.path.dirname(os.path.realpath(__file__))
data_dir = os.path.join(dir_path, '../../data')

class DataCollecter:

	def __init__(self, env, controller, policy=None):
		self.env = env
		self.controller = controller
		self.policy = policy

		self.traj_running = False
		self.traj_saved = False
		self.obs_pointer = {}

		# Get Camera Info #
		self.num_cameras = len(self.get_camera_feed()[0])
		self.cam_ids = list(env.camera_reader.camera_dict.keys())
		self.cam_ids.sort()

		# Make Sure Log Directory Exists #
		self.logdir = os.path.join(data_dir, str(date.today()))
		if not os.path.isdir(self.logdir): os.makedirs(self.logdir)

	def reset_robot(self):
		self.env._robot.establish_connection()
		self.env.reset()
		self.controller.reset_state()

	def get_user_feedback(self):
		info = self.controller.get_info()
		return deepcopy(info)

	def set_calibration_mode(self, cam_id):
		self.env.camera_reader.set_calibration_mode(cam_id)

	def set_trajectory_mode(self):
		self.env.camera_reader.set_trajectory_mode()

	def collect_trajectory(self, info=None, practice=False):
		if info is None: info = {}
		info['time'] = time.asctime().replace(" ", "_")

		if practice: filename = None
		else: filename = os.path.join(self.logdir, info['time'] + '.h5')
		save_data = filename is not None

		self.traj_running = True
		self.env._robot.establish_connection()
		controller_info = trajectory_utils.collect_trajectory(self.env, controller=self.controller,
			metadata=info, policy=self.policy, obs_pointer=self.obs_pointer, save_images=save_data,
			use_recording=save_data, save_filename=filename)
		
		self.traj_saved = controller_info['success']
		self.traj_running = False
		self.obs_pointer = {}

	def calibrate_camera(self, cam_id):
		self.traj_running = True
		self.env._robot.establish_connection()
		success = trajectory_utils.calibrate_camera(self.env, cam_id,
			controller=self.controller, obs_pointer=self.obs_pointer)
		self.traj_running = False
		self.obs_pointer = {}
		return success

	def check_calibration_info(self):
		image_dict = self.env.read_cameras(image=True)[0]['image']
		required_ids = list(image_dict.keys())
		info_dict = check_calibration_info(required_ids)
		return info_dict

	def get_gui_imgs(self, obs):
		all_cam_ids = list(obs['image'].keys())
		all_cam_ids.sort()

		gui_images = []
		for cam_id in all_cam_ids:
			img = cv2.cvtColor(obs['image'][cam_id][:,:,:3], cv2.COLOR_BGR2RGB)
			gui_images.append(img)

		return gui_images, all_cam_ids

	def get_camera_feed(self):
		if self.obs_pointer: obs = deepcopy(self.obs_pointer)
		else: obs = self.env.read_cameras()[0]
		gui_images, cam_ids = self.get_gui_imgs(obs)
		return gui_images, cam_ids

