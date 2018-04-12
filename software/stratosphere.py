#!/usr/bin/env python
# -*- coding: utf-8 -*-

# main.py

import logging
import os
import sys
import time
import multiprocessing as mp
from random import randint
import serial
import RPi.GPIO as GPIO
from smbus import SMBus
import config
import utility
import sensors
import gps_info
import camera
from shared_memory import *


def main():
    """Main probe functionality."""
    logging.info("Stratosphere 2018 system started.")
    # Set up data, GPS, NMEA and motion/DoF loggers
    gps_handler = logging.FileHandler(config.USB_DIR + config.DATA_DIR +
                                      'gps.csv')
    gps_logger = logging.getLogger('gps')
    gps_logger.setLevel(logging.DEBUG)
    gps_logger.addHandler(gps_handler)
    gps_logger.propagate = False

    nmea_handler = logging.FileHandler(config.USB_DIR + config.DATA_DIR +
                                       'nmea.csv')
    nmea_logger = logging.getLogger('nmea')
    nmea_logger.setLevel(logging.DEBUG)
    nmea_logger.addHandler(nmea_handler)
    nmea_logger.propagate = False

    data_handler = logging.FileHandler(config.USB_DIR + config.DATA_DIR +
                                       'data.csv')
    data_logger = logging.getLogger('gps')
    data_logger.setLevel(logging.DEBUG)
    data_logger.addHandler(data_handler)
    data_logger.propagate = False

    motion_handler = logging.FileHandler(config.USB_DIR + config.DATA_DIR +
                                         'motion.csv')
    motion_logger = logging.getLogger('motion')
    motion_logger.setLevel(logging.DEBUG)
    motion_logger.addHandler(motion_handler)
    motion_logger.propagate = False
    # Set up GPIO and test LEDs
    GPIO.setmode(GPIO.BOARD)
    # All LEDs
    leds = [config.MAIN_STATUS_LED_PIN,
            config.MAIN_CAM_STATUS_LED,
            config.SPARE_STATUS_LED_PIN]
    for led in leds:
        GPIO.setup(led, GPIO.OUT)
    # Turn on one by one
    for led in leds:
        GPIO.output(led, True)
        time.sleep(1)
    # Flash all of them four times
    for status in [False, True] * 4:
        for led in leds:
            GPIO.output(led, status)
        time.sleep(0.5)
    # Turn all off
    for led in leds:
        GPIO.output(led, False)
    # Initialize GPS subprocess or thread
    p = mp.Process(target=gps_info.update_gps_info,
                   args=(timestamp, altitude, latitude, longitude,
                         gps_logger, nmea_logger))
    p.start()
    # Wait for valid GPS position and time, and sync time
    logging.info('Waiting for valid initial GPS position.')
    while longitude_outdated > 0 or latitude_outdated > 0:
        time.sleep(1)
    # Set up transmitter
    logging.info('Setting up transceiver via %s.' %
                 config.SERIAL_PORT_TRANSCEIVER)
    transceiver = DRA818(
        uart=config.SERIAL_PORT_TRANSCEIVER,
        ptt_pin=config.DRA818_PTT,
        power_down_pin=config.DRA818_PD,
        rf_power_level_pin=config.DRA818_HL,
        frequency=config.SSTV_FREQUENCY,
        squelch_level=2)
    logging.info('Transceiver ok and tuned to %f MHz.' %
                 config.SSTV_FREQUENCY,)
    transceiver.set_filters(pre_emphasis=True,
                            high_pass=False,
                            low_pass=False)
    time.sleep(1)
    # Broadcast self-test start beacon
    try:
        transceiver.transmit_audio_file(
            config.SSTV_FREQUENCY,
            ['files/selftest-start.wav', 'files/aprs-1200hz-2200hz-6db.wav'])
        time.sleep(0.5)
    finally:
        transceiver.stop_transmitter()
    # Set up and start external cameras
    cam_top = camera.ExternalCamera(
        config.CAM1_PWR,
        config.CAM1_REC,
        config.CAM1_STATUS)
    status_ok = cam_top.start_recording()
    if status_ok:
        logging.info('Top camera recording started.')
    else:
        logging.error('Problem: Top camera recording not running.')
    cam_bottom = camera.ExternalCamera(
        config.CAM2_PWR,
        config.CAM2_REC,
        config.CAM2_STATUS)
    status_ok = cam_bottom.start_recording()
    if status_ok:
        logging.info('Bottom camera recording started.')
    else:
        logging.error('Problem: Bottom camera recording not running.')
    # Set up sensors and self-test sensors
    # Set up and start internal camera thread or subprocess
    # Set up 9 DOF thread
    # Set up shutdown switch thread or subprocess
    while True:
        start_time = time.time()
        # write data with gps to data logger
        # timestamp, lat, latD, long, longD, temp_int, temp_ext, temp_adc,
        # humidity_int, humidity_ext, pressure, temp_cpu, batt_voltage,
        # batt_current, batt_temp
        data_message = '%s'
