from scipy.spatial.transform import Rotation as R
from r2d2.misc.transformations import *
from collections import defaultdict
import matplotlib.pyplot as plt
from cv2 import aruco
import numpy as np
import time
import cv2

# ChAruco Board Variables
CHARUCOBOARD_ROWCOUNT = 7
CHARUCOBOARD_COLCOUNT = 10
ARUCO_DICT = aruco.Dictionary_get(aruco.DICT_4X4_50)

# Create constants to be passed into OpenCV and Aruco methods
CHARUCO_BOARD = aruco.CharucoBoard_create(
		squaresX=CHARUCOBOARD_COLCOUNT,
		squaresY=CHARUCOBOARD_ROWCOUNT,
		squareLength=0.024,
		markerLength=0.018,
		dictionary=ARUCO_DICT)

# Detector Params
detector_params = cv2.aruco.DetectorParameters_create()
detector_params.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX


def process_chessboard(image, corner_threshold=20):
	gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
	image_size = image.shape[:2]

	# Find aruco markers in the query image
	corners, ids, rejected = aruco.detectMarkers(
			image=gray,
			dictionary=ARUCO_DICT,
			parameters=detector_params
			)

	corners, ids, _, _ = cv2.aruco.refineDetectedMarkers(
		gray, CHARUCO_BOARD, corners, ids, rejected)

	# Get charuco corners and ids from detected aruco markers
	if len(corners) == 0: return None

	num_corners_found, charuco_corners, charuco_ids = aruco.interpolateCornersCharuco(
			markerCorners=corners,
			markerIds=ids,
			image=gray,
			board=CHARUCO_BOARD)

	if num_corners_found < corner_threshold: return None

	return corners, ids, charuco_corners, charuco_ids, image_size

def visualize_calibration(calibration_dict):
    shapes = ['.', 'o', 'v', '^', 's', 'x', 'D', 'h', '<', '>', '8', '1', '2', '3']
    assert len(calibration_dict) < (len(shapes) - 1)
    plt.clf()

    axes = plt.subplot(111, projection='3d')
    axes.plot(0, 0, 0, '*', label="Robot Base")
    
    for view_id in calibration_dict:
        curr_shape = shapes.pop(0)
        pose = calibration_dict[view_id]
        angle = [int(d * 180 / np.pi) for d in pose[3:]]
        label = '{0}: {1}'.format(view_id, angle)
        axes.plot(pose[0], pose[1], pose[2], curr_shape, label=label)
        
    plt.legend(loc="center right", bbox_to_anchor=(2, 0.5))
    plt.title('Calibration Visualization')
    plt.show()

def visualize_chessboard(image, visual_type=['markers', 'axes']):
	if type(visual_type) != list: visual_type = [visual_type]
	assert all([t in ['markers', 'charuco', 'axes'] for t in visual_type])

	image = np.copy(image)
	readings = process_chessboard(image)
	
	if readings is None:
		cv2.imshow('Charuco board', image)
		cv2.waitKey(20)
		return

	corners, ids, charuco_corners, charuco_ids, image_size = readings

	# Outline the aruco markers found in our query image
	if 'markers' in visual_type:
		image = aruco.drawDetectedMarkers(
			image=image,
			corners=corners)

	# Draw the Charuco board we've detected to show our calibrator the board was properly detected
	if 'charuco' in visual_type:
		image = aruco.drawDetectedCornersCharuco(
			 image=image,
			 charucoCorners=charuco_corners,
			 charucoIds=charuco_ids)

	if 'axes' in visual_type:
		calibration_error, cameraMatrix, distCoeffs, rvecs, tvecs = aruco.calibrateCameraCharuco(
			charucoCorners=[charuco_corners],
			charucoIds=[charuco_ids],
			board=CHARUCO_BOARD,
			imageSize=image_size,
			cameraMatrix=None,
			distCoeffs=None)
		# import pdb; pdb.set_trace
		cv2.drawFrameAxes(image, cameraMatrix, distCoeffs, rvecs[0], tvecs[0], 0.1)

	# Visualize
	cv2.imshow('Charuco board', image)
	cv2.waitKey(20)

