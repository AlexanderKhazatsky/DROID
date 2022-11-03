from r2d2.franka.robot import FrankaRobot
import zerorpc

if __name__ == '__main__':
	s = zerorpc.Server(FrankaRobot())
	s.bind("tcp://0.0.0.0:4242")
	s.run()
