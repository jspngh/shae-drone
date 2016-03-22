# Drone

## Simulator

### Onboard + vehicle (drone)

* In 'drone/onboard/global_classes.py' set SIM = True
* Execute the following commands in different terminals (assuming the working directory is 'drone/onboard'):
``` 
python control_module.py   
python server.py
```
* Now the drone is simulated and reachable by sending json-messages to 127.0.0.1:6330

### Stream

* Install vlc: 
``` 
sudo apt-get install vlc
```
* On the server side, send stream by executing:
```
# Replace 'video_file.mp4' with the file name of the video you want to stream.
cvlc -vvv video_file.mp4 --sout '#transcode{vcodec=h264,acodec=mpga,ab=128,channels=2,samplerate=44100}:rtp{dst=127.0.0.1,port=5000,ptype-video=96,mux=ts}'
```
  
  
* On the client side, receive stream by executing:
```
vlc rtp://127.0.0.1:5000
```
