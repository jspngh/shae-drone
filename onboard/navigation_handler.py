import os
import json
import socket
import struct
import threading
from threading import RLock
from dronekit import connect, time
from solo import Solo, Location, WayPoint, WayPointEncoder


class NavigationHandler():
    """
    This class will take care of packets of the 'navigation' message type
    """
    def __init__(self, packet, message, solo):
        """
        :type solo: Solo
        """
        self.packet = packet
        self.message = message
        self.solo = solo
        self.lock = RLock()  # this lock will be used when accessing the waypoint_queue
        self.waypoint_queue = []

    def handle_packet(self):
        if (self.message == "path"):
            handler = self.PathHandler(self.packet, self.solo, waypoint_queue=self.waypoint_queue)
            handler.handle_packet()
        elif (self.message == "start"):
            handler = self.StartHandler(self.packet, self.solo)
        elif (self.message == "stop"):
            handler = self.StopHandler(self.packet, self.solo)
        elif (self.message == "emergency"):
            handler = self.EmergencyHandler(self.packet, self.solo)
        else:
            raise ValueError  # if we get to this point, something went wrong

    class NavigationThread (threading.Thread):
        """
        This class will run in another thread
        and fly to the waypoint in the waypoint_queue
        """
        def __init__(self, threadID, solo, waypoint_queue, lock, quit):
            """
            :type solo: Solo
            :type lock: RLock
            :type quit: bool
            """
            threading.Thread.__init__(self)
            self.threadID = threadID
            self.solo = solo
            self.waypoint_queue = waypoint_queue
            self.lock = lock  # this lock will be used when accessing the waypoint_queue
            self.quit = quit

        def run(self):
            while True:
                if not self.waypoint_queue:
                    time.sleep(1)

                self.lock.acquire()
                waypoint = self.waypoint_queue[0]
                del self.waypoint_queue[0]
                self.lock.release()

                self.solo.visit_waypoint(waypoint)
                time.sleep(0.1)

    class PathHandler():
        def __init__(self, packet, waypoint_queue, lock):
            """
            :type lock: RLock
            """
            self.packet = packet
            self.waypoint_queue = waypoint_queue
            self.lock = lock  # this lock will be used when accessing the waypoint_queue

        def handle_packet(self):
            if 'Path' not in self.packet:
                raise ValueError

            waypoints = self.packet['Path']
            for json_waypoint in waypoints:
                json_location = json_waypoint['Location']
                location = Location(longitude=float(json_location['Longitude']), latitude=float(json_location['Latitude']))
                waypoint = WayPoint(location=location, order=json_waypoint['Order'])

                print "adding waypoint"
                self.lock.acquire()
                self.waypoint_queue.append(waypoint)
                self.lock.release()

    class StartHandler():
        def __init__(self, packet, solo):
            """
            :type solo: Solo
            """
            self.packet = packet
            self.solo = solo

        def handle_packet(self):
            self.solo.arm()
            self.solo.takeoff()

    class StopHandler():
        def __init__(self, packet, solo):
            """
            :type solo: Solo
            """
            self.packet = packet
            self.solo = solo

        def handle_packet(self):
            self.solo.brake()

    class EmergencyHandler():
        def __init__(self, packet, solo):
            """
            :type solo: Solo
            """
            self.packet = packet
            self.solo = solo

        def handle_packet(self):
            self.solo.land()
