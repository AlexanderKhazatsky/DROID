import json
import os
import numpy as np
import torch
from copy import deepcopy

from droid.controllers.oculus_controller import VRPolicy
from droid.evaluation.policy_wrapper import PolicyWrapperRobomimic
from droid.robot_env import RobotEnv
from droid.user_interface.data_collector import DataCollecter
from droid.user_interface.gui import RobotGUI

import robomimic.utils.file_utils as FileUtils
import robomimic.utils.torch_utils as TorchUtils
import robomimic.utils.tensor_utils as TensorUtils

import cv2


# TODO cleanup
class TempVRPolicy:
    def __init__(
        self,
        right_controller: bool = True,
        max_lin_vel: float = 1,
        max_rot_vel: float = 1,
        max_gripper_vel: float = 1,
        spatial_coeff: float = 1,
        pos_action_gain: float = 5,
        rot_action_gain: float = 2,
        gripper_action_gain: float = 3,
        rmat_reorder: list = [-2, -1, -3, 4],
    ):
        accepted_operator_positions = ['front', 'back']

        self.oculus_reader = None
        self.vr_to_global_mat = np.eye(4)
        self.max_lin_vel = max_lin_vel
        self.max_rot_vel = max_rot_vel
        self.max_gripper_vel = max_gripper_vel
        self.spatial_coeff = spatial_coeff
        self.pos_action_gain = pos_action_gain
        self.rot_action_gain = rot_action_gain
        self.gripper_action_gain = gripper_action_gain
        rmat_reorder = [2, 1, -3, 4]
        self.global_to_env_mat = None
        self.controller_id = "r" if right_controller else "l"
        self.reset_orientation = True
        self.reset_state()


    def reset_state(self):
        self._state = {
            "poses": {},
            "buttons": {"A": False, "B": False},
            "movement_enabled": False,
            "controller_on": True,
        }
        self.update_sensor = True
        self.reset_origin = True
        self.robot_origin = None
        self.vr_origin = None
        self.vr_state = None

    def _update_internal_state(self, num_wait_sec=5, hz=50):
        pass

    def _process_reading(self):
        pass

    def _limit_velocity(self, lin_vel, rot_vel, gripper_vel):
        return None, None, None

    def _calculate_action(self, state_dict, include_info=False):
        return None

    def get_info(self):
        return {
            "success": False,
            "failure": False,
            "movement_enabled": True,
            "controller_on": True,
        }

    def forward(self, obs_dict, include_info=False):
        return self._calculate_action(obs_dict["robot_state"], include_info=include_info)


import zerorpc
class TempServerInterface:
    def __init__(self, ip_address="127.0.0.1", launch=True):
        self.ip_address = ip_address
        self.establish_connection()

    def establish_connection(self):
        self.server = zerorpc.Client(heartbeat=20)
        pass

    def launch_controller(self):
        self.server.launch_controller()

    def launch_robot(self):
        self.server.launch_robot()

    def kill_controller(self):
        self.server.kill_controller()

    def update_command(self, command, action_space="cartesian_velocity", gripper_action_space="velocity", blocking=False):
        action_dict = self.server.update_command(command.tolist(), action_space, blocking)
        return action_dict

    def create_action_dict(self, command, action_space="cartesian_velocity"):
        action_dict = self.server.create_action_dict(command.tolist(), action_space)
        return action_dict

    def update_pose(self, command, velocity=True, blocking=False):
        self.server.update_pose(command.tolist(), velocity, blocking)

    def update_joints(self, command, velocity=True, blocking=False, cartesian_noise=None):
        if cartesian_noise is not None:
            cartesian_noise = cartesian_noise.tolist()
        self.server.update_joints(command.tolist(), velocity, blocking, cartesian_noise)

    def update_gripper(self, command, velocity=True, blocking=False):
        self.server.update_gripper(command, velocity, blocking)

    def get_ee_pose(self):
        return np.array(self.server.get_ee_pose())

    def get_joint_positions(self):
        return np.array(self.server.get_joint_positions())

    def get_joint_velocities(self):
        return np.array(self.server.get_joint_velocities())

    def get_gripper_state(self):
        return self.server.get_gripper_state()

    def get_robot_state(self):
        return self.server.get_robot_state()

