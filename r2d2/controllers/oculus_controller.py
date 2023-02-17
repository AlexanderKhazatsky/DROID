from r2d2.misc.transformations import quat_to_euler, euler_to_quat, quat_diff, rmat_to_quat, pose_diff
from r2d2.misc.subprocess_utils import run_threaded_command
from oculus_reader.reader import OculusReader
import numpy as np
import time

def vec_to_reorder_mat(vec):
    X = np.zeros((len(vec), len(vec)))
    for i in range(X.shape[0]):
        ind = int(abs(vec[i])) - 1
        X[i, ind] = np.sign(vec[i])
    return X

class VRPolicy:
    def __init__(self,
                 right_controller: bool = True,
                 max_lin_vel: float = 1,
                 max_rot_vel: float = 1,
                 max_gripper_vel: float = 1,
                 spatial_coeff: float = 1,
                 pos_action_gain: float = 3,
                 rot_action_gain: float = 3,
                 gripper_action_gain: float = 3,
                 rmat_reorder: list = [-2, -1, -3, 4]):

        self.oculus_reader = OculusReader()
        self.vr_to_global_mat = np.eye(4)
        self.max_lin_vel = max_lin_vel
        self.max_rot_vel = max_rot_vel
        self.max_gripper_vel = max_gripper_vel
        self.spatial_coeff = spatial_coeff
        self.pos_action_gain = pos_action_gain
        self.rot_action_gain = rot_action_gain
        self.gripper_action_gain = gripper_action_gain
        self.global_to_env_mat = vec_to_reorder_mat(rmat_reorder)
        self.controller_id = 'r' if right_controller else 'l'
        self.reset_orientation = True
        self.reset_state()

        # Start State Listening Thread #
        run_threaded_command(self._update_internal_state)

    def reset_state(self):
        self._state = {'poses': {}, 'buttons': {'A': False, 'B': False}, 
            'movement_enabled': False, 'controller_on': True}
        self.update_sensor = True
        self.reset_origin = True
        self.robot_origin = None
        self.vr_origin = None
        self.vr_state = None

    def _update_internal_state(self, num_wait_sec=5, hz=50):
        last_read_time = time.time()
        while True:
            # Regulate Read Frequency #
            time.sleep(1 / hz)

            # Read Controller
            time_since_read = time.time() - last_read_time
            poses, buttons = self.oculus_reader.get_transformations_and_buttons()
            self._state['controller_on'] = time_since_read < num_wait_sec
            if poses == {}: continue

            # Determine Control Pipeline #
            toggled = self._state['movement_enabled'] != buttons['RG']
            self.update_sensor = self.update_sensor or buttons['RG']
            self.reset_orientation = self.reset_orientation or buttons['RJ']
            self.reset_origin = self.reset_origin or toggled

            # Save Info #
            self._state['poses'] = poses
            self._state['buttons'] = buttons
            self._state['movement_enabled'] = buttons['RG']
            self._state['controller_on'] = True
            last_read_time = time.time()

            # Update Definition Of "Forward" #
            stop_updating = self._state['buttons']['RJ'] or self._state['movement_enabled']
            if self.reset_orientation:
                rot_mat = np.asarray(self._state['poses'][self.controller_id])
                if stop_updating: self.reset_orientation = False
                self.vr_to_global_mat = np.linalg.inv(rot_mat)

    def _process_reading(self):
        rot_mat = np.asarray(self._state['poses'][self.controller_id])
        rot_mat = self.global_to_env_mat @ self.vr_to_global_mat @ rot_mat
        vr_pos = self.spatial_coeff * rot_mat[:3, 3]
        vr_quat = rmat_to_quat(rot_mat[:3, :3])
        vr_gripper = self._state['buttons']['rightTrig'][0]

        self.vr_state = {'pos': vr_pos, 'quat': vr_quat, 'gripper': vr_gripper}

    def _limit_velocity(self, lin_vel, rot_vel, gripper_vel):
        """Scales down the linear and angular magnitudes of the action"""
        lin_vel_norm = np.linalg.norm(lin_vel)
        rot_vel_norm = np.linalg.norm(rot_vel)
        gripper_vel_norm = np.linalg.norm(gripper_vel)
        if lin_vel_norm > self.max_lin_vel:
            lin_vel = lin_vel * self.max_lin_vel / lin_vel_norm
        if rot_vel_norm > self.max_rot_vel:
            rot_vel = rot_vel * self.max_rot_vel / rot_vel_norm
        if gripper_vel_norm > self.max_gripper_vel:
            gripper_vel = gripper_vel * self.max_gripper_vel / gripper_vel_norm
        return lin_vel, rot_vel, gripper_vel

    def _calculate_action(self, state_dict):
        # Read Sensor #
        if self.update_sensor:
            self._process_reading()
            self.update_sensor = False

        # Read Observation
        robot_pos = np.array(state_dict['cartesian_position'][:3])
        robot_quat = euler_to_quat(state_dict['cartesian_position'][3:])
        robot_gripper = state_dict['gripper_position']

        # Reset Origin On Release #
        if self.reset_origin:
            self.robot_origin = {'pos': robot_pos, 'quat': robot_quat}
            self.vr_origin = {'pos': self.vr_state['pos'], 'quat': self.vr_state['quat']}
            self.reset_origin = False

        # Calculate Positional Action #
        robot_pos_offset = robot_pos - self.robot_origin['pos']
        target_pos_offset = self.vr_state['pos'] - self.vr_origin['pos']
        pos_action = target_pos_offset - robot_pos_offset

        # Calculate Euler Action #
        robot_quat_offset = quat_diff(robot_quat, self.robot_origin['quat'])
        target_quat_offset = quat_diff(self.vr_state['quat'], self.vr_origin['quat'])
        quat_action = quat_diff(target_quat_offset, robot_quat_offset)
        euler_action = quat_to_euler(quat_action)

        # Scale Appropriately #
        pos_action *= self.pos_action_gain
        euler_action *= self.rot_action_gain
        gripper_action = (self.vr_state['gripper'] - robot_gripper) * self.gripper_action_gain
        lin_vel, rot_vel, gripper_vel = self._limit_velocity(pos_action, euler_action, gripper_action)

        # Update Action
        action = np.concatenate([lin_vel, rot_vel, [gripper_vel]])
        return action.clip(-1, 1)

    def get_info(self):
        return {
            'success': self._state['buttons']['A'],
            'failure': self._state['buttons']['B'],
            'movement_enabled': self._state['movement_enabled'],
            'controller_on': self._state['controller_on']}

    def forward(self, obs_dict):
        if self._state['poses'] == {}:
            return np.zeros(7)
        return self._calculate_action(obs_dict['robot_state'])


