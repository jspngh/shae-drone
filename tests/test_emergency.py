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


class TestEmergency(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sim = Simulator()
        time.sleep(30)

    @classmethod
    def tearDownClass(cls):
        cls.sim.stop()

    def test_1_lift_off(self):
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

    def test_2_path_message(self):
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

    def test_3_land(self):
        # stop_message = {'message_type': 'navigation', 'message': 'stop'}
        # json_stop_message = json.dumps(stop_message)
        emergency_message = {'message_type': 'navigation', 'message': 'emergency'}
        json_em_message = json.dumps(emergency_message)

        # sock = socket.socket(socket.AF_INET,  # Internet
        #                      socket.SOCK_STREAM)  # TCP
        # # Connect to server and send data
        # sock.connect(("127.0.0.1", 6330))
        # sock.send(struct.pack(">I", len(json_stop_message)))
        # sock.send(json_stop_message)
        # data = sock.recv(2)
        # ack = struct.unpack(">H", data)[0]
        # sock.close()
        # self.assertEqual(ack, 200)

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

        time.sleep(15)  # wait a bit before going to the next test
        return

if __name__ == '__main__':
    unittest.main()