def calculate_target_to_cam(images):
	#assert (images is None) ^ (readings is None)
	corners_all = [] # Corners discovered in all images processed
	ids_all = [] # Aruco ids corresponding to corners discovered
	image_size = images[0].shape[:2]
	successes = [False] * len(images)

	for i in range(len(images)):
		assert images[i].shape[:2] == image_size
		readings = process_chessboard(images[i])
		if readings is None: continue
		charuco_corners, charuco_ids = readings[2], readings[3]
		corners_all.append(charuco_corners)
		ids_all.append(charuco_ids)
		successes[i] = True

	calibration_error, cameraMatrix, distCoeffs, rvecs, tvecs = aruco.calibrateCameraCharuco(
			charucoCorners=corners_all,
			charucoIds=ids_all,
			board=CHARUCO_BOARD,
			imageSize=image_size,
			cameraMatrix=None,
			distCoeffs=None)

	print('Error: ', calibration_error)

	rmats = [R.from_rotvec(rvec.flatten()).as_matrix() for rvec in rvecs]
	tvecs = [tvec.flatten() for tvec in tvecs]

	return rmats, tvecs, successes

def calculate_gripper_to_base(images, gripper_poses, eval_images=None):
	if eval_images is None: eval_images = images
	all_R_target2cam, all_t_target2cam, successes = calculate_target_to_cam(eval_images)
	rmats, tvecs = [], []

	gripper2target_pose = calibrate_gripper_to_target(images, gripper_poses)
	R_gripper2target = R.from_euler('xyz', gripper2target_pose[3:]).as_matrix()
	t_gripper2target = np.array(gripper2target_pose[:3])

	cam2base_pose = calibrate_cam_to_base(images, gripper_poses)
	R_cam2base = R.from_euler('xyz', cam2base_pose[3:]).as_matrix()
	t_cam2base = np.array(cam2base_pose[:3])

	for i in range(len(all_R_target2cam)):
		R_gripper2cam = all_R_target2cam[i] @ R_gripper2target
		t_gripper2cam = all_R_target2cam[i] @ t_gripper2target + all_t_target2cam[i]

		R_gripper2base = R_cam2base @ R_gripper2cam
		t_gripper2base = R_cam2base @ t_gripper2cam + t_cam2base

		rmats.append(R_gripper2base)
		tvecs.append(t_gripper2base)

	return rmats, tvecs, successes

def calibrate_gripper_to_target(images, gripper_poses):
	#print('GRIPPER2TARGET CALIBRATION ASSUMES TAG ATTATCHED TO GRIPPER')
	R_target2cam, t_target2cam, successes = calculate_target_to_cam(images)
	gripper_poses = np.array(gripper_poses)[successes]

	t_base2gripper = [- R.from_euler('xyz', pose[3:6]).inv().as_matrix() @ np.array(pose[:3]) \
		for pose in gripper_poses]
	R_base2gripper = [R.from_euler('xyz', pose[3:6]).inv().as_matrix() \
		for pose in gripper_poses]

	rmat, pos = cv2.calibrateHandEye(
		R_gripper2base=R_target2cam,
		t_gripper2base=t_target2cam,
		R_target2cam=R_base2gripper,
		t_target2cam=t_base2gripper,
		method=4,
	)

	pos = pos.flatten()
	angle = R.from_matrix(rmat).as_euler('xyz')
	pose = np.concatenate([pos, angle])

	return pose