"""
altitude = mp.Value("d", 0.0)
altitude_outdated = mp.Value("i", 1)
latitude = mp.Value("d", 0.0)
latitude_direction = mp.Value("c", "N")
latitude_outdated = mp.Value("i", 1)
longitude = mp.Value("d", 0.0)
longitude_direction = mp.Value("c", "E")
longitude_outdated = mp.Value("i", 1)
continue_gps = mp.Value("i", 1)
next_threshold = -1
internal_temp = mp.Value("d", 0.0)
external_temp = mp.Value("d", 0.0)
external_temp_ADC = mp.Value("d", 0.0)
cpu_temp = mp.Value("d", 0.0)
battery_voltage = mp.Value("d", 0.0)
discharge_current = mp.Value("d", 0.0)
battery_temp = mp.Value("d", 0.0)
atmospheric_pressure = mp.Value("d", 0.0)
humidity_internal = mp.Value("d", 0.0)
humidity_external = mp.Value("d", 0.0)
"""
        datalogger.info(data_message)
        # Delay tx by random number of 0..10 secs in order to minimize
        # collisions on the APRS frequency
        time.sleep(random.random * 10)
        # send APRS meta-data (only every x times)
        telemetry_definition = aprs.generate_aprs_telemetry_definition()
        status = aprs.send_aprs(telemetry_definition)
        # send APRS position and core data (only every x times)
        aprs_position_msg = generate_aprs_position()
        status = aprs.send_aprs(aprs_position_msg)
        # send APRS weather data (only every x times)
        aprs_weather_msg = generate_aprs_weather()
        status = aprs.send_aprs(aprs_weather_msg)
        # wait for remaining time
        delay = APRS_DELAY - (time.time() - start_time)
        if delay > 0:
            time.sleep(delay)
        # send SSTV (only every x times)
        status = send_sstv(
            transceiver,
            config.SSTV_FREQUENCY,
            last_sstv_image,
            protocol=config.SSTV_MODE)
        # check battery status and shutdown / reduce operation
        # -> also check SUV status
        # check free disk space and shutdown processes if needed
        # wait for remaining time
        delay = SSTV_DELAY - (time.time() - start_time)
        if delay > 0:
            time.sleep(delay)


if __name__ == "__main__":
    # Check that USB media is available, writeable, and with sufficient
    # capacity
    utility.check_and_initialize_USB()
    # Configure main logging
    FORMAT = '%(asctime)-15s %(levelname)10s:  %(message)s'
    logging.basicConfig(filename=os.path.join(
        config.USB_DIR, "main.log"), level=logging.DEBUG, format=FORMAT)
    # Log to standard output as well
    std_logger = logging.StreamHandler()
    std_logger.setFormatter(logging.Formatter(FORMAT))
    logging.getLogger().addHandler(std_logger)
    main()

