from enum import Enum

# GoPro constants as defined in https://docs.google.com/document/d/1CcYOCZRw9C4sIQu4xDXjPMkxZYROmTLB0EtpZamnq74/edit#

GOPRO_V1_SPEC_VERSION = 1
GOPRO_V2_SPEC_VERSION = 2

CAPTURE_MODE_VIDEO = 0
CAPTURE_MODE_PHOTO = 1
CAPTURE_MODE_BURST = 2  # Burst only for Hero 3+
CAPTURE_MODE_TIMELAPSE = 3
CAPTURE_MODE_MULTISHOT = 4  # Multishot only for Hero4

SHUTTER_STATUS_STOP_VIDEO = 0
SHUTTER_STATUS_START_VIDEO = 1
SHUTTER_STATUS_STOP_BURST = 2
SHUTTER_STATUS_START_BURST = 3

MODEL_NONE = 0
MODEL_HERO3PLUS_SILVER = 10
MODEL_HERO3PLUS_BLACK = 11

STATUS_NO_GOPRO = 0
STATUS_INCOMPATIBLE_GOPRO = 1
STATUS_GOPRO_CONNECTED = 2
STATUS_GOPRO_ERROR = 3

RECORD_COMMAND_STOP = 0
RECORD_COMMAND_START = 1
RECORD_COMMAND_TOGGLE = 2

VIDEO_FORMAT_NTSC = 0
VIDEO_FORMAT_PAL = 1


class MAV_MODE_GIMBAL(Enum):
    MAV_MODE_GIMBAL_UNINITIALIZED = 0  # Gimbal is powered on but has not started initializing yet
    MAV_MODE_GIMBAL_CALIBRATING_PITCH = 1  # Gimbal is currently running calibration on the pitch axis
    MAV_MODE_GIMBAL_CALIBRATING_ROLL = 2  # Gimbal is currently running calibration on the roll axis
    MAV_MODE_GIMBAL_CALIBRATING_YAW = 3  # Gimbal is currently running calibration on the yaw axis
    MAV_MODE_GIMBAL_INITIALIZED = 4  # Gimbal has finished calibrating and initializing, but is relaxed pending reception of first rate command from copter
    MAV_MODE_GIMBAL_ACTIVE = 5  # Gimbal is actively stabilizing
    MAV_MODE_GIMBAL_RATE_CMD_TIMEOUT = 6
    # Gimbal is relaxed because it missed more than 10 expected rate command messages in a row.
    # Gimbal will move back to active mode when it receives a new rate command
    MAV_MODE_GIMBAL_ENUM_END = 7  #



class GIMBAL_AXIS(Enum):
    GIMBAL_AXIS_YAW = 0,  # Gimbal yaw axis
    GIMBAL_AXIS_PITCH = 1,  # Gimbal pitch axis
    GIMBAL_AXIS_ROLL = 2,  # Gimbal roll axis
    GIMBAL_AXIS_ENUM_END = 3,  #


class GIMBAL_AXIS_CALIBRATION_STATUS(Enum):
    GIMBAL_AXIS_CALIBRATION_STATUS_IN_PROGRESS = 0,  # Axis calibration is in progress
    GIMBAL_AXIS_CALIBRATION_STATUS_SUCCEEDED = 1,  # Axis calibration succeeded
    GIMBAL_AXIS_CALIBRATION_STATUS_FAILED = 2,  # Axis calibration failed
    GIMBAL_AXIS_CALIBRATION_STATUS_ENUM_END = 3,  #


class GIMBAL_AXIS_CALIBRATION_REQUIRED(Enum):
    GIMBAL_AXIS_CALIBRATION_REQUIRED_UNKNOWN = 0,  # Whether or not this axis requires calibration is unknown at this time
    GIMBAL_AXIS_CALIBRATION_REQUIRED_TRUE = 1,  # This axis requires calibration
    GIMBAL_AXIS_CALIBRATION_REQUIRED_FALSE = 2,  # This axis does not require calibration
    GIMBAL_AXIS_CALIBRATION_REQUIRED_ENUM_END = 3,  #


