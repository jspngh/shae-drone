from dronekit import Gimbal, Vehicle, VehicleMode, SystemStatus, connect, time
from pymavlink.mavutil import mavlink
import math


class Solo:
    def __init__(self, vehicle):
        """
        :type vehicle: Vehicle
        """
        self.vehicle = vehicle
        return

    # Get all vehicle attributes (state)
    def print_state(self):
        print "Vehicle state:"
        print " Global Location: %s" % self.vehicle.location.global_frame
        print " Global Location (relative altitude): %s" % self.vehicle.location.global_relative_frame
        print " Local Location: %s" % self.vehicle.location.local_frame
        print " Attitude: %s" % self.vehicle.attitude
        print " Velocity: %s" % self.vehicle.velocity
        print " Battery: %s" % self.vehicle.battery
        print " Last Heartbeat: %s" % self.vehicle.last_heartbeat
        print " Heading: %s" % self.vehicle.heading
        print " Groundspeed: %s" % self.vehicle.groundspeed
        print " Airspeed: %s" % self.vehicle.airspeed
        print " Mode: %s" % self.vehicle.mode.name
        print " Is Armable?: %s" % self.vehicle.is_armable
        print " Armed: %s" % self.vehicle.armed

    def arm(self):
        self.vehicle.mode = VehicleMode("GUIDED")
        while self.vehicle.mode != "GUIDED":
            time.sleep(0.1)
        print "Control granted"
        if self.vehicle.armed is False:
            # Don't let the user try to arm until autopilot is ready
            print " Waiting for vehicle to initialise..."
            while not self.vehicle.is_armable:
                time.sleep(1)
            self.vehicle.armed = True
            print 'Vehicle Armed'

    # brake - Stop the solo moving
    def brake(self):
        mode = self.vehicle.mode
        msg = self.vehicle.message_factory.set_mode_encode(0, mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED, 17)
        self.vehicle.send_mavlink(msg)
        self.vehicle.flush()
        self.vehicle.mode = mode

    # land - Land the solo moving
    def land(self):
        self.vehicle.mode = VehicleMode("LAND")
        while self.vehicle.mode != "LAND":
            time.sleep(0.1)

    # takeoff - takeoff to some altitude, needs armed status - params: meters
    def takeoff(self, altitude_meters=1):
        if self.vehicle.mode != 'GUIDED':
            print '\033[91m' + "DroneDirectError: 'takeoff({0})' was not executed. Vehicle was not in GUIDED mode".format(altitude_meters) + '\033[0m'
            return

        while not self.vehicle.armed:
            print " Waiting for arming..."
            time.sleep(1)

        print "Taking off..."
        if self.vehicle.system_status != SystemStatus('STANDBY'):
            print "Already airborne"
            return
        self.vehicle.simple_takeoff(altitude_meters)
        # Wait until the vehicle reaches a safe height before processing the goto (otherwise the command
        #  after Vehicle.simple_takeoff will execute immediately).
        while self.vehicle.mode == 'GUIDED':
            # Break and return from function just below target altitude.
            if self.vehicle.location.global_relative_frame.alt >= altitude_meters * 0.95:
                print "Takeoff Complete"
                return
            time.sleep(1)
        print '\033[93m' + "DroneDirectError: 'takeoff({0})' was interrupted. Vehicle was swicthed out of GUIDED mode".format(altitude_meters) + '\033[0m'

    # step_left - Send the copter left some distance - params: distance meters
    def translate(self, x=0, y=0, z=0, wait_for_arrival=False, dist_thres=0.3):
        if self.fence_breach:
            raise StandardError("You are outside of the fence")
        if self.vehicle.mode != 'GUIDED':
            print '\033[91m' + "DroneDirectError: 'translate({0},{1},{2})' was not executed. Vehicle was not in GUIDED mode".format(x, y, z) + '\033[0m'
            return
        # limit our update rate
        if (time.time() - self.last_send_translate) < 1.0 / self.update_rate:
            return
        yaw = self.vehicle.attitude.yaw  # radians
        location = self.vehicle.location.global_relative_frame  # latlon

        # rotate to earth-frame angles
        x_ef = y * math.cos(yaw) - x * math.sin(yaw)
        y_ef = y * math.sin(yaw) + x * math.cos(yaw)

        latlon_to_m = 111319.5   # converts lat/lon to meters
        lat = x_ef / latlon_to_m + location.lat
        lon = y_ef / latlon_to_m + location.lon
        alt = z + location.alt
        msg = self.vehicle.message_factory.set_position_target_global_int_encode(
            0,  # time_boot_ms (not used)
            0, 0,  # target system, target component
            mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT,  # frame
            0b0000111111111000,  # type_mask (only speeds enabled)
            lat * 1e7,  # lat_int - X Position in WGS84 frame in 1e7 * meters
            lon * 1e7,  # lon_int - Y Position in WGS84 frame in 1e7 * meters
            alt,  # alt - Altitude in meters in AMSL altitude, not WGS84 if absolute or relative,
                  # above terrain if GLOBAL_TERRAIN_ALT_INT
            0,  # X velocity in NED frame in m/s
            0,  # Y velocity in NED frame in m/s
            0,  # Z velocity in NED frame in m/s
            0, 0, 0,  # afx, afy, afz acceleration (not supported yet, ignored in GCS_Mavlink)
            0, 0)  # yaw, yaw_rate (not supported yet, ignored in GCS_Mavlink)

        # send command to vehicle
        self.vehicle.send_mavlink(msg)
        self.vehicle.flush()
        self.last_send_translate = time.time()
        self.point(0)
        print "translating..."
        if wait_for_arrival:
            while self.vehicle.mode == "GUIDED":
                veh_loc = self.vehicle.location.global_relative_frame
                diff_lat_m = (lat - veh_loc.lat) * latlon_to_m
                diff_lon_m = (lon - veh_loc.lon) * latlon_to_m
                diff_alt_m = alt - veh_loc.alt
                dist_xyz = math.sqrt(diff_lat_m**2 + diff_lon_m**2 + diff_alt_m**2)
                if dist_xyz < dist_thres:
                    print "Arrived"
                    return
            print '\033[93m' + "DroneDirectError: 'translate({0},{1},{2})' was interrupted. Vehicle was switched out of GUIDED mode".format(x, y, z) + '\033[0m'

    def control_gimbal(self, pitch, roll, yaw):
        gmbl = Gimbal(vehicle=self.vehicle)
        while gmbl.pitch != pitch:
            gmbl.rotate(pitch, roll, yaw)
        gmbl.release()
