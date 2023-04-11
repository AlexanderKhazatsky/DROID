# R2D2: Residential Robot Demonstration Dataset

The repository provides the code for contributing to and using the R2D2 dataset.

NOTE: This repository has two dependencies listed below. If you are setting this up on the robot NUC (i.e., the "server" machine), (1) is required. If you are setting this up on the control workstation (i.e., the "client" machine), (2) is required. The Setup Guide below explains how to install these dependencies.

(1) https://github.com/facebookresearch/fairo

(2) https://github.com/rail-berkeley/oculus_reader

## Setup Guide
Setup this repository on both the server and client machine (i.e., NUC and workstation, respectively).

Note: It is possible to set everything up on just the NUC (without using a workstation) to get the code running and test things out. If you wish to do this, just follow every step below: all steps for the NUC and workstation combined.

Create and activate a conda environment:
```bash
conda create -n polymetis-local python=3.8 # Use python 3.8 to avoid dependency issues
conda activate polymetis-local
conda install mamba -n base -c conda-forge # For faster conda package installation
```

(On the NUC) Install Polymetis:
```bash
mamba install -c pytorch -c fair-robotics -c aihabitat -c conda-forge polymetis
```

(On the workstation) Install the Oculus VR teleoperation package:
```bash
pip install git+https://github.com/rail-berkeley/oculus_reader.git
```

If this is your first time using `oculus_reader`, please follow the setup instructions in the README here: https://github.com/rail-berkeley/oculus_reader.

Install other necessary packages:

```bash
pip install -e .
pip install --no-deps -r requirements.txt # --no-deps prevents installing package dependencies to avoid dependency issues
```

Regardless of the machine, go into r2d2/misc/parameters.py, and:
- Set robot_ip to match the IP address of your robot
- Set nuc_ip to match the IP address of your NUC
- Set gripper_type as 'franka' or 'robotiq' (default Franka gripper or Robotiq gripper)
- Set operator_position as 'front' or 'back' (teleoperator stands in front of or behind the robot)
- Set camera_type as 'realsense' or 'zed' (RealSense or ZED camera)

If you are setting this up on the robot NUC:
- In r2d2/misc/parameters.py, set "sudo_password" to your machine's corresponding sudo password. Sudo access is needed to launch the robot. The rest of the parameters can be ignored for now.

If you are setting this up on the control workstation:
- Go into r2d2/misc/parameters.py
- Set robot_ip to match the IP address of your robot
- Set nuc_ip to match the IP address of your NUC
- Update the Charuco board parameters to match yours. If you ordered it through calib.io, the parameters should be on the board.
- With the cameras plugged in, launch the GUI, and go to the calibration page. Clicking the camera ID’s will show you which view they correspond to. Update hand_camera_id, varied_3rd_person_camera_id, and fixed_3rd_person_camera_id values in parameters.py with the correct camera ID for each camera.

Identify where your `conda.sh` file is located. By default, most users will find it at the path `~/anaconda3/etc/profile.d/conda.sh`. After you locate it:
- Go into r2d2/franka/launch_robot.sh and modify the path to `conda.sh` on line 1. Use the ABSOLUTE path (e.g., `/home/username/anaconda3/etc/profile.d/conda.sh`).
- Go into r2d2/franka/launch_gripper.sh and modify the path to `conda.sh` on line 1. Use the ABSOLUTE path (e.g., `/home/username/anaconda3/etc/profile.d/conda.sh`).

Finally, modify the robot and gripper launch scripts to be compatible with either the default Franka gripper or Robotiq gripper:
- Go into r2d2/franka/launch_robot.sh and uncomment the `launch_robot.py` line corresponding to your gripper type. Remove or comment out the other line.
- Go into r2d2/franka/launch_gripper.sh and uncomment the `launch_gripper.py` line corresponding to your gripper type. Remove or comment out the other line.

## Usage

### Server Machine (NUC)
Activate the polymetis conda environment:

```bash
conda activate polymetis-local
```

Start the server:

```python
python scripts/server/run_server.py
```

### Client Machine (Workstation)
After activating your conda environment, try collecting a trajectory:

```python
python scripts/tests/collect_trajectory.py
```

To collect data, run:
```python
python scripts/main.py
```