class GOPRO_HEARTBEAT_STATUS(Enum):
    GOPRO_HEARTBEAT_STATUS_DISCONNECTED = 0,  # No GoPro connected
    GOPRO_HEARTBEAT_STATUS_INCOMPATIBLE = 1,  # The detected GoPro is not HeroBus compatible
    GOPRO_HEARTBEAT_STATUS_CONNECTED = 2,  # A HeroBus compatible GoPro is connected
    GOPRO_HEARTBEAT_STATUS_ERROR = 3,  # An unrecoverable error was encountered with the connected GoPro, it may require a power cycle
    GOPRO_HEARTBEAT_STATUS_ENUM_END = 4,  #


class GOPRO_HEARTBEAT_FLAGS(Enum):
    GOPRO_FLAG_RECORDING = 1,  # GoPro is currently recording
    GOPRO_HEARTBEAT_FLAGS_ENUM_END = 2,  #


class GOPRO_REQUEST_STATUS(Enum):
    GOPRO_REQUEST_SUCCESS = 0,  # The write message with ID indicated succeeded
    GOPRO_REQUEST_FAILED = 1,  # The write message with ID indicated failed
    GOPRO_REQUEST_STATUS_ENUM_END = 2,  #


class GOPRO_COMMAND(Enum):
    GOPRO_COMMAND_POWER = 0,  # (Get/Set)
    GOPRO_COMMAND_CAPTURE_MODE = 1,  # (Get/Set)
    GOPRO_COMMAND_SHUTTER = 2,  # (___/Set)
    GOPRO_COMMAND_BATTERY = 3,  # (Get/___)
    GOPRO_COMMAND_MODEL = 4,  # (Get/___)
    GOPRO_COMMAND_VIDEO_SETTINGS = 5,  # (Get/Set)
    GOPRO_COMMAND_LOW_LIGHT = 6,  # (Get/Set)
    GOPRO_COMMAND_PHOTO_RESOLUTION = 7,  # (Get/Set)
    GOPRO_COMMAND_PHOTO_BURST_RATE = 8,  # (Get/Set)
    GOPRO_COMMAND_PROTUNE = 9,  # (Get/Set)
    GOPRO_COMMAND_PROTUNE_WHITE_BALANCE = 10,  # (Get/Set) Hero 3+ Only
    GOPRO_COMMAND_PROTUNE_COLOUR = 11,  # (Get/Set) Hero 3+ Only
    GOPRO_COMMAND_PROTUNE_GAIN = 12,  # (Get/Set) Hero 3+ Only
    GOPRO_COMMAND_PROTUNE_SHARPNESS = 13,  # (Get/Set) Hero 3+ Only
    GOPRO_COMMAND_PROTUNE_EXPOSURE = 14,  # (Get/Set) Hero 3+ Only
    GOPRO_COMMAND_TIME = 15,  # (Get/Set)
    GOPRO_COMMAND_CHARGING = 16,  # (Get/Set)
    GOPRO_COMMAND_ENUM_END = 17,  #


class GOPRO_CAPTURE_MODE(Enum):
    GOPRO_CAPTURE_MODE_VIDEO = 0,  # Video mode
    GOPRO_CAPTURE_MODE_PHOTO = 1,  # Photo mode
    GOPRO_CAPTURE_MODE_BURST = 2,  # Burst mode, hero 3+ only
    GOPRO_CAPTURE_MODE_TIME_LAPSE = 3,  # Time lapse mode, hero 3+ only
    GOPRO_CAPTURE_MODE_MULTI_SHOT = 4,  # Multi shot mode, hero 4 only
    GOPRO_CAPTURE_MODE_PLAYBACK = 5,  # Playback mode, hero 4 only, silver only except when LCD or HDMI is connected to black
    GOPRO_CAPTURE_MODE_SETUP = 6,  # Playback mode, hero 4 only
    GOPRO_CAPTURE_MODE_UNKNOWN = 255,  # Mode not yet known
    GOPRO_CAPTURE_MODE_ENUM_END = 256,  #


