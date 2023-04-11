source ~/anaconda3/etc/profile.d/conda.sh
conda activate polymetis-local
pkill -9 gripper
# If using the Robotiq gripper, keep the lines below. Otherwise, comment them out.
chmod a+rw /dev/ttyUSB0
launch_gripper.py gripper=robotiq_2f gripper.comport=/dev/ttyUSB0
# If using the Franka gripper, keep the line below. Otherwise, comment it out.
# launch_gripper.py gripper=franka_hand gripper.executable_cfg.robot_ip=172.16.0.8 # NOTE: Change the robot_ip to match the robot_ip in r2d2.misc.parameters!
