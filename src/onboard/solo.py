import sys
import math
import logging
from threading import RLock
from pymavlink.mavutil import mavlink
from dronekit import VehicleMode, Battery, Attitude, SystemStatus, LocationGlobal, LocationGlobalRelative, time

from GoProManager import GoProManager
from GoProConstants import GOPRO_RESOLUTION, GOPRO_FRAME_RATE
from global_classes import Location, WayPoint, WayPointEncoder, DroneType, logformat, dateformat


## @ingroup Onboard
#
# The Solo class is a wrapper around DroneKit functionality that can also be used by drones other than the Solo.
# The most important functions are 'arm', 'takeoff', 'land' and 'visit_waypoint'.
class Solo:
    def __init__(self, vehicle, height=4, speed=5, update_rate=15, logging_level=logging.CRITICAL, log_type='console', filename=''):
        """
        Args:
            vehicle: a DroneKit Vehicle
            height: the height that the drone should fly on
            speed: the flying speed on the drone
            update_rate: not used by any of the functions used in Project Shae
            logging_level: the level that should be used for logging, e.g. DEBUG
            log_type: log to stdout ('console') or to a file ('file')
            filename: the name of the file if log_type is 'file'
        """
        ## a DroneKit vehicle, that will be used to control the drone
        self.vehicle = vehicle
        ## a lock to guarantee that no threads ask the drone for e.g. his location, while a takeoff is taking place
        self.solo_lock = RLock()  # make sure that only 1 thread can access the vehicle at the same time
        ## a boolean, when this becomes 'True', the solo should stop visiting waypoints
        self.is_halted = False

        # When you want to receive GoPro messages, this will have to be uncommented
        # However, using it might insert some instabilities

        # self.goproManager = GoProManager(logging_level=logging_level, log_type=log_type, filename=filename)
        # self.vehicle.add_attribute_listener('gopro_status', self.goproManager.state_callback)
        # self.vehicle.add_attribute_listener(attr_name='GOPRO_GET_RESPONSE', observer=self.goproManager.get_response_callback)
        # self.vehicle.add_message_listener(name='GOPRO_GET_RESPONSE', fn=self.goproManager.get_response_callback)
        # self.vehicle.add_attribute_listener('GOPRO_SET_RESPONSE', self.goproManager.set_response_callback)

        self.fence_breach = False
        self.last_send_point = 0
        self.last_send_move = 0
        self.last_send_translate = 0

        ## how close should the drone get to its WayPoint before it is considered "reached"
        self.distance_threshold = 1.0
        self.update_rate = update_rate  # this attribute is not used by any of the functions used in Project Shae
        ## the height that the drone should fly on
        self.height = height
        ## the flying speed on the drone
        self.speed = speed
        ## the amount of frames per second the camera uses
        self.camera_fps = None
        ## the resolution of the camera
        self.camera_resolution = None
        ## angle of the camera
        self.camera_angle = None
        ## the DroneType of the drone that is used
        self.drone_type = DroneType('3DR', 'Solo')

        # set up self.logger
        ## logger instance
        self.logger = logging.getLogger("Solo")
        formatter = logging.Formatter(logformat, datefmt=dateformat)
        if log_type == 'console':
            handler = logging.StreamHandler(stream=sys.stdout)
        elif log_type == 'file':
            handler = logging.FileHandler(filename=filename)
        handler.setFormatter(formatter)
        handler.setLevel(logging_level)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging_level)

        return

    ## arm the solo, making it available for automatic takeoff and flight
    def arm(self):
        self.solo_lock.acquire()
        self.vehicle.mode = VehicleMode("GUIDED")
        while self.vehicle.mode != "GUIDED":
            time.sleep(0.1)
        self.logger.debug("control granted")
        if self.vehicle.armed is False:
            # Don't let the user try to arm until autopilot is ready
            self.logger.debug("waiting for vehicle to initialise...")
            while not self.vehicle.is_armable:
                time.sleep(1)
            self.vehicle.armed = True
            self.logger.info("the solo is now armed")
        self.solo_lock.release()

    ## Launch the drone to predefined height, the drone has to be armed on beforehand
    def takeoff(self):
        self.solo_lock.acquire()
        if self.vehicle.mode != 'GUIDED':
            self.logger.error("DroneDirectError: 'takeoff({0})' was not executed. \
                              Vehicle was not in GUIDED mode".format(self.height))
            self.solo_lock.release()
            return -1

        while not self.vehicle.armed:
            self.logger.debug("waiting for arming...")
            time.sleep(1)

        if self.vehicle.system_status != SystemStatus('STANDBY'):
            self.logger.debug("solo was already airborne")
            loc = self.vehicle.location.global_frame
            loc.alt = loc.alt + self.height
            self.vehicle.commands.goto(loc)
            self.vehicle.flush()
            self.logger.debug("command flushed")
            self.solo_lock.release()
            return

        self.logger.info("the solo is now taking off")
        self.vehicle.simple_takeoff(self.height)
        # Wait until the vehicle reaches a safe height
        # while self.vehicle.mode == 'GUIDED':
        while True:
            self.logger.debug("solo is in {0} mode".format(self.vehicle.mode))
            if self.vehicle.location.global_relative_frame.alt >= self.height * 0.95:  # Trigger just below target alt.
                self.logger.info("the solo is now ready to fly")
                self.solo_lock.release()
                return 0
            time.sleep(1)
        # Sometimes the Solo will switch out of GUIDED mode during takeoff
        # If this happens, we will return -1 so we can try again
        self.logger.error("DroneDirectError: 'takeoff({0})' was interrupted. \
                          Vehicle was swicthed out of GUIDED mode".format(self.height))
        self.solo_lock.release()
        return -1

    ## Stop the drone from visiting waypoints, this does not land the drone
    def halt(self):
        self.solo_lock.acquire()
        self.is_halted = True
        self.solo_lock.release()

    # Stop the drone from moving, this does not land the drone
    def brake(self):
        self.solo_lock.acquire()
        mode = self.vehicle.mode
        msg = self.vehicle.message_factory.set_mode_encode(0, mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED, 17)
        self.vehicle.send_mavlink(msg)
        self.vehicle.flush()
        self.vehicle.mode = mode
        self.solo_lock.release()

    # Land the drone
    def land(self):
        self.solo_lock.acquire()
        self.vehicle.mode = VehicleMode("LAND")
        while self.vehicle.mode != "LAND":
            self.vehicle.mode = VehicleMode("LAND")
            time.sleep(0.1)
        self.logger.info("Landing Solo...")
        self.solo_lock.release()

    def visit_waypoint(self, waypoint):
        """
        Fly to the coordinates of the waypoint
        This function only returns when the solo has visited the waypoint

        Args:
            waypoint: a WayPoint
        """
        # Here we don't need to take the lock, since we want to be able to send heartbeats while we visit waypoints

        location = LocationGlobalRelative(lat=waypoint.location.latitude, lon=waypoint.location.longitude, alt=self.height)
        self.vehicle.simple_goto(location=location, airspeed=self.speed)

        latlon_to_m = 1.113195e5   # converts lat/lon to meters
        while self.vehicle.mode == "GUIDED":
            veh_loc = self.vehicle.location.global_relative_frame
            diff_lat_m = (location.lat - veh_loc.lat) * latlon_to_m
            diff_lon_m = (location.lon - veh_loc.lon) * latlon_to_m
            diff_alt_m = location.alt - veh_loc.alt
            dist_xyz = math.sqrt(diff_lat_m**2 + diff_lon_m**2 + diff_alt_m**2)
            if dist_xyz > self.distance_threshold and not self.is_halted:
                time.sleep(0.5)
            else:
                if not self.is_halted:
                    self.logger.info("Solo arrived at waypoint")
                else:
                    self.logger.info("Solo was halted")
                    self.is_halted = False  # reset the self.is_halted attribute
                return

    ## Point the copter in a direction
    def point(self, degrees, relative=True):
        """
        This won't be used in this project, but might prove useful for future uses
        """
        self.solo_lock.acquire()
        if self.fence_breach:
            raise StandardError("You are outside of the fence")
        if self.vehicle.mode != 'GUIDED':
            self.logger.error("DroneDirectError: 'point({0})' was not executed. \
                              Vehicle was not in GUIDED mode".format(degrees))
            self.solo_lock.release()
            return
        # limit our update rate
        if (time.time() - self.last_send_point) < 1.0 / self.update_rate:
            self.solo_lock.release()
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
        self.solo_lock.release()

    # step_left - Send the solo left some distance - params: distance meters
    def translate(self, x=0, y=0, z=0, wait_for_arrival=False):
        """
        This won't be used in this project, but might prove useful for future uses
        """
        self.solo_lock.acquire()
        if self.fence_breach:
            self.solo_lock.release()
            raise StandardError("You are outside of the fence")
        if self.vehicle.mode != 'GUIDED':
            self.logger.error("DroneDirectError: 'translate({0},{1},{2})' was not executed. \
                              Vehicle was not in GUIDED mode".format(x, y, z))
            self.solo_lock.release()
            return
        # limit our update rate
        if (time.time() - self.last_send_translate) < 1.0 / self.update_rate:
            self.solo_lock.release()
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
        self.logger.info("translating...")
        if wait_for_arrival:
            while self.vehicle.mode == "GUIDED":
                veh_loc = self.vehicle.location.global_relative_frame
                diff_lat_m = (lat - veh_loc.lat) * latlon_to_m
                diff_lon_m = (lon - veh_loc.lon) * latlon_to_m
                diff_alt_m = alt - veh_loc.alt
                dist_xyz = math.sqrt(diff_lat_m**2 + diff_lon_m**2 + diff_alt_m**2)
                if dist_xyz < self.distance_threshold:
                    self.logger.info("Arrived")
                    self.solo_lock.release()
                    return
            self.logger.error("DroneDirectError: 'translate({0},{1},{2})' was interrupted. \
                              Vehicle was switched out of GUIDED mode".format(x, y, z))
        self.solo_lock.release()

    def get_battery_level(self):
        self.solo_lock.acquire()
        batt = self.vehicle.battery
        self.solo_lock.release()
        return batt.level

    def get_drone_type(self):
        return self.drone_type

    def get_location(self):
        self.solo_lock.acquire()
        veh_loc = self.vehicle.location.global_relative_frame
        loc = Location(longitude=veh_loc.lon, latitude=veh_loc.lat)
        self.solo_lock.release()
        return loc

    def get_gps_signal_strength(self):
        self.solo_lock.acquire()
        ss = self.vehicle.gps_0.satellites_visible
        if ss is None:
            ss = -1
        self.solo_lock.release()
        return ss

    def get_speed(self):
        self.solo_lock.acquire()
        airspeed = self.vehicle.airspeed
        self.solo_lock.release()
        return airspeed

    def get_target_speed(self):
        return self.speed

    def set_target_speed(self, speed):
        """
        Args:
            speed: desired speed of the drone
        """
        self.speed = speed
        return

    def set_distance_threshold(self, threshold):
        """
        Args:
            threshold: threshold to use to determine wheter the Solo has reached a waypoint
        """
        self.distance_threshold = threshold
        return

    def get_height(self):
        self.solo_lock.acquire()
        loc = self.vehicle.location
        self.solo_lock.release()
        return loc.global_relative_frame.alt

    def get_target_height(self):
        return self.height

    def set_target_height(self, height):
        """
        Args:
            height: desired height of the drone
        """
        self.height = height
        return

    def get_orientation(self):
        self.solo_lock.acquire()
        att = self.vehicle.attitude
        self.solo_lock.release()
        return att.yaw

    def get_camera_angle(self):
         # self.solo_lock.acquire()
         # angle = self.vehicle.gimbal.pitch()
         # self.solo_lock.release()
        return angle

    def set_camera_angle(self, angle):
        """
        Args:
            angle: desired angle of the camera: 0 = ahead, 90 = down
        """
         # self.control_gimbal(-angle)
        return

    def get_camera_fps(self):
        self.logger.debug("sending gopro mavlink message")
        command = mavlink.GOPRO_COMMAND_VIDEO_SETTINGS
        msg = self.vehicle.message_factory.gopro_get_request_encode(0,
                                                                    mavlink.MAV_COMP_ID_GIMBAL,  # target system, target component
                                                                    command)
        self.vehicle.send_mavlink(msg)
        self.vehicle.flush()

        # wait some time for the video settings to be updated
        time.sleep(1)
        num_frame_rate = self.goproManager.videoFrameRate
        if num_frame_rate == GOPRO_FRAME_RATE.GOPRO_FRAME_RATE_12:
            return 12
        elif num_frame_rate == GOPRO_FRAME_RATE.GOPRO_FRAME_RATE_15:
            return 15
        elif num_frame_rate == GOPRO_FRAME_RATE.GOPRO_FRAME_RATE_24:
            return 24
        elif num_frame_rate == GOPRO_FRAME_RATE.GOPRO_FRAME_RATE_25:
            return 25
        elif num_frame_rate == GOPRO_FRAME_RATE.GOPRO_FRAME_RATE_30:
            return 30
        elif num_frame_rate == GOPRO_FRAME_RATE.GOPRO_FRAME_RATE_48:
            return 48
        elif num_frame_rate == GOPRO_FRAME_RATE.GOPRO_FRAME_RATE_50:
            return 50
        elif num_frame_rate == GOPRO_FRAME_RATE.GOPRO_FRAME_RATE_60:
            return 60
        elif num_frame_rate == GOPRO_FRAME_RATE.GOPRO_FRAME_RATE_80:
            return 80
        elif num_frame_rate == GOPRO_FRAME_RATE.GOPRO_FRAME_RATE_90:
            return 90
        elif num_frame_rate == GOPRO_FRAME_RATE.GOPRO_FRAME_RATE_100:
            return 100
        elif num_frame_rate == GOPRO_FRAME_RATE.GOPRO_FRAME_RATE_120:
            return 120
        elif num_frame_rate == GOPRO_FRAME_RATE.GOPRO_FRAME_RATE_240:
            return 250
        else:
            return 0  # something went wrong

    def set_camera_fps(self, fps):
        return

    def get_camera_resolution(self):
        self.logger.debug("sending gopro mavlink message")
        command = mavlink.GOPRO_COMMAND_VIDEO_SETTINGS
        msg = self.vehicle.message_factory.gopro_get_request_encode(0,
                                                                    mavlink.MAV_COMP_ID_GIMBAL,  # target system, target component
                                                                    command)
        self.vehicle.send_mavlink(msg)
        self.vehicle.flush()

        # wait some time for the video settings to be updated
        time.sleep(1)
        num_resolution = self.goproManager.videoResolution
        # we will only handle a subpart of all available resolutions
        # the others will not be used
        if num_resolution == GOPRO_RESOLUTION.GOPRO_RESOLUTION_480p:
            return 480
        elif num_resolution == GOPRO_RESOLUTION.GOPRO_RESOLUTION_720p:
            return 720
        elif num_resolution == GOPRO_RESOLUTION.GOPRO_RESOLUTION_960p:
            return 960
        elif num_resolution == GOPRO_RESOLUTION.GOPRO_RESOLUTION_1080p:
            return 1080
        elif num_resolution == GOPRO_RESOLUTION.GOPRO_RESOLUTION_1440p:
            return 1440
        else:
            return 0  # something went wrong

    def set_camera_resolution(self, resolution):
        return

    def control_gimbal(self, pitch=None, roll=None, yaw=None):
        self.solo_lock.acquire()
        self.logger.info("Operating Gimbal...")
        gmbl = self.vehicle.gimbal
        if pitch is None:
            pitch = gmbl.pitch()
        if roll is None:
            roll = gmbl.roll()
        if yaw is None:
            yaw = gmbl.yaw()

        while gmbl.pitch != pitch:
            gmbl.rotate(pitch, roll, yaw)
            print gmbl.pitch
            time.sleep(0.1)

        gmbl.release
        self.logger.info("Gimbal Operation Complete")
        self.solo_lock.release()

    def distance_to_waypoint(self, waypoint):
        """
        This function was taken from http://python.dronekit.io/examples/mission_basic.html

        Args:
            waypoint: WayPoint
        Returns:
            distance in metres to the waypoint
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

        Args:
            original_location: a Location
        Returns:
            a LocationGlobal object containing the latitude/longitude `dNorth` and `dEast` metres from the
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

        Args:
            aLocation1: a Location
            aLocation2: a Location
        Returns:
            the ground distance in metres between two LocationGlobal objects.
        """
        latlon_to_m = 1.113195e5   # converts lat/lon to meters
        dlat = aLocation2.latitude - aLocation1.latitude
        dlong = aLocation2.longitude - aLocation1.longitude
        return math.sqrt((dlat * dlat) + (dlong * dlong)) * latlon_to_m

    def condition_yaw(self, heading, relative=False):
        """
        This function was taken from http://python.dronekit.io/examples/guided-set-speed-yaw-demo.html
        This won't be used in this project, but might prove useful for future uses

        Send MAV_CMD_CONDITION_YAW message to point vehicle at a specified heading (in degrees).

        This method sets an absolute heading by default, but you can set the `relative` parameter
        to `True` to set yaw relative to the current yaw heading.

        By default the yaw of the vehicle will follow the direction of travel. After setting
        the yaw using this function there is no way to return to the default yaw "follow direction
        of travel" behaviour

        For more information see:
        http://ardupilot.org/copter/docs/common-mavlink-mission-command-messages-mav_cmd.html#mav-cmd-condition-yaw
        """
        if relative:
            is_relative = 1  # yaw relative to direction of travel
        else:
            is_relative = 0  # yaw is an absolute angle
        # create the CONDITION_YAW command using command_long_encode()
        msg = self.vehicle.message_factory.command_long_encode(
            0, 0,    # target system, target component
            mavlink.MAV_CMD_CONDITION_YAW,  # command
            0,  # confirmation
            heading,      # param 1, yaw in degrees
            0,            # param 2, yaw speed deg/s
            1,            # param 3, direction -1 ccw, 1 cw
            is_relative,  # param 4, relative offset 1, absolute angle 0
            0, 0, 0)      # param 5 ~ 7 not used
        # send command to vehicle
        self.vehicle.send_mavlink(msg)
