import os
import json
import socket
import struct
import threading
from threading import RLock
from dronekit import connect, time
from solo import Solo, Location, WayPoint, WayPointEncoder


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

    def handle_packet(self):
        try:
            if (self.message == "heartbeat"):  # the status message is a heartbeat message
                # location = self.solo.get_location
                print "handle"
            else:                         # this is an array with the attributes that were required
                if not isinstance(self.message, list):  # if it is not a list, something went wrong
                    raise ValueError
                for status_request in self.message:
                    if (status_request['Key'] == "battery_level"):
                        print "handle"
                    elif (status_request['Key'] == "current_location"):
                        print "handle"
                    elif (status_request['Key'] == "drone_type"):
                        print "handle"
                    elif (status_request['Key'] == "waypoint_reached"):
                        print "handle"
                    else:
                        raise ValueError  # if we get to this point, something went wrong
        except ValueError:
            print "handle error"
