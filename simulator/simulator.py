import sys
import time
import signal
from subprocess import Popen, PIPE


class Simulator:
    def __init__(self):
        self.server_process = Popen(['python2', '../onboard/server.py', '--level', 'debug', '--simulate'])
        self.control_process = Popen(['python2', '../onboard/control_module.py', '-level', 'debug', '-simulate'])

        # capture kill signals to send it to the subprocesses
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, signal, frame):
        print "Exiting simulator"
        self.server_process.send_signal(sig=signal)
        self.control_process.send_signal(sig=signal)
        sys.exit(0)


if __name__ == '__main__':
    simulator = Simulator()
    signal.pause()
