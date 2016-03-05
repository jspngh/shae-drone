import os
import socket
import json
from json import JSONEncoder
from dronekit import connect, time
from solo import Solo


class WayPoint():
    def __init__(self, location, order):
        """
        :param location: the location of the waypoint, with longitude and latitude
        :type location: Location
        :param order: details in which order the waypoints should be visited
        :type order: int
        """
        self.location = location
        self.order = order


class WayPointEncoder(JSONEncoder):
    def default(self, wp):
        loc = {'Latitude': wp.location.latitude, 'Longitude': wp.location.longitude}
        res = {'Order': wp.order, 'Location': loc}
        return res


class Location():
    def __init__(self, longitude=0.0, latitude=0.0):
        self.longitude = longitude
        self.latitude = latitude


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
