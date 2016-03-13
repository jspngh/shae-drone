from dronekit import connect, VehicleMode
import time
from dronekit_sitl import SITL


class VehicleSimulator():
    def __init__(self):
        self.vehicle = None
        self.sitl = None

    def get_vehicle(self):
        if self.vehicle is None:
            if self.sitl is None:
                # Start SITL
                self.sitl = SITL()
                self.sitl.download('solo', '1.2.0', verbose=True)
                sitl_args = ['-I0', '--model', 'quad', '--home=51.022593,3.709853,584,353']
                self.sitl.launch(sitl_args, await_ready=True, restart=True)
                connection_string = 'tcp:127.0.0.1:5760'

            # Connect to the Vehicle.
            #   Set `wait_ready=True` to ensure default attributes are populated before `connect()` returns.
            print "\nConnecting to vehicle on: %s" % connection_string
            self.vehicle = connect(connection_string, wait_ready=True)
            print self.vehicle
            self.vehicle.wait_ready('autopilot_version')

        return self.vehicle

    def close(self):
        # Close vehicle if its exists
        if self.vehicle is not None:
            print "Close vehicle object\n"
            self.vehicle.close()

        # Shut down simulator if it was started.
        if self.sitl is not None:
            self.sitl.stop()
