from r2d2.camera_utils.wrappers.multi_camera_wrapper import MultiCameraWrapper
from r2d2.calibration.calibration_utils import load_calibration_info
from r2d2.misc.transformations import change_pose_frame
from r2d2.misc.server_interface import ServerInterface
from r2d2.misc.parameters import robot_ip, hand_camera_id
from r2d2.misc.time import time_ms
from copy import deepcopy
import numpy as np
import time
import gym


class RobotEnv(gym.Env):
    
    def __init__(self):
        
        # Initialize Gym Environment
        super().__init__()

        # Physics
        self.max_lin_vel = 2.0
        self.max_rot_vel = 2.0
        self.max_gripper_vel = 4.0
        self.DoF = 6
        self.hz = 15

        # Robot Configuration
        self.reset_joints = np.array([0., -np.pi/4,  0, -3/4 * np.pi, 0,  np.pi/2, 0.])
        if robot_ip is None:
            from franka.robot import FrankaRobot
            self._robot = FrankaRobot()
        else:
            self._robot = ServerInterface(ip_address=robot_ip)

        # Create Cameras
        self.camera_reader = MultiCameraWrapper()
        self.calibration_dict = load_calibration_info()

        # Reset Robot
        self.reset()

    def step(self, action):
        # Check Action
        assert len(action) == (self.DoF + 1)
        assert (action.max() <= 1) and (action.min() >= -1)

        # Update Robot
        action = self._limit_velocity(action)
        action_info = self.update_robot(action, action_space='cartesian', delta=True)

        # Return Action Info
        return action_info

    def _limit_velocity(self, action):
        """Scales down the linear and angular magnitudes of the action"""
        lin_vel, rot_vel, gripper_vel = action[:3], action[3:6], action[6]
        
        lin_vel_norm = np.linalg.norm(lin_vel)
        rot_vel_norm = np.linalg.norm(rot_vel)
        gripper_vel_norm = np.linalg.norm(gripper_vel)
        
        if lin_vel_norm > 1: lin_vel = lin_vel / lin_vel_norm
        if rot_vel_norm > 1: rot_vel = rot_vel / rot_vel_norm
        if gripper_vel_norm > 1: gripper_vel = gripper_vel / gripper_vel_norm
        
        lin_vel = lin_vel * self.max_lin_vel / self.hz
        rot_vel = rot_vel * self.max_rot_vel / self.hz
        gripper_vel = gripper_vel * self.max_gripper_vel / self.hz

        return np.concatenate([lin_vel, rot_vel, [gripper_vel]])

    def reset(self, joints=None):
        if joints is None: joints = self.reset_joints
        self._robot.update_gripper(0, delta=False, blocking=True)
        self._robot.update_joints(joints, delta=False, blocking=True)

    def update_robot(self, action, action_space='cartesian', delta=True, blocking=False):
        action_info = self._robot.update_command(action, action_space=action_space, delta=delta, blocking=blocking)
        return action_info

    def read_cameras(self, image=True, depth=False, pointcloud=False):
        return self.camera_reader.read_cameras(image=True, depth=False, pointcloud=False)

    def get_state(self):
        timestamp_dict = {'read_start': time_ms()}
        state_dict = self._robot.get_robot_state()
        timestamp_dict['read_end'] = time_ms()
        return state_dict, timestamp_dict

    def get_camera_extrinsics(self, state_dict):
        # Adjust gripper camere by current pose
        extrinsics = deepcopy(self.calibration_dict)
        for cam_id in self.calibration_dict:
            if hand_camera_id not in cam_id: continue
            gripper_pose = state_dict['ee_state'][:6]
            extrinsics[cam_id + '_gripper_offset'] = extrinsics[cam_id]
            extrinsics[cam_id] = change_pose_frame(extrinsics[cam_id], gripper_pose)
        return extrinsics

    def get_observation(self, robot_state=True, camera_extrinsics=True, image=True, depth=False, pointcloud=False):
        read_cameras = any([image, depth, pointcloud])
        obs_dict = {'timestamp': {}}

        if robot_state:
            state_dict, timestamp_dict = self.get_state()
            obs_dict['robot_state'] = state_dict
            obs_dict['timestamp']['robot_state'] = timestamp_dict
        if read_cameras:
            camera_obs, camera_timestamp = self.read_cameras(
                image=image, depth=depth, pointcloud=pointcloud)
            obs_dict.update(camera_obs)
            obs_dict['timestamp']['cameras'] = camera_timestamp
        if camera_extrinsics:
            assert robot_state
            extrinsics = self.get_camera_extrinsics(state_dict)
            obs_dict['camera_extrinsics'] = extrinsics

        return obs_dict
