import sys
import logging
import threading
from dronekit import time

from solo import Solo
from global_classes import Location, WayPoint, WayPointEncoder, WayPointQueue, logformat, dateformat


## @ingroup Onboard
# @brief This class will take care of packets of the 'navigation' message type
class NavigationHandler():
    def __init__(self, solo, queue, navigation_thread, logging_level, log_type='console', filename=''):
        """
        Initiate the handler

        Args:
            solo: Solo instance
            queue: WayPointQueue instance
            navigation_thread: NavigationThread instance
            logging_level: the level that should be used for logging, e.g. DEBUG
            log_type: log to stdout ('console') or to a file ('file')
            filename: the name of the file if log_type is 'file'
        """
        self.packet = None
        self.message = None
        self.solo = solo
        self.waypoint_queue = queue
        self.navigation_thread = navigation_thread

        # set up logging
        self.logger = logging.getLogger("Navigation Handler")
        formatter = logging.Formatter(logformat, datefmt=dateformat)
        if log_type == 'console':
            handler = logging.StreamHandler(stream=sys.stdout)
        elif log_type == 'file':
            handler = logging.FileHandler(filename=filename)
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

        self.logger.info("preparing the solo for takeoff")
        self.solo.arm()
        retval = self.solo.takeoff()
        if retval == -1:
            # takeoff failed
            # we will try one more time
            self.logger.info("retrying takeoff")
            self.solo.arm()
            retval = self.solo.takeoff()

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
        self.navigation_thread.stop_thread()
        self.solo.land()


## @ingroup Onboard
# @brief This class will run in another thread and fly to the waypoints in the waypoint queue
class NavigationThread (threading.Thread):
    def __init__(self, solo, waypoint_queue, logging_level, log_type='console', filename=''):
        """
        Initiate the thread

        Args:
            solo: Solo instance
            waypoint_queue: WayPointQueue instance
            logging_level: the level that should be used for logging, e.g. DEBUG
            log_type: log to stdout ('console') or to a file ('file')
            filename: the name of the file if log_type is 'file'
        """
        threading.Thread.__init__(self)
        self.solo = solo
        self.waypoint_queue = waypoint_queue
        self.quit = False
        self.rth = False

        # set up logging
        self.logger = logging.getLogger("Navigation Thread")
        formatter = logging.Formatter(logformat, datefmt=dateformat)
        if log_type == 'console':
            handler = logging.StreamHandler(stream=sys.stdout)
        elif log_type == 'file':
            handler = logging.FileHandler(filename=filename)
        handler.setFormatter(formatter)
        handler.setLevel(logging_level)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging_level)

    def run(self):
        while not self.quit:
            if self.waypoint_queue.is_empty():
                time.sleep(1)
            else:
                self.logger.debug("getting waypoint")
                waypoint = self.waypoint_queue.remove_waypoint()

                self.logger.info("the solo is flying to a new waypoint")
                self.solo.visit_waypoint(waypoint)
                self.logger.info("the solo arrived at the waypoint")
                time.sleep(0.1)

        if self.rth and not self.waypoint_queue.is_empty():
            home = self.waypoint_queue.remove_waypoint()
            self.logger.info("the solo is returning to his launch location")
            self.solo.visit_waypoint(home)
            self.solo.land()

    def return_to_home(self):
        self.logger.debug("returning to home")
        self.solo.halt()
        self.quit = True
        self.rth = True

    def stop_thread(self):
        self.logger.info("stopping the navigation-thread")
        self.solo.halt()
        self.quit = True
        self.rth = False
