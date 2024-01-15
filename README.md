# R2D2: Residential Robot Demonstration Dataset

The repository provides the code for contributing to and using the R2D2 dataset.

NOTE: This repository has two dependencies listed below. If you are setting this up on the robot NUC, (1) is required. If you are setting this up on the control workstation, (2) is required:

(1) https://github.com/facebookresearch/fairo

(2) https://github.com/rail-berkeley/oculus_reader

## Setup Guide
Setup this repository on both the server and client machine (ie: NUC and workstation)

Install the necesary packages:

```bash
pip install -e .

# Done like this to avoid dependency issues
pip install dm-robotics-moma==0.5.0 --no-deps
pip install dm-robotics-transformations==0.5.0 --no-deps
pip install dm-robotics-agentflow==0.5.0 --no-deps
pip install dm-robotics-geometry==0.5.0 --no-deps
pip install dm-robotics-manipulation==0.5.0 --no-deps
pip install dm-robotics-controllers==0.5.0 --no-deps
```

If you are using miniconda instead of anaconda:
- Go into r2d2/franka, then open launch_gripper.sh and launch_robot.sh
- In both files, change the word anaconda to miniconda, change the paths to be absolute (ie. starting from /home), and save it
- Go into scripts/server, and do the same thing to launch_server.sh

Regardless of the machine, go into r2d2/misc/parameters.py, and:
- Set robot_ip to match the IP address of your robot
- Set nuc_ip to match the IP address of your NUC

If you are setting this up on the robot NUC:
- In r2d2/misc/parameters.py, set "sudo_password" to your machine's corresponding sudo password. Sudo access is needed to launch the robot. The rest of the parameters can be ignored for now.
- For the robot_type variable, enter 'fr3' or 'panda' depending on which Franka robot you are using

If you are setting this up on the control workstation:
- Go into r2d2/misc/parameters.py
- Set robot_serial_number to match your robot's serial number (found on your franka website, under Settings -> Franka World -> Control S/N)
- For the robot_type variable, enter 'fr3' or 'panda' depending on which Franka robot you are using
- Update the Charuco board parameters to match yours. If you ordered it through calib.io, the parameters should be on the board.
- With the cameras plugged in, launch the GUI, and go to the calibration page. Clicking the camera ID’s will show you which view they correspond to. Update hand_camera_id, varied_3rd_person_camera_id, and fixed_3rd_person_camera_id values in parameters.py with the correct camera ID for each camera.

To make R2D2 compatible with polymetis:
- If you have an FR3, you will need [these](https://drive.google.com/drive/folders/178-MJTAVV0m5_RDs2ScUNcYameGDA0Eg?usp=sharing) files
- If you have a Panda, you will need [these](https://drive.google.com/drive/folders/1wXTQQbFKjd9ed3yKxB4td9GzA_XrR7Xk?usp=sharing) files
- Go into fairo/polymetis/polymetis/conf/robot_client/:
  - Delete the default franka_hardware.yaml file
  - Replace it with the franka_hardware[robot_name].yaml file from the folder linked above for your respective robot
  - Delete the “[robot_name]” text from the file name. For example, change franka_hardware[FR3].yaml to  franka_hardware.yaml
  - IMPORTANT: Open up your new franka_hardware.yaml file, and change executable_cfg.robot_ip to match your robot’s IP address
- Go into fairo/polymetis/polymetis/conf/robot_model/:
  - Delete the default franka_panda.yaml file
  - Replace it with the franka_panda[robot_name].yaml file from the folder linked above for your respective robot
  - Delete the “[robot_name]” text from the file name. For example, change franka_panda[FR3].yaml to  franka_panda.yaml
  - Note: Yes, this might seem a bit wrong if you have an FR3, but the file needs to be named franka_panda.yaml

## Usage

### Server Machine
Activate the polymetis conda environment:

```bash
conda activate polymetis-local
```

Start the server:

```python
python scripts/server/run_server.py
```

### Client Machine
After activating your conda environment, try collecting a trajectory:

```python
python scripts/tests/collect_trajectory.py
```

To collect data, run:
```python
python scripts/main.py
```
