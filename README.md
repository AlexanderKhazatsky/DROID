# R2D2: Residential Robot Demonstration Dataset

The repository provides the code for contributing to and using the R2D2 dataset.

NOTE: Depending on whether this repository is being installed on the server or client machine, it may expect either of the two repositories to be setup:

1) https://github.com/facebookresearch/fairo
2) https://github.com/rail-berkeley/oculus_reader

## Setup Guide
Setup this repository on both the server and client machine (ie: NUC and workstation)

Install the necesary packages:

```bash
pip install -e .

# Done like this to avoid dependency issues
pip install dm-robotics-moma==0.4.0 --no-deps
pip install dm-robotics-transformations==0.4.0 --no-deps
pip install dm-robotics-agentflow==0.4.0 --no-deps
pip install dm-robotics-geometry==0.4.0 --no-deps
pip install dm-robotics-manipulation==0.4.0 --no-deps
pip install dm-robotics-controllers==0.4.0 --no-deps
```

In r2d2/misc/parameters.py, set "sudo_password" to your machine's corresponding sudo password. Sudo access is needed to launch the robot.

## Usage

### Server Machine
Activate the polymetis conda environment:
```bash conda activate polymetis-local```

Start the server:
```python python scripts/server/run_server.py```

### Client Machine
Run a basic test with the desired parameters:
```python python scripts/tests/basic_test.py```
