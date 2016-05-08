import os
import sys
import time
import signal
import logging
import threading
from subprocess import Popen

from dronekit_sitl import SITL
from stream_simulator import StreamSimulator
from shae.onboard.server import Server
from shae.onboard.control_module import ControlModule
from shae.onboard.global_classes import logformat, dateformat


## @ingroup Simulator
class ServerSimulator(threading.Thread):
    def __init__(self, logger):
        threading.Thread.__init__(self)
        self.logger = logger
        self.server = Server(logger=logger, SIM=True)

    def run(self):
        self.server.run()

    def stop_thread(self):
        self.server.close()
        self.logger.debug('closed server')


## @ingroup Simulator
class ControlModuleSimulator(threading.Thread):
    def __init__(self, logger, log_lvl):
        threading.Thread.__init__(self)
        self.logger = logger
        self.control_module = ControlModule(logger=logger, log_level=log_lvl, SIM=True)

    def run(self):
        self.control_module.run()

    def stop_thread(self):
        self.control_module.close()
        self.logger.debug('closed control module')


## @brief The Simulator.
# @ingroup Simulator
class Simulator:
    def __init__(self):
        # SITL is the system in the loop simulator from dronekit
        self.sitl = SITL()
        self.sitl.download('solo', '1.2.0', verbose=True)
        sitl_args = ['solo', '--home=51.011447,3.711648,5,0']
        self.sitl.launch(sitl_args, await_ready=True, restart=True, verbose=True)

        #############################################################################################################
        # This is old code from when the onboard and simulator code were no modules yet
        # It is used to find the correct directories and start the correct processes, and might prove useful in the future

        # # This simulator can be invoked from the /simulator directory and the /tests directory
        # # Hardcoding relative paths should be avoided
        # current_dir = os.path.abspath(os.curdir)
        # parent_dir = os.path.dirname(current_dir)
        # drone_dir = os.path.join(parent_dir, "drone")
        # simulator_dir = os.path.join(parent_dir, "simulator")
        # onboard_dir = os.path.join(parent_dir, "onboard")
        # # Search for the drone directory containing the /simulator and /onboard directories
        # # Or stop if we find the /simulator and /onboard directories
        # while not (os.path.exists(drone_dir) or (os.path.exists(simulator_dir) and os.path.exists(onboard_dir))):
        #     current_dir = parent_dir
        #     parent_dir = os.path.dirname(current_dir)
        #     if parent_dir == current_dir:
        #         print "Could not find files"
        #         sys.exit(1)  # we did not find one of the necessary files
        #     drone_dir = os.path.join(parent_dir, "drone")
        #     simulator_dir = os.path.join(parent_dir, "simulator")
        #     onboard_dir = os.path.join(parent_dir, "onboard")
        # if os.path.exists(drone_dir):
        #     # we found the drone directory
        #     simulator_dir = os.path.join(drone_dir, "simulator")
        #     onboard_dir = os.path.join(drone_dir, "onboard")
        # video_dir = os.path.join(simulator_dir, "videos")
        # video_footage = os.path.join(video_dir, "testfootage.h264")
        # server = os.path.join(onboard_dir, "server.py")
        # control_module = os.path.join(onboard_dir, "control_module.py")
        # if not (os.path.exists(simulator_dir) and
        #         os.path.exists(onboard_dir) and
        #         os.path.exists(video_footage) and
        #         os.path.exists(server) and
        #         os.path.exists(control_module)):
        #     print "Could not find files"
        #     sys.exit(1)  # we did not find one of the necessary files

        # The server and control modules were started as seperate processes
        # This gave issues when trying to measure the code coverage, hence we changed it to threads

        # env_vars = os.environ.copy()
        # env_vars["COVERAGE_PROCESS_START"] = ".coveragerc"
        # self.server_process = Popen(['python2', server, '--level', 'debug', '--simulate'], env=env_vars)
        # self.control_process = Popen(['python2', control_module, '--level', 'debug', '--simulate'], env=env_vars)
        #############################################################################################################

        # Now that we have modules, we can just do this
        current_dir = os.path.dirname(os.path.realpath(__file__))  # this is the directory of the file
        video_footage = os.path.join(current_dir, 'videos', 'testfootage.h264')
        self.stream_simulator = StreamSimulator(video_footage)
        self.stream_simulator.start()

        log_level = logging.DEBUG
        simulation_logger = logging.getLogger("Simulator")
        formatter = logging.Formatter(logformat, datefmt=dateformat)
        handler = logging.StreamHandler(stream=sys.stdout)
        # To log to a file, this could be used
        # handler = logging.FileHandler(filename=log_file)
        handler.setFormatter(formatter)
        handler.setLevel(log_level)
        simulation_logger.addHandler(handler)
        simulation_logger.setLevel(log_level)
        self.logger = simulation_logger

        self.server_thread = ServerSimulator(logger=simulation_logger)
        self.control_thread = ControlModuleSimulator(logger=simulation_logger, log_lvl=log_level)
        self.server_thread.start()
        self.control_thread.start()

        # capture kill signals to send it to the subprocesses
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, signal, frame):
        self.logger.debug("Exiting simulator")
        self.stop()
        sys.exit(0)

    def stop(self):
        self.stream_simulator.stop_thread()
        self.logger.debug("Stopping server and control module")
        self.server_thread.stop_thread()
        self.control_thread.stop_thread()
        self.logger.debug("Sleeping")
        time.sleep(5.0)
        self.logger.debug("Stopping SITL")
        self.sitl.stop()


if __name__ == '__main__':
    simulator = Simulator()
    signal.pause()
