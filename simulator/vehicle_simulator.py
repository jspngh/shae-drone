import time
from subprocess import Popen
from dronekit_sitl import SITL
from dronekit import connect, VehicleMode
# from stream_simulator import StreamSimulator


class SitlWrapper():
    def __init__(self):
        # Start SITL
        self.sitl = SITL()
        self.sitl.download('solo', '1.2.0', verbose=True)
        sitl_args = ['solo', '--home=51.022627,3.709807,5,0']
        self.sitl.launch(sitl_args, await_ready=True, restart=True)

        # stream_simulator = StreamSimulator()
        # stream_simulator.start

    def close(self):
        # Shut down simulator if it was started.
        if self.sitl is not None:
            self.sitl.stop()

        # Shut down stream simulator
        # self.stream_simulator.stop()
