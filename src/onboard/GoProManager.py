#
# This file handles GoPro commands and holds GoPro state
#
import sys
import yaml
import logging
import threading
from pymavlink import mavutil

from GoProConstants import *
from global_classes import logformat, dateformat

VALID_GET_COMMANDS = (mavutil.mavlink.GOPRO_COMMAND_POWER,
                      mavutil.mavlink.GOPRO_COMMAND_CAPTURE_MODE,
                      mavutil.mavlink.GOPRO_COMMAND_BATTERY,
                      mavutil.mavlink.GOPRO_COMMAND_MODEL,
                      mavutil.mavlink.GOPRO_COMMAND_VIDEO_SETTINGS,
                      mavutil.mavlink.GOPRO_COMMAND_LOW_LIGHT,
                      mavutil.mavlink.GOPRO_COMMAND_PHOTO_RESOLUTION,
                      mavutil.mavlink.GOPRO_COMMAND_PHOTO_BURST_RATE,
                      mavutil.mavlink.GOPRO_COMMAND_PROTUNE,
                      mavutil.mavlink.GOPRO_COMMAND_PROTUNE_WHITE_BALANCE,
                      mavutil.mavlink.GOPRO_COMMAND_PROTUNE_COLOUR,
                      mavutil.mavlink.GOPRO_COMMAND_PROTUNE_GAIN,
                      mavutil.mavlink.GOPRO_COMMAND_PROTUNE_SHARPNESS,
                      mavutil.mavlink.GOPRO_COMMAND_PROTUNE_EXPOSURE,
                      mavutil.mavlink.GOPRO_COMMAND_TIME,
                      mavutil.mavlink.GOPRO_COMMAND_CHARGING)

VALID_SET_COMMANDS = (mavutil.mavlink.GOPRO_COMMAND_POWER,
                      mavutil.mavlink.GOPRO_COMMAND_CAPTURE_MODE,
                      mavutil.mavlink.GOPRO_COMMAND_SHUTTER,
                      mavutil.mavlink.GOPRO_COMMAND_VIDEO_SETTINGS,
                      mavutil.mavlink.GOPRO_COMMAND_LOW_LIGHT,
                      mavutil.mavlink.GOPRO_COMMAND_PHOTO_RESOLUTION,
                      mavutil.mavlink.GOPRO_COMMAND_PHOTO_BURST_RATE,
                      mavutil.mavlink.GOPRO_COMMAND_PROTUNE,
                      mavutil.mavlink.GOPRO_COMMAND_PROTUNE_WHITE_BALANCE,
                      mavutil.mavlink.GOPRO_COMMAND_PROTUNE_COLOUR,
                      mavutil.mavlink.GOPRO_COMMAND_PROTUNE_GAIN,
                      mavutil.mavlink.GOPRO_COMMAND_PROTUNE_SHARPNESS,
                      mavutil.mavlink.GOPRO_COMMAND_PROTUNE_EXPOSURE,
                      mavutil.mavlink.GOPRO_COMMAND_TIME,
                      mavutil.mavlink.GOPRO_COMMAND_CHARGING)

REQUERY_COMMANDS = (mavutil.mavlink.GOPRO_COMMAND_VIDEO_SETTINGS,
                    mavutil.mavlink.GOPRO_COMMAND_LOW_LIGHT,
                    mavutil.mavlink.GOPRO_COMMAND_PHOTO_RESOLUTION,
                    mavutil.mavlink.GOPRO_COMMAND_PHOTO_BURST_RATE,
                    mavutil.mavlink.GOPRO_COMMAND_PROTUNE,
                    mavutil.mavlink.GOPRO_COMMAND_PROTUNE_WHITE_BALANCE,
                    mavutil.mavlink.GOPRO_COMMAND_PROTUNE_COLOUR,
                    mavutil.mavlink.GOPRO_COMMAND_PROTUNE_GAIN,
                    mavutil.mavlink.GOPRO_COMMAND_PROTUNE_SHARPNESS,
                    mavutil.mavlink.GOPRO_COMMAND_PROTUNE_EXPOSURE)


