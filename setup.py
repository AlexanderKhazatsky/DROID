#!/usr/bin/env python

from distutils.core import setup

setup(name='r2d2',
      version='1.0',
      license='MIT License',
      install_requires=['scipy', 'zerorpc', 'gym', 'torch', 'torchvision', 'opencv-python==4.6.0.66', 'opencv-contrib-python==4.6.0.66', 'tqdm', 'imageio', 'Pillow', 'matplotlib', 'h5py', 'open3d', 'psutil', 'protobuf==3.20.1', 'mujoco==2.2.1', 'dm-control==1.0.5',],
     )
