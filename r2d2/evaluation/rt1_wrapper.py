from pathlib import Path
from PIL import Image
import tensorflow as tf
import numpy as np
from tf_agents.policies import py_tf_eager_policy
import tf_agents
from tf_agents.trajectories import time_step as ts

from r2d2.user_interface.eval_gui import GoalCondPolicy

def resize(image):
    image = tf.image.resize_with_pad(image, target_width=320, target_height=256)
    image = tf.cast(image, tf.uint8)
    return image


def load_goals():
    return (resize(tf.convert_to_tensor(np.random.rand(128, 128, 3))),
            resize(tf.convert_to_tensor(np.random.rand(128, 128, 3))))


class RT1Policy(GoalCondPolicy):
    def __init__(self, checkpoint_path, goal_images=None, camera_obs_keys=[]):
        """goal_images is a tuple of two goal images."""
        self._policy = py_tf_eager_policy.SavedModelPyTFEagerPolicy(
            model_path=checkpoint_path,
            load_specs_from_pbtxt=True,
            use_tf_function=True)
        self.obs = self._run_dummy_inference()
        self._goal_images = goal_images
        self._policy_state = self._policy.get_initial_state(batch_size=1)
        self._camera_obs_keys = camera_obs_keys

    def _run_dummy_inference(self):
        observation = tf_agents.specs.zero_spec_nest(
            tf_agents.specs.from_spec(self._policy.time_step_spec.observation))
        tfa_time_step = ts.transition(observation, reward=np.zeros((), dtype=np.float32))
        policy_state = self._policy.get_initial_state(batch_size=1)
        action = self._policy.action(tfa_time_step, policy_state)
        return observation

    def forward(self, observation):
        # construct observation
        if not self._goal_images:
            # throw exception saying no goal images were provided
            raise Exception("No goal images were provided")

        self.obs['goal_image'] = self._goal_images[0]
        self.obs['goal_image1'] = self._goal_images[1]

        for i, key in enumerate(self._camera_obs_keys):
            if i == 0:
                self.obs['image'] = resize(tf.convert_to_tensor(observation['image'][key][:, :, :3].copy()[..., ::-1]))
            elif i == 1:
                self.obs['image1'] = resize(tf.convert_to_tensor(observation['image'][key][:, :, :3].copy()[..., ::-1]))

        tfa_time_step = ts.transition(self.obs, reward=np.zeros((), dtype=np.float32))

        policy_step = self._policy.action(tfa_time_step, self._policy_state)
        self._policy_state = policy_step.state
        action = np.concatenate([policy_step.action['world_vector'],
                               policy_step.action['rotation_delta'],
                               policy_step.action['gripper_closedness_action']])
        print(f"returning action: {action}")
        return action
    
    def load_goal_imgs(self, img_dict):
            goal_images = []
            for key in self._camera_obs_keys:
                goal_images.append(resize(tf.convert_to_tensor(img_dict[key])))
            self._goal_images = goal_images
    
    def load_lang(self, text):
        return super().load_lang(text)