import zerorpc
import numpy as np

class ServerInterface:
    def __init__(self, ip_address='127.0.0.1', launch=True):
        self.ip_address = ip_address
        self.establish_connection()
        
        if launch:
            self.launch_controller()
            self.launch_robot()

    def establish_connection(self):
        self.server = zerorpc.Client(heartbeat=20)
        self.server.connect('tcp://' + self.ip_address + ':4242')
        
    def launch_controller(self):
        self.server.launch_controller()

    def launch_robot(self):
        self.server.launch_robot()

    def kill_controller(self):
        self.server.kill_controller()

    def update_command(self, action, action_space='cartesian', delta=True, blocking=False):
        action_dict = self.server.update_command(action.tolist(), action_space, delta, blocking)
        return action_dict

    def update_pose(self, pose, delta=False, blocking=False):
        self.server.update_pose(joints.tolist(), delta, blocking)

    def update_joints(self, joints, delta=False, blocking=False):
        self.server.update_joints(joints.tolist(), delta, blocking)

    def update_gripper(self, close_percentage, delta=True, blocking=False):
        self.server.update_gripper(close_percentage, delta, blocking)

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
