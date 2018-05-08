#!/usr/bin/env python
# -*- coding: utf-8 -*-
# gps_info.py
# Taken from Alex Stolz' camera module code
# $ sudo pip install pynmea2
# https://blog.retep.org/2012/06/18/getting-gps-to-work-on-a-raspberry-pi/
# $ sudo lsusb
# $ tail -n 200 /var/log/syslog | grep USB | grep tty
# $ sudo apt-get install gpsd gpsd-clients python-gps
# $ sudo gpsd /dev/ttyACM0 -F /var/run/gpsd.sock
# $ cgps -s
# $ sudo apt-get install ntp # to set clock using gps
# $ gps ntp
# $ sudo service ntp restart
# $ ntpq -p

import logging
import os
import time
import datetime
import serial
import pynmea2
import config
import utility
from shared_memory import *


def set_to_flight_mode(uart, baudrate):
    """Sets the Neo 6M GPS module to flight mode for high altitude
    operation.Based on the work described in
    https://ukhas.org.uk/guides:ublox6.

    Args:
        uart (str): The path of the GPS UART.

        baudrate (int): The GPS baudrate (4800 or 9600)."""
    logging.info('Sending flight mode commands to GPS at %s' % uart +
                 'with baud rate %d.' % baudrate)
    # Command sequence taken from https://ukhas.org.uk/guides:ublox6
    flight_command = [
        0xB5, 0x62, 0x06, 0x24, 0x24, 0x00, 0xFF, 0xFF,
        0x06, 0x03, 0x00, 0x00, 0x00, 0x00, 0x10, 0x27, 0x00, 0x00,
        0x05, 0x00, 0xFA, 0x00, 0xFA, 0x00, 0x64, 0x00, 0x2C, 0x01,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x16, 0xDC]
    expected_response = [
        0xB5,  # header
        0x62,  # header
        0x05,  # class
        0x01,  # id
        0x02,  # length
        0x00,  #
        flight_command[2],  # ACK class
        flight_command[3]   # ACK id
    ]
    # Checksum must be appended because lists are immutable
    chk_a = 0
    chk_b = 0
    for i in range(2, 8):
        chk_a += expected_response[i]  # CK_A
        chk_b += chk_a  # CK_B
    expected_response.append(chk_a)
    expected_response.append(chk_b)
    with serial.Serial(uart, baudrate, timeout=3) as ser:
        for byte in flight_command:
            ser.write(chr(byte))
            logging.debug('GPS Command %02x HEX to %s.' % (byte, uart))
        ack = ser.read(10)  # read up to ten bytes
    ack = [ord(c) for c in ack]
    status = cmp(ack, expected_response)
    if status:
        logging.info('SUCCESS: GPS set to flight mode')
    else:
        logging.error('ERROR: Setting GPS to flight mode failed.')
    return status


def get_info(uart, baudrate, nmea_logger=None):
    """Tries to fetch and parse a new $GPRMC or $GPGGA from the GPS.

    Args:
        uart (str): The path of the GPS UART.

        baudrate (int): The GPS baudrate (4800 or 9600).

        nmea_logger: A logger object for raw NMEA data. If note, the
        default logger will be used.

    Returns:
        msg: a pynmea2 message object

        date: a pynmea2 date object
    """
    with serial.Serial(uart, baudrate, timeout=1) as ser:
        date = None
        while True:
            line = ser.readline()
            if nmea_logger is not None:
                nmea_logger.info('NMEA: %s, %s' % (
                    datetime.datetime.utcnow().isoformat(), line.strip()))
            else:
                logging.debug('NMEA: %s, %s' % (
                    datetime.datetime.utcnow().isoformat(), line.strip()))
            if line.startswith("$GPRMC"):
                msg = pynmea2.parse(line)
                date = msg.datestamp
                logging.debug('GPS data from RMC: date=%s' % date)
            elif line.startswith("$GPGGA"):
                msg = pynmea2.parse(line)
                logging.debug('GPS data from GGA: time=%s lat=%s\
 long=%s alt=%s' % (msg.timestamp, msg.latitude, msg.longitude, msg.altitude))
                return msg, date


