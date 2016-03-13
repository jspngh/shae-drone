from dronekit import connect, VehicleMode
import time
from vehicle_simulator import VehicleSimulator

vehicle_simulator = VehicleSimulator()
vehicle = vehicle_simulator.get_vehicle()

## Function copied out of 'simple goto' example: http://python.dronekit.io/examples/simple_goto.html
def arm_and_takeoff(aTargetAltitude):
    """
    Arms vehicle and fly to aTargetAltitude.
    """

    print "Basic pre-arm checks"
    # Don't try to arm until autopilot is ready
    while not vehicle.is_armable:
        print " Waiting for vehicle to initialise..."
        time.sleep(1)


    print "Arming motors"
    # Copter should arm in GUIDED mode
    vehicle.mode = VehicleMode("GUIDED")
    vehicle.armed = True

    # Confirm vehicle armed before attempting to take off
    while not vehicle.armed:
        print " Waiting for arming..."
        time.sleep(1)

    print "Taking off!"
    vehicle.simple_takeoff(aTargetAltitude) # Take off to target altitude

    # Wait until the vehicle reaches a safe height before processing the goto (otherwise the command 
    #  after Vehicle.simple_takeoff will execute immediately).
    while True:
        print " Altitude: ", vehicle.location.global_relative_frame.alt
        #Break and return from function just below target altitude.        
        if vehicle.location.global_relative_frame.alt>=aTargetAltitude*0.95:
            print "Reached target altitude"
            break
        time.sleep(1)

def flight_to_point(latitude, longitude, altitude):
    point = LocationGlobalRelative(latitude, longitude, altitude)
    vehicle.simple_goto(point)

arm_and_takeoff(3)

vehicle_simulator.close()

print("Ended")
