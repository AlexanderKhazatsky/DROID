import os
import random
from collections import defaultdict
from r2d2.camera_utils.camera_readers.realsense_camera import gather_realsense_cameras
from r2d2.camera_utils.camera_readers.zed_camera import gather_zed_cameras
from r2d2.camera_utils.info import get_camera_type
from r2d2.misc.parameters import camera_type


class MultiCameraWrapper:
    def __init__(self, camera_kwargs={}):
        # Open Cameras #
        accepted_camera_types = ['realsense', 'zed']
        assert camera_type in accepted_camera_types, f"Invalid camera_type specified in r2d2.misc.parameters! Must be one of the following: {accepted_camera_types}"
        if camera_type == 'realsense':
            cameras = gather_realsense_cameras()
        else: # 'zed'
            cameras = gather_zed_cameras()
        self.camera_dict = {cam.serial_number: cam for cam in cameras}

        # Set Correct Parameters #
        for cam_id in self.camera_dict.keys():
            cam_type = get_camera_type(cam_id)
            curr_cam_kwargs = camera_kwargs.get(cam_type, {})
            self.camera_dict[cam_id].set_reading_parameters(**curr_cam_kwargs)

        # Launch Camera #
        self.set_trajectory_mode()

    ### Calibration Functions ###
    def get_camera(self, camera_id):
        return self.camera_dict[camera_id]

    def set_calibration_mode(self, cam_id):
        self.camera_dict[cam_id].set_calibration_mode()

    def set_trajectory_mode(self):
        for cam in self.camera_dict.values():
            cam.set_trajectory_mode()

    ### Data Storing Functions ###
    def start_recording(self, recording_folderpath):
        subdir = os.path.join(recording_folderpath, 'SVO' if camera_type == 'zed' else 'MP4')
        if not os.path.isdir(subdir):
            os.makedirs(subdir)
        file_suffix = '.svo' if camera_type == 'zed' else '.mp4'
        for cam in self.camera_dict.values():
            filepath = os.path.join(subdir, cam.serial_number + file_suffix)
            cam.start_recording(filepath)

    def stop_recording(self):
        for cam in self.camera_dict.values():
            cam.stop_recording()

    ### Basic Camera Functions ###
    def read_cameras(self):
        full_obs_dict = defaultdict(dict)
        full_timestamp_dict = {}

        # Read Cameras In Randomized Order #
        all_cam_ids = list(self.camera_dict.keys())
        random.shuffle(all_cam_ids)

        for cam_id in all_cam_ids:
            if not self.camera_dict[cam_id].is_running():
                continue
            data_dict, timestamp_dict = self.camera_dict[cam_id].read_camera()

            for key in data_dict:
                full_obs_dict[key].update(data_dict[key])
            full_timestamp_dict.update(timestamp_dict)

        return full_obs_dict, full_timestamp_dict

    def disable_cameras(self):
        for camera in self.camera_dict.values():
            camera.disable_camera()
