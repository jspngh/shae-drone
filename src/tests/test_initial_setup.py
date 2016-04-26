import sys
import json
import time
import socket
import unittest

from shae.simulator import Simulator


class TestSetup(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sim = Simulator()
        time.sleep(30)

    @classmethod
    def tearDownClass(cls):
        cls.sim.stop()

    def test_1_setup(self):
        bcsocket = socket.socket(socket.AF_INET,        # Internet
                                 socket.SOCK_DGRAM)     # UDP
        bcsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        bcsocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        bcsocket.settimeout(10)
        bcsocket.bind(('', 4849))

        hello_received = 0

        while hello_received < 2:

            data, address = bcsocket.recvfrom(4096)

            print "Received {0}, from {1}".format(data, address)

            message = json.loads(data)

            if 'message_type' not in message:
                self.fail('Json was not parsed correctly')
            self.assertEqual(message['message_type'], 'hello')
            self.assertEqual(message['ip_drone'], '127.0.0.1')
            self.assertEqual(message['port_stream'], 5502)
            self.assertEqual(message['port_commands'], 6330)
            self.assertEqual(message['stream_file'], 'rtp://127.0.0.1:5000')
            self.assertEqual(message['vision_width'], 0.0001)

            hello_received += 1

        hello_response = {'message_type': 'hello'}
        json_response = json.dumps(hello_response)

        bcsocket.sendto(json_response, address)

        time.sleep(10)
        return


if __name__ == '__main__':
    unittest.main()
