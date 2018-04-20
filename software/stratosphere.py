#!/usr/bin/env python
# -*- coding: utf-8 -*-

# main.py

import logging
import os
import time
import datetime
import multiprocessing as mp
import RPi.GPIO as GPIO
import config
import utility
import sensors
import gps_info
import camera
from shared_memory import *


def camera_handler():
    """tbd"""
    # record video
    # take still image
    # take SSTV still image with larger font and different text
    # update sstv image path variable
    # monitor freespace and update / shutdown
    # continue until graceful shutdown
    # cleanup
    pass


def sensors_handler():
    # update all shared memory variables from sensors (except 9 DOF)
    # including battery_discharge_capacity = I * V
    while sensors_active:
        start_time = time.time()
        internal_temp.value = sensors.get_temperature_DS18B20(sensor_id='')
        external_temp.value = sensors.get_temperature_DS18B20(sensor_id='')
        external_temp_ADC.value = sensors.get_temperature_external()
        humidity_internal.value = sensors.get_humidity(
            sensor=SENSOR_ID_HUMIDITY_INT)
        humidity_external.value = sensors.get_humidity(
            sensor=SENSOR_ID_HUMIDITY_EXT)
        atmospheric_pressure.value = sensors.get_pressure()
        battery_voltage, discharge_current, \
            battery_temperature = sensors.get_battery_status()
        battery_voltage.value = battery_voltage
        discharge_current.value = discharge_current
        battery_temp.value = battery_temperature
        cpu_temp.value = sensors.get_temperature_cpu()
        delay = 1.0 / config.SENSOR_POLL_RATE - (time.time() - start_time)
        if delay > 0:
            time.sleep(delay)


def main():
    global sensors_active, camera_active
    """Main probe functionality."""
    logging.info("Stratosphere 2018 system started.")
#TODO: Turn off S.USV charging!
    status = utility.disable_usv_charging()
    if status:
        logging.info('S.USV charging disabled.')
    else:
        logging.error('ERROR: S.USV charging not disabled.')
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
    while longitude_outdated.value > 0 or latitude_outdated.value > 0:
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
    # add wait for ack
    cam_bottom = camera.ExternalCamera(
        config.CAM2_PWR,
        config.CAM2_REC,
        config.CAM2_STATUS)
    status_ok = cam_bottom.start_recording()
    if status_ok:
        logging.info('Bottom camera recording started.')
    else:
        logging.error('Problem: Bottom camera recording not running.')
    # Add wait for ack
    # tbd
    # Set up sensors and self-test sensors
    # a) self-test sensors
    # tbd
    # b) start thread
    sensors_active = True
    sensors_thread = mp.Process(target=sensors_handler)
    sensors_thread.start()
    # Set up and start internal camera thread or subprocess
    camera_active = True
    camera_thread = mp.Process(target=camera_handler)
    camera_thread.start()
    # Set up 9 DOF thread
    # Set up shutdown switch thread or subprocess
    aprs_counter = config.APRS_RATE
    aprs_meta_data_counter = config.APRS_META_DATA_RATE
    sstv_counter = config.SSTV_RATE
    while True:
        start_time = time.time()
        # Write data with gps to data logger
        # timestamp, lat, latD, long, longD, altitude,
        # temp_int, temp_ext, temp_adc,
        # humidity_int, humidity_ext, pressure, temp_cpu,
        # batt_voltage, batt_current, batt_temp,
        # cpu_temp
        data_message = '%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,\
         %s, %s, %s, %s, %s' % (
            datetime.datetime.utcnow().isoformat(),
            latitude.value,
            latitude_direction.value,
            longitude.value,
            longitude_direction.value,
            altitude.value,
            internal_temp.value,
            external_temp.value,
            external_temp_ADC.value,
            humidity_internal.value,
            humidity_external.value,
            atmospheric_pressure.value,
            battery_voltage.value,
            discharge_current.value,
            battery_temp.value,
            cpu_temp.value
        )
        datalogger.info(data_message)
        # Delay tx by random number of 0..10 secs in order to minimize
        # collisions on the APRS frequency
        time.sleep(random.random * 10)
        if aprs_meta_data_counter <= 0:
            # send APRS meta-data (only every n-th cycle)
            telemetry_definition = aprs.generate_aprs_telemetry_definition()
            aprs.send_aprs(telemetry_definition, full_power=True)
            aprs_meta_data_counter = config.APRS_META_DATA_RATE
        else:
            aprs_meta_data_counter -= 1
        if aprs_counter <= 0:
            # send APRS position and core data (only every n-th cycle)
            aprs_position_msg = generate_aprs_position()
            aprs.send_aprs(aprs_position_msg, full_power=True)
            # send APRS weather data
            aprs_weather_msg = generate_aprs_weather()
            aprs.send_aprs(aprs_weather_msg, full_power=True)
            aprs_counter = config.APRS_RATE
        else:
            aprs_counter -= 1
        if sstv_counter <= 0:
            # Send audio beacon
            transceiver.transmit_audio_file(
                config.SSTV_FREQUENCY,
                [config.AUDIO_BEACON], full_power=False)
            time.sleep(1)
            fn = last_sstv_image.value
            if os.path.exists(fn):
                fn_sstv = resize_image(fn, protocol=config.SSTV_MODE)
                send_sstv(transceiver, config.SSTV_FREQUENCY,
                          fn_sstv, protocol=config.SSTV_MODE)
        # check battery status and shutdown / reduce operation
        # monitor shutdown switch
        # monitor battery voltage
        # reduce / turn off functionality if needed
        # Also check SUV status
        # check free disk space and shutdown processes if needed
        # Wait for remaining time of the cycle
        delay = config.CYCLE_DURATION - (time.time() - start_time)
        if delay > 0:
            time.sleep(delay)
        else:
            logging.info('Warning: Transmissions exceed duration of cycle.')
    # cleanup
    # turn off transmitter
    # gpio
    # all threads
    # shutdown


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

