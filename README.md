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

Regardless of the machine, go into r2d2/misc/parameters.py, and:
- Set robot_ip to match the IP address of your robot
- Set nuc_ip to match the IP address of your NUC

If you are setting this up on the robot NUC:
- In r2d2/misc/parameters.py, set "sudo_password" to your machine's corresponding sudo password. Sudo access is needed to launch the robot. The rest of the parameters can be ignored for now.

If you are setting this up on the control workstation:
- Go into r2d2/misc/parameters.py
- Set robot_ip to match the IP address of your robot
- Set nuc_ip to match the IP address of your NUC
- Update the Charuco board parameters to match yours. If you ordered it through calib.io, the parameters should be on the board.
- With the cameras plugged in, launch the GUI, and go to the calibration page. Clicking the camera ID’s will show you which view they correspond to. Update hand_camera_id, varied_3rd_person_camera_id, and fixed_3rd_person_camera_id values in parameters.py with the correct camera ID for each camera.


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
