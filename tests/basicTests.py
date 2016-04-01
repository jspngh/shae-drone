import unittest
import json
import socket
import struct
import sys

sys.path.append('../onboard/')
from global_classes import Location, WayPoint, WayPointEncoder, WayPointQueue

class BasicTests(unittest.TestCase):
    def test_one(self):
        self.assertEqual('foo'.upper(), 'FOO')

    def test_two(self):
        self.assertTrue('FOO'.isupper())
        self.assertFalse('Foo'.isupper())

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
