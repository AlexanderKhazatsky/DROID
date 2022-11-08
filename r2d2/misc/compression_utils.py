from collections import defaultdict
from moviepy.editor import *
from io import BytesIO
from PIL import Image
import nupy as np

FRAMES_PER_SECOND = 15

def apply_img_compression(traj_data, compression_type=None):
	for obs in traj_data['observations']:
		for frame_dict in obs['images']:
			img = Image.fromarray(np.copy(frame_dict['array']))
			byte_array = io.BytesIO()
			img.save(byte_array, format=compression_type)
			frame_dict['array'] = byte_array

def invert_img_compression(traj_data):
	for obs in traj_data['observations']:
		for frame_dict in obs['images']:
			img = Image.open(np.copy(frame_dict['array']))
			frame_dict['array'] = np.array(img)

def apply_video_compression(traj_data):
	videos = defaultdict(list)
	for obs in traj_data['observations']:
		for frame_dict in obs['images']:
			img = np.copy(frame_dict['array'])
			sn = frame_dict['serial_number']
			videos[sn].append(img)
			del frame_dict['array']

	for sn in videos.keys():
		video_clip = ImageSequenceClip(videos[sn], fps=FRAMES_PER_SECOND)
		byte_array = io.BytesIO()

		my_clip.write_videofile(byte_array, codec='mp4')
		videos[sn] = byte_array

	traj_data['videos'] = videos

def invert_video_compression(traj_data):

	for sn in traj_data['videos'].keys():
		video_clip = VideoFileClip(traj_data['videos'][sn])
		traj_data['videos'][sn] = video_clip

	for i in range(len(traj_data['observations'])):
		obs = traj_data['observations'][i]
		for frame_dict in obs['images']:
			sn = frame_dict['serial_number']
			img = traj_data['videos'][sn].get_frame(i / FRAMES_PER_SECOND)
			frame_dict['array'] = np.copy(img)

	del traj_data['videos']