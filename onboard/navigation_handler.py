import os
import sys
import json
import socket
import struct
import logging
import threading
from logging import Logger
from dronekit import connect, time

from solo import Solo
from global_classes import Location, WayPoint, WayPointEncoder, WayPointQueue, logformat, dateformat


class NavigationHandler():
    """
    This class will take care of packets of the 'navigation' message type
    """
    def __init__(self, solo, queue, navigation_thread, logging_level):
        """
        :type solo: Solo
        :type queue: WayPointQueue
        :type navigation_thread: NavigationThread
        """
        self.packet = None
        self.message = None
        self.solo = solo
        self.waypoint_queue = queue
        self.navigation_thread = navigation_thread

        # set up logging
        self.logger = logging.getLogger("Navigation Handler")
        formatter = logging.Formatter(logformat, datefmt=dateformat)
        handler = logging.StreamHandler(stream=sys.stdout)  # TODO
        handler.setFormatter(formatter)
        handler.setLevel(logging_level)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging_level)

    def handle_packet(self, packet, message):
        self.packet = packet
        self.message = message

        if (self.message == "path"):
            self.logger.debug("Handling path message")
            self.handle_path_packet()
        elif (self.message == "start"):
            self.logger.debug("Handling start message")
            self.handle_start_packet()
        elif (self.message == "stop"):
            self.logger.debug("Handling stop message")
            self.handle_stop_packet()
        elif (self.message == "rth"):
            self.logger.debug("Handling 'Return To Home' message")
            self.handle_rth_packet()
        elif (self.message == "emergency"):
            self.logger.debug("Handling emergency message")
            self.handle_emergency_packet()
        else:
            raise ValueError  # if we get to this point, something went wrong

    def handle_path_packet(self):
        if 'waypoints' not in self.packet:
            raise ValueError

        waypoints = self.packet['waypoints']
        for json_waypoint in waypoints:
            json_location = json_waypoint['location']
            location = Location(longitude=float(json_location['longitude']), latitude=float(json_location['latitude']))
            waypoint = WayPoint(location=location, order=json_waypoint['order'])

            self.logger.info("Adding waypoint...")
            self.waypoint_queue.insert_waypoint(waypoint)
        # sort waypoints on order
        self.waypoint_queue.sort_waypoints()
        self.logger.info("Sorted the waypoints...")

    def handle_start_packet(self):
        home_location = self.solo.get_location()
        self.waypoint_queue.queue_lock.acquire()
        self.waypoint_queue.home = home_location
        self.waypoint_queue.queue_lock.release()

        self.logger.info("Arming Solo...")
        self.solo.arm()
        self.solo.takeoff()

    def handle_stop_packet(self):
        self.solo.brake()

    def handle_rth_packet(self):
        self.waypoint_queue.queue_lock.acquire()
        home_location = self.waypoint_queue.home
        self.waypoint_queue.queue_lock.release()
        self.waypoint_queue.clear_queue()
        home_waypoint = WayPoint(location=home_location, order=-1)
        self.waypoint_queue.insert_waypoint(home_waypoint, side='front')
        self.navigation_thread.return_to_home()

    def handle_emergency_packet(self):
        self.solo.land()


class NavigationThread (threading.Thread):
    """
    This class will run in another thread
    and fly to the waypoints in the waypoint_queue
    """
    def __init__(self, threadID, solo, waypoint_queue, logging_level):
        """
        :type solo: Solo
        :type waypoint_queue: WayPointQueue
        """
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.solo = solo
        self.waypoint_queue = waypoint_queue
        self.quit = False
        self.rth = False

        # set up logging
        self.logger = logging.getLogger("Navigation Thread")
        formatter = logging.Formatter('[%(levelname)s] %(message)s')
        handler = logging.StreamHandler(stream=sys.stdout)
        handler.setFormatter(formatter)
        handler.setLevel(logging_level)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging_level)

    def run(self):
        while not self.quit:
            if self.waypoint_queue.is_empty():
                time.sleep(1)
            else:
                self.logger.debug("Getting waypoint")
                waypoint = self.waypoint_queue.remove_waypoint()

                self.logger.info("Visiting waypoint...")
                self.solo.visit_waypoint(waypoint)
                self.logger.info("Waypoint visited")
                time.sleep(0.1)

        if self.rth and not self.waypoint_queue.is_empty():
            home = self.waypoint_queue.remove_waypoint()
            self.solo.visit_waypoint(home)
            self.solo.land()

    def return_to_home(self):
        self.logger.debug("Returning to home location")
        self.solo.halt()
        self.quit = True
        self.rth = True

    def stop_thread(self):
        self.logger.debug("Stopping navigation thread")
        self.solo.halt()
        self.quit = True
        self.rth = False
