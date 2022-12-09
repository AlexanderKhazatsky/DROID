#!/usr/bin/env python

from distutils.core import setup

setup(name='r2d2',
      version='1.0',
      license='MIT License',
      install_requires=['scipy', 'pyrealsense2', 'moviepy', 'opencv-python', 'opencv-contrib-python', 'zerorpc', 'gym', 'Pillow', 'protobuf==3.20.1', 'mujoco==2.2.1', 'dm-control==1.0.5'],
     )