import gym
hand_camera_id = '138422074005'
static_camera_id = '140122076178'
from droid.calibration.calibration_utils import load_calibration_info
from droid.camera_utils.info import camera_type_dict
from droid.camera_utils.wrappers.multi_camera_wrapper import MultiCameraWrapper
from droid.misc.parameters import hand_camera_id, nuc_ip
from droid.misc.server_interface import ServerInterface
from droid.misc.time import time_ms
from droid.misc.transformations import change_pose_frame
class TempRobotEnv(gym.Env):
    def __init__(self, action_space="cartesian_velocity", gripper_action_space=None, camera_kwargs={}, do_reset=True):
        # Initialize Gym Environment
        super().__init__()

        # Define Action Space #
        assert action_space in ["cartesian_position", "joint_position", "cartesian_velocity", "joint_velocity"]
        self.action_space = action_space
        self.gripper_action_space = gripper_action_space
        self.check_action_range = "velocity" in action_space

        # Robot Configuration
        self.reset_joints = np.array([0, 0.06, 0, -2.3,  0, 2.35, 0.8])
        self.randomize_low = np.array([-0.05, -0.05, -0.05, -0.15, -0.15, -0.15])
        self.randomize_high = np.array([0.05, 0.05, 0.05, 0.15, 0.15, 0.15])
        self.DoF = 7 if ('cartesian' in action_space) else 8
        self.control_hz = 5

        nuc_ip = '172.16.0.7'
        from droid.calibration.calibration_utils import load_calibration_info
        from droid.camera_utils.info import camera_type_dict
        from droid.camera_utils.wrappers.multi_camera_wrapper import MultiCameraWrapper
        from droid.misc.parameters import hand_camera_id, nuc_ip
        from droid.misc.server_interface import ServerInterface
        from droid.misc.time import time_ms
        from droid.misc.transformations import change_pose_frame
        self._robot = TempServerInterface(ip_address=nuc_ip)

        # Create Cameras
        self.camera_reader = MultiCameraWrapper(camera_kwargs)
        self.calibration_dict = load_calibration_info()
        self.camera_type_dict = camera_type_dict

        # Reset Robot
        if do_reset:
            self.reset()

    def step(self, action):
        # Check Action
        assert len(action) == self.DoF
        if self.check_action_range:
            assert (action.max() <= 1) and (action.min() >= -1), f'action: {action}'

        # Update Robot
        action_info = self.update_robot(
            action,
            action_space=self.action_space,
            gripper_action_space=self.gripper_action_space,
        )

        # Return Action Info
        return action_info

    def reset(self, randomize=False):
        pass

    def update_robot(self, action, action_space="cartesian_velocity", gripper_action_space=None, blocking=False):
        pass

    def create_action_dict(self, action):
        return None

    def read_cameras(self):
        camera_obs = {
            "image": {
                "138422074005": np.zeros((128,128,3), dtype=np.uint8),
                "140122076178": np.zeros((128,128,3), dtype=np.uint8)
            }
        }
        camera_timestamp = {}
        return camera_obs, camera_timestamp

    def get_state(self):
        state_dict = {
            "cartesian_position": np.zeros((6,)),
            "gripper_position": 0., # should be single float, not array
            "joint_positions": [0,0,0,0,0,0,0],
            "joint_velocities": [0,0,0,0,0,0,0],
            "joint_torques_computed": [0,0,0,0,0,0,0],
            "prev_joint_torques_computed": [0,0,0,0,0,0,0],
            "prev_joint_torques_computed_safened": [0,0,0,0,0,0,0],
            "motor_torques_measured": [0,0,0,0,0,0,0],
            "prev_controller_latency_ms": [0,0,0,0,0,0,0],
            "prev_command_successful": True,
        }

        import time
        timestamp_dict = {
            "robot_timestamp_seconds": time.time(),
            "robot_timestamp_nanos": time.time(),
        }
        return state_dict, timestamp_dict

    def get_camera_extrinsics(self, state_dict):
        # Adjust gripper camere by current pose
        extrinsics = deepcopy(self.calibration_dict)
        for cam_id in self.calibration_dict:
            if hand_camera_id not in cam_id:
                continue
            gripper_pose = state_dict["cartesian_position"]
            extrinsics[cam_id + "_gripper_offset"] = extrinsics[cam_id]
            extrinsics[cam_id] = extrinsics[cam_id]
        return extrinsics

    def get_observation(self):
        obs_dict = {"timestamp": {}}

        # Robot State #
        state_dict, timestamp_dict = self.get_state()
        obs_dict["robot_state"] = state_dict
        obs_dict["timestamp"]["robot_state"] = timestamp_dict

        # Camera Readings #
        camera_obs, camera_timestamp = self.read_cameras()
        obs_dict.update(camera_obs)
        obs_dict["timestamp"]["cameras"] = camera_timestamp

        # Camera Info #
        obs_dict["camera_type"] = deepcopy(self.camera_type_dict)
        extrinsics = self.get_camera_extrinsics(state_dict)
        obs_dict["camera_extrinsics"] = extrinsics

        intrinsics = {}
        for cam in self.camera_reader.camera_dict.values():
            cam_intr_info = cam.get_intrinsics()
            for (full_cam_id, info) in cam_intr_info.items():
                intrinsics[full_cam_id] = info["cameraMatrix"]
        obs_dict["camera_intrinsics"] = intrinsics

        return obs_dict