class GOPRO_RESOLUTION(Enum):
    GOPRO_RESOLUTION_480p = 0,  # 848 x 480 (480p)
    GOPRO_RESOLUTION_720p = 1,  # 1280 x 720 (720p)
    GOPRO_RESOLUTION_960p = 2,  # 1280 x 960 (960p)
    GOPRO_RESOLUTION_1080p = 3,  # 1920 x 1080 (1080p)
    GOPRO_RESOLUTION_1440p = 4,  # 1920 x 1440 (1440p)
    GOPRO_RESOLUTION_2_7k_17_9 = 5,  # 2704 x 1440 (2.7k-17:9)
    GOPRO_RESOLUTION_2_7k_16_9 = 6,  # 2704 x 1524 (2.7k-16:9)
    GOPRO_RESOLUTION_2_7k_4_3 = 7,  # 2704 x 2028 (2.7k-4:3)
    GOPRO_RESOLUTION_4k_16_9 = 8,  # 3840 x 2160 (4k-16:9)
    GOPRO_RESOLUTION_4k_17_9 = 9,  # 4096 x 2160 (4k-17:9)
    GOPRO_RESOLUTION_720p_SUPERVIEW = 10,  # 1280 x 720 (720p-SuperView)
    GOPRO_RESOLUTION_1080p_SUPERVIEW = 11,  # 1920 x 1080 (1080p-SuperView)
    GOPRO_RESOLUTION_2_7k_SUPERVIEW = 12,  # 2704 x 1520 (2.7k-SuperView)
    GOPRO_RESOLUTION_4k_SUPERVIEW = 13,  # 3840 x 2160 (4k-SuperView)
    GOPRO_RESOLUTION_ENUM_END = 14,  #


class GOPRO_FRAME_RATE(Enum):
    GOPRO_FRAME_RATE_12 = 0,  # 12 FPS
    GOPRO_FRAME_RATE_15 = 1,  # 15 FPS
    GOPRO_FRAME_RATE_24 = 2,  # 24 FPS
    GOPRO_FRAME_RATE_25 = 3,  # 25 FPS
    GOPRO_FRAME_RATE_30 = 4,  # 30 FPS
    GOPRO_FRAME_RATE_48 = 5,  # 48 FPS
    GOPRO_FRAME_RATE_50 = 6,  # 50 FPS
    GOPRO_FRAME_RATE_60 = 7,  # 60 FPS
    GOPRO_FRAME_RATE_80 = 8,  # 80 FPS
    GOPRO_FRAME_RATE_90 = 9,  # 90 FPS
    GOPRO_FRAME_RATE_100 = 10,  # 100 FPS
    GOPRO_FRAME_RATE_120 = 11,  # 120 FPS
    GOPRO_FRAME_RATE_240 = 12,  # 240 FPS
    GOPRO_FRAME_RATE_12_5 = 13,  # 12.5 FPS
    GOPRO_FRAME_RATE_ENUM_END = 14,  #


class GOPRO_FIELD_OF_VIEW(Enum):
    GOPRO_FIELD_OF_VIEW_WIDE = 0,  # 0x00: Wide
    GOPRO_FIELD_OF_VIEW_MEDIUM = 1,  # 0x01: Medium
    GOPRO_FIELD_OF_VIEW_NARROW = 2,  # 0x02: Narrow
    GOPRO_FIELD_OF_VIEW_ENUM_END = 3,  #


class GOPRO_VIDEO_SETTINGS_FLAGS(Enum):
    GOPRO_VIDEO_SETTINGS_TV_MODE = 1,  # 0 = NTSC, 1 = PAL
    GOPRO_VIDEO_SETTINGS_FLAGS_ENUM_END = 2,  #


