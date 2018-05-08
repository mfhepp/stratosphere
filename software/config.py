#!/usr/bin/env python
# -*- coding: utf-8 -*-

# config.py
# Configuration settings for the probe and its sensors
import RPi.GPIO as GPIO

# Mission configuration
DEBUG = True
POLL_FREQUENCY = 1  # Sensor poll frequency in Hz
CALLSIGN = 'DL0UBW'  # insert your mission callsign
APRS_SSID = CALLSIGN + '-11'
MISSION_TEXT = 'High-Altitude Balloon \nMission STRATOSPHERE 2018\n' + CALLSIGN
APRS_COMMENT = 'UniBwM Balloon 2018'
IMAGE_TEXT = 'High-Altitude Balloon Mission DL0UBW, UniBwM \
%(time)s\nalt=%(alt)s, lat=%(lat)s, lon=%(lon)s'
VIDEO_TEXT = 'High-Altitude Balloon Mission DL0UBW, UniBwM \
%(time)s\nalt=%(alt)s m, lat=%(lat)s, lon=%(lon)s'
COPYRIGHT_TEXT = 'Copyright (c) 2018 Universitaet der Bundeswehr Muenchen'

# Power management settings
BATTERY_VOLTAGE_SYSTEM_SHUTDOWN = 7.5
BATTERY_VOLTAGE_SAVE_ENERGY = 9.0

# Directories and filenames
USB_DIR = "/media/usbstick/"  # Mounting point of the external USB stick
DISK_SPACE_MINIMUM = 16 * 1024 * 1024 * 1024  # 16 GB
VIDEO_RECORDING_DISK_SPACE_MINIMUM = 4 * 1024 * 1024 * 1024  # 4 GB
LOGFILE_DIR = "logfiles/"
VIDEO_DIR = "videos/"
IMAGE_DIR = "still_images/"
DATA_DIR = "data/"
AUDIO_BEACON = "/home/pi/files/beacon-english.wav"
AUDIO_SELFTEST_START = '/home/pi/files/selftest-start.wav'
AUDIO_SELFTEST_OK = '/home/pi/files/selftest-ok.wav'
AUDIO_SELFTEST_FAILED = '/home/pi/files/selftest-failed.wav'  # not used?
AUDIO_APRS_TEST_SIGNAL = '/home/pi/files/aprs-1200hz-2200hz-6db.wav'
SSTV_TEST_IMAGE = '/home/pi/files/sstv-testbild-small.png'

# GPS
GPS_SERIAL_PORT = "/dev/ttyUSB0"  # just an example
GPS_SERIAL_PORT_BAUDRATE = 9600  # just an example
GPS_POLLTIME = 0.1  # in seconds
GPS_OBFUSCATION = True
GPS_OBFUSCATION_DELTA = {'lat': -0.15, 'lon': 0.25}
# GPS_ALTITUDE_MODE_CEILING = 10000
# Altitude at which GPS will be switched to Airborne-6 mode
# with <1g Acceleration; TBD
# Not used, we turn this mode on right from the beginning.

# Sensors
# 3-wire sensors
SENSOR_ID_INTERNAL_TEMP = "00000771bf4e"
SENSOR_ID_BATTERY_TEMP = "000007717589"
SENSOR_ID_EXTERNAL_TEMP = "0000077147fe"
# I2C sensors
"""I2C Address Check:
0x1E - LSM9DS1-M
0x40 - HTU21D-F
0x48 - ADC ADS1115
0x6B - LSM9DS1_AG
0x77 - BMP280 (evtl. 76)
ADC ADS115 - 0x48 (1001000) ADR -> GND
    0x49 (1001001) ADR -> VDD /
    0x4A (1001010) ADR -> SDA /
    0x4B (1001011) ADR -> SCL
BME280  (address 0x76 when SDO=0 or 0x77 when SDO=1)
LSM9DS1
// SDO_XM and SDO_G are both pulled high, so our addresses are:
#define LSM9DS1_M   0x1E (// Would be 0x1C if SDO_M is LOW)
#define LSM9DS1_AG  0x6B (// Would be 0x6A if SDO_AG is LOW)
HTU21D-F - the I2C address is 0x40 and you can't change it!"""
SENSOR_ID_ADC = 0x48
SENSOR_ID_PRESSURE = 0x77  # BME280 (Note: Not BM**P**280)
SENSOR_ID_HUMIDITY_EXT = 0x40  # HTU21D-F
SENSOR_ID_MOTION_M = 0x1E
SENSOR_ID_MOTION_AG = 0x6B
USV_ID = 0x0F
RTC_ID = 0x68
# ADC channels
# A0 External temperature via 1 k voltage divider, R sensor 500 - 1500 R for
# -100 ... + 100 °C
# V -  voltage divider 1 k against + 3.3. V
# At R=500 (-100 °C) - R=1500 (+100°C) = 1.1 - 2.2 V (outer pins!)
# A1 = U Batt via 10k : 1 k voltage divider (* 0,1)
# A2 = I Batt via 2.2 to 10 k voltage divider at 2,5 V +/- 0,185 V/A
SENSOR_ADC_CHANNEL_EXTERNAL_TEMPERATURE = 0
SENSOR_ADC_CHANNEL_BATTERY_VOLTAGE = 1
SENSOR_ADC_CHANNEL_CURRENT = 2
SENSOR_POLL_RATE = 1  # in Hz

