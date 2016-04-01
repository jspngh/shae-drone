import unittest
import sys
from time import sleep

sys.path.append("../src")
from stream_simulator import StreamSimulator 

class TestStreamSimulator(unittest.TestCase):
    
    def __init__(self):
        self.stream_simulator = StreamSimulator()

    def test_stream_thread_start_and_stop(self):
        self.stream_simulator.start()
        self.assertTrue(self.stream_simulator.isAlive())

        self.stream_simulator.stop_thread()
        sleep(3)
        self.assertFalse(self.stream_simulator.isAlive())

test_class = TestStreamSimulator()
test_class.test_stream_thread_start_and_stop()