def update_gps_info(gps_logger=None, nmea_logger=None):
    """This function continuously updates the shared memory variables
    for GPS data and is meant to run as a child process.
    It also writes a GPS position log file.

    It stops once the shared memory variable continue_gps contains 0.

    Args:
        gps_logger: A logger object for the GPS data. Disabled if None.
        nmea_logger: A logger object for the raw NMEA data. Disabled if None.
    """

    last_time_update = time.time() - 31  # -31 means to force initial update

    while continue_gps.value:
        gps_data, datestamp = get_info(
            config.GPS_SERIAL_PORT, config.GPS_SERIAL_PORT_BAUDRATE,
            nmea_logger=nmea_logger)
        try:
            if datestamp is not None:
                time_string = datestamp.strftime("%Y-%m-%dT") \
                    + str(gps_data.timestamp)[:8] + "Z"
                logging.info('=> DEBUG: time_string = %s, len=%i' % (time_string, len(time_string)))
                timestamp.value = time_string
            else:
                timestamp.value = str(gps_data.timestamp)
            if time.time() > last_time_update + 30:
                last_time_update = time.time()
                # Update system time only twice per minute (ca.)
                try:
                    # os.system("sudo date --set '%s' > /dev/null 2>&1" %
                    os.system("sudo date --set '%s' > /dev/null" %
                              timestamp.value)
                    logging.info('System time updated from GPS.')
                except Exception as msg_time:
                    logging.error('Could not set the system time.')
                    logging.exception(msg_time)
        except Exception as msg:
            timestamp.value = "01-01-1970T00:00:00Z"
            logging.exception(msg)
        try:
            altitude.value = gps_data.altitude
            altitude_outdated.value = 0
            if altitude.value > altitude_max.value:
                altitude_max.value = altitude.value
        except (TypeError, ValueError):
            altitude_outdated.value = 1
            logging.warning('GPS altitude data invalid.')
        except Exception as msg:
            altitude_outdated.value = 1
            logging.exception(msg)
        try:
            latitude.value = float(gps_data.latitude)
            latitude_direction.value = gps_data.lat_dir
            latitude_outdated.value = 0
        except (TypeError, ValueError):
            latitude_outdated.value = 1
            logging.warning('GPS latitude data invalid.')
        except Exception as msg:
            latitude_outdated.value = 1
            logging.exception(msg)
        try:
            longitude.value = float(gps_data.longitude)
            longitude_direction.value = gps_data.lon_dir
            longitude_outdated.value = 0
        except (TypeError, ValueError):
            longitude_outdated.value = 1
            logging.warning('GPS longitude data invalid.')
        except Exception as msg:
            longitude_outdated.value = 1
            logging.exception(msg)
        if gps_logger is not None:
            gps_logger.info('%s,%s,%s,%s,%s,%s,%s,%s,%s,%s' %
                            (datetime.datetime.utcnow().isoformat(),
                             latitude.value,
                             latitude_direction.value,
                             longitude.value,
                             longitude_direction.value,
                             altitude.value,
                             timestamp.value,
                             latitude_outdated.value,
                             longitude_outdated.value,
                             altitude_outdated.value))
        time.sleep(config.GPS_POLLTIME)
    return


if __name__ == '__main__':
    import aprs
    global continue_gps
    logging.basicConfig(level=logging.DEBUG)
    utility.check_and_initialize_USB()
    gps_fn = os.path.join(config.USB_DIR + config.DATA_DIR + 'gps.csv')
    gps_handler = logging.FileHandler(gps_fn)
    gps_logger = logging.getLogger('gps')
    gps_logger.setLevel(logging.DEBUG)
    gps_logger.addHandler(gps_handler)
    gps_logger.propagate = False
    nmea_fn = os.path.join(config.USB_DIR + config.DATA_DIR + 'nmea.csv')
    nmea_handler = logging.FileHandler(nmea_fn)
    nmea_logger = logging.getLogger('nmea')
    nmea_logger.setLevel(logging.DEBUG)
    nmea_logger.addHandler(nmea_handler)
    nmea_logger.propagate = False
    uart = config.GPS_SERIAL_PORT
    baudrate = config.GPS_SERIAL_PORT_BAUDRATE
    logging.info('GPS found at %s with %i baud' % (uart, baudrate))
    logging.info('Trying to read current position.')
    msg, date = get_info(uart, baudrate)
    logging.info('Trying to set GPS to flight mode.')
    set_to_flight_mode(uart, baudrate)
    # Initialize GPS subprocess or thread
    p = mp.Process(target=update_gps_info,
                   args=(gps_logger, nmea_logger))
    p.start()
    # Wait for valid GPS position and time, and sync time
    logging.info('Waiting for valid initial GPS position.')
    while longitude_outdated.value > 0 or latitude_outdated.value > 0:
        time.sleep(1)
    logging.info('Now reading GPS info from shared memory.')
    for i in range(12):
        logging.info('GPS: lat=%f %s, lon=%f %s, alt=%fm, timestamp: %s' %
                     (latitude.value, latitude_direction.value,
                      longitude.value, longitude_direction.value,
                      altitude.value, timestamp.value))
        lat = latitude.value
        lon = longitude.value
        latitude_string = '%07.2f%s' % (
            aprs.DD_to_DMS(lat), latitude_direction.value)
        longitude_string = '%08.2f%s' % (
            aprs.DD_to_DMS(lon), longitude_direction.value)
        logging.info('APRS: lat=%s, lon=%s' % (
            latitude_string, longitude_string))
        time.sleep(3)
    logging.info('Terminating GPS thread. Please wait.')
    continue_gps.value = 0
    time.sleep(4)
    p.terminate()
    p.join()
    logging.info('Goodbye.')

