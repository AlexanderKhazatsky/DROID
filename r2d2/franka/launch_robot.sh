source /home/panda4/miniconda3/etc/profile.d/conda.sh # TODO: Revert to `source ~/anaconda3/etc/profile.d/conda.sh` before release.
conda activate polymetis-local
pkill -9 run_server
pkill -9 franka_panda_cl
# # If using the Robotiq gripper, keep the line below. Otherwise, comment it out.
# launch_robot.py robot_client=franka_hardware
# If using the Franka gripper, keep the line below. Otherwise, comment it out.
launch_robot.py robot_client=franka_hardware robot_client.executable_cfg.robot_ip=172.16.0.11
