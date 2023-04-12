from r2d2.controllers.oculus_controller import VRPolicy
from r2d2.robot_env import RobotEnv
from r2d2.trajectory_utils.misc import calibrate_camera

# Make the robot env
env = RobotEnv()
controller = VRPolicy()
camera_id = "19824535"

print("Ready")
calibrate_camera(env, camera_id, controller)
