#!/usr/bin/env python
# -*- coding: utf-8 -*-

# main.py

import logging
import os
import subprocess
import time
import datetime
import random
import multiprocessing as mp
import RPi.GPIO as GPIO
import config
import utility
import sensors
import gps_info
import camera
import dra818
import aprs
import sstv
from PIL import Image, ImageDraw, ImageFont
from shared_memory import *


def camera_handler():
    """This handler will record a video, take a still image, and create
    an SSTV still image with annotations."""
    while main_camera_active.value:
        try:
            if utility.check_free_disk_space(
                    minimum=config.VIDEO_RECORDING_DISK_SPACE_MINIMUM):
                logging.info('Starting main camera recording, d = 60 sec.')
                fn_video = camera.InternalCamera.video_recording(
                    duration=60, preview=True)
                logging.info('Main camera recording saved to %s.' % fn_video)
            else:
                logging.warning('WARNING: Less than 4 GB disk space, ' +
                                'video recording skipped')
            logging.info('Main camera still image capture started.')
            fn_still = camera.InternalCamera.take_snapshot()
            logging.info('Main camera still image saved to %s.' % fn_still)
            # Take SSTV still image with larger font and different text
            fn_sstv = camera.InternalCamera.take_snapshot(annotate=False)
            logging.info('SSTV image saved to %s.' % fn_sstv)
            fn_sstv_final = sstv.resize_image(fn_sstv,
                                              protocol=config.SSTV_MODE)
            image = Image.open(open(fn_sstv_final, 'rb'))
            text_field = ImageDraw.Draw(image)
            font = ImageFont.truetype(
                '/usr/share/fonts/truetype/freefont/FreeMono.ttf', 18)
            print config.CALLSIGN
            text_field.text((5, 5), '%s \n Alt: %.2f' % (
                config.MISSION_TEXT, altitude.value), font=font)
            image.save(fn_sstv_final)
            logging.info('Annotated SSTV image saved to %s.' % fn_sstv_final)
            # Update SSTV image path variable
            last_sstv_image.value = fn_sstv_final
        except Exception as msg:
            logging.exception(msg)


def sensors_handler():
    """This handler reads all relevant sensors and updates all shared
    memory variables from sensor readings, except for the 9-DOF sensor,
    which needs a higher poll rate."""
    # TODO / Improvement: Including battery_discharge_capacity = I * V
    while sensors_active.value:
        try:
            start_time = time.time()
            internal_temp.value = sensors.get_temperature_DS18B20(
                sensor_id=config.SENSOR_ID_INTERNAL_TEMP)
            external_temp.value = sensors.get_temperature_DS18B20(
                sensor_id=config.SENSOR_ID_EXTERNAL_TEMP)
            external_temp_ADC.value = sensors.get_temperature_external()
            battery_voltage.value, discharge_current.value,\
                battery_temp.value = sensors.get_battery_status()
            cpu_temp.value = sensors.get_temperature_cpu()
            atmospheric_pressure.value, humidity_internal.value =\
                sensors.get_pressure_internal_humidity()
            sensor = sensors.HTU21D(busno=1,
                                    address=config.SENSOR_ID_HUMIDITY_EXT)
            humidity_external.value = sensor.read_humidity()
            delay = 1.0 / config.SENSOR_POLL_RATE - (time.time() - start_time)
            if delay > 0:
                time.sleep(delay)
        except Exception as msg:
            logging.exception(msg)


