from r2d2.camera_utils.readers.recorded_zed_camera import RecordedZedCamera
from r2d2.camera_utils.info import get_camera_type
from collections import defaultdict
import random
import glob

class RecordedMultiCameraWrapper:

	def __init__(self, recording_folderpath, camera_kwargs={}):

		# Open Camera Readers #
		all_filepaths = glob.glob(recording_folderpath + '/*.svo')
		
		self.camera_dict = {}
		for f in all_filepaths:
			serial_number = f.split('/')[-1][:-4]
			cam_type = get_camera_type(serial_number)
			curr_cam_kwargs = camera_kwargs.get(cam_type, {})

			self.camera_dict[serial_number] = RecordedZedCamera(f, serial_number)
			self.camera_dict[serial_number].set_reading_parameters(**curr_cam_kwargs)

	def read_cameras(self, index=None, timestamp_dict={}):
		full_obs_dict = defaultdict(dict)

		# Read Cameras In Randomized Order #
		all_cam_ids = list(self.camera_dict.keys())
		random.shuffle(all_cam_ids)

		for cam_id in all_cam_ids:
			timestamp = timestamp_dict.get(cam_id +'_frame_received', None)
			if index is not None: self.camera_dict[cam_id].set_frame_index(index)
			data_dict = self.camera_dict[cam_id].read_camera(timestamp=timestamp)
			
			# Process Returned Data #
			if data_dict is None: return None
			for key in data_dict: full_obs_dict[key].update(data_dict[key])

		return full_obs_dict

	def disable_cameras(self):
		for camera in self.camera_dict.values():
			camera.disable_camera()






	# def set_camera_id(self, camera_id):
	# 	# Open Recorded Camera File #
	# 	f = self.camera_filepath_dict[camera_id]
	# 	self.current_camera = RecordedZedCamera(f, camera_id)
	# 	self.current_cam_id = camera_id

	# 	# Set Reading Parameters #
	# 	cam_type = get_camera_type(camera_id)
	# 	resolution = self.resolution_kwargs.get(cam_type, (0,0))
	# 	self.current_camera.set_reading_parameters(
	# 			image=self.image, depth=self.depth, pointcloud=self.pointcloud,
	# 			concatenate_images=self.concatenate_images, resolution=resolution)

	# def update_timestep_with_camera_obs(self, timestep, check_timestep=True):
	# 	'''Updates Timestep With Camera Obs. Returns True if success, False otherwise.'''

	# 	# Check That We Need To Read #
	# 	if not self.should_read_cameras: return {}

	# 	# Get Timestamp Info #
	# 	#timestamp_dict = timestep['observation']['timestamp']['cameras']
	# 	if check_timestep:
	# 		timestamp = timestep['observation']['timestamp']['cameras'][self.current_cam_id +'_frame_received']
	# 	else:
	# 		timestamp = None

	# 	# Read Camera + Add Data To Timestep #
	# 	camera_obs = self.current_camera.read_camera(timestamp=timestamp)
	# 	if camera_obs is None: return False

	# 	# Update Timestep, Return True
	# 	# for key in camera_obs:
	# 	# 	if key in timestep['observation']:
	# 	# 		timestep['observation'][key].update(camera_obs[key])
	# 	# 	else:
	# 	# 		timestep['observation'][key] = camera_obs[key]

	# 	return True

	# def update_timestep_observations(self, timestep_list, ind_to_save):
	# 	if type(timestep_list) != list: timestep_list = [timestep_list]
	# 	all_cam_ids = list(self.camera_filepath_dict.keys())

	# 	for cam_id in all_cam_ids:
	# 		self.set_camera_id(cam_id)

	# 		# frame_count = self.current_camera.get_frame_count()
	# 		# for i in range(frame_count):
	# 		# 	self.current_camera.read_camera()


	# 		for i in range(len(ind_to_save)):
	# 			# Read Camera #
	# 			self.current_camera.set_frame_index(ind_to_save[i])
	# 			success = self.update_timestep_with_camera_obs(timestep_list, check_timestep=False)
				
	# 			# Handle Failure Case #
	# 			if not success:
	# 				ind_to_save = ind_to_save[:i]
	# 				timestep_list = timestep_list[:i]
	# 				break

	# 		# Close File Reader #
	# 		self.current_camera.disable_camera()
