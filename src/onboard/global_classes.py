from json import JSONEncoder
from threading import RLock

## @defgroup Global_classes
# @ingroup Onboard

logformat = '[%(levelname)s] %(asctime)s in \'%(name)s\': %(message)s'
dateformat = '%m-%d %H:%M:%S'


def print_help(filename):
    """
    Print some help information that is displayed when calling 'filename --help'

    Args:
        filename: the name of the file for which the help information should be printed
    """
    print 'Usage: ' + filename + ' -s -l <logging_level> -t <logging_type> -f <outputfile>'
    print 'Options:'
    print '  -l --level: \t\t Specify the logging level\n' \
          '\t\t\t The available options are \'debug\', \'info\', \'warning\' and \'critical\'\n' \
          '\t\t\t This defaults to \'critical\''
    print '  -t --type: \t\t Specify the logging type, available options are:\n' \
          '\t\t\t   \'console\', which prints the logs to the console, this is the default\n' \
          '\t\t\t   \'file\', which prints the logs to a file, a filename needs to be specified'
    print '  -f --file: \t\t Specify the name of the logfile'
    print '  -s --simulate: \t Indicate that a simulated vehicle is used'
    print '  -h --help: \t\t Display this information'


## @ingroup Global_classes
# @brief Codes to tell the workstation what to expect
#
# When sending a message to the workstation, the message will be preceded by one of these codes
class MessageCodes():
    ACK = 200
    STATUS_RESPONSE = 300
    HEARTBEAT_REQUEST = 400
    START_HEARTBEAT = 404
    ERR = 500


## @ingroup Global_classes
# @brief The type of drone the onboard code is written for
#
# This can be used to let the workstation know what type of drone it's dealing with
class DroneType():
    def __init__(self, manufacturer, model):
        self.manufacturer = manufacturer
        self.model = model


## @ingroup Global_classes
# @brief Parses the DroneType class to JSON
class DroneTypeEncoder(JSONEncoder):
    def default(self, drone):
        if isinstance(drone, DroneType):
            dt = {'manufacturer': drone.manufacturer, 'model': drone.model}
            return dt


## @ingroup Global_classes
# @brief Class that holds the coordinates of a location
class Location():
    def __init__(self, longitude=0.0, latitude=0.0):
        self.longitude = longitude
        self.latitude = latitude


## @ingroup Global_classes
# @brief Parses the Location class to JSON
class LocationEncoder(JSONEncoder):
    def default(self, loc):
        loc = {'latitude': loc.latitude, 'longitude': loc.longitude}
        return loc


## @ingroup Global_classes
# @brief Combines a location with an order
#
# These are objects the drone will fly to, in order
class WayPoint():
    def __init__(self, location, order):
        """
        @param location: the location of the waypoint, with longitude and latitude
        @type location: Location
        @param order: details in which order the waypoints should be visited
        @type order: int
        """
        self.location = location
        self.order = order


## @ingroup Global_classes
# @brief Parses the WayPoint class to JSON
class WayPointEncoder(JSONEncoder):
    def default(self, wp):
        loc = {'latitude': wp.location.latitude, 'longitude': wp.location.longitude}
        res = {'order': wp.order, 'location': loc}
        return res


## @ingroup Global_classes
# @brief Class to hold a series of object from the WayPoint class
#
# This class holds a lock in order to provide some protection against concurrent modification.
# Also provides functionality to sort Waypoints based on their order
class WayPointQueue():
    def __init__(self):
        self.queue_lock = RLock()  # this lock will be used when accessing the waypoint queue
        self.queue = []
        self.current_waypoint = None
        self.last_waypoint_order = -1
        self.home = None

    def insert_waypoint(self, waypoint, side='back'):
        """
        Args:
            waypoint: a WayPoint
            side: specifies whether to insert the waypoint in the front or the back of the queue
        """
        self.queue_lock.acquire()
        if side == 'front':
            self.queue = [waypoint] + self.queue
        else:
            self.queue.append(waypoint)
        self.queue_lock.release()

    def remove_waypoint(self, side='front'):
        """
        Args:
            side: specifies whether to remove the waypoint from the front or the back of the queue
        """
        self.queue_lock.acquire()
        if side == 'back':
            waypoint = self.queue.pop()
        else:
            waypoint = self.queue[0]
            self.queue = self.queue[1:]
        if self.current_waypoint is not None:
            self.last_waypoint_order = self.current_waypoint.order
        self.current_waypoint = waypoint
        self.queue_lock.release()
        return waypoint

    def sort_waypoints(self):
        """
        Sort the waypoints in the queue.

        This function uses BubbleSort which is not efficient for large lists,
        but we only have a limited number of waypoints in the queue, so this shouldn't be a bottleneck.
        """
        self.queue_lock.acquire()
        wp_ord = 0
        for j in range(0, len(self.queue)):
            last_wp_ord = -1
            for i in range(0, len(self.queue) - j):
                waypoint = self.queue[i]
                if not isinstance(waypoint, WayPoint):
                    return  # this should not be happening
                wp_ord = self.queue[i].order
                if wp_ord < last_wp_ord:
                    self.queue[i], self.queue[i - 1] = self.queue[i - 1], self.queue[i]
                else:
                    last_wp_ord = wp_ord
        self.queue_lock.release()

    def is_empty(self):
        """
        Returns:
            a boolean telling whether the queue is empty or not
        """
        self.queue_lock.acquire()
        result = not self.queue
        if result is False and self.last_waypoint_order != -1:
            self.last_waypoint_order = -2
        self.queue_lock.release()
        return result

    def clear_queue(self):
        """
        Remove all items from the queue
        """
        self.queue_lock.acquire()
        self.queue = []
        self.queue_lock.release()