def main():
    """Main probe functionality."""
    global cam_top
    global cam_bottom
    global transceiver
    logging.info("Stratosphere 2018 system started.")
    utility.disable_usv_charging()
    logging.info('S.USV charging disabled.')
    # Set up data, GPS, NMEA and motion/DoF loggers
    gps_path = os.path.join(config.USB_DIR + config.DATA_DIR + 'gps.csv')
    gps_handler = logging.FileHandler(gps_path)
    gps_logger = logging.getLogger('gps')
    gps_logger.setLevel(logging.DEBUG)
    gps_logger.addHandler(gps_handler)
    gps_logger.propagate = False

    nmea_path = os.path.join(config.USB_DIR + config.DATA_DIR + 'nmea.csv')
    nmea_handler = logging.FileHandler(nmea_path)
    nmea_logger = logging.getLogger('nmea')
    nmea_logger.setLevel(logging.DEBUG)
    nmea_logger.addHandler(nmea_handler)
    nmea_logger.propagate = False

    data_path = os.path.join(config.USB_DIR + config.DATA_DIR + 'data.csv')
    data_handler = logging.FileHandler(data_path)
    data_logger = logging.getLogger('data')
    data_logger.setLevel(logging.DEBUG)
    data_logger.addHandler(data_handler)
    data_logger.propagate = False

    motion_path = os.path.join(config.USB_DIR + config.DATA_DIR + 'motion.csv')
    motion_handler = logging.FileHandler(motion_path)
    motion_logger = logging.getLogger('motion')
    motion_logger.setLevel(logging.DEBUG)
    motion_logger.addHandler(motion_handler)
    motion_logger.propagate = False
    # Set up GPIO
    GPIO.setmode(GPIO.BOARD)
    # Init power-down switch
    GPIO.setup(config.POWER_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    # Test all LEDs
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
    GPIO.output(config.MAIN_STATUS_LED_PIN, True)
    # Spare LED indicates power-on-sequence, will turn off when done.
    GPIO.output(config.SPARE_STATUS_LED_PIN, True)
    # Set up transmitter
    logging.info('Setting up transceiver via %s.' %
                 config.SERIAL_PORT_TRANSCEIVER)
    transceiver = dra818.DRA818(
        uart=config.SERIAL_PORT_TRANSCEIVER,
        ptt_pin=config.DRA818_PTT,
        power_down_pin=config.DRA818_PD,
        rf_power_level_pin=config.DRA818_HL,
        frequency=config.SSTV_FREQUENCY,
        squelch_level=8)
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
            [config.AUDIO_SELFTEST_START])
        time.sleep(0.5)
    finally:
        transceiver.stop_transmitter()
    # Initialize GPS subprocess / thread
    continue_gps.value = 1
    p_gps = mp.Process(target=gps_info.update_gps_info,
                       args=(gps_logger, nmea_logger))
    p_gps.start()
    # Wait for valid GPS position and time, and sync time
    logging.info('Waiting for valid initial GPS position.')
    while longitude_outdated.value > 0 or latitude_outdated.value > 0:
        time.sleep(1)
    # Initialize IMU logging subprocess / thread
    imu_logging_active.value = 1
    logging.info('Starting IMU logging.')
    p_imu = mp.Process(target=sensors.log_IMU_data, args=(motion_logger, 10.0))
    p_imu.start()
    logging.info('IMU logging OK.')
    # Initialize sensor reading subprocess / thread
    sensors_active.value = 1
    logging.info('Starting sensors logging.')
    p_sensors = mp.Process(target=sensors_handler)
    p_sensors.start()
    logging.info('Sensors logging OK.')
    # Set up and start internal camera thread or subprocess
    main_camera_active.value = 1
    logging.info('Starting main camera process.')
    p_camera = mp.Process(target=camera_handler)
    p_camera.start()
    logging.info('Main camera OK.')
    logging.info('Sending four telemetry definition messages.')
    status = aprs.send_telemetry_definitions(full_power=config.APRS_FULL_POWER)
    if status:
        logging.info('OK: APRS telemetry definitions.')
    else:
        logging.error('ERROR: Problem sending APRS telemetry definitions.')
    logging.info('Sending initial APRS position report.')
    for i in range(3):
        status = aprs.send_aprs(aprs.generate_aprs_position(telemetry=True),
                                full_power=config.APRS_FULL_POWER)
        if status:
            logging.info('OK: Initial APRS packet sent. [%i of 3]' % (i + 1))
        else:
            logging.error('ERROR: Problem sending initial APRS packet.')
        time.sleep(2)
    # SSTV Test
    fn = last_sstv_image.value.strip()
    logging.info('Sending SSTV file %s.' % fn)
    if os.path.exists(fn):
        sstv.send_sstv(transceiver, config.SSTV_FREQUENCY, fn,
                       protocol=config.SSTV_MODE)
    else:
        logging.warning('SSTV file not found.')
    # Set up and start external camera
    logging.info('Waiting for top camera boot-up delay.')
