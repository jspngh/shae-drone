from dronekit import connect, time
from solo import Solo

SIM = False

print "connecting to drone..."
if SIM:
    vehicle = connect('tcp:127.0.0.1:5760', wait_ready=True)
else:
    vehicle = connect('udpin:0.0.0.0:14550', wait_ready=True)

s = Solo(vehicle=vehicle)
s.print_state
s.arm()
s.takeoff()
s.translate(x=1, y=0, z=0, wait_for_arrival=True, dist_thres=1)
s.control_gimbal(pitch=-90, yaw=vehicle.gimbal.yaw, roll=vehicle.gimbal.roll)
time.sleep(1)
s.control_gimbal(pitch=-90, yaw=0, roll=0)
s.control_gimbal(pitch=0, yaw=0, roll=0)
s.translate(x=-1, y=0, z=1, wait_for_arrival=True, dist_thres=1)
s.land()

print vehicle.attitude
