import sys
import types
import socket
from dronekit import Vehicle


class ServerSimulatorMetaClass(type):
    def __new__(cls, name, bases, attrs):
        return super(ServerSimulatorMetaClass, cls).__new__(cls, name, bases, attrs)

    @classmethod
    def decorator(cls, func):
        def wrapper(*args, **kwargs):
            print 'before', func.func_name
            result = func(*args, **kwargs)
            print 'after', func.func_name
            return result
        return wrapper


class ServerSimulator(Server):
    __metaclass__ = ServerSimulatorMetaClass

    def __init__(self, *args):
        print 'test'
        # super(ServerSimulator, self).__init__(*args)

    def handle_raw(self, raw):
        print raw