# TODO
    for i in range(3):
        logging.info('%i sec' % i)
        time.sleep(1)
    # Start external camera unit.
    # TBD: Add wait for acknowledgment.
    # Problem is that it is hard to check whether the camera unit is
    # actually running.
    cam_top = camera.ExternalCamera(
        config.CAM2_PWR,
        config.CAM2_REC,
        config.CAM2_STATUS)
    status_ok = cam_top.start_recording()
    if status_ok:
        logging.info('Top camera recording started.')
    else:
        logging.error('ERROR: Top camera recording not running.')
    # Send self-test completion audio message
    try:
        transceiver.transmit_audio_file(
            config.SSTV_FREQUENCY, [config.AUDIO_SELFTEST_OK])
    finally:
        transceiver.stop_transmitter()

    aprs_counter = config.APRS_RATE
    aprs_meta_data_counter = config.APRS_META_DATA_RATE
    sstv_counter = config.SSTV_RATE
    sstv_active = True
    beacon_counter = 4  # Voice beacon only every 4th SSTV transmission
    logging.info('Starting main thread with the following rates:')
    logging.info('\taprs_counter = %s' % aprs_counter)
    logging.info('\taprs_meta_data_counter = %s' % aprs_meta_data_counter)
    logging.info('\tsstv_counter = %s' % sstv_counter)
    GPIO.output(config.SPARE_STATUS_LED_PIN, False)
    while True:
        try:
            start_time = time.time()
            # Write data with gps to data logger
            # timestamp, lat, latD, long, longD, altitude,
            # temp_int, temp_ext, temp_adc,
            # humidity_int, humidity_ext, pressure, temp_cpu,
            # batt_voltage, batt_current, batt_temp,
            # cpu_temp
            data_message = '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,\
%s,%s,%s,%s' % (
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
            data_logger.info(data_message)
            # Send APRS beacon
            # Delay tx by random number of 0..10 secs in order to minimize
            # collisions on the APRS frequency
            time.sleep(random.random() * 10)
            if aprs_meta_data_counter <= 0:
                logging.info('Sending four APRS telemetry definitions.')
                # Send APRS meta-data (only every n-th cycle)
                status = aprs.send_telemetry_definitions(
                    full_power=config.APRS_FULL_POWER)
                logging.info('Transmission status: %s' % status)
                aprs_meta_data_counter = config.APRS_META_DATA_RATE
            else:
                aprs_meta_data_counter -= 1
            if aprs_counter <= 0:
                # Send APRS position and telemetry data (only every n-th cycle)
                # We need to update the following two variables manually
                logging.info('Sending APRS position with telemetry.')
                cam_top_recording.value = int(cam_top.get_recording_status())
                # cam_bottom_recording.value = \
                # int(cam_bottom.get_recording_status())
                aprs_position_msg = aprs.generate_aprs_position(telemetry=True)
                aprs.send_aprs(aprs_position_msg,
                               full_power=config.APRS_FULL_POWER)
                aprs_counter = config.APRS_RATE
            else:
                aprs_counter -= 1
            if sstv_active and sstv_counter <= 0:
                # Send audio beacon
                if beacon_counter <= 0:
                    logging.info('Sending audio beacon.')
                    transceiver.transmit_audio_file(
                        config.SSTV_FREQUENCY,
                        [config.AUDIO_BEACON], full_power=False)
                    beacon_counter = 0
                else:
                    beacon_counter -= 1
                time.sleep(5)
                fn = last_sstv_image.value.strip()
                logging.info('Sending SSTV file %s.' % fn)
                if os.path.exists(fn):
                    sstv.send_sstv(transceiver, config.SSTV_FREQUENCY,
                                   fn, protocol=config.SSTV_MODE)
                sstv_counter = config.SSTV_RATE
            else:
                sstv_counter -= 1
            # Check free disk space and shutdown processes if needed
            # If less than 2 GB, turn off main camera thread
            if not utility.check_free_disk_space(minimum=2 * 1024**3):
                main_camera_active.value = 0
                # maybe also shutdown system, but difficult to test
            # Check battery status and shutdown / reduce operation
            u, i, t = sensors.get_battery_status()
            if u < config.BATTERY_VOLTAGE_SAVE_ENERGY:
                logging.warning(
                    'Battery voltage low (%.2fV), turning off SSTV.' % u)
                sstv_active = False
            if u < config.BATTERY_VOLTAGE_SYSTEM_SHUTDOWN:
                logging.error(
                    'Battery voltage VERY LOW (%.2fV), [shutting down].' % u)
    # RISK: If battery voltage sensor is defective, system will be shut down.
    # So disabled right now.
    #            shutdown()
            # Initialize shutdown switch
            GPIO.setmode(GPIO.BOARD)
            GPIO.setup(config.POWER_BUTTON_PIN, GPIO.IN,
                       pull_up_down=GPIO.PUD_UP)
            # Wait for remaining time of the cycle
            delay = config.CYCLE_DURATION - (time.time() - start_time)
            GPIO.setmode(GPIO.BOARD)
            GPIO.setup(config.SPARE_STATUS_LED_PIN, GPIO.OUT)
            if delay > 0:
                logging.info('Waiting %.1f s to complete cycle.' % delay)
                for i in range(int(delay / 1)):
                    GPIO.output(config.SPARE_STATUS_LED_PIN, True)
                    time.sleep(1)
                    GPIO.output(config.SPARE_STATUS_LED_PIN, False)
                    # We should watch the switch also during the waiting time
                    switch = GPIO.input(config.POWER_BUTTON_PIN)
                    if not switch:
                        break
            else:
                logging.info(
                    'Warning: Transmissions longer than duration of cycle.')
            # Now check again for shutdown switch
            switch = GPIO.input(config.POWER_BUTTON_PIN)
            if not switch:
                counter = 0
                logging.info('Power-down switch detected.')
                while not GPIO.input(config.POWER_BUTTON_PIN):
                    counter += 1
                    time.sleep(0.1)
                    # Switch must be closed for >= 5 sec
                    if counter > 50:
                            # Graceful shutdown sequence.
                            logging.info('Starting shut down sequence now.')
                            try:
                                transceiver.stop_transmitter()
                            except Exception as msg:
                                logging.exception(msg)
                            # Shut down threads gracefully
                            continue_gps.value = 0
                            main_camera_active.value = 0
                            sensors_active.value = 0
                            imu_logging_active.value = 0
                            # We need to mark the GPS data as
                            # potentially outdated
                            altitude_outdated.value = 1
                            latitude_outdated.value = 1
                            longitude_outdated.value = 1
                            # Send power-down request to camera unit
                            logging.info('Shutting down top camera.')
                            cam_top.power_on_off()
                            # Broadcast shutdown beacon
                            try:
                                transceiver.transmit_audio_file(
                                    config.SSTV_FREQUENCY,
                                    [config.AUDIO_SHUTDOWN])
                            finally:
                                transceiver.stop_transmitter()
                            # Now wait for processes to finish
                            logging.info('Waiting for GPS process.')
                            p_gps.join(35)
                            logging.info('Done.')
                            logging.info('Waiting for IMU process.')
                            p_imu.join(35)
                            logging.info('Done.')
                            logging.info('Waiting for sensors process.')
                            p_sensors.join(35)
                            logging.info('Done.')
                            logging.info('Waiting for main camera process.')
                            p_camera.join(90)
                            logging.info('Done.')
                            logging.info('Sending "sudo shutdown -h now".')
                            subprocess.call('sudo shutdown -h now',
                                            shell=True)
                # Abort shutdown if button released
                counter = 0
            else:
                time.sleep(0.1)
            logging.info('Power switch status: %s [CTRL-C to stop]' % switch)
            # TBD: Also check S.USV status
        except KeyboardInterrupt:
            print 'CTRL-C detected. Shutting down threads.'
            # Graceful shutdown sequence.
            logging.info('Starting shut down sequence now.')
            try:
                transceiver.stop_transmitter()
            except Exception as msg:
                logging.exception(msg)
            # Shut down threads gracefully
            continue_gps.value = 0
            main_camera_active.value = 0
            sensors_active.value = 0
            imu_logging_active.value = 0
            # We need to mark the GPS data as potentially outdated
            altitude_outdated.value = 1
            latitude_outdated.value = 1
            longitude_outdated.value = 1
            # Send power-down request to camera unit
            logging.info('Shutting down top camera.')
            cam_top.power_on_off()
            # Now wait for processes to finish
            logging.info('Waiting for GPS process.')
            p_gps.join(35)
            logging.info('Done.')
            logging.info('Waiting for IMU process.')
            p_imu.join(35)
            logging.info('Done.')
            logging.info('Waiting for sensors process.')
            p_sensors.join(35)
            logging.info('Done.')
            logging.info('Waiting for main camera process.')
            p_camera.join(90)
            logging.info('Done.')
            break
        except Exception as msg:
            logging.exception(msg)
        finally:
            transceiver.stop_transmitter()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Check that USB media is available, writeable, and with sufficient
    # capacity
    utility.check_and_initialize_USB()
    # Delete APRS telemetry definition files
    try:
        wav_files = ['/home/pi/aprs_telemetry_%i.wav' % i for i in range(4)]
        for fn in wav_files:
            os.remove(fn)
    except OSError:
        pass
    logging.info('Waiting 5 sec. for user abort, press CTRL-C to exit.')
    time.sleep(5)
    logging.info('Starting main software.')
    # Set up logging
    """log_filename = os.path.join(config.USB_DIR, 'logfiles', 'main.log')
    print log_filename
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
        datefmt='%m-%d %H:%M',
        filename=log_filename,
        filemode='w')
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)"""
    main()



