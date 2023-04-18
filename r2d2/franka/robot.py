# ROBOT SPECIFIC IMPORTS
import grpc
import numpy as np
import os
import time
import torch
from polymetis import GripperInterface, RobotInterface
from r2d2.misc.parameters import sudo_password, gripper_type
from r2d2.misc.subprocess_utils import run_terminal_command, run_threaded_command

# UTILITY SPECIFIC IMPORTS
from r2d2.misc.transformations import add_poses, euler_to_quat, pose_diff, quat_to_euler
from r2d2.robot_ik.robot_ik_solver import RobotIKSolver


class FrankaRobot:
    def launch_controller(self):
        try:
            self.kill_controller()
        except:
            pass
        accepted_gripper_types = ['franka', 'robotiq']
        assert gripper_type in accepted_gripper_types, f"Invalid gripper_type specified in r2d2.misc.parameters! Must be one of the following: {accepted_gripper_types}"
        dir_path = os.path.dirname(os.path.realpath(__file__))
        print('Launching robot...')
        self._robot_process = run_terminal_command(
            "echo " + sudo_password + " | sudo -S " + "bash " + dir_path + "/launch_robot.sh"
        )
        print('Launching gripper...')
        self._gripper_process = run_terminal_command(
            "echo " + sudo_password + " | sudo -S " + "bash " + dir_path + "/launch_gripper.sh"
        )
        self._server_launched = True
        if gripper_type == 'franka':
            sleep_time = 20 # Franka seems to take longer to launch
        else: # 'robotiq'
            sleep_time = 5
        for i in range(sleep_time):
            print(f'Waiting for robot and gripper launch to finish... {i+1} / {sleep_time}')
            time.sleep(1)

    def launch_robot(self):
        self._robot = RobotInterface(ip_address="localhost")
        self._gripper = GripperInterface(ip_address="localhost")
        if gripper_type == 'franka':
            self._curr_gripper_state = None
            self._last_grasp_time = time.time()
            self._franka_gripper_cooldown = 1 # cannot send open/close commands more than once per sec if using franka gripper
        self._max_gripper_width = self._gripper.metadata.max_width
        self._ik_solver = RobotIKSolver()

    def kill_controller(self):
        self._robot_process.kill()
        self._gripper_process.kill()

    def update_command(self, command, action_space="cartesian_velocity", blocking=False):
        action_dict = self.create_action_dict(command, action_space=action_space)
        self.update_joints(action_dict["joint_position"], velocity=False, blocking=blocking)
        if gripper_type == 'franka':
            self.update_gripper(action_dict["gripper_action"], velocity=False, blocking=blocking)
        else: # 'robotiq'
            self.update_gripper(action_dict["gripper_position"], velocity=False, blocking=blocking)
        return action_dict

    def update_pose(self, command, velocity=False, blocking=False):
        if blocking:
            if velocity:
                curr_pose = self.get_ee_pose()
                cartesian_delta = self._ik_solver.cartesian_velocity_to_delta(command)
                command = add_poses(cartesian_delta, curr_pose)

            pos = torch.Tensor(command[:3])
            quat = torch.Tensor(euler_to_quat(command[3:6]))

            if self._robot.is_running_policy():
                self._robot.terminate_current_policy()
            try:
                self._robot.move_to_ee_pose(pos, quat)
            except grpc.RpcError:
                pass
        else:
            if not velocity:
                curr_pose = self.get_ee_pose()
                cartesian_delta = pose_diff(command, curr_pose)
                command = self._ik_solver.cartesian_delta_to_velocity(cartesian_delta)

            robot_state = self.get_robot_state()[0]
            joint_velocity = self._ik_solver.cartesian_velocity_to_joint_velocity(command, robot_state=robot_state)

            self.update_joints(joint_velocity, velocity=True, blocking=False)

    def update_joints(self, command, velocity=False, blocking=False, cartesian_noise=None):
        if cartesian_noise is not None:
            command = self.add_noise_to_joints(command, cartesian_noise)
        command = torch.Tensor(command)

        if velocity:
            joint_delta = self._ik_solver.joint_velocity_to_delta(command)
            command = joint_delta + self._robot.get_joint_positions()

        def helper_non_blocking():
            if not self._robot.is_running_policy():
                self._robot.start_cartesian_impedance()
            try:
                self._robot.update_desired_joint_positions(command)
            except grpc.RpcError:
                pass

        if blocking:
            if self._robot.is_running_policy():
                self._robot.terminate_current_policy()
            try:
                self._robot.move_to_joint_positions(command)
            except grpc.RpcError:
                pass
            self._robot.start_cartesian_impedance()
        else:
            run_threaded_command(helper_non_blocking)

    def _update_franka_gripper(self, command, blocking):
        desired_gripper_state = 'close' if command < 0 else 'open'
        time_since_last_grasp = time.time() - self._last_grasp_time
        # Only send the grasp command if this is the first time grasping, or if the desired grasp state (open/close) is not the same as the current grasp state.
        # Also, wait for the cooldowns to expire before sending commands (to not overwhelm the Franka gripper and cause it to bug out).
        if self._curr_gripper_state is None or (desired_gripper_state != self._curr_gripper_state and time_since_last_grasp > self._franka_gripper_cooldown):
            target_grasp_width = 0 if desired_gripper_state == 'close' else self._gripper.metadata.max_width # ranges between 0 and 0.08 for Franka gripper
            self._gripper.grasp(speed=0.1, force=0.1, grasp_width=target_grasp_width, epsilon_inner=1, epsilon_outer=1, blocking=blocking)
            self._curr_gripper_state = desired_gripper_state
            self._last_grasp_time = time.time()

    def _update_robotiq_gripper(self, command, velocity, blocking):
        if velocity:
            gripper_delta = self._ik_solver.gripper_velocity_to_delta(command)
            command = gripper_delta + self.get_gripper_position()
        command = float(np.clip(command, 0, 1))
        self._gripper.goto(width=self._max_gripper_width * (1 - command), speed=0.05, force=0.1, blocking=blocking)

    def update_gripper(self, command, velocity=True, blocking=False):
        if gripper_type == 'franka':
            self._update_franka_gripper(command=command, blocking=blocking)
        else: # 'robotiq'
            self._update_robotiq_gripper(command=command, velocity=velocity, blocking=blocking)

    def add_noise_to_joints(self, original_joints, cartesian_noise):
        original_joints = torch.Tensor(original_joints)

        pos, quat = self._robot.robot_model.forward_kinematics(original_joints)
        curr_pose = pos.tolist() + quat_to_euler(quat).tolist()
        new_pose = add_poses(cartesian_noise, curr_pose)

        new_pos = torch.Tensor(new_pose[:3])
        new_quat = torch.Tensor(euler_to_quat(new_pose[3:]))

        noisy_joints, success = self._robot.solve_inverse_kinematics(new_pos, new_quat, original_joints)

        if success:
            desired_joints = noisy_joints
        else:
            desired_joints = original_joints

        return desired_joints.tolist()

    def get_joint_positions(self):
        return self._robot.get_joint_positions().tolist()

    def get_joint_velocities(self):
        return self._robot.get_joint_velocities().tolist()

    def get_gripper_position(self):
        return 1 - (self._gripper.get_state().width / self._max_gripper_width)

    def get_ee_pose(self):
        pos, quat = self._robot.get_ee_pose()
        angle = quat_to_euler(quat.numpy())
        return np.concatenate([pos, angle]).tolist()

    def get_robot_state(self):
        robot_state = self._robot.get_robot_state()
        gripper_position = self.get_gripper_position()
        pos, quat = self._robot.robot_model.forward_kinematics(torch.Tensor(robot_state.joint_positions))
        cartesian_position = pos.tolist() + quat_to_euler(quat.numpy()).tolist()

        state_dict = {
            "cartesian_position": cartesian_position,
            "gripper_position": gripper_position,
            "joint_positions": list(robot_state.joint_positions),
            "joint_velocities": list(robot_state.joint_velocities),
            "joint_torques_computed": list(robot_state.joint_torques_computed),
            "prev_joint_torques_computed": list(robot_state.prev_joint_torques_computed),
            "prev_joint_torques_computed_safened": list(robot_state.prev_joint_torques_computed_safened),
            "motor_torques_measured": list(robot_state.motor_torques_measured),
            "prev_controller_latency_ms": robot_state.prev_controller_latency_ms,
            "prev_command_successful": robot_state.prev_command_successful,
        }

        timestamp_dict = {
            "robot_timestamp_seconds": robot_state.timestamp.seconds,
            "robot_timestamp_nanos": robot_state.timestamp.nanos,
        }

        return state_dict, timestamp_dict

    def create_action_dict(self, action, action_space, robot_state=None):
        assert action_space in ["cartesian_position", "joint_position", "cartesian_velocity", "joint_velocity"]
        if robot_state is None:
            robot_state = self.get_robot_state()[0]
        action_dict = {"robot_state": robot_state}
        velocity = "velocity" in action_space

        if velocity:
            action_dict["gripper_velocity"] = action[-1]
            gripper_delta = self._ik_solver.gripper_velocity_to_delta(action[-1])
            gripper_position = robot_state["gripper_position"] + gripper_delta
            action_dict["gripper_position"] = float(np.clip(gripper_position, 0, 1))
        else:
            action_dict["gripper_position"] = float(np.clip(action[-1], 0, 1))
            gripper_delta = action_dict["gripper_position"] - robot_state["gripper_position"]
            gripper_velocity = self._ik_solver.gripper_delta_to_velocity(gripper_delta)
            action_dict["gripper_delta"] = gripper_velocity

        # If using the Franka gripper (not Robotiq), overwrite the gripper action as a binary (open/close) value.
        if gripper_type == 'franka':
            action_dict['gripper_action'] = -1. if action[-1] < 0. else 1.

        if 'cartesian' in action_space:
            if velocity:
                action_dict["cartesian_velocity"] = action[:-1]
                cartesian_delta = self._ik_solver.cartesian_velocity_to_delta(action[:-1])
                action_dict["cartesian_position"] = add_poses(
                    cartesian_delta, robot_state["cartesian_position"]
                ).tolist()
            else:
                action_dict["cartesian_position"] = action[:-1]
                cartesian_delta = pose_diff(action[:-1], robot_state["cartesian_position"])
                cartesian_velocity = self._ik_solver.cartesian_delta_to_velocity(cartesian_delta)
                action_dict["cartesian_velocity"] = cartesian_velocity.tolist()

            action_dict["joint_velocity"] = self._ik_solver.cartesian_velocity_to_joint_velocity(
                action_dict["cartesian_velocity"], robot_state=robot_state
            ).tolist()
            joint_delta = self._ik_solver.joint_velocity_to_delta(action_dict["joint_velocity"])
            action_dict["joint_position"] = (joint_delta + np.array(robot_state["joint_positions"])).tolist()

        if "joint" in action_space:
            # NOTE: Joint to Cartesian has undefined dynamics due to IK
            if velocity:
                action_dict["joint_velocity"] = action[:-1]
                joint_delta = self._ik_solver.joint_velocity_to_delta(action[:-1])
                action_dict["joint_position"] = (joint_delta + np.array(robot_state["joint_positions"])).tolist()
            else:
                action_dict["joint_position"] = action[:-1]
                joint_delta = np.array(action[:-1]) - np.array(robot_state["joint_positions"])
                joint_velocity = self._ik_solver.joint_delta_to_velocity(joint_delta)
                action_dict["joint_velocity"] = joint_velocity.tolist()

        return action_dict
