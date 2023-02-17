from r2d2.trajectory_utils.misc import visualize_trajectory

trajectory_folderpath = '/home/sasha/R2D2/data/success/2023-02-16/Thu_Feb_16_16:27:00_2023'

h5_filepath = trajectory_folderpath + '/trajectory.h5'
recording_folderpath = trajectory_folderpath + '/recordings'
visualize_trajectory(filepath=h5_filepath, recording_folderpath=recording_folderpath)
