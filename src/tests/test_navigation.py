import sys
import json
import time
import socket
import struct
import unittest

from shae.onboard.global_classes import Location, WayPoint, WayPointEncoder, WayPointQueue
from shae.simulator.simulator import Simulator


class TestNavigation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sim = Simulator()
        time.sleep(30)

    @classmethod
    def tearDownClass(cls):
        cls.sim.stop()

    def test_1_waypoint_queue(self):
        random_list = [4, 3, 6, 1, 5, 2, 3]
        sorted_list = [1, 2, 3, 3, 4, 5, 6]
        wpq = WayPointQueue()
        for i in random_list:
            wp = WayPoint(location=Location(longitude=i, latitude=i), order=i)
            wpq.insert_waypoint(wp)
        wpq.sort_waypoints()
        for i, wp in enumerate(wpq.queue):
            self.assertEqual(wp.order, sorted_list[i])

    def test_2_lift_off(self):
        start_message = {'message_type': 'navigation', 'message': 'start'}
        json_start_message = json.dumps(start_message)

        sock = socket.socket(socket.AF_INET,  # Internet
                             socket.SOCK_STREAM)  # TCP
        # Connect to server and send data
        sock.connect(("127.0.0.1", 6330))
        sock.send(struct.pack(">I", len(json_start_message)))
        sock.send(json_start_message)
        data = sock.recv(2)
        ack = struct.unpack(">H", data)[0]
        sock.close()
        self.assertEqual(ack, 200)
        time.sleep(1)  # wait a bit before going to the next test

        return

    def test_3_path_message(self):
        waypoints = []
        # for i in range(0, 4):
        tmp_loc_1 = Location(latitude=51.022721, longitude=3.709819)
        tmp_loc_2 = Location(latitude=51.022480, longitude=3.709903)
        tmp_loc_3 = Location(latitude=51.022788, longitude=3.710054)
        waypoints.append(WayPoint(location=tmp_loc_1, order=1))
        waypoints.append(WayPoint(location=tmp_loc_2, order=2))
        waypoints.append(WayPoint(location=tmp_loc_3, order=3))
        path_message = {'message_type': 'navigation', 'message': 'path', 'waypoints': waypoints}
        json_path_message = json.dumps(path_message, cls=WayPointEncoder)

        sock = socket.socket(socket.AF_INET,  # Internet
                             socket.SOCK_STREAM)  # TCP
        # Connect to server and send data
        sock.connect(("127.0.0.1", 6330))
        sock.send(struct.pack(">I", len(json_path_message)))
        sock.send(json_path_message)
        data = sock.recv(2)
        ack = struct.unpack(">H", data)[0]
        sock.close()
        self.assertEqual(ack, 200)

        time.sleep(15)  # wait a bit before going to the next test
        return

    def test_4_heartbeat_message(self):
        battery_message = {'message_type': 'status', 'message': 'heartbeat'}
        json_dt_message = json.dumps(battery_message)

        sock = socket.socket(socket.AF_INET,  # Internet
                             socket.SOCK_STREAM)  # TCP
        # Connect to server and send data
        sock.connect(("127.0.0.1", 6330))
        sock.send(struct.pack(">I", len(json_dt_message)))
        sock.send(json_dt_message)
        data = sock.recv(2)
        ack = struct.unpack(">H", data)[0]
        data = sock.recv(2)
        length = struct.unpack(">H", data)[0]
        response = sock.recv(length)
        print response
        sock.close()
        self.assertEqual(ack, 300)
        self.assertNotEqual(length, 0)
        time.sleep(1)  # wait a bit before going to the next test

        return

    def test_5_rth_message(self):
        rth_message = {'message_type': 'navigation', 'message': 'rth'}
        json_rth_message = json.dumps(rth_message)

        sock = socket.socket(socket.AF_INET,  # Internet
                             socket.SOCK_STREAM)  # TCP
        # Connect to server and send data
        sock.connect(("127.0.0.1", 6330))
        sock.send(struct.pack(">I", len(json_rth_message)))
        sock.send(json_rth_message)
        data = sock.recv(2)
        ack = struct.unpack(">H", data)[0]
        sock.close()
        self.assertEqual(ack, 200)
        print 'before last sleep'
        time.sleep(35)  # wait a bit before going to the next test
        print 'after last sleep'
        return


if __name__ == '__main__':
    unittest.main()
