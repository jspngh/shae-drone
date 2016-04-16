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


class TestStatus(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sim = Simulator()
        time.sleep(30)

    @classmethod
    def tearDownClass(cls):
        cls.sim.stop()

    def test_1_dronetype_message(self):
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
        response = sock.recv(length)
        print response
        sock.close()
        self.assertEqual(ack, 300)
        self.assertNotEqual(length, 0)
        time.sleep(1)  # wait a bit before going to the next test

        return

    def test_2_battery_message(self):
        dronetype_message = {'message_type': 'status', 'message': [{'key': 'battery_level'}]}
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
        response = sock.recv(length)
        print response
        sock.close()
        self.assertEqual(ack, 300)
        self.assertNotEqual(length, 0)
        time.sleep(1)  # wait a bit before going to the next test

        return

    def test_3_heartbeat_message(self):
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

    def test_4_all_status_message(self):
        all_status_message = {'message_type': 'status', 'message': 'all_statuses'}
        json_dt_message = json.dumps(all_status_message)

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

if __name__ == '__main__':
    unittest.main()
