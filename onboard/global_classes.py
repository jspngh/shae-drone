import logging
from json import JSONEncoder
from threading import RLock

SIM = False
logging_level = logging.DEBUG


class DroneType():
    def __init__(self, manufacturer, model):
        self.manufacturer = manufacturer
        self.model = model


class DroneTypeEncoder(JSONEncoder):
    def default(self, drone):
        if isinstance(drone, DroneType):
            dt = {'Manufacturer': drone.manufacturer, 'Model': drone.model}
            return {'drone_type': dt}


class Location():
    def __init__(self, longitude=0.0, latitude=0.0):
        self.longitude = longitude
        self.latitude = latitude


class LocationEncoder(JSONEncoder):
    def default(self, loc):
        loc = {'Latitude': loc.latitude, 'Longitude': loc.longitude}
        return {'current_location': loc}


class WayPoint():
    def __init__(self, location, order):
        """
        :param location: the location of the waypoint, with longitude and latitude
        :type location: Location
        :param order: details in which order the waypoints should be visited
        :type order: int
        """
        self.location = location
        self.order = order


class WayPointEncoder(JSONEncoder):
    def default(self, wp):
        loc = {'Latitude': wp.location.latitude, 'Longitude': wp.location.longitude}
        res = {'Order': wp.order, 'Location': loc}
        return res


class WayPointQueue():
    def __init__(self):
        self.queue_lock = RLock()  # this lock will be used when accessing the waypoint queue
        self.queue = []

    def insert_waypoint(self, waypoint, side='back'):
        """
        :type waypoint: WayPoint
        :param side: specifies whether to insert the waypoint in the front or the back of the queue
        """
        self.queue_lock.acquire()
        if side == 'front':
            self.queue = [waypoint] + self.queue
        else:
            self.queue.append(waypoint)
        self.queue_lock.release()

    def remove_waypoint(self, side='front'):
        """
        :param side: specifies whether to remove the waypoint from the front or the back of the queue
        """
        self.queue_lock.acquire()
        if side == 'back':
            waypoint = self.queue.pop()
        else:
            waypoint = self.queue[0]
            self.queue = self.queue[1:]
        self.queue_lock.release()
        return waypoint

    def sort_waypoints(self):
        """
        Sorts the waypoints in the queue.
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
