from r2d2.camera_utils.wrappers.multi_camera_wrapper import MultiCameraWrapper
from r2d2.misc.transformations import add_angles, angle_diff
from r2d2.misc.server_interface import ServerInterface
from collections import defaultdict
import numpy as np
import time
import gym



class RobotEnv(gym.Env):
    
    def __init__(self, ip_address=None):
        
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
        if ip_address is None:
            from franka.robot import FrankaRobot
            self._robot = FrankaRobot()
        else:
            self._robot = ServerInterface(ip_address=ip_address)

        # Create Cameras
        self.camera_reader = MultiCameraWrapper()

        self.delay = defaultdict(list)

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
        return self.get_observation()

    def update_robot(self, action, action_space='cartesian', delta=True):
        action_info = self._robot.update_command(action, action_space=action_space, delta=delta)
        return action_info

    def get_images(self):
        return self.camera_reader.read_cameras()

    def get_state(self):
        state_dict = self._robot.get_robot_state()
        return state_dict, time.time()

    def get_observation(self, include_images=True, include_robot_state=True):
        obs_dict = {}
        timestamp_dict = {}

        if include_images:
            camera_dict, camera_timestamp_dict = self.get_images()

            # for cam in camera_timestamp_dict:
            #     self.delay[cam].append(time.time() - camera_timestamp_dict[cam])

            obs_dict['camera_dict'] = camera_dict
            timestamp_dict['cameras'] = camera_timestamp_dict
        if include_robot_state:
            state_dict, read_time = self.get_state()
            obs_dict['state_dict'] = state_dict
            timestamp_dict['robot_state'] = read_time

        # if np.random.uniform() < 0.05:
        #     for key in self.delay:
        #         print(np.array(self.delay[key]).mean())

        return obs_dict, timestamp_dict

    # def is_robot_reset(self, epsilon=0.1):
    #     curr_joints = self._robot.get_joint_positions()
    #     joint_dist = np.linalg.norm(curr_joints - self.reset_joints)
    #     return joint_dist < epsilon
