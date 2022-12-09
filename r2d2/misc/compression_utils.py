from numba import njit, prange
import numpy as np
import imageio
import time

MIN_DEPTH = 0
MAX_DEPTH = 2000

#@njit
def depth_to_rgb(depth):
	d = (depth - MIN_DEPTH) / (MAX_DEPTH - MIN_DEPTH) * 1529
	rgb = np.zeros((3), dtype=np.uint8)

	# Get R Value #
	if (0 <= d <= 255) or (1275 < d <= 1529): rgb[0] = 255
	elif (255 < d <= 510): rgb[0] = 255 - d
	elif (510 < d <= 1020): rgb[0] = 0
	elif (1020 < d <= 1275): rgb[0] = d - 1020
	else: raise ValueError

	# Get G Value #
	if (0 < d <= 255): rgb[1] = d #possible bug (<)
	elif (255 < d <= 510): rgb[1] = 255
	elif (510 < d <= 765): rgb[1] = 765 - d
	elif (765 < d <= 1529): rgb[1] = 0
	else: raise ValueError

	# Get B Value #
	if (0 < d <= 765): rgb[2] = d  #possible bug (<)
	elif (765 < d <= 1020): rgb[2] = d - 765
	elif (1020 < d <= 1275): rgb[2] = 255
	elif (1275 < d <= 1529): rgb[2] = 1529 - d
	else: raise ValueError

	return rgb

#@njit
def rgb_to_depth(rgb):
	r, g, b = rgb[0], rgb[1], rgb[2]

	if (r >= g) and (r >= b) and (g > b): d = g - b
	elif (r >= g) and (r >= b) and (g <= b): d = g - b + 1529
	elif (g >= r) and (g >= b): d = b - r + 510
	elif (b >= g) and (b >= r): d = r - g + 1020
	else: raise ValueError

	depth = MIN_DEPTH + ((MAX_DEPTH - MIN_DEPTH) * d) / 1529

	return np.uint16(depth)

#@njit(parallel=True)
def encode_depth_data(data):
	data = np.clip(data, a_min=MIN_DEPTH, a_max=MAX_DEPTH)
	encoding = np.zeros((data.shape[0], data.shape[1], 3), dtype=np.uint8)
	for i in range(data.shape[0]):
		for j in range(data.shape[1]):
			print(data[i, j])
			rgb = depth_to_rgb(data[i, j])
			d = rgb_to_depth(rgb)

			if data[i, j] != d: import pdb; pdb.set_trace()

			encoding[i, j] = depth_to_rgb(data[i, j])
	return encoding

#@njit(parallel=True)
def decode_depth_data(data):
	decoding = np.zeros((data.shape[0], data.shape[1]), dtype=np.uint16)
	for i in range(data.shape[0]):
		for j in range(data.shape[1]):
			decoding[i, j] = rgb_to_depth(data[i, j])
	return decoding

class MP4Writer:
	def __init__(self, filepath):
		self._writer = imageio.get_writer(filepath,
			format='mp4', macro_block_size=1)

	def append(self, img):
		self._writer.append_data(img)

	def close(self):
		self._writer.close()

class DepthMP4Writer(MP4Writer):
	def append(self, img):
		start = time.time()
		data = encode_depth_data(img)
		print('Compress Time: ', time.time() - start)
		self._writer.append_data(data)

def mp4_to_frames(filepath, depth=False):
	reader = imageio.get_reader(filepath, format='mp4')
	if depth: frames = [decode_depth_data(d) for d in reader]
	else: frames = [d for d in reader]
	return frames


# from collections import defaultdict
# from moviepy.editor import *
# from io import BytesIO
# from PIL import Image
# import numpy as np

# FRAMES_PER_SECOND = 15

# def apply_img_compression(traj_data, compression_type):
# 	for obs in traj_data['observations']:
# 		for frame_dict in obs['images']:
# 			img = Image.fromarray(frame_dict['array'])
# 			byte_array = BytesIO()
# 			try:
# 				img.save(byte_array, format=compression_type)
# 				print('success!')
# 			except:
# 				import pdb; pdb.set_trace()
# 			frame_dict['compressed_array'] = byte_array
# 			del frame_dict['array']

# def invert_img_compression(traj_data):
# 	for obs in traj_data['observations']:
# 		for frame_dict in obs['images']:
# 			img = Image.open(frame_dict['compressed_array'])
# 			frame_dict['array'] = np.array(img)
# 			del frame_dict['compressed_array']

# def apply_video_compression(traj_data):
# 	videos = defaultdict(list)
# 	for obs in traj_data['observations']:
# 		for frame_dict in obs['images']:
# 			img = np.copy(frame_dict['array'])
# 			sn = frame_dict['serial_number']
# 			videos[sn].append(img)
# 			del frame_dict['array']

# 	for sn in videos.keys():
# 		video_clip = ImageSequenceClip(videos[sn], fps=FRAMES_PER_SECOND)
# 		byte_array = BytesIO()

# 		video_clip.write_videofile(byte_array, codec='mp4')
# 		videos[sn] = byte_array

# 	traj_data['videos'] = videos

# def invert_video_compression(traj_data):

# 	for sn in traj_data['videos'].keys():
# 		video_clip = VideoFileClip(traj_data['videos'][sn])
# 		traj_data['videos'][sn] = video_clip

# 	for i in range(len(traj_data['observations'])):
# 		obs = traj_data['observations'][i]
# 		for frame_dict in obs['images']:
# 			sn = frame_dict['serial_number']
# 			img = traj_data['videos'][sn].get_frame(i / FRAMES_PER_SECOND)
# 			frame_dict['array'] = np.copy(img)

# 	del traj_data['videos']