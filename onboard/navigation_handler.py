import os
import json
import socket
import struct
import threading
import logging
import sys
from logging import Logger
from global_classes import logging_level
from dronekit import connect, time
from solo import Solo
from global_classes import Location, WayPoint, WayPointEncoder, WayPointQueue


class NavigationHandler():
    """
    This class will take care of packets of the 'navigation' message type
    """
    def __init__(self, packet, message, solo, queue):
        """
        :type solo: Solo
        :type queue: WayPointQueue
        """
        self.packet = packet
        self.message = message
        self.solo = solo
        self.waypoint_queue = queue

        # set up logging
        self.nav_logger = logging.getLogger("Navigation Handler")
        formatter = logging.Formatter('[%(levelname)s] %(message)s')
        handler = logging.StreamHandler(stream=sys.stdout)
        handler.setFormatter(formatter)
        handler.setLevel(logging_level)
        self.nav_logger.addHandler(handler)
        self.nav_logger.setLevel(logging_level)

    def handle_packet(self):
        if (self.message == "path"):
            handler = self.PathHandler(self.packet, waypoint_queue=self.waypoint_queue, lock=self.lock, logger=self.nav_logger)
            handler.handle_packet()
        elif (self.message == "start"):
            handler = self.StartHandler(self.packet, self.solo, logger=self.nav_logger)
            handler.handle_packet()
        elif (self.message == "stop"):
            handler = self.StopHandler(self.packet, self.solo, logger=self.nav_logger)
            handler.handle_packet()
        elif (self.message == "emergency"):
            handler = self.EmergencyHandler(self.packet, self.solo, logger=self.nav_logger)
            handler.handle_packet()
        else:
            raise ValueError  # if we get to this point, something went wrong

    class NavigationThread (threading.Thread):
        """
        This class will run in another thread
        and fly to the waypoints in the waypoint_queue
        """
        def __init__(self, threadID, solo, waypoint_queue, quit):
            """
            :type solo: Solo
            :type waypoint_queue: WayPointQueue
            :type quit: bool
            """
            threading.Thread.__init__(self)
            self.threadID = threadID
            self.solo = solo
            self.waypoint_queue = waypoint_queue
            self.quit = quit

            # set up logging
            self.logger = logging.getLogger("Navigation Thread")
            formatter = logging.Formatter('[%(levelname)s] %(message)s')
            handler = logging.StreamHandler(stream=sys.stdout)
            handler.setFormatter(formatter)
            handler.setLevel(logging_level)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging_level)

        def run(self):
            while True:
                if not self.waypoint_queue:
                    time.sleep(1)
                else:
                    waypoint = self.waypoint_queue.remove_waypoint()

                    self.logger.info("Visiting waypoint...")
                    self.solo.visit_waypoint(waypoint)
                    self.logger.info("Waypoint visited")
                    time.sleep(0.1)

    class PathHandler():
        def __init__(self, packet, waypoint_queue, logger):
            """
            :type waypoint_queue: WayPointQueue
            :type logger: Logger
            """
            self.packet = packet
            self.waypoint_queue = waypoint_queue
            self.logger = logger

        def handle_packet(self):
            if 'Path' not in self.packet:
                raise ValueError

            waypoints = self.packet['Path']
            for json_waypoint in waypoints:
                json_location = json_waypoint['Location']
                location = Location(longitude=float(json_location['Longitude']), latitude=float(json_location['Latitude']))
                waypoint = WayPoint(location=location, order=json_waypoint['Order'])

                self.logger.info("Adding waypoint...")
                self.waypoint_queue.insert_waypoint(waypoint)
            # sort waypoints on order
            self.waypoint_queue.sort_waypoints()

    class StartHandler():
        def __init__(self, packet, solo, logger):
            """
            :type solo: Solo
            :type logger: Logger
            """
            self.packet = packet
            self.solo = solo
            self.logger = logger

        def handle_packet(self):
            self.logger.info("Arming Solo...")
            self.solo.arm()
            self.solo.takeoff()

    class StopHandler():
        def __init__(self, packet, solo, logger):
            """
            :type solo: Solo
            :type logger: Logger
            """
            self.packet = packet
            self.solo = solo
            self.logger = logger

        def handle_packet(self):
            self.solo.brake()

    class EmergencyHandler():
        def __init__(self, packet, solo, logger):
            """
            :type solo: Solo
            :type logger: Logger
            """
            self.packet = packet
            self.solo = solo
            self.logger = logger

        def handle_packet(self):
            self.solo.land()