class GOPRO_PHOTO_RESOLUTION(Enum):
    GOPRO_PHOTO_RESOLUTION_5MP_MEDIUM = 0,  # 5MP Medium
    GOPRO_PHOTO_RESOLUTION_7MP_MEDIUM = 1,  # 7MP Medium
    GOPRO_PHOTO_RESOLUTION_7MP_WIDE = 2,  # 7MP Wide
    GOPRO_PHOTO_RESOLUTION_10MP_WIDE = 3,  # 10MP Wide
    GOPRO_PHOTO_RESOLUTION_12MP_WIDE = 4,  # 12MP Wide
    GOPRO_PHOTO_RESOLUTION_ENUM_END = 5,  #


class GOPRO_PROTUNE_WHITE_BALANCE(Enum):
    GOPRO_PROTUNE_WHITE_BALANCE_AUTO = 0,  # Auto
    GOPRO_PROTUNE_WHITE_BALANCE_3000K = 1,  # 3000K
    GOPRO_PROTUNE_WHITE_BALANCE_5500K = 2,  # 5500K
    GOPRO_PROTUNE_WHITE_BALANCE_6500K = 3,  # 6500K
    GOPRO_PROTUNE_WHITE_BALANCE_RAW = 4,  # Camera Raw
    GOPRO_PROTUNE_WHITE_BALANCE_ENUM_END = 5,  #


class GOPRO_PROTUNE_COLOUR(Enum):
    GOPRO_PROTUNE_COLOUR_STANDARD = 0,  # Auto
    GOPRO_PROTUNE_COLOUR_NEUTRAL = 1,  # Neutral
    GOPRO_PROTUNE_COLOUR_ENUM_END = 2,  #


class GOPRO_PROTUNE_GAIN(Enum):
    GOPRO_PROTUNE_GAIN_400 = 0,  # ISO 400
    GOPRO_PROTUNE_GAIN_800 = 1,  # ISO 800 (Only Hero 4)
    GOPRO_PROTUNE_GAIN_1600 = 2,  # ISO 1600
    GOPRO_PROTUNE_GAIN_3200 = 3,  # ISO 3200 (Only Hero 4)
    GOPRO_PROTUNE_GAIN_6400 = 4,  # ISO 6400
    GOPRO_PROTUNE_GAIN_ENUM_END = 5,  #


class GOPRO_PROTUNE_SHARPNESS(Enum):
    GOPRO_PROTUNE_SHARPNESS_LOW = 0,  # Low Sharpness
    GOPRO_PROTUNE_SHARPNESS_MEDIUM = 1,  # Medium Sharpness
    GOPRO_PROTUNE_SHARPNESS_HIGH = 2,  # High Sharpness
    GOPRO_PROTUNE_SHARPNESS_ENUM_END = 3,  #


