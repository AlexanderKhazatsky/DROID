from scipy.spatial.transform import Rotation as R
import numpy as np

def quat_to_euler(quat, degrees=False):
    euler = R.from_quat(quat).as_euler('xyz', degrees=degrees)
    return euler

def euler_to_quat(euler, degrees=False):
    return R.from_euler('xyz', euler, degrees=degrees).as_quat()

def quat_diff(target, source):
    result = R.from_quat(target) * R.from_quat(source).inv()
    return result.as_quat()

def angle_diff(target, source):
    result = R.from_euler('xyz', target) * R.from_euler('xyz', source).inv()
    return result.as_euler('xyz')

def add_angles(delta, source, degrees=False):
    delta_rot = R.from_euler('xyz', delta, degrees=degrees)
    source_rot = R.from_euler('xyz', source, degrees=degrees)
    new_rot = delta_rot * source_rot
    return new_rot.as_euler('xyz', degrees=degrees)

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
