# ROBOT SPECIFIC IMPORTS
from polymetis import RobotInterface, GripperInterface
from r2d2.robot_ik.robot_ik_solver import RobotIKSolver
import grpc

# UTILITY SPECIFIC IMPORTS
from r2d2.misc.transformations import euler_to_quat, quat_to_euler, add_poses, pose_diff
from r2d2.misc.subprocess_utils import run_terminal_command, run_threaded_command
from r2d2.misc.parameters import sudo_password
import numpy as np
import torch
import time
import os

def create_action_dict(action, action_space, delta, robot_state, ik_solver):
    assert action_space in ['cartesian', 'joint']
    assert delta in [True, False]
    action_dict = {}

    if delta:
        action_dict['gripper_delta'] = action[-1]
        gripper = robot_state['ee_state'][-1] + action[-1]
        action_dict['gripper'] = float(np.clip(gripper, 0, 1))
    else:
        action_dict['gripper'] = action[-1]
        gripper_delta = action[-1] - robot_state['ee_state'][-1]
        action_dict['gripper_delta'] = float(np.clip(gripper_delta, 0, 1))

    if action_space == 'cartesian':
        if delta:
            action_dict['cartesian_delta'] = action[:-1]
            action_dict['cartesian'] = add_poses(action[:-1], robot_state['ee_state'][:-1]).tolist()
        else:
            action_dict['cartesian'] = action[:-1]
            action_dict['cartesian_delta'] = pose_diff(action[:-1], robot_state['ee_state'][:-1]).tolist()
        
        action_dict['joint_delta'] = ik_solver.compute(action_dict['cartesian_delta'], robot_state=robot_state)[0].tolist()
        action_dict['joint'] = (np.array(action_dict['joint_delta']) + np.array(robot_state['joint_positions'])).tolist()

    if action_space == 'joint':
        # NOTE: Joint to cartesian has undefined dynamics due to IK
        if delta:
            action_dict['joint_delta'] = action[:-1]
            action_dict['joint'] = (np.array(action[:-1]) + np.array(robot_state['joint_positions'])).tolist()
        else:
            action_dict['joint'] = action[:-1]
            action_dict['joint_delta'] = (np.array(action[:-1]) - np.array(robot_state['joint_positions'])).tolist()

    return action_dict


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

    def update_command(self, action, action_space='cartesian', delta=True, blocking=False):
        action_dict = create_action_dict(action, action_space=action_space, delta=delta,
            robot_state=self.get_robot_state(), ik_solver=self._ik_solver)
        self.update_joints(action_dict['joint'], delta=False, blocking=blocking)
        self.update_gripper(action_dict['gripper'], delta=False, blocking=blocking)
        return action_dict

    def update_pose(self, pose, delta=False, blocking=False):
        if blocking:
            if delta: pose = add_poses(pose, self.get_ee_pose())
            pos = torch.Tensor(pose[:3])
            quat = torch.Tensor(euler_to_quat(pose[3:6]))

            if self._robot.is_running_policy():
                self._robot.terminate_current_policy()
                time.sleep(2)

            try: self._robot.move_to_ee_pose(pos, quat)
            except grpc.RpcError: pass
        else:
            if not delta: pose = pose_diff(pose, self.get_ee_pose())
            joint_delta = self._ik_solver.compute(pose, robot_state=self.get_robot_state())[0]
            self.update_joints(joint_delta, delta=True, blocking=False)

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
        
        if blocking: gripper_cmd()
        else: run_threaded_command(gripper_cmd)

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