import math
from pymavlink.mavutil import mavlink
from dronekit import VehicleMode, SystemStatus, LocationGlobal, LocationGlobalRelative, time
from global_classes import Location, WayPoint, WayPointEncoder


class Solo:
    def __init__(self, vehicle, update_rate=15):
        """
        :type vehicle: Vehicle
        """
        self.vehicle = vehicle
        self.fence_breach = False
        self.last_send_point = 0
        self.last_send_move = 0
        self.last_send_translate = 0
        self.update_rate = update_rate
        self.height = 3
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
            self.vehicle.mode = VehicleMode("LAND")
            time.sleep(0.1)
        print "Landing Solo..."

    # takeoff - takeoff to some altitude, needs armed status - params: meters
    def takeoff(self):
        if self.vehicle.mode != 'GUIDED':
            print '\033[91m' + "DroneDirectError: 'takeoff({0})' was not executed. Vehicle was not in GUIDED mode".format(self.height) + '\033[0m'
            return

        while not self.vehicle.armed:
            print " Waiting for arming..."
            time.sleep(1)

        print "Taking off..."
        if self.vehicle.system_status != SystemStatus('STANDBY'):
            print "Already airborne"
            return
        self.vehicle.simple_takeoff(self.height)
        # Wait until the vehicle reaches a safe height before processing the goto (otherwise the command
        #  after Vehicle.simple_takeoff will execute immediately).
        while self.vehicle.mode == 'GUIDED':
            if self.vehicle.location.global_relative_frame.alt >= self.height * 0.95:  # Trigger just below target alt.
                print "Takeoff Complete"
                return
            time.sleep(1)
        print '\033[93m' + "DroneDirectError: 'takeoff({0})' was interrupted. Vehicle was swicthed out of GUIDED mode".format(self.height) + '\033[0m'

    # point - Point the copter in a direction
    def point(self, degrees, relative=True):

        if self.fence_breach:
            raise StandardError("You are outside of the fence")
        if self.vehicle.mode != 'GUIDED':
            print '\033[91m' + "DroneDirectError: 'point({0})' was not executed. Vehicle was not in GUIDED mode".format(degrees) + '\033[0m'
            return
        # limit our update rate
        if (time.time() - self.last_send_point) < 1.0 / self.update_rate:
            return
        if relative:
            is_relative = 1  # yaw relative to direction of travel
        else:
            is_relative = 0  # yaw is an absolute angle

        if degrees != 0:
            direction = int(degrees / abs(degrees))
        else:
            direction = 1
        degrees = degrees % 360
        # create the CONDITION_YAW command using command_long_encode()
        msg = self.vehicle.message_factory.command_long_encode(
            0, 0,    # target system, target component
            mavlink.MAV_CMD_CONDITION_YAW,  # command
            0,  # confirmation
            degrees,      # param 1, yaw in degrees
            0,            # param 2, yaw speed deg/s
            direction,    # param 3, direction -1 ccw, 1 cw
            is_relative,  # param 4, relative offset 1, absolute angle 0
            0, 0, 0)      # param 5 ~ 7 not used
        # send command to vehicle
        self.vehicle.send_mavlink(msg)
        self.vehicle.flush()
        self.last_send_point = time.time()

    # step_left - Send the solo left some distance - params: distance meters
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

        latlon_to_m = 1.113195e5   # converts lat/lon to meters
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

    def visit_waypoint(self, waypoint, dist_thres=0.3):
        """
        :type waypoint: WayPoint
        """
        latlon_to_m = 1.113195e5   # converts lat/lon to meters

        location = LocationGlobalRelative(lat=waypoint.location.latitude, lon=waypoint.location.longitude, alt=self.height)
        self.vehicle.simple_goto(location=location, groundspeed=10)

        while self.vehicle.mode == "GUIDED":
            veh_loc = self.vehicle.location.global_relative_frame
            diff_lat_m = (location.lat - veh_loc.lat) * latlon_to_m
            diff_lon_m = (location.lon - veh_loc.lon) * latlon_to_m
            diff_alt_m = location.alt - veh_loc.alt
            dist_xyz = math.sqrt(diff_lat_m**2 + diff_lon_m**2 + diff_alt_m**2)
            if dist_xyz > dist_thres:
                time.sleep(0.5)
            else:
                return

    def control_gimbal(self, pitch, roll, yaw):
        print "Operating Gimbal..."
        gmbl = self.vehicle.gimbal
        while gmbl.pitch != pitch:
            gmbl.rotate(pitch, roll, yaw)
            print gmbl.pitch
            time.sleep(0.1)
        gmbl.release
        print "Gimbal Operation Complete"

    def distance_to_waypoint(self, waypoint):
        """
        This function was taken from http://python.dronekit.io/examples/mission_basic.html

        :type waypoint: WayPoint
        :returns: distance in metres to the waypoint
        """
        lat = waypoint.location.latitude
        lon = waypoint.location.longitude
        alt = self.height

        target_waypoint_location = LocationGlobalRelative(lat, lon, alt)
        distance_to_point = self.get_distance_metres(self.vehicle.location.global_frame, target_waypoint_location)
        return distance_to_point

    def get_location_metres(self, original_location, dNorth, dEast):
        """
        This function was taken from http://python.dronekit.io/examples/mission_basic.html

        :type original_location: Location
        :returns: a LocationGlobal object containing the latitude/longitude `dNorth` and `dEast` metres from the
                  specified `original_location`. The returned Location has the same `alt` value
                  as `original_location`.
        """
        earth_radius = 6378137.0  # Radius of "spherical" earth
        # Coordinate offsets in radians
        dLat = dNorth / earth_radius
        dLon = dEast / (earth_radius * math.cos(math.pi * original_location.lat / 180))

        # New position in decimal degrees
        newlat = original_location.latitude + (dLat * 180 / math.pi)
        newlon = original_location.longitude + (dLon * 180 / math.pi)
        return LocationGlobal(newlat, newlon, original_location.alt)

    def get_distance_metres(self, aLocation1, aLocation2):
        """
        This function was taken from http://python.dronekit.io/examples/mission_basic.html

        :type aLocation1: Location
        :type aLocation2: Location
        :returns: the ground distance in metres between two LocationGlobal objects.
        """
        latlon_to_m = 1.113195e5   # converts lat/lon to meters
        dlat = aLocation2.latitude - aLocation1.latitude
        dlong = aLocation2.longitude - aLocation1.longitude
        return math.sqrt((dlat * dlat) + (dlong * dlong)) * latlon_to_m
