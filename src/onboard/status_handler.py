import sys
import copy
import json
import logging
from dronekit import time

from solo import Solo
from global_classes import DroneTypeEncoder, LocationEncoder, WayPoint, WayPointEncoder, WayPointQueue, logformat, dateformat


## @ingroup Onboard
# @brief This class will take care of packets of the 'status' message type
class StatusHandler():
    def __init__(self, solo, queue, logging_level, log_type='console', filename=''):
        """
        Initiate the handler

        Args:
            solo: Solo instance
            queue: WayPointQueue instance
            logging_level: the level that should be used for logging, e.g. DEBUG
            log_type: log to stdout ('console') or to a file ('file')
            filename: the name of the file if log_type is 'file'
        """
        ## The entire request from the workstation
        self.packet = None
        ## Message component from the request
        self.message = None
        ## Solo instance
        self.solo = solo
        ## WayPointQueue instance
        self.waypoint_queue = queue

        # set up logging
        ## logger instance
        self.stat_logger = logging.getLogger("Status Handler")
        formatter = logging.Formatter(logformat, datefmt=dateformat)
        if log_type == 'console':
            handler = logging.StreamHandler(stream=sys.stdout)
        elif log_type == 'file':
            handler = logging.FileHandler(filename=filename)
        handler.setFormatter(formatter)
        handler.setLevel(logging_level)
        self.stat_logger.addHandler(handler)
        self.stat_logger.setLevel(logging_level)

    def handle_packet(self, packet, message):
        self.packet = packet
        self.message = message
        if (self.message == "all_statuses"):
            self.waypoint_queue.queue_lock.acquire()
            last_wayp_ord = self.waypoint_queue.last_waypoint_order
            self.waypoint_queue.queue_lock.release()

            battery = self.solo.get_battery_level()
            gps_signal_strength = self.solo.get_gps_signal_strength()
            loc = self.solo.get_location()
            orientation = self.solo.get_orientation()
            drone_type = self.solo.get_drone_type()
            speed = self.solo.get_speed()
            target_speed = self.solo.get_target_speed()
            height = self.solo.get_height()
            target_height = self.solo.get_target_height()
            drone_type = self.solo.get_drone_type()
            drone_type.__dict__

            data = {'current_location': loc,
                    'waypoint_order': last_wayp_ord,
                    'battery_level': battery,
                    'gps_signal': gps_signal_strength,
                    'orientation': orientation,
                    'speed': speed,
                    'selected_speed': target_speed,
                    'height': height,
                    'selected_height': target_height,
                    'drone_type': drone_type.__dict__}
            return self.create_packet(data, cls=LocationEncoder, heartbeat=False)

        elif (self.message == "heartbeat"):  # a heartbeat was requested
            self.waypoint_queue.queue_lock.acquire()
            last_wayp_ord = self.waypoint_queue.last_waypoint_order
            self.waypoint_queue.queue_lock.release()
            height = self.solo.get_height()
            battery = self.solo.get_battery_level()
            gps_signal_strength = self.solo.get_gps_signal_strength()
            loc = self.solo.get_location()
            orientation = self.solo.get_orientation()

            data = {'current_location': loc,
                    'waypoint_order': last_wayp_ord,
                    'orientation': orientation,
                    'battery_level': battery,
                    'gps_signal': gps_signal_strength,
                    'height': height}

            return self.create_packet(data, cls=LocationEncoder, heartbeat=True)

        else:                                       # this is an array with the attributes that were required
            if not isinstance(self.message, list):  # if it is not a list, something went wrong
                self.stat_logger.warning("Message not a list")
                raise ValueError("FormatError")
            for status_request in self.message:
                if (status_request['key'] == "battery_level"):
                    battery = self.solo.get_battery_level()
                    data = {'battery_level': battery}
                    return self.create_packet(data)

                if (status_request['key'] == "gps_signal"):
                    gps_signal_strength = self.solo.get_gps_signal_strength()
                    data = {'gps_signal': gps_signal_strength}
                    return self.create_packet(data)

                elif (status_request['key'] == "current_location"):
                    loc = self.solo.get_location()
                    loc_message = {'current_location': loc}
                    return self.create_packet(loc_message, cls=LocationEncoder)

                elif (status_request['key'] == "drone_type"):
                    self.stat_logger.info("Getting dronetype")
                    drone_type = self.solo.get_drone_type()
                    return self.create_packet({'drone_type': drone_type}, cls=DroneTypeEncoder)

                elif (status_request['key'] == "waypoint_order"):
                    # this message is obsolete, instead the drone will let the workstation know whether
                    # it has reached the next waypoint through its status
                    self.stat_logger.info("Obsolete waypoint reached message received")

                elif (status_request['key'] == "next_waypoint"):
                    self.waypoint_queue.queue_lock.acquire()
                    next_wp = self.waypoint_queue.queue[0]
                    self.waypoint_queue.queue_lock.release()
                    data = json.dumps(next_wp, cls=WayPointEncoder)  # TODO: remove the json.dumps
                    return self.create_packet(data)

                elif (status_request['key'] == "next_waypoints"):
                    self.waypoint_queue.queue_lock.acquire()
                    wpq = copy.deepcopy(self.waypoint_queue.queue)
                    self.waypoint_queue.queue_lock.release()
                    path_message = {'next_waypoints': wpq}
                    data = json.dumps(path_message, cls=WayPointEncoder)  # TODO: remove the json.dumps
                    return self.create_packet(data)

                elif (status_request['key'] == "speed"):
                    speed = self.solo.get_speed()
                    data = {'speed': speed}
                    return self.create_packet(data)

                elif (status_request['key'] == "selected_speed"):
                    target_speed = self.solo.get_target_speed()
                    data = {'selected_speed': target_speed}
                    return self.create_packet(data)

                elif (status_request['key'] == "height"):
                    height = self.solo.get_height()
                    data = {'height': height}
                    return self.create_packet(data)

                elif (status_request['key'] == "selected_height"):
                    target_height = self.solo.get_target_height()
                    data = {'selected_height': target_height}
                    return self.create_packet(data)

                elif (status_request['Key'] == "orientation"):
                    orientation = self.solo.get_orientation()
                    data = {'orientation': orientation}
                    return self.create_packet(data)

                elif (status_request['Key'] == "camera_angle"):
                    camera_angle = self.solo.get_camera_angle()
                    data = {'camera_angle': camera_angle}
                    return self.create_packet(data)

                elif (status_request['key'] == "fps"):
                    fps = self.solo.get_camera_fps()
                    data = {'fps': fps}
                    return self.create_packet(data)

                elif (status_request['key'] == "resolution"):
                    resolution = self.solo.get_camera_resolution()
                    data = {'resolution': resolution}
                    return self.create_packet(data)

                else:
                    raise ValueError  # if we get to this point, something went wrong

    def create_packet(self, data, cls=None, heartbeat=False):
        """
        Create a packet in JSON format from some data
        Args:
            data: dict with data that should come in the packet
        """
        now = time.time()
        localtime = time.localtime(now)
        milliseconds = '%03d' % int((now - int(now)) * 1000)
        timestamp = time.strftime('%d%m%Y%H%M%S', localtime) + milliseconds

        if heartbeat:
            data.update({'message_type': 'status', 'timestamp': timestamp, 'heartbeat': True})
        else:
            data.update({'message_type': 'status', 'timestamp': timestamp, 'heartbeat': False})

        return json.dumps(data, cls=cls)
