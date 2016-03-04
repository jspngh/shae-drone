import unittest
import json
from json import JSONEncoder
import sys
sys.path.append('../onboard/')
from control_classes import WayPoint, Location, PathHandler, WayPointEncoder


class BasicTests(unittest.TestCase):
    def test_one(self):
        self.assertEqual('foo'.upper(), 'FOO')

    def test_two(self):
        self.assertTrue('FOO'.isupper())
        self.assertFalse('Foo'.isupper())

    def test_control_module(self):
        waypoints = []
        for i in range(0, 4):
            tmp_loc = Location(i, i)
            waypoints.append(WayPoint(location=tmp_loc, order=i))
        path_message = {'MessageType': 'control', 'Message': 'path', 'Path': waypoints}
        json_message = json.dumps(path_message, cls=WayPointEncoder)
        message = json.loads(json_message)
        waypoint_queue = []
        path_handler = PathHandler(message, waypoint_queue)
        path_handler.handle_packet()
        for waypoint in path_handler.waypoint_queue:
            if waypoint.location.longitude not in range(0, 4) or waypoint.location.latitude not in range(0, 4):
                self.fail


if __name__ == '__main__':
    unittest.main()
