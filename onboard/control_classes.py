import os
import socket
import json
from dronekit import connect, time
from solo import Solo, Location, WayPoint, WayPointEncoder


class PathHandler():
    def __init__(self, packet, waypoint_queue):
        self.packet = packet
        self.waypoint_queue = waypoint_queue
        return

    def handle_packet(self):
        if 'Path' not in self.packet:
            raise ValueError

        waypoints = self.packet['Path']
        for json_waypoint in waypoints:
            json_location = json_waypoint['Location']
            location = Location(longitude=float(json_location['Longitude']), latitude=float(json_location['Latitude']))
            waypoint = WayPoint(location=location, order=json_waypoint['Order'])
            print "adding waypoint"
            self.waypoint_queue.append(waypoint)
        # should not be here, is here for testing
        self.solo.arm()
        self.solo.takeoff()
        self.solo.visit_waypoints(waypoint_queue=self.waypoint_queue)


class StartHandler():
    def __init__(self, packet, solo):
        """
        :type solo: Solo
        """
        self.packet = packet
        self.solo = solo
        return

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
        return

    def handle_packet(self):
        self.solo.brake()


class EmergencyHandler():
    def __init__(self, packet, solo):
        """
        :type solo: Solo
        """
        self.packet = packet
        self.solo = solo
        return

    def handle_packet(self):
        self.solo.land()