def eval_launcher(variant, run_id, exp_id):
    # Get Directory #
    dir_path = os.path.dirname(os.path.realpath(__file__))

    # Prepare Log Directory #
    variant["exp_name"] = os.path.join(variant["exp_name"], "run{0}/id{1}/".format(run_id, exp_id))
    log_dir = os.path.join(dir_path, "../../evaluation_logs", variant["exp_name"])

    # Set Random Seeds #
    torch.manual_seed(variant["seed"])
    np.random.seed(variant["seed"])

    # Set Compute Mode #
    use_gpu = variant.get("use_gpu", False)
    torch.device("cuda:0" if use_gpu else "cpu")

    ckpt_path = variant["ckpt_path"]

    device = TorchUtils.get_torch_device(try_to_use_cuda=True)
    ckpt_dict = FileUtils.maybe_dict_from_checkpoint(ckpt_path=ckpt_path)
    config = json.loads(ckpt_dict["config"])

    ### infer image size ###
    for obs_key in ckpt_dict["shape_metadata"]["all_shapes"].keys():
        if 'static_image' in obs_key:
            imsize = max(ckpt_dict["shape_metadata"]["all_shapes"][obs_key])
            break

    ckpt_dict["config"] = json.dumps(config)
    policy, _ = FileUtils.policy_from_checkpoint(ckpt_dict=ckpt_dict, device=device, verbose=True)
    policy.goal_mode = config["train"]["goal_mode"]
    policy.eval_mode = True

    # determine the action space (relative or absolute)
    action_keys = config["train"]["action_keys"]
    if "action/rel_pos" in action_keys:
        action_space = "cartesian_velocity"
        for k in action_keys:
            assert not k.startswith("action/abs_")
    elif "action/abs_pos" in action_keys:
        action_space = "cartesian_position"
        for k in action_keys:
            assert not k.startswith("action/rel_")
    else:
        raise ValueError

    # determine the action space for the gripper
    if "action/gripper_velocity" in action_keys:
        gripper_action_space = "velocity"
    elif "action/gripper_position" in action_keys:
        gripper_action_space = "position"
    else:
        raise ValueError

    # Prepare Policy Wrapper #
    data_processing_kwargs = dict(
        timestep_filtering_kwargs=dict(
            action_space=action_space,
            gripper_action_space=gripper_action_space,
            robot_state_keys=["cartesian_position", "gripper_position", "joint_positions"],
            # camera_extrinsics=[],
        ),
        image_transform_kwargs=dict(
            remove_alpha=True,
            bgr_to_rgb=True,
            to_tensor=True,
            augment=False,
        ),
    )
    timestep_filtering_kwargs = data_processing_kwargs.get("timestep_filtering_kwargs", {})
    image_transform_kwargs = data_processing_kwargs.get("image_transform_kwargs", {})

    policy_data_processing_kwargs = {}
    policy_timestep_filtering_kwargs = policy_data_processing_kwargs.get("timestep_filtering_kwargs", {})
    policy_image_transform_kwargs = policy_data_processing_kwargs.get("image_transform_kwargs", {})

    policy_timestep_filtering_kwargs.update(timestep_filtering_kwargs)
    policy_image_transform_kwargs.update(image_transform_kwargs)

    fs = config["train"]["frame_stack"]

    wrapped_policy = PolicyWrapperRobomimic(
        policy=policy,
        timestep_filtering_kwargs=policy_timestep_filtering_kwargs,
        image_transform_kwargs=policy_image_transform_kwargs,
        frame_stack=fs,
        eval_mode=True,
    )

    camera_kwargs = dict(
        hand_camera=dict(image=True, concatenate_images=False, resolution=(imsize, imsize), resize_func="cv2"),
        static_camera=dict(image=True, concatenate_images=False, resolution=(imsize, imsize), resize_func="cv2"),
    )
    
    policy_camera_kwargs = {}
    policy_camera_kwargs.update(camera_kwargs)

    env = RobotEnv( # TODO recover
    # env = TempRobotEnv( # TODO delete
        action_space=policy_timestep_filtering_kwargs["action_space"],
        gripper_action_space=policy_timestep_filtering_kwargs["gripper_action_space"],
        camera_kwargs=policy_camera_kwargs
    )
    controller = VRPolicy() # TODO recover
    # controller = TempVRPolicy() # TODO delete

    # Launch GUI #
    data_collector = DataCollecter(
        env=env,
        controller=controller,
        policy=wrapped_policy,
        save_traj_dir=log_dir,
        save_data=variant.get("save_data", True),
    )
    RobotGUI(robot=data_collector)


