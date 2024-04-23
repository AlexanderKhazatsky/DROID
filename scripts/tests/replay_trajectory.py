from droid.robot_env import RobotEnv
from droid.trajectory_utils.misc import replay_trajectory

trajectory_folderpath = "/iris/u/moojink/prismatic-dev/DROID/data--debug/success/2024-04-22/Mon_Apr_22_17:24:14_2024"
action_space = "cartesian_velocity"

# Make the robot env
env = RobotEnv(action_space=action_space)

# Replay Trajectory #
h5_filepath = trajectory_folderpath + "/trajectory.h5"
while True:
    replay_trajectory(env, filepath=h5_filepath, action_space=action_space)
