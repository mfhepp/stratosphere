# config.py
# Configuration settings for the probe and its sensors

# Sensors
SERIAL_PORT_GPS = "/dev/ttyAMA0" # just an example
GPS_ALTITUDE_MODE_CEILING = 10000 # Altitude at which GPS will be switched to Airborne-6 mode with <1g Acceleration; TBD

SERIAL_PORT_TRANSCEIVER = "/dev/ttyAMA0" # just an example
# 3-wire sensors
SENSOR_ID_INTERNAL_TEMP = ""
SENSOR_ID_BATTERY_TEMP = ""
SENSOR_ID_EXTERNAL_TEMP = ""
# I2C sensors
SENSOR_ID_ADC = ""
SENSOR_ID_PRESSURE = ""
SENSOR_ID_HUMIDITY = ""
SENSOR_ID_MOTION = ""
# ADC channels
SENSOR_ADC_CHANNEL_BATTERY_VOLTAGE = 0
SENSOR_ADC_CHANNEL_CURRENT = 1
SENSOR_ADC_CHANNEL_EXTERNAL_TEMPERATURE = 2

# Transceiver
CALLSIGN = "DO1MFH" # insert your mission callsign 
TRANSMISSION_POWER_DEFAULT = 'low' # low = 0.5 W, high = 1 W
APRS_ON = True
APRS_FREQUENCY = 144.800
APRS_RATE = 60 # one transmission per 60 seconds
SSTV_ON = True
SSTV_FREQUENCY = 144.500
SSTV_MODE = "r36" # Robot 36
# Martin 1: m1 / Martin 2: m2 / Scottie 1: s1 / Scottie 2: s2 / Scottie DX: sdx / Robot 36: r36
# Values from https://github.com/hatsunearu/pisstvpp
SSTV_DELAY = 60 # wait 60 seconds after each transmission

# Directories and filenames
LOGFILE_DIR = "/logfiles/"
VIDEO_DIR = "/videos/"
IMAGE_DIR = "/still_images/"
SSTV_DIR = "/sstv/"
DATA_DIR = "/data/"