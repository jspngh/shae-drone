import os
import sys
import copy
import json
import socket
import struct
import logging
import threading
import datetime
from logging import Logger
from threading import RLock
from dronekit import connect, time

from solo import Solo
from global_classes import DroneType, DroneTypeEncoder, Location, LocationEncoder, WayPoint, WayPointEncoder, WayPointQueue


class StatusHandler():
    """
    This class will take care of packets of the 'status' message type
    """
    def __init__(self, packet, message, solo, queue, logging_level):
        """
        :type solo: Solo
        :type queue: WayPointQueue
        """
        self.packet = packet
        self.message = message
        self.solo = solo
        self.waypoint_queue = queue

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
            if (self.message == "all_statuses"):  # TODO: all status attributes are requested
                battery = self.solo.get_battery_level()
                loc = self.solo.get_location()
                drone_type = self.solo.get_drone_type()
                speed = self.solo.get_speed()
                target_speed = self.solo.get_target_speed()
                height = self.solo.get_height()
                target_height = self.solo.get_target_height()

            elif (self.message == "heartbeat"):  # a heartbeat was requested
                loc = self.solo.get_location()
                wp_reached = False  # TODO
                data = {'Location': loc, 'Reached WP': wp_reached}
                return self.create_packet(data, cls=LocationEncoder)

            else:                                       # this is an array with the attributes that were required
                if not isinstance(self.message, list):  # if it is not a list, something went wrong
                    self.stat_logger.warning("Message not a list")
                    raise ValueError
                for status_request in self.message:
                    if (status_request['Key'] == "battery_level"):
                        battery = self.solo.get_battery_level()
                        data = {'battery_level': battery}
                        return self.create_packet(data)

                    elif (status_request['Key'] == "current_location"):
                        loc = self.solo.get_location()
                        loc_message = {'current_location': loc}
                        return self.create_packet(loc_message, cls=LocationEncoder)

                    elif (status_request['Key'] == "drone_type"):
                        self.stat_logger.info("Getting dronetype")
                        drone_type = self.solo.get_drone_type()
                        dt_message = json.dumps(drone_type, cls=DroneTypeEncoder)
                        return self.create_packet(dt_message)

                    elif (status_request['Key'] == "waypoint_reached"):
                        # this message is obsolete, instead the drone will let the workstation know whether
                        # it has reached the next waypoint through its status
                        self.stat_logger.info("Obsolete waypoint reached message received")

                    elif (status_request['Key'] == "next_waypoint"):
                        self.waypoint_queue.queue_lock.acquire()
                        next_wp = self.waypoint_queue.queue[0]
                        self.waypoint_queue.queue_lock.release()
                        data = json.dumps(next_wp, cls=WayPointEncoder)
                        return self.create_packet(data)

                    elif (status_request['Key'] == "next_waypoints"):
                        self.waypoint_queue.queue_lock.acquire()
                        wpq = copy.deepcopy(self.waypoint_queue.queue)
                        self.waypoint_queue.queue_lock.release()
                        path_message = {'next_waypoints': wpq}
                        data = json.dumps(path_message, cls=WayPointEncoder)
                        return self.create_packet(data)

                    elif (status_request['Key'] == "speed"):
                        speed = self.solo.get_speed()
                        data = {'speed': speed}
                        return self.create_packet(data)

                    elif (status_request['Key'] == "selected_speed"):
                        target_speed = self.solo.get_target_speed()
                        data = {'selected_speed': target_speed}
                        return self.create_packet(data)

                    elif (status_request['Key'] == "height"):
                        height = self.solo.get_height()
                        data = {'height': height}
                        return self.create_packet(data)

                    elif (status_request['Key'] == "selected_height"):
                        target_height = self.solo.get_target_height()
                        data = {'selected_height': target_height}
                        return self.create_packet(data)

                    elif (status_request['Key'] == "camera_angle"):
                        camera_angle = self.solo.get_camera_angle()
                        data = {'camera_angle': camera_angle}
                        return self.create_packet(data)

                    elif (status_request['Key'] == "fps"):
                        fps = self.solo.get_camera_fps()
                        data = {'fps': fps}
                        return self.create_packet(data)

                    elif (status_request['Key'] == "resolution"):
                        resolution = self.solo.get_camera_resolution()
                        data = {'resolution': resolution}
                        return self.create_packet(data)

                    else:
                        raise ValueError  # if we get to this point, something went wrong
        except ValueError:
            print "handle error"

    def create_packet(self, data, cls=None):
        """
        :type data: dict
        """
        now = time.time()
        localtime = time.localtime(now)
        milliseconds = '%03d' % int((now - int(now)) * 1000)
        timestamp = time.strftime('%Y/%m/%d-%H:%M:%S:', localtime) + milliseconds

        data.update({'MessageType': 'status', 'Timestamp': timestamp})
        return json.dumps(data, cls=cls)
