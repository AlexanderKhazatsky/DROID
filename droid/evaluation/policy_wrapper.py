import numpy as np
import sys
import torch
from collections import deque

from droid.data_processing.timestep_processing import TimestepProcesser
# TODO (@moojink) Hack so that the interpreter can find robomimic
sys.path.append("/iris/u/moojink/prismatic-dev/droid_policy_learning/")
import robomimic.utils.obs_utils as ObsUtils
import robomimic.utils.torch_utils as TorchUtils
import robomimic.utils.tensor_utils as TensorUtils


def converter_helper(data, batchify=True):
    if torch.is_tensor(data):
        pass
    elif isinstance(data, np.ndarray):
        data = torch.from_numpy(data)
    else:
        raise ValueError

    if batchify:
        data = data.unsqueeze(0)
    return data


def np_dict_to_torch_dict(np_dict, batchify=True):
    torch_dict = {}

    for key in np_dict:
        curr_data = np_dict[key]
        if isinstance(curr_data, dict):
            torch_dict[key] = np_dict_to_torch_dict(curr_data)
        elif isinstance(curr_data, np.ndarray) or torch.is_tensor(curr_data):
            torch_dict[key] = converter_helper(curr_data, batchify=batchify)
        elif isinstance(curr_data, list):
            torch_dict[key] = [converter_helper(d, batchify=batchify) for d in curr_data]
        else:
            raise ValueError

    return torch_dict


class PolicyWrapper:
    def __init__(self, policy, timestep_filtering_kwargs, image_transform_kwargs, eval_mode=True):
        self.policy = policy

        if eval_mode:
            self.policy.eval()
        else:
            self.policy.train()

        self.timestep_processor = TimestepProcesser(
            ignore_action=True, **timestep_filtering_kwargs, image_transform_kwargs=image_transform_kwargs
        )

    def forward(self, observation):
        timestep = {"observation": observation}
        processed_timestep = self.timestep_processor.forward(timestep)
        torch_timestep = np_dict_to_torch_dict(processed_timestep)
        action = self.policy(torch_timestep)[0]
        np_action = action.detach().numpy()
        return np_action


class PolicyWrapperRobomimic:
    def __init__(self, policy, timestep_filtering_kwargs, image_transform_kwargs, frame_stack, eval_mode=True, dataset_statistics=None):
        self.policy = policy

        assert eval_mode is True

        self.fs_wrapper = FrameStackWrapper(num_frames=frame_stack)
        self.fs_wrapper.reset()
        self.policy.start_episode()

        self.timestep_processor = TimestepProcesser(
            ignore_action=True, **timestep_filtering_kwargs, image_transform_kwargs=image_transform_kwargs
        )

        self.dataset_statistics = dataset_statistics

    def forward(self, observation, task_label):
        timestep = {"observation": observation}
        processed_timestep = self.timestep_processor.forward(timestep)

        extrinsics_dict = processed_timestep["extrinsics_dict"]
        intrinsics_dict = processed_timestep["intrinsics_dict"]
        assert len(processed_timestep["observation"]["camera"]["image"]["static_camera"].shape) == 3

        if "state" in observation["robot_state"]:
            obs = {
                "state": observation["robot_state"]["state"],
                "image": processed_timestep["observation"]["camera"]["image"]["static_camera"],
            }
        elif "cartesian_position" in observation["robot_state"]:
            obs = {
                "robot_state/cartesian_position": observation["robot_state"]["cartesian_position"],
                "robot_state/gripper_position": [observation["robot_state"]["gripper_position"]], # wrap as array, raw data is single float
                "static_image": processed_timestep["observation"]["camera"]["image"]["static_camera"],
            }
        else:
            raise ValueError("Missing robot proprio state in input!")

        # set item of obs as np.array
        for k in obs:
            obs[k] = np.array(obs[k])

        self.fs_wrapper.add_obs(obs)
        obs_history = self.fs_wrapper.get_obs_history()
        obs_history["task_label"] = task_label
        action = self.policy(obs_history)

        return action

    def reset(self):
        self.fs_wrapper.reset()
        self.policy.start_episode()
    

class FrameStackWrapper:
    """
    Wrapper for frame stacking observations during rollouts. The agent
    receives a sequence of past observations instead of a single observation
    when it calls @env.reset, @env.reset_to, or @env.step in the rollout loop.
    """
    def __init__(self, num_frames):
        """
        Args:
            num_frames (int): number of past observations (including current observation)
                to stack together. Must be greater than 1 (otherwise this wrapper would
                be a no-op).
        """
        self.num_frames = num_frames

        ### TODO: add action padding option + adding action to obs to include action history in obs ###

        # keep track of last @num_frames observations for each obs key
        self.obs_history = None

    def _set_initial_obs_history(self, init_obs):
        """
        Helper method to get observation history from the initial observation, by
        repeating it.

        Returns:
            obs_history (dict): a deque for each observation key, with an extra
                leading dimension of 1 for each key (for easy concatenation later)
        """
        self.obs_history = {}
        for k in init_obs:
            self.obs_history[k] = deque(
                [init_obs[k][None] for _ in range(self.num_frames)], 
                maxlen=self.num_frames,
            )

    def reset(self):
        self.obs_history = None

    def get_obs_history(self):
        """
        Helper method to convert internal variable @self.obs_history to a 
        stacked observation where each key is a numpy array with leading dimension
        @self.num_frames.
        """
        # concatenate all frames per key so we return a numpy array per key
        if self.num_frames == 1:
            return { k : np.concatenate(self.obs_history[k], axis=0)[0] for k in self.obs_history }
        else:
            return { k : np.concatenate(self.obs_history[k], axis=0) for k in self.obs_history }

    def add_obs(self, obs):
        if self.obs_history is None:
            self._set_initial_obs_history(obs)

        # update frame history
        for k in obs:
            # make sure to have leading dim of 1 for easy concatenation
            self.obs_history[k].append(obs[k][None])