class GOPRO_PROTUNE_EXPOSURE(Enum):
    GOPRO_PROTUNE_EXPOSURE_NEG_5_0 = 0,  # -5.0 EV (Hero 3+ Only)
    GOPRO_PROTUNE_EXPOSURE_NEG_4_5 = 1,  # -4.5 EV (Hero 3+ Only)
    GOPRO_PROTUNE_EXPOSURE_NEG_4_0 = 2,  # -4.0 EV (Hero 3+ Only)
    GOPRO_PROTUNE_EXPOSURE_NEG_3_5 = 3,  # -3.5 EV (Hero 3+ Only)
    GOPRO_PROTUNE_EXPOSURE_NEG_3_0 = 4,  # -3.0 EV (Hero 3+ Only)
    GOPRO_PROTUNE_EXPOSURE_NEG_2_5 = 5,  # -2.5 EV (Hero 3+ Only)
    GOPRO_PROTUNE_EXPOSURE_NEG_2_0 = 6,  # -2.0 EV
    GOPRO_PROTUNE_EXPOSURE_NEG_1_5 = 7,  # -1.5 EV
    GOPRO_PROTUNE_EXPOSURE_NEG_1_0 = 8,  # -1.0 EV
    GOPRO_PROTUNE_EXPOSURE_NEG_0_5 = 9,  # -0.5 EV
    GOPRO_PROTUNE_EXPOSURE_ZERO = 10,  # 0.0 EV
    GOPRO_PROTUNE_EXPOSURE_POS_0_5 = 11,  # +0.5 EV
    GOPRO_PROTUNE_EXPOSURE_POS_1_0 = 12,  # +1.0 EV
    GOPRO_PROTUNE_EXPOSURE_POS_1_5 = 13,  # +1.5 EV
    GOPRO_PROTUNE_EXPOSURE_POS_2_0 = 14,  # +2.0 EV
    GOPRO_PROTUNE_EXPOSURE_POS_2_5 = 15,  # +2.5 EV (Hero 3+ Only)
    GOPRO_PROTUNE_EXPOSURE_POS_3_0 = 16,  # +3.0 EV (Hero 3+ Only)
    GOPRO_PROTUNE_EXPOSURE_POS_3_5 = 17,  # +3.5 EV (Hero 3+ Only)
    GOPRO_PROTUNE_EXPOSURE_POS_4_0 = 18,  # +4.0 EV (Hero 3+ Only)
    GOPRO_PROTUNE_EXPOSURE_POS_4_5 = 19,  # +4.5 EV (Hero 3+ Only)
    GOPRO_PROTUNE_EXPOSURE_POS_5_0 = 20,  # +5.0 EV (Hero 3+ Only)
    GOPRO_PROTUNE_EXPOSURE_ENUM_END = 21,  #


class GOPRO_CHARGING(Enum):
    GOPRO_CHARGING_DISABLED = 0,  # Charging disabled
    GOPRO_CHARGING_ENABLED = 1,  # Charging enabled
    GOPRO_CHARGING_ENUM_END = 2,  #


class GOPRO_MODEL(Enum):
    GOPRO_MODEL_UNKNOWN = 0,  # Unknown gopro model
    GOPRO_MODEL_HERO_3_PLUS_SILVER = 1,  # Hero 3+ Silver (HeroBus not supported by GoPro)
    GOPRO_MODEL_HERO_3_PLUS_BLACK = 2,  # Hero 3+ Black
    GOPRO_MODEL_HERO_4_SILVER = 3,  # Hero 4 Silver
    GOPRO_MODEL_HERO_4_BLACK = 4,  # Hero 4 Black
    GOPRO_MODEL_ENUM_END = 5,  #


class GOPRO_BURST_RATE(Enum):
    GOPRO_BURST_RATE_3_IN_1_SECOND = 0,  # 3 Shots / 1 Second
    GOPRO_BURST_RATE_5_IN_1_SECOND = 1,  # 5 Shots / 1 Second
    GOPRO_BURST_RATE_10_IN_1_SECOND = 2,  # 10 Shots / 1 Second
    GOPRO_BURST_RATE_10_IN_2_SECOND = 3,  # 10 Shots / 2 Second
    GOPRO_BURST_RATE_10_IN_3_SECOND = 4,  # 10 Shots / 3 Second (Hero 4 Only)
    GOPRO_BURST_RATE_30_IN_1_SECOND = 5,  # 30 Shots / 1 Second
    GOPRO_BURST_RATE_30_IN_2_SECOND = 6,  # 30 Shots / 2 Second
    GOPRO_BURST_RATE_30_IN_3_SECOND = 7,  # 30 Shots / 3 Second
    GOPRO_BURST_RATE_30_IN_6_SECOND = 8,  # 30 Shots / 6 Second
    GOPRO_BURST_RATE_ENUM_END = 9,  #
