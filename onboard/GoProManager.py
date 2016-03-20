#
# This file handles GoPro commands and holds GoPro state
#
import Queue
import threading
import struct
import time
import sys
import logging
from pymavlink import mavutil
import app_packet
from GoProConstants import *
from global_classes import logging_level

logger = logging.getLogger("Navigation Handler")
formatter = logging.Formatter('[%(levelname)s] %(message)s')
handler = logging.StreamHandler(stream=sys.stdout)
handler.setFormatter(formatter)
handler.setLevel(logging_level)
logger.addHandler(handler)
logger.setLevel(logging_level)

# tuple of message types that we handle
GOPROMESSAGES = \
    (
        app_packet.GOPRO_SET_ENABLED,
        app_packet.GOPRO_SET_REQUEST,
        app_packet.GOPRO_RECORD,
        app_packet.GOPRO_REQUEST_STATE,
        app_packet.GOPRO_SET_EXTENDED_REQUEST
    )

# see https://docs.google.com/document/d/1CcYOCZRw9C4sIQu4xDXjPMkxZYROmTLB0EtpZamnq74/edit#heading=h.y6z65lvic5q5
VALID_GET_COMMANDS = \
    (
        mavutil.mavlink.GOPRO_COMMAND_POWER,
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
        mavutil.mavlink.GOPRO_COMMAND_CHARGING,
    )

VALID_SET_COMMANDS = \
    (
        mavutil.mavlink.GOPRO_COMMAND_POWER,
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
        mavutil.mavlink.GOPRO_COMMAND_CHARGING,
    )

REQUERY_COMMANDS = \
    (
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
    )


