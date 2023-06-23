from cv2 import aruco

# Robot Params #
# TODO: Revert all to blank strings before release.
nuc_ip = '172.16.0.7'
robot_ip = '172.16.0.11'
sudo_password = ''
if sudo_password == '':
    raise ValueError('Must set sudo_password in r2d2/misc/parameters.py!')
robot_serial_number = "295341-1326374"
gripper_type = 'franka' # 'franka' or 'robotiq'
operator_position = 'front' # 'front' or 'back'

# Camera Params #
# TODO: Revert all to blank strings before release.
camera_type = 'realsense' # 'realsense' or 'zed'
hand_camera_id = '138422074005'
varied_camera_1_id = '23404442'
varied_camera_2_id = '29838012'

# Charuco Board Params #
CHARUCOBOARD_ROWCOUNT = 9
CHARUCOBOARD_COLCOUNT = 14
CHARUCOBOARD_CHECKER_SIZE = 0.020
CHARUCOBOARD_MARKER_SIZE = 0.016
ARUCO_DICT = aruco.Dictionary_get(aruco.DICT_5X5_100)

# Code Version [DONT CHANGE] #
r2d2_version = "1.1"