class GoProManager():
    def __init__(self, logging_level):
        # GoPro heartbeat state
        self.status = mavutil.mavlink.GOPRO_HEARTBEAT_STATUS_DISCONNECTED
        self.captureMode = CAPTURE_MODE_VIDEO
        self.isRecording = False
        # Additional GoPro state
        self.battery = 0
        self.model = MODEL_NONE
        self.videoFormat = VIDEO_FORMAT_NTSC
        self.videoResolution = 0
        self.videoFrameRate = 0
        self.videoFieldOfView = 0
        self.videoLowLight = False
        self.photoResolution = 0
        self.photoBurstRate = 0
        self.videoProtune = False
        self.videoProtuneWhiteBalance = 0
        self.videoProtuneColor = 0
        self.videoProtuneGain = 0
        self.videoProtuneSharpness = 0
        self.videoProtuneExposure = 0

        # is the GoPro currently handling a message?
        self.isGoproBusy = False
        # when the last message was sent
        self.lastRequestSent = 0.0
        # lock access to shot manager state
        self.lock = threading.Lock()

        self.logger = logging.getLogger("GoProManager")
        formatter = logging.Formatter(logformat, datefmt=dateformat)
        handler = logging.StreamHandler(stream=sys.stdout)  # TODO
        handler.setFormatter(formatter)
        handler.setLevel(logging_level)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging_level)

        self.logger.debug("Inited GoProManager")

    def state_callback(self, vehicle, name, message):
        self.lock.acquire()
        try:
            self.internal_state_callback(message)
        except Exception as e:
            self.logger.debug("state_callback error: %s" % e)
        finally:
            self.lock.release()

    def internal_state_callback(self, state):
        status = state.status
        captureMode = state.capture_mode
        isRecording = (state.flags & mavutil.mavlink.GOPRO_FLAG_RECORDING) != 0

        if self.status != status:
            self.status = status
            self.logger.debug("Gopro status changed to %d" % (self.status))

        if self.captureMode != captureMode:
            self.captureMode = captureMode
            self.logger.debug("Gopro capture mode changed to %d" % (self.captureMode))

        if self.isRecording != isRecording:
            self.isRecording = isRecording
            self.logger.debug("Gopro recording status changed to %d" % (self.isRecording))

    def get_response_callback(self, vehicle, name, message):
        self.lock.acquire()
        try:
            self.logger.debug("Got a response: {0}".format(message))
            # just to be sure, cast message to a string
            parsable_response = str(message)
            # the original message has the form `name {interesting part}`, so get rid of the preamble
            clean_response = parsable_response.replace(name + ' ', '')
            # use yaml to load the message into a dict
            yaml_response = yaml.load(clean_response)
            self.internal_get_response_callback(yaml_response)
        except Exception as e:
            self.logger.debug("get_response_callback error: %s" % e)
        finally:
            self.lock.release()

    def internal_get_response_callback(self, response):
        command = response['cmd_id']
        status = response['status']
        value = response['value']
        if status != mavutil.mavlink.GOPRO_REQUEST_SUCCESS:
            self.logger.debug("Gopro get request for command %d failed with status %d" % (command, status))
            return

        if command == mavutil.mavlink.GOPRO_COMMAND_CAPTURE_MODE:
            captureMode = value[0]
            if self.captureMode != captureMode:
                self.captureMode = captureMode
                self.logger.debug("Gopro capture mode changed to %d" % (self.captureMode))
        elif command == mavutil.mavlink.GOPRO_COMMAND_MODEL:
            model = value[0]
            if self.model != model:
                self.model = model
                self.logger.debug("Gopro model changed to %d" % (self.model))
        elif command == mavutil.mavlink.GOPRO_COMMAND_BATTERY:
            battery = value[0]
            if self.battery != battery:
                self.battery = battery
                self.logger.debug("Gopro battery changed to %d" % (self.battery))
        elif command == mavutil.mavlink.GOPRO_COMMAND_VIDEO_SETTINGS:
            videoResolution = value[0]
            videoFrameRate = value[1]
            videoFieldOfView = value[2]
            videoFormat = VIDEO_FORMAT_NTSC if (value[3] & mavutil.mavlink.GOPRO_VIDEO_SETTINGS_TV_MODE) == 0 else VIDEO_FORMAT_PAL
            if self.videoResolution != videoResolution:
                self.videoResolution = videoResolution
                self.logger.debug("Gopro video resolution changed to %d" % (self.videoResolution))
            if self.videoFrameRate != videoFrameRate:
                self.videoFrameRate = videoFrameRate
                self.logger.debug("Gopro video frame rate changed to %d" % (self.videoFrameRate))
            if self.videoFieldOfView != videoFieldOfView:
                self.videoFieldOfView = videoFieldOfView
                self.logger.debug("Gopro video field of view changed to %d" % (self.videoFieldOfView))
            if self.videoFormat != videoFormat:
                self.videoFormat = videoFormat
                self.logger.debug("Gopro video format changed to %d" % (self.videoFormat))
        elif command == mavutil.mavlink.GOPRO_COMMAND_LOW_LIGHT:
            videoLowLight = value[0] != 0
            if self.videoLowLight != videoLowLight:
                self.videoLowLight = videoLowLight
                self.logger.debug("Gopro low light changed to %d" % (self.videoLowLight))
        elif command == mavutil.mavlink.GOPRO_COMMAND_PHOTO_RESOLUTION:
            photoResolution = value[0]
            if self.photoResolution != photoResolution:
                self.photoResolution = photoResolution
                self.logger.debug("Gopro photo resolution changed to %d" % (self.photoResolution))
        elif command == mavutil.mavlink.GOPRO_COMMAND_PHOTO_BURST_RATE:
            photoBurstRate = value[0]
            if self.photoBurstRate != photoBurstRate:
                self.photoBurstRate = photoBurstRate
                self.logger.debug("Gopro photo burst rate changed to %d" % (self.photoBurstRate))
        elif command == mavutil.mavlink.GOPRO_COMMAND_PROTUNE:
            videoProtune = value[0] != 0
            if self.videoProtune != videoProtune:
                self.videoProtune = videoProtune
                self.logger.debug("Gopro video protune changed to %d" % (self.videoProtune))
        elif command == mavutil.mavlink.GOPRO_COMMAND_PROTUNE_WHITE_BALANCE:
            videoProtuneWhiteBalance = value[0]
            if self.videoProtuneWhiteBalance != videoProtuneWhiteBalance:
                self.videoProtuneWhiteBalance = videoProtuneWhiteBalance
                self.logger.debug("Gopro video protune white balance changed to %d" % (self.videoProtuneWhiteBalance))
        elif command == mavutil.mavlink.GOPRO_COMMAND_PROTUNE_COLOUR:
            videoProtuneColor = value[0]
            if self.videoProtuneColor != videoProtuneColor:
                self.videoProtuneColor = videoProtuneColor
                self.logger.debug("Gopro video protune color changed to %d" % (self.videoProtuneColor))
        elif command == mavutil.mavlink.GOPRO_COMMAND_PROTUNE_GAIN:
            videoProtuneGain = value[0]
            if self.videoProtuneGain != videoProtuneGain:
                self.videoProtuneGain = videoProtuneGain
                self.logger.debug("Gopro video protune gain changed to %d" % (self.videoProtuneGain))
        elif command == mavutil.mavlink.GOPRO_COMMAND_PROTUNE_SHARPNESS:
            videoProtuneSharpness = value[0]
            if self.videoProtuneSharpness != videoProtuneSharpness:
                self.videoProtuneSharpness = videoProtuneSharpness
                self.logger.debug("Gopro video protune sharpness changed to %d" % (self.videoProtuneSharpness))
        elif command == mavutil.mavlink.GOPRO_COMMAND_PROTUNE_EXPOSURE:
            videoProtuneExposure = value[0]
            if self.videoProtuneExposure != videoProtuneExposure:
                self.videoProtuneExposure = videoProtuneExposure
                self.logger.debug("Gopro video protune exposure changed to %d" % (self.videoProtuneExposure))
        else:
            self.logger.debug("Got unexpected Gopro callback for command %d" % (command))

    def set_response_callback(self, vehicle, name, message):
        self.lock.acquire()
        try:
            self.internal_set_response_callback(message)
        except Exception as e:
            self.logger.debug("set_response_callback error: %s" % e)
        finally:
            self.lock.release()

    def internal_set_response_callback(self, response):
        command = response[0]
        status = response[1]

        self.logger.debug("Got Gopro set response for command %d with status %d" % (command, status))