class GoProManager():
    def __init__(self):
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

        # self.enabled = True
        # self.setGimbalEnabledParam()

        logger.debug("Inited GoProManager")

    def state_callback(self, vehicle, name, message):
        self.lock.acquire()
        try:
            self.internal_state_callback(message)
        except Exception as e:
            logger.debug("state_callback error: %s" % e)
        finally:
            self.lock.release()

    def internal_state_callback(self, state):
        status = state.status
        captureMode = state.capture_mode
        isRecording = (state.flags & mavutil.mavlink.GOPRO_FLAG_RECORDING) != 0
        sendState = False

        if self.status != status:
            self.status = status
            logger.debug("Gopro status changed to %d" % (self.status))
            sendState = True

            # right now, query status when we initially connect
            # if self.status == mavutil.mavlink.GOPRO_HEARTBEAT_STATUS_CONNECTED:
            #     self.isGoproBusy = False
            #     self.msgQueue = Queue.Queue()
            #     self.sendGoProRequest(mavutil.mavlink.GOPRO_COMMAND_CAPTURE_MODE)
            #     self.sendGoProRequest(mavutil.mavlink.GOPRO_COMMAND_BATTERY)
            #     self.sendGoProRequest(mavutil.mavlink.GOPRO_COMMAND_MODEL)
            #     self.sendGoProRequest(mavutil.mavlink.GOPRO_COMMAND_VIDEO_SETTINGS)
            #     self.sendGoProRequest(mavutil.mavlink.GOPRO_COMMAND_LOW_LIGHT)
            #     self.sendGoProRequest(mavutil.mavlink.GOPRO_COMMAND_PHOTO_RESOLUTION)
            #     self.sendGoProRequest(mavutil.mavlink.GOPRO_COMMAND_PHOTO_BURST_RATE)
            #     self.sendGoProRequest(mavutil.mavlink.GOPRO_COMMAND_PROTUNE)
            #     self.sendGoProRequest(mavutil.mavlink.GOPRO_COMMAND_PROTUNE_WHITE_BALANCE)
            #     self.sendGoProRequest(mavutil.mavlink.GOPRO_COMMAND_PROTUNE_COLOUR)
            #     self.sendGoProRequest(mavutil.mavlink.GOPRO_COMMAND_PROTUNE_GAIN)
            #     self.sendGoProRequest(mavutil.mavlink.GOPRO_COMMAND_PROTUNE_SHARPNESS)
            #     self.sendGoProRequest(mavutil.mavlink.GOPRO_COMMAND_PROTUNE_EXPOSURE)

        if self.captureMode != captureMode:
            self.captureMode = captureMode
            logger.debug("Gopro capture mode changed to %d" % (self.captureMode))
            sendState = True

        if self.isRecording != isRecording:
            self.isRecording = isRecording
            logger.debug("Gopro recording status changed to %d" % (self.isRecording))
            sendState = True

        if sendState:
            self.sendState()

    def get_response_callback(self, vehicle, name, message):
        self.lock.acquire()
        logger.debug("Got a response:{0}".format(name))
        logger.debug("Got a response:{0}".format(message))
        try:
            self.internal_get_response_callback(message)
        except Exception as e:
            logger.debug("get_response_callback error: %s" % e)
        finally:
            self.lock.release()

    def internal_get_response_callback(self, response):
        command = response[0]
        status = response[1]
        value = response[2]
        sendState = False
        logger.debug("Got a response: %d" % (value))
        if status != mavutil.mavlink.GOPRO_REQUEST_SUCCESS:
            logger.debug("Gopro get request for command %d failed with status %d" % (command, status))
            return

        if command == mavutil.mavlink.GOPRO_COMMAND_CAPTURE_MODE:
            captureMode = value[0]
            if self.captureMode != captureMode:
                self.captureMode = captureMode
                sendState = True
                logger.debug("Gopro capture mode changed to %d" % (self.captureMode))
        elif command == mavutil.mavlink.GOPRO_COMMAND_MODEL:
            model = value[0]
            if self.model != model:
                self.model = model
                sendState = True
                logger.debug("Gopro model changed to %d" % (self.model))
        elif command == mavutil.mavlink.GOPRO_COMMAND_BATTERY:
            battery = value[0]
            if self.battery != battery:
                self.battery = battery
                sendState = True
                logger.debug("Gopro battery changed to %d" % (self.battery))
        elif command == mavutil.mavlink.GOPRO_COMMAND_VIDEO_SETTINGS:
            videoResolution = value[0]
            videoFrameRate = value[1]
            videoFieldOfView = value[2]
            videoFormat = VIDEO_FORMAT_NTSC if (value[3] & mavutil.mavlink.GOPRO_VIDEO_SETTINGS_TV_MODE) == 0 else VIDEO_FORMAT_PAL
            if self.videoResolution != videoResolution:
                self.videoResolution = videoResolution
                sendState = True
                logger.debug("Gopro video resolution changed to %d" % (self.videoResolution))
            if self.videoFrameRate != videoFrameRate:
                self.videoFrameRate = videoFrameRate
                sendState = True
                logger.debug("Gopro video frame rate changed to %d" % (self.videoFrameRate))
            if self.videoFieldOfView != videoFieldOfView:
                self.videoFieldOfView = videoFieldOfView
                sendState = True
                logger.debug("Gopro video field of view changed to %d" % (self.videoFieldOfView))
            if self.videoFormat != videoFormat:
                self.videoFormat = videoFormat
                sendState = True
                logger.debug("Gopro video format changed to %d" % (self.videoFormat))
        elif command == mavutil.mavlink.GOPRO_COMMAND_LOW_LIGHT:
            videoLowLight = value[0] != 0
            if self.videoLowLight != videoLowLight:
                self.videoLowLight = videoLowLight
                sendState = True
                logger.debug("Gopro low light changed to %d" % (self.videoLowLight))
        elif command == mavutil.mavlink.GOPRO_COMMAND_PHOTO_RESOLUTION:
            photoResolution = value[0]
            if self.photoResolution != photoResolution:
                self.photoResolution = photoResolution
                sendState = True
                logger.debug("Gopro photo resolution changed to %d" % (self.photoResolution))
        elif command == mavutil.mavlink.GOPRO_COMMAND_PHOTO_BURST_RATE:
            photoBurstRate = value[0]
            if self.photoBurstRate != photoBurstRate:
                self.photoBurstRate = photoBurstRate
                sendState = True
                logger.debug("Gopro photo burst rate changed to %d" % (self.photoBurstRate))
        elif command == mavutil.mavlink.GOPRO_COMMAND_PROTUNE:
            videoProtune = value[0] != 0
            if self.videoProtune != videoProtune:
                self.videoProtune = videoProtune
                sendState = True
                logger.debug("Gopro video protune changed to %d" % (self.videoProtune))
        elif command == mavutil.mavlink.GOPRO_COMMAND_PROTUNE_WHITE_BALANCE:
            videoProtuneWhiteBalance = value[0]
            if self.videoProtuneWhiteBalance != videoProtuneWhiteBalance:
                self.videoProtuneWhiteBalance = videoProtuneWhiteBalance
                sendState = True
                logger.debug("Gopro video protune white balance changed to %d" % (self.videoProtuneWhiteBalance))
        elif command == mavutil.mavlink.GOPRO_COMMAND_PROTUNE_COLOUR:
            videoProtuneColor = value[0]
            if self.videoProtuneColor != videoProtuneColor:
                self.videoProtuneColor = videoProtuneColor
                sendState = True
                logger.debug("Gopro video protune color changed to %d" % (self.videoProtuneColor))
        elif command == mavutil.mavlink.GOPRO_COMMAND_PROTUNE_GAIN:
            videoProtuneGain = value[0]
            if self.videoProtuneGain != videoProtuneGain:
                self.videoProtuneGain = videoProtuneGain
                sendState = True
                logger.debug("Gopro video protune gain changed to %d" % (self.videoProtuneGain))
        elif command == mavutil.mavlink.GOPRO_COMMAND_PROTUNE_SHARPNESS:
            videoProtuneSharpness = value[0]
            if self.videoProtuneSharpness != videoProtuneSharpness:
                self.videoProtuneSharpness = videoProtuneSharpness
                sendState = True
                logger.debug("Gopro video protune sharpness changed to %d" % (self.videoProtuneSharpness))
        elif command == mavutil.mavlink.GOPRO_COMMAND_PROTUNE_EXPOSURE:
            videoProtuneExposure = value[0]
            if self.videoProtuneExposure != videoProtuneExposure:
                self.videoProtuneExposure = videoProtuneExposure
                sendState = True
                logger.debug("Gopro video protune exposure changed to %d" % (self.videoProtuneExposure))
        else:
            logger.debug("Got unexpected Gopro callback for command %d" % (command))

        if sendState:
            self.sendState()

        self.processMsgQueue()

    def set_response_callback(self, vehicle, name, message):
        self.lock.acquire()
        try:
            self.internal_set_response_callback(message)
        except Exception as e:
            logger.debug("set_response_callback error: %s" % e)
        finally:
            self.lock.release()

    def internal_set_response_callback(self, response):
        command = response[0]
        status = response[1]

        logger.debug("Got Gopro set response for command %d with status %d" % (command, status))
        if status != mavutil.mavlink.GOPRO_REQUEST_SUCCESS:
            # if a set request failed, return current state to resynchronize client
            self.sendState()

        self.processMsgQueue()

    # wrapper to create a gopro_get_request mavlink message with the given command
    def sendGoProRequest(self, command):
        if command not in VALID_GET_COMMANDS:
            logger.debug("Got invalid Gopro get command %d" % (command))
            return

        msg = self.shotMgr.vehicle.message_factory.gopro_get_request_encode(0,
                                                                            mavutil.mavlink.MAV_COMP_ID_GIMBAL,  # target system, target component
                                                                            command)

        self.queueMsg(msg)

    # wrapper to create a gopro_set_request mavlink message with the given command and value
    def sendGoProCommand(self, command, value):
        if command not in VALID_SET_COMMANDS:
            logger.debug("Got invalid Gopro set command %d" % (command))
            return
        if not self.isValidCommandValue(value):
            logger.debug("Invalid value for Gopro set command %d" % (command))
            return

        msg = self.shotMgr.vehicle.message_factory.gopro_set_request_encode(0,
                                                                            mavutil.mavlink.MAV_COMP_ID_GIMBAL,    # target system, target component
                                                                            command, value)

        self.queueMsg(msg)

        # Follow up with a get request if notification of change is required
        if command in REQUERY_COMMANDS:
            self.sendGoProRequest(command)

    def isValidCommandValue(self, value):
        if value[0] < 0 or value[0] > 255:
            return False
        if value[1] < 0 or value[1] > 255:
            return False
        if value[2] < 0 or value[2] > 255:
            return False
        if value[3] < 0 or value[3] > 255:
            return False
        return True

    # handle a call to start/stop/toggle recording on the given mode
    def handleRecordCommand(self, mode, command):
        if self.status == mavutil.mavlink.GOPRO_HEARTBEAT_STATUS_DISCONNECTED or self.status == mavutil.mavlink.GOPRO_HEARTBEAT_STATUS_INCOMPATIBLE:
            logger.debug("handleRecordCommand called but GoPro is not connected")
            return

        logger.debug("handleRecordCommand called with mode %d, command %d" % (mode, command))

        if mode == CAPTURE_MODE_VIDEO:
            # do we want to start or stop recording?
            if command == RECORD_COMMAND_STOP:
                startstop = 0
            elif command == RECORD_COMMAND_START:
                startstop = 1
            elif command == RECORD_COMMAND_TOGGLE:
                startstop = 0 if self.isRecording else 1
            else:
                return

            # don't start recording if we're already recording
            if self.isRecording and startstop == 1:
                return

            logger.debug("Sending command for video recording: %d" % (startstop))

            # we're not in video mode, switch to it!
            if self.captureMode != CAPTURE_MODE_VIDEO:
                self.sendGoProCommand(mavutil.mavlink.GOPRO_COMMAND_CAPTURE_MODE, (CAPTURE_MODE_VIDEO, 0, 0, 0))

            self.sendGoProCommand(mavutil.mavlink.GOPRO_COMMAND_SHUTTER, (startstop, 0, 0, 0))
        elif mode == CAPTURE_MODE_PHOTO or mode == CAPTURE_MODE_BURST or mode == CAPTURE_MODE_MULTISHOT:
            # don't handle nonsensical commands
            if command == RECORD_COMMAND_STOP:
                return

            # for now, let's try switching out of video mode, taking a picture, and then switching back
            if self.captureMode == CAPTURE_MODE_VIDEO:
                self.sendGoProCommand(mavutil.mavlink.GOPRO_COMMAND_CAPTURE_MODE, (CAPTURE_MODE_PHOTO, 0, 0, 0))
                self.sendGoProCommand(mavutil.mavlink.GOPRO_COMMAND_SHUTTER, (1, 0, 0, 0))
                self.sendGoProCommand(mavutil.mavlink.GOPRO_COMMAND_CAPTURE_MODE, (CAPTURE_MODE_VIDEO, 0, 0, 0))
                logger.debug("Sending command to take go to photo mode, take a still, and return")
            else:
                self.sendGoProCommand(mavutil.mavlink.GOPRO_COMMAND_SHUTTER, (1, 0, 0, 0))
                logger.debug("Sending command to take a still/burst/multishot")

    # since the gopro can't handle multiple messages at once, we wait for a response before sending
    # each subsequent message.  This is how we queue up messages
    def queueMsg(self, msg):
        if self.isGoproBusy and time.time() > self.lastRequestSent + 2.0:
            self.isGoproBusy = False
            self.msgQueue = Queue.Queue()
            logger.debug("no gopro response delivered before timeout (%s seconds ago), flushing queue" % (time.time() - self.lastRequestSent))
            # return current state to resynchronize client
            self.sendState()

        if self.isGoproBusy:
            self.msgQueue.put(msg)
            logger.debug("queuing up gopro message.  Queue size is now %d" % (self.msgQueue.qsize()))
        else:
            self.isGoproBusy = True
            self.lastRequestSent = time.time()
            # Need to send False for fix_targeting so our message gets routed to the gimbal
            self.shotMgr.vehicle.send_mavlink(msg)
            logger.debug("no queue, just sending message %s" % msg)

    # called whenever the message queue is ready to send another message.
    def processMsgQueue(self):
        if self.msgQueue.empty():
            self.isGoproBusy = False
        else:
            msg = self.msgQueue.get_nowait()
            self.lastRequestSent = time.time()
            # Need to send False for fix_targeting so our message gets routed to the gimbal
            self.shotMgr.vehicle.send_mavlink(msg)
            logger.debug("sending message from the queue.  Size is now %d" % (self.msgQueue.qsize()))

    # shotManager receives this gopro control packet and passes it here
    def handlePacket(self, type, data):
        self.lock.acquire()
        try:
            self.internalHandlePacket(type, data)
        finally:
            self.lock.release()

    def internalHandlePacket(self, type, data):
        if type == app_packet.GOPRO_SET_ENABLED:
            (enabled, ) = struct.unpack('<I', data)
            self.setGoProEnabled(enabled > 0)
        elif type == app_packet.GOPRO_SET_REQUEST:
            (command, value) = struct.unpack('<HH', data)
            self.sendGoProCommand(command, (value, 0, 0, 0))
        elif type == app_packet.GOPRO_RECORD:
            (startstop, ) = struct.unpack('<I', data)
            self.handleRecordCommand(self.captureMode, startstop)
        elif type == app_packet.GOPRO_REQUEST_STATE:
            self.sendState()
        elif type == app_packet.GOPRO_SET_EXTENDED_REQUEST:
            (command, value1, value2, value3, value4, ) = struct.unpack("<HBBBB", data)
            self.sendGoProCommand(command, (value1, value2, value3, value4))

    # Tell the gimbal to turn Gopro comms on/off depending on if our internal
    # flag is set to on/off
    def setGimbalEnabledParam(self):
        value = 1.0 if self.enabled else 0.0

        msg = self.shotMgr.vehicle.message_factory.param_set_encode(
            0, mavutil.mavlink.MAV_COMP_ID_GIMBAL,    # target system, target component
            "GMB_GP_CTRL", value, mavutil.mavlink.MAV_PARAM_TYPE_REAL32
        )

        self.shotMgr.vehicle.send_mavlink(msg)

    # enable/disable Gopro controls
    def setGoProEnabled(self, enabled):
        self.enabled = enabled
        self.setGimbalEnabledParam()
