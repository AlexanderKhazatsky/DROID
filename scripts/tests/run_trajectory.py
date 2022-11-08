from r2d2.robot_env import RobotEnv
from r2d2.controllers.oculus_controller import VRPolicy
from r2d2.misc import trajectory_utils
import numpy as np

# Test Parameters #
server_is_client = False
server_ip_address = '172.16.0.1'
use_oculus = True
max_steps = 1000
# Test Parameters #


ip_address = None if server_is_client else server_ip_address
env = RobotEnv(ip_address=ip_address)

if use_oculus:
    controller = VRPolicy()
    controller.reset_state()
else:
    controller = lambda obs: np.array([0.01, 0, 0, 0, 0, 0, 0])
    
print('READY')
trajectory_utils.collect_trajectory(env, controller=controller, wait_for_controller=True)

# for i in range(max_steps):
# 	obs = env.get_state()
# 	a = controller.get_action(obs)
# 	env.step(a)









# from r2d2.robot_env import RobotEnv
# from r2d2.controllers.oculus_controller import VRPolicy
# import numpy as np

# # Test Parameters #
# server_is_client = False
# server_ip_address = '172.16.0.1'
# use_oculus = True
# max_steps = 1000
# # Test Parameters #


# ip_address = None if server_is_client else server_ip_address
# env = RobotEnv(ip_address=ip_address)
# env.reset()

# if use_oculus:
#     controller = VRPolicy()
#     controller.reset_state()
# else:
#     controller = lambda obs: np.array([0.01, 0, 0, 0, 0, 0, 0])
    
# print('READY')
# for i in range(max_steps):
# 	obs = env.get_state()
# 	a = controller.get_action(obs)
# 	env.step(a)
