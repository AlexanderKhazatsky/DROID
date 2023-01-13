from r2d2.robot_env import RobotEnv
from r2d2.controllers.oculus_controller import VRPolicy
from r2d2.misc.trajectory_utils import *

# Make the robot env
env = RobotEnv()
controller = VRPolicy()

print('Ready')
collect_trajectory(env, controller=controller)