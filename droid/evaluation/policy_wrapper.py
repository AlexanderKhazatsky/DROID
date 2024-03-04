import numpy as np
import torch

from droid.data_processing.timestep_processing import TimestepProcesser


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

        # a_star = np.cumsum(processed_timestep['observation']['state']) / 7
        # print('Policy Action: ', np_action)
        # print('Expert Action: ', a_star)
        # print('Error: ', np.abs(a_star - np_action).mean())

        # import pdb; pdb.set_trace()
        return np_action
