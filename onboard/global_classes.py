import logging
from json import JSONEncoder


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


class Location():
    def __init__(self, longitude=0.0, latitude=0.0):
        self.longitude = longitude
        self.latitude = latitude


class LocationEncoder(JSONEncoder):
    def default(self, loc):
        loc = {'Latitude': loc.latitude, 'Longitude': loc.longitude}
        return {'current_location': loc}


class DroneType():
    def __init__(self, manufacturer, model):
        self.manufacturer = manufacturer
        self.model = model


class DroneTypeEncoder(JSONEncoder):
    def default(self, drone):
        if isinstance(drone, DroneType):
            dt = {'Manufacturer': drone.manufacturer, 'Model': drone.model}
            return {'drone_type': dt}

SIM = True
logging_level = logging.DEBUG