# target_pose = np.array([0.6807800531387329, -0.12813058495521545, 0.3646218478679657, 1.5014798853428837, 0.03399652669021358, -0.1661899333745161])
# curr_pose = np.array(state_dict['cartesian_position'])

# pose_action = pose_diff(target_pose, curr_pose)

# if np.linalg.norm(pose_action) < 0.5:
#     gripper_action = 1 - robot_gripper
# else:
#     gripper_action = 0 - robot_gripper

# lin_vel, rot_vel, gripper_vel = self._limit_velocity(pose_action[:3], pose_action[3:], gripper_action)


# from r2d2.misc.transformations import quat_to_euler, euler_to_quat, quat_diff, rmat_to_quat
# from r2d2.misc.subprocess_utils import run_threaded_command
# from oculus_reader.reader import OculusReader
# import numpy as np
# import time

# def vec_to_reorder_mat(vec):
#     X = np.zeros((len(vec), len(vec)))
#     for i in range(X.shape[0]):
#         ind = int(abs(vec[i])) - 1
#         X[i, ind] = np.sign(vec[i])
#     return X

# class VRPolicy:
#     def __init__(self,
#                  right_controller: bool = True,
#                  max_lin_vel: float = 1,
#                  max_rot_vel: float = 1,
#                  max_gripper_vel: float = 1,
#                  spatial_coeff: float = 1,
#                  pos_action_gain: float = 3,
#                  rot_action_gain: float = 3,
#                  gripper_action_gain: float = 3,
#                  rmat_reorder: list = [-2, -1, -3, 4]):

#         self.oculus_reader = OculusReader()
#         self.vr_to_global_mat = np.eye(4)
#         self.robot_origin = {'pos': None, 'quat': None}
#         self.vr_origin = {'pos': None, 'quat': None}
#         self.max_lin_vel = max_lin_vel
#         self.max_rot_vel = max_rot_vel
#         self.max_gripper_vel = max_gripper_vel
#         self.spatial_coeff = spatial_coeff
#         self.pos_action_gain = pos_action_gain
#         self.rot_action_gain = rot_action_gain
#         self.gripper_action_gain = gripper_action_gain
#         self.global_to_env_mat = vec_to_reorder_mat(rmat_reorder)
#         self.controller_id = 'r' if right_controller else 'l'
#         self.reset_orientation = True
#         self.reset_state()

#         # Start State Listening Thread #
#         run_threaded_command(self._update_internal_state)

#     def reset_state(self):
#         self._state = {'poses': {}, 'buttons': {'A': False, 'B': False}, 
#             'movement_enabled': False, 'controller_on': True}
#         self.reset_origin = True

