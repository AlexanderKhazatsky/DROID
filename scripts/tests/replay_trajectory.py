from r2d2.trajectory_utils.misc import replay_trajectory
from r2d2.robot_env import RobotEnv

trajectory_folderpath = '/home/sasha/R2D2/data/success/2023-02-16/Thu_Feb_16_16:27:00_2023'
action_space = 'joint_position'

# Make the robot env
env = RobotEnv(action_space=action_space)

# Replay Trajectory #
h5_filepath = trajectory_folderpath + '/trajectory.h5'
replay_trajectory(env, filepath=h5_filepath)