from robot_env import RobotEnv
from controllers.oculus_controller import VRPolicy
import numpy as np
import time

env = RobotEnv(ip_address='172.16.0.1')
#env = RobotEnv()
controller = VRPolicy()

STEP_ENV = True
 
env.reset()
controller.reset_state()
print('READY')
max_steps = 10000
for i in range(max_steps):
	obs = env.get_state()
	a = controller.get_action(obs)
	if STEP_ENV: env.step(a)
	else: time.sleep(0.2)
	#print(np.round(a, 3))