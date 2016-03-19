import os
import json
import socket
import struct
import threading
import logging
import sys
from logging import Logger
from threading import RLock
from dronekit import connect, time
from solo import Solo
from global_classes import logging_level, DroneType, DroneTypeEncoder, Location, LocationEncoder, WayPoint, WayPointEncoder


class StatusHandler():
    """
    This class will take care of packets of the 'status' message type
    """
    def __init__(self, packet, message, solo):
        """
        :type solo: Solo
        """
        self.packet = packet
        self.message = message
        self.solo = solo

        # set up logging
        self.stat_logger = logging.getLogger("Status Handler")
        formatter = logging.Formatter('[%(levelname)s] %(message)s')
        handler = logging.StreamHandler(stream=sys.stdout)
        handler.setFormatter(formatter)
        handler.setLevel(logging_level)
        self.stat_logger.addHandler(handler)
        self.stat_logger.setLevel(logging_level)

    def handle_packet(self):
        try:
            if (self.message == "all_statuses"):  # all status attributes are requested
                battery = self.solo.get_battery_level()
                loc = self.solo.get_location()
                drone_type = self.solo.get_drone_type()
                speed = self.solo.get_speed()
                target_speed = self.solo.get_target_speed()
                height = self.solo.get_height()
                target_height = self.solo.get_target_height()
            else:                                       # this is an array with the attributes that were required
                if not isinstance(self.message, list):  # if it is not a list, something went wrong
                    self.stat_logger.warning("Message not a list")
                    raise ValueError
                for status_request in self.message:
                    if (status_request['Key'] == "battery_level"):
                        battery = self.solo.get_battery_level()
                        return {'battery_level': battery}

                    elif (status_request['Key'] == "current_location"):
                        loc = self.solo.get_location()
                        loc_message = json.dumps(loc, cls=LocationEncoder)
                        return loc_message

                    elif (status_request['Key'] == "drone_type"):
                        self.stat_logger.info("Getting dronetype")
                        drone_type = self.solo.get_drone_type()
                        dt_message = json.dumps(drone_type, cls=DroneTypeEncoder)
                        return dt_message

                    elif (status_request['Key'] == "waypoint_reached"):
                        print "handle"
                        # is_reached =

                    elif (status_request['Key'] == "next_waypoint"):
                        print "handle"
                        #  = self.solo.

                    elif (status_request['Key'] == "next_waypoints"):
                        print "handle"
                        #  = self.solo.

                    elif (status_request['Key'] == "speed"):
                        speed = self.solo.get_speed()
                        return {'speed': speed}

                    elif (status_request['Key'] == "selected_speed"):
                        target_speed = self.solo.get_target_speed()
                        return {'selected_speed': target_speed}

                    elif (status_request['Key'] == "height"):
                        height = self.solo.get_height()
                        return {'height': height}

                    elif (status_request['Key'] == "selected_height"):
                        target_height = self.solo.get_target_height()
                        return {'selected_height': target_height}

                    elif (status_request['Key'] == "camera_angle"):
                        camera_angle = self.solo.get_camera_angle()
                        return {'camera_angle': camera_angle}

                    elif (status_request['Key'] == "fps"):
                        fps = self.solo.get_camera_fps()
                        return {'fps': fps}

                    elif (status_request['Key'] == "resolution"):
                        resolution = self.solo.get_camera_resolution()
                        return {'resolution': resolution}

                    else:
                        raise ValueError  # if we get to this point, something went wrong
        except ValueError:
            print "handle error"
