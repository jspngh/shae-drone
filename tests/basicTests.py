import unittest
import json
import socket
import struct
import sys
sys.path.append('../onboard/')
from global_classes import Location, WayPoint, WayPointEncoder, WayPointQueue
from navigation_handler import NavigationHandler


class BasicTests(unittest.TestCase):
    def test_one(self):
        self.assertEqual('foo'.upper(), 'FOO')

    def test_two(self):
        self.assertTrue('FOO'.isupper())
        self.assertFalse('Foo'.isupper())

    def test_path_handler(self):
        waypoints = []
        for i in range(0, 4):
            tmp_loc = Location(i, i)
            waypoints.append(WayPoint(location=tmp_loc, order=i))
        path_message = {'MessageType': 'control', 'Message': 'path', 'Path': waypoints}
        json_message = json.dumps(path_message, cls=WayPointEncoder)
        message = json.loads(json_message)
        waypoint_queue = []
        path_handler = NavigationHandler.PathHandler(message, waypoint_queue)
        path_handler.handle_packet()
        for waypoint in path_handler.waypoint_queue:
            if waypoint.location.longitude not in range(0, 4) or waypoint.location.latitude not in range(0, 4):
                self.fail

    def test_path_messages(self):
        waypoints = []
        for i in range(0, 4):
            tmp_loc = Location(i, i)
            waypoints.append(WayPoint(location=tmp_loc, order=i))
        path_message = {'MessageType': 'control', 'Message': 'path', 'Path': waypoints}
        json_message = json.dumps(path_message, cls=WayPointEncoder)
        control_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        control_socket.connect("/tmp/uds_control")
        control_socket.send(json_message)
        raw_response = control_socket.recv(1024)
        response = struct.unpack(">I", raw_response)[0]
        control_socket.close()
        self.assertEqual(response, 200)

    def test_waypoint_queue(self):
        random_list = [4, 3, 6, 1, 5, 2, 3]
        sorted_list = [1, 2, 3, 3, 4, 5, 6]
        wpq = WayPointQueue()
        for i in random_list:
            wp = WayPoint(location=Location(longitude=i, latitude=i), order=i)
            wpq.insert_waypoint(wp)
        wpq.sort_waypoints()
        for wp in wpq.queue:
            print wp.order
        for i, wp in enumerate(wpq.queue):
            self.assertEqual(wp.order, sorted_list[i])

if __name__ == '__main__':
    unittest.main()