# Transceiver, APRS, and SSTV
PRE_EMPHASIS = True  # Whether or not we use pre-emphasis for APRS and SSTV
# mainly depends on whether the receiving devices use de-emphasis or not
# See http://www.tapr.org/pipermail/aprssig/2009-October/031608.html
# Best practice seems to be to use it.
HIGH_PASS = False
LOW_PASS = False
SQUELCH = 8  # Squelch level 0-8
# Will save power to be set to 8 in altitude but use 0 for debugging
APRS_ON = True
APRS_FULL_POWER = True  # True = 1 W, False = 0.5 W
APRS_FREQUENCY = 144.800
# should be APRS_PATH = "WIDE2-1"  # http://www.arhab.org/aprs
APRS_PATH = 'WIDE2-1'
APRS_SEQUENCE = 0  # Initial APRS sequency ID
SSTV_ON = True
SSTV_FREQUENCY = 145.200  # Warning: This requires permission from BNetzA.
SSTV_MODE = "r36"  # Robot 36
# Martin 1: m1 / Martin 2: m2 / Scottie 1: s1 / Scottie 2: s2
# Scottie DX: sdx / Robot 36: r36
# Values from https://github.com/hatsunearu/pisstvpp
# A transmission cycle is 60 seconds. The following determines how often
# the respective transmission takes place.
#     n = 0 -> every cycle (= every minutes)
#     n = 1 -> every other cycle (= every second minute)
#     n = 2 -> every third cycle (= every third minutes)
# If a component is not transmitted, a computed waiting time will guarantee
# that the cycle duration will remain 60 seconds.
# Note: This timing works only with Robots-36, since other SSTV modes
# take too long.
CYCLE_DURATION = 60  # seconds
APRS_RATE = 0  # One transmission every minute
SSTV_RATE = 1  # One SSTV image every other minute
APRS_META_DATA_RATE = 7  # APRS telemetry meta-data only every 8 minutes

# GPIO pin configuration for 1-wire, secondary cameras, power-on,
# status LEDs, etc.
# TBC - Okay, up to date
"""DONE 4. CTL CAM TOP and CTL CAM BOTTOM wiring
GPIO17 white -> BLACK PIN_BUTTON = 5 # start and shutdown signal
GPIO27 yellow --> RED PIN_REC = 7 # start/stop recording
GPIO18 grey -> BROWN PIN_ACK = 11 # acknowledge recording state
DONE CTL CAM BOTTOM verdrahten
GPIO22 white -> BLACK PIN_BUTTON = 5 # start and shutdown signal
GPIO24 yellow --> RED PIN_REC = 7 # start/stop recording
GPIO23 grey -> BROWN PIN_ACK = 11 # acknowledge recording state"""
ONE_WIRE_PIN = 7  # GPIO4 for 1-Wire Devices
POWER_BUTTON_PIN = 37  # GPIO26
MAIN_STATUS_LED_PIN = 40  # GPIO21
SPARE_STATUS_LED_PIN = 24  # GPIO8
MAIN_CAM_STATUS_LED = 26  # GPIO07


# Pins for camera units (but we only use one this time)
CAM1_PWR = 11  # GPIO27 OK
# Problem S.USV also uses GPIO 27 (GPIO_GEN2)
CAM1_REC = 13  # GPIO 27
CAM1_STATUS = 12  # GPIO18
CAM2_PWR = 15  # GPIO22
CAM2_REC = 18  # GPIO24
CAM2_STATUS = 16  # GPIO23

# GPIO and UART configuration for DORJI DRA818V transceiver module
SERIAL_PORT_TRANSCEIVER = "/dev/ttyAMA0"  # just an example
DRA818_PTT = 38  # GPIO20, Tx/Rx control pin: Low->TX; High->RX
DRA818_PD = 36  # GPIO16, Power saving control pin: Low->sleep mode;
# High->normal mode
DRA818_HL = 32  # GPIO12, RF Power Selection: Low->0.5W; floated->1W
# Reserved GPIO pins:
# GPIO2 / 3: SDA1 I2C
# GPIO3 / 5: SCL1 I2C
# GPIO14 / 8: UART TXD
# GPIO15 / 10: UART RXD

# Settings for video recording and still images
LENGTH_VIDEO = 60  # in seconds
VIDEO_PARAMS = (1920, 1080, 30)  # initial video params
IMAGE_PARAMS = (2592, 1944)  # initial image params
RESOLUTIONS = (
    # next_threshold video_params image_params
    (10000000, VIDEO_PARAMS, IMAGE_PARAMS),
    (2500000, (1440, 960, 24), (1920, 1080)),
    (500000, (1280, 720, 24), (1920, 1080)),
    (50000, (640, 480, 24), (1920, 1080)),
    (10000, (320, 240, 24), (1280, 720)))  # stop at ca. 10MB
ANNOTATE_VIDEO = True
ANNOTATE_STILL_IMAGE = True
TEXT_SIZE = 40  # 6..160, default=32
