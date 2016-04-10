import os
import sys
import time
import signal
from subprocess import Popen
from dronekit_sitl import SITL
from stream_simulator import StreamSimulator


class Simulator:
    def __init__(self):
        # SITL is the system in the loop simulator from dronekit
        self.sitl = SITL()
        self.sitl.download('solo', '1.2.0', verbose=True)
        sitl_args = ['solo', '--home=51.022627,3.709807,5,0']
        self.sitl.launch(sitl_args, await_ready=True, restart=True)

        # This simulator can be invoked from the /simulator directory and the /tests directory
        # Hardcoding relative paths should be avoided
        current_dir = os.path.abspath(os.curdir)
        parent_dir = os.path.dirname(current_dir)
        drone_dir = os.path.join(parent_dir, "drone")
        # Search for the root directory containing the /simulator and /tests directory
        while not (os.path.exists(drone_dir)):
            current_dir = parent_dir
            parent_dir = os.path.dirname(current_dir)
            if parent_dir == current_dir:
                print "Could not find files"
                sys.exit(1)  # we did not find one of the necessary files
            drone_dir = os.path.join(parent_dir, "drone")

        simulator_dir = os.path.join(drone_dir, "simulator")
        onboard_dir = os.path.join(drone_dir, "onboard")
        video_dir = os.path.join(simulator_dir, "videos")
        video_footage = os.path.join(video_dir, "testfootage.h264")
        server = os.path.join(onboard_dir, "server.py")
        control_module = os.path.join(onboard_dir, "control_module.py")
        if not (os.path.exists(simulator_dir) and
                os.path.exists(onboard_dir) and
                os.path.exists(video_footage) and
                os.path.exists(server) and
                os.path.exists(control_module)):
            print "Could not find files"
            sys.exit(1)  # we did not find one of the necessary files

        self.stream_simulator = StreamSimulator(video_footage)
        self.stream_simulator.start()

        self.server_process = Popen(['python2', server, '--level', 'debug', '--simulate'])
        self.control_process = Popen(['python2', control_module, '--level', 'debug', '--simulate'])

        # capture kill signals to send it to the subprocesses
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, signal, frame):
        print "Exiting simulator"
        self.stop()
        sys.exit(0)

    def stop(self):
        self.server_process.send_signal(sig=signal.SIGINT)
        self.control_process.send_signal(sig=signal.SIGINT)
        self.stream_simulator.stop_thread()
        time.sleep(0.5)
        self.sitl.stop()


if __name__ == '__main__':
    simulator = Simulator()
    signal.pause()
