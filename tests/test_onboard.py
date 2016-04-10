import sys
import json
import time
import socket
import struct
import unittest

sys.path.append("../simulator/src")
sys.path.append("../onboard")
from global_classes import Location, WayPoint, WayPointEncoder, WayPointQueue
from simulator import Simulator


class TestOnboard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sim = Simulator()
        time.sleep(30)

    @classmethod
    def tearDownClass(cls):
        cls.sim.stop()

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
        for i, wp in enumerate(wpq.queue):
            self.assertEqual(wp.order, sorted_list[i])

    def test_dronetype_message(self):
        dronetype_message = {'message_type': 'status', 'message': [{'key': 'drone_type'}]}
        json_dt_message = json.dumps(dronetype_message)

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
        sock.recv(length)
        sock.close()
        self.assertEqual(ack, 300)
        self.assertNotEqual(length, 0)
        time.sleep(1)  # wait a bit before going to the next test

        return

    def test_lift_off(self):
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

    def test_path_message(self):
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

        time.sleep(1)  # wait a bit before going to the next test
        return

    def test_land(self):
        stop_message = {'message_type': 'navigation', 'message': 'stop'}
        json_stop_message = json.dumps(stop_message)
        emergency_message = {'message_type': 'navigation', 'message': 'emergency'}
        json_em_message = json.dumps(emergency_message)

        sock = socket.socket(socket.AF_INET,  # Internet
                             socket.SOCK_STREAM)  # TCP
        # Connect to server and send data
        sock.connect(("127.0.0.1", 6330))
        sock.send(struct.pack(">I", len(json_stop_message)))
        sock.send(json_stop_message)
        data = sock.recv(2)
        ack = struct.unpack(">H", data)[0]
        sock.close()
        self.assertEqual(ack, 200)

        sock = socket.socket(socket.AF_INET,  # Internet
                             socket.SOCK_STREAM)  # TCP
        # Connect to server and send data
        sock.connect(("127.0.0.1", 6330))
        sock.send(struct.pack(">I", len(json_em_message)))
        sock.send(json_em_message)
        data = sock.recv(2)
        ack = struct.unpack(">H", data)[0]
        sock.close()
        self.assertEqual(ack, 200)

        time.sleep(1)  # wait a bit before going to the next test
        return

if __name__ == '__main__':
    unittest.main()
