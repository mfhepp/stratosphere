#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time
import serial
import serial.tools.list_ports
import RPi.GPIO as GPIO

from config import *
from sensors import *

import aprs.py

def test_transceiver():
    # Initialize GPIO
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(DRA818_PTT, GPIO.OUT, pull_up_down=GPIO.PUD_UP) # GPIO20, Tx/Rx control pin: Low->TX; High->RX
    GPIO.setup(DRA818_PD, GPIO.OUT, pull_up_down=GPIO.PUD_DOWN) # GPIO16, Power saving control pin: Low->sleep mode; High->normal mode
    GPIO.setup(DRA818_HL, GPIO.OUT, pull_up_down=GPIO.PUD_DOWN) # GPIO12, RF Power Selection: Low->0.5W; floated->1W
    # Initialize Transceiver

    ser = serial.Serial(
        # The default data format is: 8 data bits, 1 stop bit, no parity and 9600 kbps data rate.
        port = SERIAL_PORT_TRANSCEIVER,  # /dev/ttyAMA0, tbc
        baudrate = 9600,
        parity = serial.PARITY_NONE,
        stopbits = serial.STOPBITS_ONE,
        bytesize = serial.EIGHTBITS
    )
    if not ser.isOpen:
        ser.open()

    ser.write('AT eyz' + '\r\n')
    # 144.500 SSTV Anruf
    # write + log serial output

    # Play Sprachbake ~\sound\final\bake-dk3it-test-english-16k.wav
    # Float 32 bit Little Endian, Rate 16000 Hz, Mono
    # pre_init(frequency=22050, size=-16, channels=2, buffersize=4096) -> None
    os.system('aplay ~/sound/final/bake-dk3it-test-english-16k.wav')
    #pygame.mixer.pre_init(frequency=16000, size=32, channels=1, buffersize=4096)
    #pygame.mixer.init()
    #pygame.mixer.music.load("~/sound/final/bake-dk3it-test-english-16k.wav")
    #pygame.mixer.music.play()

def test_leds():
    GPIO.setmode(GPIO.BOARD)
    leds = [MAIN_STATUS_LED_PIN,
    SPARE_STATUS_LED_PIN,
    MAIN_CAM_STATUS_LED]
    for led in leds:
        GPIO.setup(led, GPIO.OUT)
    for led in leds:
        GPIO.output(led,True)
        time.sleep(1)
    for status in [False, True]*4:
        for led in leds:
            GPIO.output(led,status)
        time.sleep(0.5)
    for led in leds:
        GPIO.output(led,False)

def test_pwr_button():
    GPIO.setup(POWER_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    current_status = GPIO.input(POWER_BUTTON_PIN)
    print "Please toggle power button NOW(Current Status: %s)" % current_status
    while GPIO.input(POWER_BUTTON_PIN) == current_status:
        time.sleep(0.2)
    time.sleep(1)
    current_status = GPIO.input(POWER_BUTTON_PIN)
    print "Please toggle power button AGAIN (Current Status: %s)" % current_status
    while current_status == GPIO.input(POWER_BUTTON_PIN):
        time.sleep(0.2)
    return

if __name__ == "__main__":
    print "Searching for serial ports...",
    ports = list(serial.tools.list_ports.comports())
    print "%i ports founds" % len(ports)
    for p in ports:
        print p.device
        with serial.Serial(p.device, 9600, timeout=1) as ser:
            print ser.read(255)
    print "Internal temp: %s" % get_temperature_DS18B20(config.SENSOR_ID_INTERNAL_TEMP)
    print "Battery temp: %s" % get_temperature_DS18B20(config.SENSOR_ID_BATTERY_TEMP)
    print "External temp: %s" % get_temperature_DS18B20(config.SENSOR_ID_EXTERNAL_TEMP)
    print "Testing LEDs...",
    test_leds()
    print "Completed."
    print "Testing Power Button"
    test_pwr_button()
    GPIO.cleanup()

