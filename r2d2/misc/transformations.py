from scipy.spatial.transform import Rotation as R
import numpy as np

### Conversions ###
def quat_to_euler(quat, degrees=False):
    euler = R.from_quat(quat).as_euler('xyz', degrees=degrees)
    return euler

def euler_to_quat(euler, degrees=False):
    return R.from_euler('xyz', euler, degrees=degrees).as_quat()

def rmat_to_euler(rot_mat, degrees=False):
    euler = R.from_matrix(rot_mat).as_euler('xyz', degrees=degrees)
    return euler

def euler_to_rmat(euler, degrees=False):
    return R.from_euler('xyz', euler, degrees=degrees).as_matrix()

def rmat_to_quat(rot_mat, degrees=False):
    quat = R.from_matrix(rot_mat).as_quat()
    return quat

def quat_to_rmat(quat, degrees=False):
    return R.from_quat(euler, degrees=degrees).as_matrix()

### Subtractions ###
def quat_diff(target, source):
    result = R.from_quat(target) * R.from_quat(source).inv()
    return result.as_quat()

def angle_diff(target, source, degrees=False):
    target_rot = R.from_euler('xyz', target, degrees=degrees)
    source_rot = R.from_euler('xyz', source, degrees=degrees)
    result = target_rot * source_rot.inv()
    return result.as_euler('xyz')

def pose_diff(target, source, degrees=False):
    lin_diff = np.array(target[:3]) - np.array(source[:3])
    rot_diff = angle_diff(target[3:6], source[3:6], degrees=degrees)
    result = np.concatenate([lin_diff, rot_diff])
    return result

### Additions ###
def quat_add(delta, source):
    result = R.from_quat(target) * R.from_quat(source)
    return result.as_quat()

def add_angles(delta, source, degrees=False):
    delta_rot = R.from_euler('xyz', delta, degrees=degrees)
    source_rot = R.from_euler('xyz', source, degrees=degrees)
    new_rot = delta_rot * source_rot
    return new_rot.as_euler('xyz', degrees=degrees)

def add_poses(delta, source, degrees=False):
    lin_sum = np.array(delta[:3]) + np.array(source[:3])
    rot_sum = add_angles(delta[3:6], source[3:6], degrees=degrees)
    result = np.concatenate([lin_sum, rot_sum])
    return result