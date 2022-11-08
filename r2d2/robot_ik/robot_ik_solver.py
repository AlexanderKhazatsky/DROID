import numpy as np
from dm_control import mjcf
from dm_robotics.moma.effectors import (arm_effector,
										cartesian_6d_velocity_effector)
from r2d2.robot_ik.arm import FrankaArm
from r2d2.misc.transformations import angle_diff

class RobotIKSolver:

	def __init__(self):
		control_hz = 15
#		min_workspace_limits = np.array([0.0, -0.5, 0.0, 0.0, -np.pi, -np.pi])
#		max_workspace_limits = np.array([0.9, 0.5, 0.5, 2 * np.pi, np.pi, np.pi])
 
		self._arm = FrankaArm()

		self._physics = mjcf.Physics.from_mjcf_model(self._arm.mjcf_model)
		self._effector = arm_effector.ArmEffector(arm=self._arm,
									action_range_override=None,
									robot_name=self._arm.name)
		
		self._effector_model = cartesian_6d_velocity_effector.ModelParams(
			self._arm.wrist_site, self._arm.joints)

		scaler = 0.1 # Keep things slow!
		self._effector_control = cartesian_6d_velocity_effector.ControlParams(
			control_timestep_seconds=1 / control_hz,
			max_lin_vel=10.0, # Max out
			max_rot_vel=10.0, # Max out
			joint_velocity_limits=np.array([2.075 * scaler] * 4 + [2.51 * scaler] * 3),
			nullspace_joint_position_reference=[0] * 7,
			nullspace_gain=0.025, #Original: 0.025, 0.05
			regularization_weight=1e-2, #Original: 1e-2, 2e-2
			enable_joint_position_limits=True,
			minimum_distance_from_joint_position_limit=0.3, #0.3, 0.5
			joint_position_limit_velocity_scale=0.95,
			max_cartesian_velocity_control_iterations=300,
			max_nullspace_control_iterations=300)

		self._cart_effector_6d = cartesian_6d_velocity_effector.Cartesian6dVelocityEffector(
			self._arm.name, self._effector, self._effector_model, self._effector_control)

		self._cart_effector_6d.after_compile(self._arm.mjcf_model, self._physics)

#		self._cart_effector_6d = cartesian_6d_velocity_effector.limit_to_workspace(
#			self._cart_effector_6d, self._arm.wrist_site, min_workspace_limits, max_workspace_limits)

	def compute(self, ee_velocity, robot_state):
		ee_velocity = np.array(ee_velocity)
		qpos = np.array(robot_state['joint_positions'])
		qvel = np.array(robot_state['joint_velocities'])

		self._arm.update_state(self._physics, qpos, qvel)
		self._cart_effector_6d.set_control(self._physics, ee_velocity)
		joint_delta = self._physics.bind(self._arm.actuators).ctrl.copy()
		success = np.any(joint_delta)

		return joint_delta, success
