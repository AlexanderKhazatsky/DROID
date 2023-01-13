from r2d2.robot_env import RobotEnv
from r2d2.controllers.oculus_controller import VRPolicy
from r2d2.user_interface.data_collector import DataCollecter
from r2d2.user_interface.gui import RobotGUI

# Make the robot env
env = RobotEnv()
controller = VRPolicy()

# Make the data collector
data_collector = DataCollecter(env=env, controller=controller)

# Make the GUI
user_interface = RobotGUI(robot=data_collector)
