from dronekit import connect, time
from solo import Solo

SIM = True

print "connecting to drone..."
if SIM:
    vehicle = connect('tcp:127.0.0.1:5760', wait_ready=True)
else:
    vehicle = connect('udpin:0.0.0.0:14550', wait_ready=True)

s = Solo(vehicle=vehicle)
s.print_state
s.arm()
s.takeoff()
time.sleep(2)
s.land()
vehicle.release()
