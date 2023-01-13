#!/usr/bin/env python

from distutils.core import setup

# setup(name='r2d2',
#       version='1.0',
#       license='MIT License',
#       install_requires=['scipy', 'opencv-python', 'opencv-contrib-python', 'zerorpc', 'gym',
#       'Pillow', 'matplotlib', 'h5py', 'open3d', 'protobuf==3.20.1', 'mujoco==2.2.1', 'dm-control==1.0.5'],
#      )

setup(name='r2d2',
      version='1.0',
      license='MIT License',
      install_requires=['scipy', 'zerorpc', 'gym', 'opencv-python==4.6.0.66', 'opencv-contrib-python==4.6.0.66',
      'Pillow', 'matplotlib', 'h5py', 'open3d', 'protobuf', 'mujoco', 'dm-control', 'imageio',
      'dm-robotics-moma', 'dm-robotics-transformations', 'dm-robotics-agentflow', 'dm-robotics-geometry',
      'dm-robotics-manipulation', 'dm-robotics-controllers'],
     )