def calibrate_cam_to_base(images, gripper_poses):
	#print('CAM2BASE CALIBRATION ASSUMES CAMERA ATTATCHED TO BASE')

	R_target2cam, t_target2cam, successes = calculate_target_to_cam(images)
	gripper_poses = np.array(gripper_poses)[successes]

	t_base2gripper = [- R.from_euler('xyz', pose[3:6]).inv().as_matrix() @ np.array(pose[:3]) \
		for pose in gripper_poses]
	R_base2gripper = [R.from_euler('xyz', pose[3:6]).inv().as_matrix() \
		for pose in gripper_poses]

	rmat, pos = cv2.calibrateHandEye(
		R_gripper2base=R_base2gripper,
		t_gripper2base=t_base2gripper,
		R_target2cam=R_target2cam,
		t_target2cam=t_target2cam,
		method=4
	)

	pos = pos.flatten()
	angle = R.from_matrix(rmat).as_euler('xyz')
	pose = np.concatenate([pos, angle])

	return pose

def calibrate_cam_to_gripper(images, gripper_poses):
	#print('CAM2GRIPPER CALIBRATION ASSUMES CAMERA ATTATCHED TO GRIPPER')

	R_target2cam, t_target2cam, successes = calculate_target_to_cam(images)
	gripper_poses = np.array(gripper_poses)[successes]

	t_gripper2base = [np.array(pose[:3]) for pose in gripper_poses]
	R_gripper2base = [R.from_euler('xyz', pose[3:6]).as_matrix()
		for pose in gripper_poses]

	rmat, pos = cv2.calibrateHandEye(
		R_gripper2base=R_gripper2base,
		t_gripper2base=t_gripper2base,
		R_target2cam=R_target2cam,
		t_target2cam=t_target2cam,
		method=4,
	)

	pos = pos.flatten()
	angle = R.from_matrix(rmat).as_euler('xyz')
	pose = np.concatenate([pos, angle])

	return pose

def estimate_3rd_person_accuracy(images, gripper_poses, train_p=0.8):
	images, gripper_poses = np.array(images), np.array(gripper_poses)
	ind = np.random.choice(len(images), size=len(images), replace=False)
	num_train = int(len(images) * train_p)
	
	train_ind, test_ind = ind[:num_train], ind[num_train:]
	train_images, train_poses = images[train_ind], gripper_poses[train_ind]
	test_images, test_poses = images[test_ind], gripper_poses[test_ind]
	
	approx_rmats, approx_positions, successes = \
		calculate_gripper_to_base(train_images, train_poses, eval_images=test_images)
	approx_eulers = [R.from_matrix(rmat).as_euler('xyz') for rmat in approx_rmats]
	test_poses = np.array(test_poses)[successes]

	pos_error = np.array(test_poses)[:, :3] - np.array(approx_positions)
	euler_error = np.array([angle_diff(pose[3:6], approx_angle) \
		for pose, approx_angle in zip(test_poses, approx_eulers)])

	pose_error = np.concatenate([pos_error, euler_error], axis=1)
	pose_mse = np.linalg.norm(pose_error, axis=0) ** 2 / pos_error.shape[0]

	return pose_mse

def calibrate_cameras(env, traj_list):
	camera_dict = defaultdict(list)
	calibration_dict = {}
	robot_states = []

	env.reset()
	# for pose, sleep_time in traj_list:

	# 	# for now, replace this with oculus control
	# 	env.update_pose(pose)
	# 	time.sleep(sleep_time)
	# 	obs = env.get_observation()

	camera_dict = defaultdict(list)
	calibration_dict = {}
	robot_states = []

	env.reset()
	for pose, sleep_time in traj_list:

		# for now, replace this with oculus control
		env.update_pose(pose)
		time.sleep(sleep_time)
		obs = env.get_observation()

		curr_state = obs['state_dict']['ee_state']
		robot_states.append(curr_state)

		for cam_id in obs['camera_dict']:
			img_dict = obs['camera_dict'][cam_id]
			for img_id in img_dict:
				if 'rgb' in img_id:
					view_id = '{0}_{1}'.format(cam_id, img_id)
					camera_dict[view_id].append(img_dict[img_id])

	for view_id in camera_dict:
		cam2base = calibrate_cam_to_base(camera_dict[view_id], robot_state)
		calibration_dict[view_id] = cam2base
		del camera_dict[view_id]

	env.camera_reader.calibrate_cameras(calibration_dict)
	visualize_calibration(calibration_dict)