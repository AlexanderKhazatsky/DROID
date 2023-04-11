# Robot Params #
nuc_ip = '172.16.0.1'
robot_ip = '172.16.0.8'
sudo_password = 'robot'
gripper_type = 'robotiq' # 'franka' or 'robotiq'
operator_position = 'back' # 'front' or 'back'

# Camera Params #
camera_type = 'zed' # 'realsense' or 'zed'
hand_camera_id = '19824535'
varied_camera_1_id = '23404442'
varied_camera_2_id = '29838012'

# Charuco Board Params #
from cv2 import aruco
CHARUCOBOARD_ROWCOUNT = 9
CHARUCOBOARD_COLCOUNT = 14
CHARUCOBOARD_CHECKER_SIZE = 0.020
CHARUCOBOARD_MARKER_SIZE = 0.016
ARUCO_DICT = aruco.Dictionary_get(aruco.DICT_5X5_100)