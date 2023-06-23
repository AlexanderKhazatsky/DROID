from r2d2.robot_env import RobotEnv
from r2d2.trajectory_utils.misc import replay_trajectory

trajectory_folderpath = "data/success/2023-05-02/Tue_May__2_16:47:19_2023/"
action_space = "cartesian_velocity"

# Make the robot env
env = RobotEnv(action_space=action_space)

# Replay Trajectory #
h5_filepath = trajectory_folderpath + "/trajectory.h5"
while True:
    replay_trajectory(env, filepath=h5_filepath)
