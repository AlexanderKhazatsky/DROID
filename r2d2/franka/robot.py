''' Robot Server Environment Wrapper'''

# ROBOT SPECIFIC IMPORTS
from polymetis import RobotInterface, GripperInterface
from r2d2.robot_ik.robot_ik_solver import RobotIKSolver
import grpc

# UTILITY SPECIFIC IMPORTS
from r2d2.misc.transformations import euler_to_quat, quat_to_euler
from r2d2.misc.subprocess_utils import run_terminal_command, run_threaded_command
from r2d2.misc.parameters import sudo_password
import numpy as np
import torch
import time
import os


class FrankaRobot:

    def launch_controller(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self._robot_process = run_terminal_command(
            'echo ' + sudo_password + ' | sudo -S ' + 'bash ' + dir_path + '/launch_robot.sh')
        self._gripper_process = run_terminal_command(
            'echo ' + sudo_password + ' | sudo -S ' + 'bash ' + dir_path + '/launch_gripper.sh')
        time.sleep(5)

    def launch_robot(self):
        self._robot = RobotInterface(ip_address="localhost")
        self._gripper = GripperInterface(ip_address="localhost")
        self._max_gripper_width = self._gripper.metadata.max_width
        self._ik_solver = RobotIKSolver()

    def kill_controller(self):
        self._robot_process.terminate()
        self._gripper_process.terminate()

    def update_command(self, action, action_space='cartesian'):
        assert action_space in ['joint', 'cartesian']
        action_info = {}

        action_info['gripper'] = action[-1]
        action_info[action_space] = action[:-1]
        if action_space == 'cartesian':
            joint_delta, success = self._ik_solver.compute(action[:-1], robot_state=self.get_robot_state())
            action_info['joint'] = joint_delta.tolist()

        self.update_joints(action_info['joint'], delta=True, blocking=False)
        self.update_gripper(action_info['gripper'], delta=True, blocking=False)

        return action_info

    def update_joints(self, joints, delta=False, blocking=False):
        desired_joints = torch.Tensor(joints)
        if delta: desired_joints += self._robot.get_joint_positions()

        def helper_non_blocking():
            if not self._robot.is_running_policy():
                self._robot.start_cartesian_impedance()

            try: self._robot.update_desired_joint_positions(desired_joints)
            except grpc.RpcError: pass

        if blocking:
            if self._robot.is_running_policy():
                self._robot.terminate_current_policy()
                time.sleep(2)
            try: self._robot.move_to_joint_positions(desired_joints)
            except grpc.RpcError: pass
        else:
            run_threaded_command(helper_non_blocking)

    def update_gripper(self, close_percentage, delta=True, blocking=False):
        if delta: close_percentage += self.get_gripper_state()
        close_percentage = float(np.clip(close_percentage, 0, 1))

        gripper_cmd = lambda: self._gripper.goto(width=self._max_gripper_width * (1 - close_percentage),
            speed=0.05, force=0.1, blocking=blocking)
        
        if blocking: run_threaded_command(gripper_cmd)
        else: gripper_cmd()

    def get_joint_positions(self):
        return self._robot.get_joint_positions().tolist()

    def get_joint_velocities(self):
        return self._robot.get_joint_velocities().tolist()

    def get_gripper_state(self):
        return 1 - (self._gripper.get_state().width / self._max_gripper_width)

    def get_ee_pose(self):
        pos, quat = self._robot.get_ee_pose()
        angle = quat_to_euler(quat.numpy())
        return np.concatenate([pos, angle]).tolist()

    def get_robot_state(self):
        robot_state = self._robot.get_robot_state()
        gripper_state = self.get_gripper_state()
        pos, quat = self._robot.robot_model.forward_kinematics(torch.Tensor(robot_state.joint_positions))
        ee_state = pos.tolist() + quat_to_euler(quat.numpy()).tolist() + [gripper_state]
        
        return {'ee_state': ee_state,
                'joint_positions': list(robot_state.joint_positions),
                'joint_velocities': list(robot_state.joint_velocities)}
