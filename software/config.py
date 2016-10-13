#!/usr/bin/env python
# -*- coding: utf-8 -*-

# config.py
# Configuration settings for the probe and its sensors
import logging
import os
import RPi.GPIO as GPIO

# Directories and filenames
USB_DIR = "/media/usbstick/"  # This is the mounting point of the external USB stick
LOGFILE_DIR = "/logfiles/"
VIDEO_DIR = "/videos/"
IMAGE_DIR = "/still_images/"
SSTV_DIR = "/sstv/"
DATA_DIR = "/data/"

DISK_SPACE_MINIMUM = 16*1024*1024*1024  # 16 GB

# Test of USB stick is available, if not, try to mount
# Test if USB stick has at least 30 GB free capacity

# Configure logging
FORMAT = '%(asctime)-15s %(levelname)10s:  %(message)s'
# Log to a file
logging.basicConfig(filename=os.path.join(USB_DIR, "main.log"), level=logging.DEBUG, format=FORMAT)
# Log to standard output as well
std_logger = logging.StreamHandler()
std_logger.setFormatter(logging.Formatter(FORMAT))
logging.getLogger().addHandler(std_logger)

# GPS
SERIAL_PORT_GPS = "/dev/ttyUSB0"  # just an example
GPS_POLLTIME = 2 # in seconds
GPS_ALTITUDE_MODE_CEILING = 10000
# Altitude at which GPS will be switched to Airborne-6 mode
# with <1g Acceleration; TBD

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
SENSOR_ID_ADC = ""
SENSOR_ID_PRESSURE = ""
SENSOR_ID_HUMIDITY = ""
SENSOR_ID_MOTION = ""
# ADC channels
# A0 Ext Temperature über 1 k Voltage Divider, R Sensor 500 - 1500 R für -100 ... + 100 Grad V -  Spannungsteiler 1 k Ohm gegen + 3.3. V - bei 500 (-100 Grad)  - 1500 R (+100 Grad) = 1.1 - 2.2. V (außenkontakte!)
# A1 = U Batt über 10k : 1 k Voltage Divider (*0,1)
# A2 = I Batt über 2,2 zu 10 k Voltage Divider bei 2,5 V +/- 0,185 V/A
SENSOR_ADC_CHANNEL_EXTERNAL_TEMPERATURE = 0
SENSOR_ADC_CHANNEL_BATTERY_VOLTAGE = 1
SENSOR_ADC_CHANNEL_CURRENT = 2

# Transceiver
CALLSIGN = "DL0UBW" # insert your mission callsign
APRS_SSID = CALLSIGN + "-11"
TRANSMISSION_POWER_DEFAULT = GPIO.LOW # low = 0.5 W, high = 1 W
PRE_EMPHASIS = 0 # Whether or not we use pre-emphasis for transmitting APRS and SSTV
# 0 turn on;1 turn off
# mainly depends on whether the receiving devices use de-emphasis or not
# See http://www.tapr.org/pipermail/aprssig/2009-October/031608.html
HIGH_PASS = 1  # 0 turn on;1 turn off
LOW_PASS = 1  # 0 turn on;1 turn off
SQUELCH = 0  # squelch level 0-8, will save power to be set to 8 in altitude but useful at 0 for debugging
APRS_ON = True
APRS_FREQUENCY = 144.800
APRS_RATE = 60 # one transmission per 60 seconds
APRS_PATH = "WIDE2-1" # http://www.arhab.org/aprs
SSTV_ON = True
SSTV_FREQUENCY = 145.200 # or 144.600 # TBC
SSTV_MODE = "r36" # Robot 36
# Martin 1: m1 / Martin 2: m2 / Scottie 1: s1 / Scottie 2: s2 / Scottie DX: sdx / Robot 36: r36
# Values from https://github.com/hatsunearu/pisstvpp
SSTV_DELAY = 60 # wait 60 seconds after each transmission

# GPIO pin configuration for 1-wire, secondary cameras, power-on, status LEDs, etc.
# TBC - Okay, up to date
"""DONE 4. CTL CAM TOP und CTL CAM BOTTOM verdrahten
GPIO17 weiss -> BLACK PIN_BUTTON = 5 # start and shutdown signal
GPIO27 gelb --> RED PIN_REC = 7 # start/stop recording
GPIO18 grau -> BROWN PIN_ACK = 11 # acknowledge recording state
DONE CTL CAM BOTTOM verdrahten
GPIO22 weiss -> BLACK PIN_BUTTON = 5 # start and shutdown signal
GPIO24 gelb --> RED PIN_REC = 7 # start/stop recording
GPIO23 grau -> BROWN PIN_ACK = 11 # acknowledge recording state"""
ONE_WIRE_PIN = 7 # GPIO4 for 1-Wire Devices
POWER_BUTTON_PIN = 37 # GPIO26
MAIN_STATUS_LED_PIN = 40 # GPIO21
SPARE_STATUS_LED_PIN = 24 # GPIO8
MAIN_CAM_STATUS_LED = 26 # GPIO07
CAM1_PWR = 11 # GPIO17
CAM1_REC = 13 # GPIO13
CAM1_STATUS = 12 # GPIO18
CAM2_PWR = 15 # GPIO22
CAM2_REC = 18 # GPIO14
CAM2_STATUS = 16 # GPIO23

# GPIO and UART configuration for DORJI DRA818V transceiver module
# OK, checked
SERIAL_PORT_TRANSCEIVER = "/dev/ttyAMA0" # just an example
DRA818_PTT = 38 # GPIO20, Tx/Rx control pin: Low->TX; High->RX
DRA818_PD = 36 # GPIO16, Power saving control pin: Low->sleep mode; High->normal mode
DRA818_HL = 32 # GPIO12, RF Power Selection: Low->0.5W; floated->1W
# Reserved GPIO pins:
# GPIO2 / 3: SDA1 I2C
# GPIO3 / 5: SCL1 I2C
# GPIO14 / 8: UART TXD
# GPIO15 / 10: UART RXD

