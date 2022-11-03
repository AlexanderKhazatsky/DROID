'''
Xbox Controller Class
USE DETAILS: Create an instance, call get_action() to get action, and get_info() for data collection information
QUESTIONS: If you have questions, reach out to Sasha :)
'''

import pygame
import numpy as np

pygame.init()
pygame.joystick.init()

class XboxController:

    def __init__(self, env):
        # Initialize Controller
        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()

        # Control Parameters
        self.threshold = 0.1
        self.DoF = env._DoF

        # Save Gripper
        self.gripper_closed = False
        self.button_resetted = True

    def get_action(self):
        pygame.event.get()

        # XYZ Dimensions
        x = - self.joystick.get_axis(1)
        y = - self.joystick.get_axis(0)
        z = (self.joystick.get_axis(5) - self.joystick.get_axis(2)) / 2

        # Orientation Dimensions
        yaw = self.joystick.get_axis(3)
        pitch = -self.joystick.get_axis(4)
        roll = self.joystick.get_button(4) - self.joystick.get_button(5)

        # Process Pose Action
        pose_action = np.array([x, y, z, roll, pitch, yaw])[:self.DoF]
        pose_action[np.abs(pose_action) < self.threshold] = 0.

        # Process Gripper Action
        self._update_gripper_state(self.joystick.get_button(0))
        gripper_action = [self.gripper_closed * 2 - 1]

        #return np.array([x, y, z, pitch, roll, gripper])
        return np.concatenate([pose_action, gripper_action])

    def get_info(self):
        pygame.event.get()
        reset_episode = self.joystick.get_button(15)
        save_episode = self.joystick.get_button(11)
        delete_episode = self.joystick.get_button(16)
        
        if reset_episode:
            self.gripper_closed = False
            self.button_resetted = True

        return {'reset_episode': reset_episode, 'save_episode': save_episode, 'delete_episode': delete_episode}

    def _update_gripper_state(self, toggle_gripper):
        if toggle_gripper and self.button_resetted:
            self.gripper_closed = not self.gripper_closed
            self.button_resetted = False

        if not toggle_gripper:
            self.button_resetted = True


