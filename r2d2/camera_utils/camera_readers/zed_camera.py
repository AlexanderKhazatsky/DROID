from copy import deepcopy

import cv2
import numpy as np

from r2d2.misc.parameters import hand_camera_id
from r2d2.misc.time import time_ms

try:
    import pyzed.sl as sl
except ModuleNotFoundError:
    print("WARNING: You have not setup the ZED cameras, and currently cannot use them")


def gather_zed_cameras():
    all_zed_cameras = []
    try:
        cameras = sl.Camera.get_device_list()
    except NameError:
        return []

    for cam in cameras:
        cam = ZedCamera(cam)
        all_zed_cameras.append(cam)

    return all_zed_cameras


resize_func_map = {"cv2": cv2.resize, None: None}


class ZedCamera:
    def __init__(self, camera):
        # Save Parameters #
        self.serial_number = str(camera.serial_number)
        self.is_hand_camera = self.serial_number == hand_camera_id
        self.current_mode = None
        self._extriniscs = {}

    def set_reading_parameters(
        self,
        image=True,
        depth=False,
        pointcloud=False,
        concatenate_images=False,
        resolution=(0, 0),
        resize_func=None,
    ):
        # Non-Permenant Values #
        self.traj_image = image
        self.traj_concatenate_images = concatenate_images
        self.traj_resolution = resolution

        # Permenant Values #
        self.depth = depth
        self.pointcloud = pointcloud
        self.resize_func = resize_func_map[resize_func]

    ### Camera Modes ###
    def set_calibration_mode(self):
        # Only Proceed If Necesary
        if self._current_mode == 'calibration': return

        # Update Relevant Info #
        self.image = True
        self.concatenate_images = False
        self.skip_reading = False
        self.current_mode = "calibration"
        self.zed_resolution = sl.Resolution(0, 0)
        self.resizer_resolution = (0, 0)

        # Activate High Resolution Mode #
        init_params = sl.InitParameters(
            depth_minimum_distance=0.1,
            camera_resolution=sl.RESOLUTION.HD2K,
            camera_fps=15)
        self._configure_camera(init_params)

    def set_trajectory_mode(self):
        # Only Proceed If Necesary
        if self._current_mode == 'trajectory': return

        # Update Relevant Info #
        self.image = self.traj_image
        self.concatenate_images = self.traj_concatenate_images
        self.skip_reading = not any([self.image, self.depth, self.pointcloud])
        self.current_mode = "trajectory"

        if self.resize_func is None:
            self.zed_resolution = sl.Resolution(*self.traj_resolution)
            self.resizer_resolution = (0, 0)
        else:
            self.zed_resolution = sl.Resolution(0, 0)
            self.resizer_resolution = self.traj_resolution

        # Activate Low Resolution Mode #
        init_params = sl.InitParameters(
            depth_minimum_distance=0.1,
            camera_resolution=sl.RESOLUTION.HD720,
            camera_fps=60)
        self._configure_camera(init_params)

    def _configure_camera(self, init_params):
        # Set Camera #
        init_params.set_from_serial_number(int(self.serial_number))
        self.latency = int(2.5 * (1e3 / init_params.camera_fps))

        # Close Existing Camera #
        self.disable_camera()

        # Initialize Readers #
        self._cam = sl.Camera()
        self._sbs_img = sl.Mat()
        self._left_img = sl.Mat()
        self._right_img = sl.Mat()
        self._left_depth = sl.Mat()
        self._right_depth = sl.Mat()
        self._left_pointcloud = sl.Mat()
        self._right_pointcloud = sl.Mat()

        # Open Camera #
        print("Opening Zed: ", self.serial_number)
        self._cam.open(init_params)
        self._runtime = sl.RuntimeParameters()

        # Save Intrinsics #
        calib_params = self._cam.get_camera_information().camera_configuration.calibration_parameters
        self._intrinsics = {
            self.serial_number + "_left": self._process_intrinsics(calib_params.left_cam),
            self.serial_number + "_right": self._process_intrinsics(calib_params.right_cam),
        }

    ### Calibration Utilities ###
    def _process_intrinsics(self, params):
        intrinsics = {}
        intrinsics["cameraMatrix"] = np.array([[params.fx, 0, params.cx], [0, params.fy, params.cy], [0, 0, 1]])
        intrinsics["distCoeffs"] = np.array(list(params.disto))
        return intrinsics

    def get_intrinsics(self):
        return deepcopy(self._intrinsics)

    ### Recording Utilities ###
    def start_recording(self, filename):
        assert filename.endswith(".svo")
        recording_param = sl.RecordingParameters(filename, sl.SVO_COMPRESSION_MODE.H265)
        err = self._cam.enable_recording(recording_param)
        assert err == sl.ERROR_CODE.SUCCESS

    def stop_recording(self):
        self._cam.disable_recording()

    ### Basic Camera Utilities ###
    def _process_frame(self, frame):
        frame = deepcopy(frame.get_data())
        if self.resizer_resolution == (0, 0):
            return frame
        return self.resize_func(frame, self.resizer_resolution)

    def read_camera(self):
        # Skip if Read Unnecesary #
        if self.skip_reading:
            return {}, {}

        # Read Camera #
        timestamp_dict = {self.serial_number + "_read_start": time_ms()}
        err = self._cam.grab(self._runtime)
        if err != sl.ERROR_CODE.SUCCESS:
            return None
        timestamp_dict[self.serial_number + "_read_end"] = time_ms()

        # Benchmark Latency #
        received_time = self._cam.get_timestamp(sl.TIME_REFERENCE.IMAGE).get_milliseconds()
        timestamp_dict[self.serial_number + "_frame_received"] = received_time
        timestamp_dict[self.serial_number + "_estimated_capture"] = received_time - self.latency

        # Return Data #
        data_dict = {}

        if self.image:
            if self.concatenate_images:
                self._cam.retrieve_image(self._sbs_img, sl.VIEW.SIDE_BY_SIDE, resolution=self.zed_resolution)
                data_dict["image"] = {self.serial_number: self._process_frame(self._sbs_img)}
            else:
                self._cam.retrieve_image(self._left_img, sl.VIEW.LEFT, resolution=self.zed_resolution)
                self._cam.retrieve_image(self._right_img, sl.VIEW.RIGHT, resolution=self.zed_resolution)
                data_dict["image"] = {
                    self.serial_number + "_left": self._process_frame(self._left_img),
                    self.serial_number + "_right": self._process_frame(self._right_img),
                }
        # if self.depth:
        # 	self._cam.retrieve_measure(self._left_depth, sl.MEASURE.DEPTH, resolution=self.resolution)
        # 	self._cam.retrieve_measure(self._right_depth, sl.MEASURE.DEPTH_RIGHT, resolution=self.resolution)
        # 	data_dict['depth'] = {
        # 		self.serial_number + '_left': self._left_depth.get_data().copy(),
        # 		self.serial_number + '_right': self._right_depth.get_data().copy()}
        # if self.pointcloud:
        # 	self._cam.retrieve_measure(self._left_pointcloud, sl.MEASURE.XYZRGBA, resolution=self.resolution)
        # 	self._cam.retrieve_measure(self._right_pointcloud, sl.MEASURE.XYZRGBA_RIGHT, resolution=self.resolution)
        # 	data_dict['pointcloud'] = {
        # 		self.serial_number + '_left': self._left_pointcloud.get_data().copy(),
        # 		self.serial_number + '_right': self._right_pointcloud.get_data().copy()}

        return data_dict, timestamp_dict

    def disable_camera(self):
        if self.current_mode == "disabled":
            return
        if hasattr(self, "_cam"):
            print("Closing Zed: ", self.serial_number)
            self._cam.close()
        self.current_mode = "disabled"

    def is_running(self):
        return self.current_mode != "disabled"
