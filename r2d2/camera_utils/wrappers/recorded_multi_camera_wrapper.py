import glob
import random
from collections import defaultdict

from r2d2.camera_utils.info import get_camera_type
from r2d2.camera_utils.recording_readers.mp4_reader import MP4Reader
from r2d2.camera_utils.recording_readers.svo_reader import SVOReader


class RecordedMultiCameraWrapper:
    def __init__(self, recording_folderpath, camera_kwargs={}):
        # Open Camera Readers #
        svo_filepaths = glob.glob(recording_folderpath + "/*.svo")
        mp4_filepaths = glob.glob(recording_folderpath + "/*.mp4")
        all_filepaths = svo_filepaths + mp4_filepaths

        self.camera_dict = {}
        for f in all_filepaths:
            serial_number = f.split("/")[-1][:-4]
            cam_type = get_camera_type(serial_number)
            curr_cam_kwargs = camera_kwargs.get(cam_type, {})

            if f.endswith(".svo"):
                Reader = SVOReader
            elif f.endswith(".mp4"):
                Reader = MP4Reader
            else:
                raise ValueError

            self.camera_dict[serial_number] = Reader(f, serial_number)
            self.camera_dict[serial_number].set_reading_parameters(**curr_cam_kwargs)

    def read_cameras(self, index=None, timestamp_dict={}):
        full_obs_dict = defaultdict(dict)

        # Read Cameras In Randomized Order #
        all_cam_ids = list(self.camera_dict.keys())
        random.shuffle(all_cam_ids)

        for cam_id in all_cam_ids:
            timestamp = timestamp_dict.get(cam_id + "_frame_received", None)
            if index is not None:
                self.camera_dict[cam_id].set_frame_index(index)
            data_dict = self.camera_dict[cam_id].read_camera(correct_timestamp=timestamp)

            # Process Returned Data #
            if data_dict is None:
                return None
            for key in data_dict:
                full_obs_dict[key].update(data_dict[key])

        return full_obs_dict

    def disable_cameras(self):
        for camera in self.camera_dict.values():
            camera.disable_camera()
