import unittest
import sys
sys.path.append("../src")
from stream_simulator import StreamSimulator 

class TestStreamSimulator(unittest.TestCase):
    
    def __init__(self):
        self.stream_simulator = StreamSimulator()

    def test_stream_thread_start(self):
        self.stream_simulator.start()
        self.assertTrue(self.stream_simulator.isAlive())
        self.stream_simulator.stop_thread()

test_class = TestStreamSimulator()
test_class.test_stream_thread_start()