def get_goal_im(variant, run_id, exp_id):
    # Get Directory #
    dir_path = os.path.dirname(os.path.realpath(__file__))

    # Prepare Log Directory #
    variant["exp_name"] = os.path.join(variant["exp_name"], "run{0}/id{1}/".format(run_id, exp_id))
    log_dir = os.path.join(dir_path, "../../evaluation_logs", variant["exp_name"])

    # Set Random Seeds #
    torch.manual_seed(variant["seed"])
    np.random.seed(variant["seed"])

    # Set Compute Mode #
    use_gpu = variant.get("use_gpu", False)
    torch.device("cuda:0" if use_gpu else "cpu")

    ckpt_path = variant["ckpt_path"]

    device = TorchUtils.get_torch_device(try_to_use_cuda=True)
    ckpt_dict = FileUtils.maybe_dict_from_checkpoint(ckpt_path=ckpt_path)
    config = json.loads(ckpt_dict["config"])

    ### infer image size ###
    imsize = max(ckpt_dict["shape_metadata"]["all_shapes"]["camera/image/hand_camera_left_image"])

    ckpt_dict["config"] = json.dumps(config)
    policy, _ = FileUtils.policy_from_checkpoint(ckpt_dict=ckpt_dict, device=device, verbose=True)

    # determine the action space (relative or absolute)
    action_keys = config["train"]["action_keys"]
    if "action/rel_pos" in action_keys:
        action_space = "cartesian_velocity"
        for k in action_keys:
            assert not k.startswith("action/abs_")
    elif "action/abs_pos" in action_keys:
        action_space = "cartesian_position"
        for k in action_keys:
            assert not k.startswith("action/rel_")
    else:
        raise ValueError

    # determine the action space for the gripper
    if "action/gripper_velocity" in action_keys:
        gripper_action_space = "velocity"
    elif "action/gripper_position" in action_keys:
        gripper_action_space = "position"
    else:
        raise ValueError

    # Prepare Policy Wrapper #
    data_processing_kwargs = dict(
        timestep_filtering_kwargs=dict(
            action_space=action_space,
            gripper_action_space=gripper_action_space,
            robot_state_keys=["cartesian_position", "gripper_position", "joint_positions"],
            # camera_extrinsics=[],
        ),
        image_transform_kwargs=dict(
            remove_alpha=True,
            bgr_to_rgb=True,
            to_tensor=True,
            augment=False,
        ),
    )
    timestep_filtering_kwargs = data_processing_kwargs.get("timestep_filtering_kwargs", {})
    image_transform_kwargs = data_processing_kwargs.get("image_transform_kwargs", {})

    policy_data_processing_kwargs = {}
    policy_timestep_filtering_kwargs = policy_data_processing_kwargs.get("timestep_filtering_kwargs", {})
    policy_image_transform_kwargs = policy_data_processing_kwargs.get("image_transform_kwargs", {})

    policy_timestep_filtering_kwargs.update(timestep_filtering_kwargs)
    policy_image_transform_kwargs.update(image_transform_kwargs)

    wrapped_policy = PolicyWrapperRobomimic(
        policy=policy,
        timestep_filtering_kwargs=policy_timestep_filtering_kwargs,
        image_transform_kwargs=policy_image_transform_kwargs,
        frame_stack=config["train"]["frame_stack"],
        eval_mode=True,
    )

    camera_kwargs = dict(
        hand_camera=dict(image=True, concatenate_images=False, resolution=(imsize, imsize), resize_func="cv2"),
        static_camera=dict(image=True, concatenate_images=False, resolution=(imsize, imsize), resize_func="cv2"),
    )
    
    policy_camera_kwargs = {}
    policy_camera_kwargs.update(camera_kwargs)

    env = RobotEnv(
        action_space=policy_timestep_filtering_kwargs["action_space"],
        gripper_action_space=policy_timestep_filtering_kwargs["gripper_action_space"],
        camera_kwargs=policy_camera_kwargs,
        do_reset=False
    )

    ims = env.read_cameras()[0]["image"]
    if not os.path.exists('eval_params'):
        os.makedirs('eval_params')
    for k in ims.keys():
        image = ims[k]
        cv2.imwrite(f'eval_params/{k}.png', image[:, :, :3])
    return ims
