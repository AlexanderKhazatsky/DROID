# Robot Params #
robot_ip = '172.16.0.1'
sudo_password = 'robot'

# Camera Names #
hand_camera_id = '19824535'

camera_names = {
	hand_camera_id: 'Hand Camera',
	'23404442': 'Fixed View Camera',
	'': 'Varied View Camera #1',
	'29838012': 'Varied View Camera #2',
}

# Charuco Board Params #
from cv2 import aruco
CHARUCOBOARD_ROWCOUNT = 9
CHARUCOBOARD_COLCOUNT = 14
CHARUCOBOARD_CHECKER_SIZE = 0.020
CHARUCOBOARD_MARKER_SIZE = 0.016
ARUCO_DICT = aruco.Dictionary_get(aruco.DICT_5X5_100)