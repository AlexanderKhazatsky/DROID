# iris_robots


Moving the robot:

1) Go to the franka website (address=172.16.0.8), and unlock the joints
2) In three different terminal tabs, enter "conda activate polymetis-local"
3) In terminal 1, enter: launch_robot.py robot_client=franka_hardware robot_client.executable_cfg.robot_ip=172.16.0.8
4a) In terminal 2, run sudo chmod a+rw /dev/ttyUSB0
4b) In terminal 2, run launch_gripper.py gripper=robotiq_2f gripper.comport=/dev/ttyUSB0
5) In terminal 3, run whatever robot script you are trying to use.

Using The Oculus:
- 

Shutting down the robot:
- Lock the joints