#     def _update_internal_state(self, num_wait_sec=5, hz=50):
#         last_read_time = time.time()
#         while True:
#             # Regulate Read Frequency
#             time.sleep(1/hz)

#             # Read Controller
#             time_since_read = time.time() - last_read_time
#             poses, buttons = self.oculus_reader.get_transformations_and_buttons()
#             self._state['controller_on'] = time_since_read < num_wait_sec
#             if poses == {}: continue

#             self._state['poses'] = poses
#             self._state['buttons'] = buttons
#             self._state['movement_enabled'] = buttons['RG']
#             self._state['controller_on'] = True
#             last_read_time = time.time()

#             self.reset_orientation = self.reset_orientation or self._state['buttons']['RJ'] #\

#             # Update Origin When Button Not Pressed
#             if not self._state['movement_enabled']: self.reset_origin = True

#             # Update "Forward" On First Press
#             if self.reset_orientation:
#                 rot_mat = np.asarray(self._state['poses'][self.controller_id])
#                 if self._state['buttons']['RJ']: self.reset_orientation = False
#                 if self._state['movement_enabled']: self.reset_orientation = False
#                 self.vr_to_global_mat = np.linalg.inv(rot_mat)

#     def _process_reading(self):
#         rot_mat = np.asarray(self._state['poses'][self.controller_id])
#         rot_mat = self.global_to_env_mat @ self.vr_to_global_mat @ rot_mat
#         vr_pos = self.spatial_coeff * rot_mat[:3, 3]
#         vr_quat = rmat_to_quat(rot_mat[:3, :3])

#         return vr_pos, vr_quat

#     def _limit_velocity(self, lin_vel, rot_vel, gripper_vel):
#         """Scales down the linear and angular magnitudes of the action"""
#         lin_vel_norm = np.linalg.norm(lin_vel)
#         rot_vel_norm = np.linalg.norm(rot_vel)
#         gripper_vel_norm = np.linalg.norm(gripper_vel)
#         if lin_vel_norm > self.max_lin_vel:
#             lin_vel = lin_vel * self.max_lin_vel / lin_vel_norm
#         if rot_vel_norm > self.max_rot_vel:
#             rot_vel = rot_vel * self.max_rot_vel / rot_vel_norm
#         if gripper_vel_norm > self.max_gripper_vel:
#             gripper_vel = gripper_vel * self.max_gripper_vel / gripper_vel_norm
#         return lin_vel, rot_vel, gripper_vel

#     def _calculate_action(self, state_dict):
#         # Read Sensor
#         vr_pos, vr_quat = self._process_reading()
#         vr_gripper = np.array(self._state['buttons']['rightTrig'])

#         # Read Observation
#         robot_pos = np.array(state_dict['cartesian_pose'][:3])
#         robot_quat = euler_to_quat(state_dict['cartesian_pose'][3:6])
#         robot_gripper = state_dict['gripper_position']

#         # Reset Origin On Release #
#         if self.reset_origin:
#             self.robot_origin = {'pos': robot_pos, 'quat': robot_quat}
#             self.vr_origin = {'pos': vr_pos, 'quat': vr_quat}
#             self.reset_origin = False

#         # Calculate Positional Action
#         robot_pos_offset = robot_pos - self.robot_origin['pos']
#         target_pos_offset = vr_pos - self.vr_origin['pos']
#         pos_action = target_pos_offset - robot_pos_offset

#         # Calculate Euler Action
#         robot_quat_offset = quat_diff(robot_quat, self.robot_origin['quat'])
#         target_quat_offset = quat_diff(vr_quat, self.vr_origin['quat'])
#         quat_action = quat_diff(target_quat_offset, robot_quat_offset)
#         euler_action = quat_to_euler(quat_action)

#         # Scale Appropriately
#         pos_action *= self.pos_action_gain
#         euler_action *= self.rot_action_gain
#         gripper_action = (vr_gripper - robot_gripper) * self.gripper_action_gain
#         lin_vel, rot_vel, gripper_vel = self._limit_velocity(pos_action, euler_action, gripper_action)
                
#         # Update Action
#         action = np.concatenate([lin_vel, rot_vel, gripper_vel])
#         return action.clip(-1, 1)

#     def get_info(self):
#         return {
#             'success': self._state['buttons']['A'],
#             'failure': self._state['buttons']['B'],
#             'movement_enabled': self._state['movement_enabled'],
#             'controller_on': self._state['controller_on']}

#     def forward(self, obs_dict):
#         if self._state['poses'] == {}: return np.zeros(7)
#         action = self._calculate_action(obs_dict['robot_state'])
#         return action
