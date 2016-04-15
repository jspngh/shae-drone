import sys
import copy
import json
import logging
from dronekit import time

from solo import Solo
from global_classes import DroneTypeEncoder, LocationEncoder, WayPoint, WayPointEncoder, WayPointQueue, logformat, dateformat


class StatusHandler():
    """
    This class will take care of packets of the 'status' message type
    """
    def __init__(self, solo, queue, logging_level):
        """
        :type solo: Solo
        :type queue: WayPointQueue
        """
        self.packet = None
        self.message = None
        self.solo = solo
        self.waypoint_queue = queue

        # set up logging
        self.stat_logger = logging.getLogger("Status Handler")
        formatter = logging.Formatter(logformat, datefmt=dateformat)
        handler = logging.StreamHandler(stream=sys.stdout)  # TODO
        handler.setFormatter(formatter)
        handler.setLevel(logging_level)
        self.stat_logger.addHandler(handler)
        self.stat_logger.setLevel(logging_level)

    def handle_packet(self, packet, message):
        self.packet = packet
        self.message = message
        try:
            if (self.message == "all_statuses"):  # TODO: all status attributes are requested
                self.waypoint_queue.queue_lock.acquire()
                curr_wayp = self.waypoint_queue.current_waypoint
                self.waypoint_queue.queue_lock.release()
                if curr_wayp is None:
                    wp_order = -1
                else:
                    wp_order = curr_wayp.order
                battery = self.solo.get_battery_level()
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
                        'waypoint_order': wp_order,
                        'battery_level': battery,
                        'orientation': orientation,
                        'speed': speed,
                        'selected_speed': target_speed,
                        'height': height,
                        'selected_height': target_height,
                        'drone_type': drone_type.__dict__}
                return self.create_packet(data, cls=LocationEncoder, heartbeat=False)

            elif (self.message == "heartbeat"):  # a heartbeat was requested
                self.waypoint_queue.queue_lock.acquire()
                curr_wayp = self.waypoint_queue.current_waypoint
                self.waypoint_queue.queue_lock.release()
                if curr_wayp is None:
                    wp_order = -1
                else:
                    wp_order = curr_wayp.order
                battery = self.solo.get_battery_level()
                loc = self.solo.get_location()
                orientation = self.solo.get_orientation()
                data = {'current_location': loc, 'waypoint_order': wp_order, 'orientation': orientation, 'battery_level': battery}

                return self.create_packet(data, cls=LocationEncoder, heartbeat=True)

            else:                                       # this is an array with the attributes that were required
                if not isinstance(self.message, list):  # if it is not a list, something went wrong
                    self.stat_logger.warning("Message not a list")
                    raise ValueError
                for status_request in self.message:
                    if (status_request['key'] == "battery_level"):
                        battery = self.solo.get_battery_level()
                        data = {'battery_level': battery}
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
        except ValueError:
            print "handle error"

    def create_packet(self, data, cls=None, heartbeat=False):
        """
        :type data: dict
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
