import sys
import time
import signal
from subprocess import Popen, PIPE
from dronekit_sitl import SITL
from stream_simulator import StreamSimulator


class Simulator:
    def __init__(self):
        # SITL is the system in the loop simulator from dronekit
        self.sitl = SITL()
        self.sitl.download('solo', '1.2.0', verbose=True)
        sitl_args = ['solo', '--home=51.022627,3.709807,5,0']
        self.sitl.launch(sitl_args, await_ready=True, restart=True)

        # TODO: test if waiting for sitl here is necessary
#        time.sleep(2)

        self.stream_simulator = StreamSimulator()
        self.stream_simulator.start()

        self.server_process = Popen(['python2', '../../onboard/server.py', '--level', 'debug', '--simulate'])
        self.control_process = Popen(['python2', '../../onboard/control_module.py', '--level', 'debug', '--simulate'])

        # capture kill signals to send it to the subprocesses
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, signal, frame):
        print "Exiting simulator"
        self.sitl.stop()
        self.server_process.send_signal(sig=signal)
        self.control_process.send_signal(sig=signal)
        self.stream_simulator.stop_thread()
        sys.exit(0)


if __name__ == '__main__':
    simulator = Simulator()
    signal.pause()
