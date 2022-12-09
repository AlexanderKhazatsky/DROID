from r2d2.misc.compression_utils import MP4Writer, DepthMP4Writer, encode_depth_data, decode_depth_data
from r2d2.misc.subprocess_utils import run_threaded_command
from collections import defaultdict
from queue import Queue, Empty
from copy import deepcopy
import numpy as np
import imageio
import h5py
import io


import os



def write_dict_to_hdf5(hdf5_file, data_dict):

	for key in data_dict.keys():
		# Examine Data #
		curr_data = data_dict[key]
		if type(curr_data) == list:
			curr_data = np.array(curr_data)
		dtype = type(curr_data)

		# Unwrap If Dictionary #
		if dtype == dict:
			if key not in hdf5_file: hdf5_file.create_group(key)
			write_dict_to_hdf5(hdf5_file[key], curr_data)
			continue

		# Make Room For Data #
		if key not in hdf5_file:
			if dtype != np.ndarray: dshape = ()
			else: dtype, dshape = curr_data.dtype, curr_data.shape
			hdf5_file.create_dataset(key, (1, *dshape), maxshape=(None, *dshape), dtype=dtype)
		else:
			hdf5_file[key].resize(hdf5_file[key].shape[0] + 1, axis=0)

		# Save Data #
		hdf5_file[key][-1] = curr_data

class TrajectoryWriter:

	def __init__(self, filepath, metadata=None, exists_ok=True): #TODO
		self._filepath = filepath
		self._hdf5_file = h5py.File(filepath, 'w')
		self._queue_dict = defaultdict(Queue)
		self._video_writers = {}
		self._video_buffers = {}
		self._open = True

		self._count_dict = defaultdict(lambda: 0)

		# Add Metadata
		if metadata is not None:
			self._update_metadata(metadata)

		# Start HDF5 Writer Thread #
		hdf5_writer = lambda data: write_dict_to_hdf5(self._hdf5_file, data)
		run_threaded_command(self._write_from_queue, args=(hdf5_writer, self._queue_dict['hdf5'], 'hdf5'))

	def write_timestep(self, timestep):
		self._update_video_files(timestep)
		del timestep['observations']['camera_dict']

		self._queue_dict['hdf5'].put(timestep)

	def _update_metadata(self, metadata):
		for key in metadata:
			self._hdf5_file.attr[key] = deepcopy(metadata[key])

	def _write_from_queue(self, writer, queue, video_id):
		while self._open:
			try: data = queue.get(timeout=1)
			except Empty: continue
			writer(data)
			queue.task_done()
			self._count_dict[video_id] += 1

	def _update_video_files(self, timestep):
		camera_dict = timestep['observations']['camera_dict']

		for camera_id in list(camera_dict):
			for image_id in list(camera_dict[camera_id]):

				# Get Frame #
				img = camera_dict[camera_id][image_id]
				del camera_dict[camera_id][image_id]

				# Create Writer And Buffer #
				video_id = '{0}_{1}'.format(camera_id, image_id)

				if video_id not in self._video_buffers:
					self._video_buffers[video_id] = io.BytesIO()
					Writer = DepthMP4Writer if 'depth' in video_id else MP4Writer
					self._video_writers[video_id] = Writer(self._video_buffers[video_id])
					run_threaded_command(self._write_from_queue, args=
							(self._video_writers[video_id].append, self._queue_dict[video_id], video_id))

					# if 'rgb' in video_id:
					# 	self._video_buffers[video_id] = io.BytesIO()
					# 	self._video_writers[video_id] = imageio.get_writer(self._video_buffers[video_id],
					# 		format='mp4', macro_block_size=1)					
					# 	run_threaded_command(self._write_from_queue, args=
					# 		(self._video_writers[video_id].append_data, self._queue_dict[video_id], video_id))
					# else:
					# 	folder = self._filepath[:-8] + '/depth/' + video_id
					# 	run_threaded_command(self._write_from_queue_depth, args=(folder, self._queue_dict[video_id], video_id))
				if 'depth' in video_id:
					new_img = img + 100
					encoded = encode_depth_data(new_img)
					decoded = decode_depth_data(encoded)
					import pdb; pdb.set_trace()
				self._queue_dict[video_id].put(img)

	def close(self):
		print(self._count_dict)

		# Finish Remaining Jobs #
		[queue.join() for queue in self._queue_dict.values()]

		# TODO: Organize back info camera_id/image_id
		video_folder = self._hdf5_file['observations'].create_group('videos')
		for video_id in self._video_writers:
			self._video_writers[video_id].close()
			serialized_video = np.asarray(self._video_buffers[video_id].getvalue())
			video_folder.create_dataset(video_id, data=serialized_video)

		self._hdf5_file.close()
		self._open = False
