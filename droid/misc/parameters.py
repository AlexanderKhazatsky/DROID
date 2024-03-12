import os
from cv2 import aruco

# Robot Params #
nuc_ip = "172.16.0.3"
robot_ip = "172.16.0.2"
sudo_password = "tri-robots123"
robot_type = "fr3"  # 'panda' or 'fr3'
robot_serial_number = ""

# Camera ID's #
hand_camera_id = "16522755"
varied_camera_1_id = "29431508"
varied_camera_2_id = "29513368"

# Charuco Board Params #
CHARUCOBOARD_ROWCOUNT = 9
CHARUCOBOARD_COLCOUNT = 14
CHARUCOBOARD_CHECKER_SIZE = 0.020
CHARUCOBOARD_MARKER_SIZE = 0.016
ARUCO_DICT = aruco.Dictionary_get(aruco.DICT_5X5_100)

# Ubuntu Pro Token (RT PATCH) #
ubuntu_pro_token = ""

# Code Version [DONT CHANGE] #
droid_version = "1.3"

