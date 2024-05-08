import os
from cv2 import aruco

# Robot Params #
# TODO: Revert all to blank strings before release.
nuc_ip = '172.16.0.7'
robot_ip = '172.16.0.22'
sudo_password = ''
if sudo_password == '':
    raise ValueError('Must set sudo_password in droid/misc/parameters.py!')
robot_type = "panda"  # 'panda' or 'fr3'
robot_serial_number = "295341-1325480"
gripper_type = 'franka' # 'franka' or 'robotiq'
operator_position = 'front' # 'front' or 'back'

# Camera Params #
# TODO: Revert all to blank strings before release.
camera_type = 'realsense' # 'realsense' or 'zed'
hand_camera_id = '138422074005'
static_camera_id = '140122076178'

# Charuco Board Params #
CHARUCOBOARD_ROWCOUNT = 9
CHARUCOBOARD_COLCOUNT = 14
CHARUCOBOARD_CHECKER_SIZE = 0.019
CHARUCOBOARD_MARKER_SIZE = 0.015
ARUCO_DICT = aruco.Dictionary_get(aruco.DICT_4X4_100)

# Ubuntu Pro Token (RT PATCH) #
ubuntu_pro_token = ""

# Code Version [DONT CHANGE] #
droid_version = "1.3"

