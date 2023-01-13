from r2d2.robot_env import RobotEnv
from r2d2.controllers.oculus_controller import VRPolicy
from r2d2.misc.trajectory_utils import *

# Make the robot env
env = RobotEnv()
controller = VRPolicy()
camera_id = '19824535'

print('Ready')
calibrate_camera(env, camera_id, controller)