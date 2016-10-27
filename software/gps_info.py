#!/usr/bin/env python
# -*- coding: utf-8 -*-
# gps_info.py
# taken from Alex Stolz' camera module code
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


import serial
import pynmea2
from config import logging, gps_logger
from serial.tools import list_ports

device = None
baudrate = None

def get_device_settings():
    for o in list_ports.comports():
        for baud in (4800, 9600):
            try:
                with serial.Serial(o.device, baud, timeout=1) as ser:
                    for i in range(10):
                        line = ser.readline()
                        if line.startswith("$GPRMC") or line.startswith("$GPGGA"):
                            return o.device, baud
            except Exception as msg:
                logging.exception(msg)
    return None, None

def set_to_flight_mode():
    '''Sets the Neo 6M GPS module to flight mode for high altitude operation.
    Based on the work described in https://ukhas.org.uk/guides:ublox6.'''
    global device, baudrate
    if device is None:
        device, baudrate = get_device_settings()
        if device is None:
            logging.debug("Erro: No GPS device found")
            return False
        else:
            #print "listen to serial device '%s' with baud rate %d" %(device, baudrate)
            logging.debug("GPS: Listening to serial port '%s' with baud rate %d" %(device, baudrate))

    # Taken from https://ukhas.org.uk/guides:ublox6
    flight_command = [0xB5, 0x62, 0x06, 0x24, 0x24, 0x00, 0xFF, 0xFF, 0x06, 0x03, 0x00, 0x00, 0x00, 0x00, 0x10, 0x27, 0x00, 0x00,
    0x05, 0x00, 0xFA, 0x00, 0xFA, 0x00, 0x64, 0x00, 0x2C, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x16, 0xDC]

    expected_response = [ 0xB5,  # header
                0x62,  # header
                0x05,  # class
                0x01,  # id
                0x02,  # length
                0x00,  #
                flight_command[2],  # ACK class
                flight_command[3] # ACK id
                ]
    # Checksum must be appended because lists are immutable
    chk_a = 0
    chk_b = 0
    for i in range(2,8):
        chk_a += expected_response[i]  # CK_A
        chk_b += chk_a  # CK_B

    expected_response.append(chk_a)
    expected_response.append(chk_b)

    with serial.Serial(device, baudrate, timeout=3) as ser:
        for byte in flight_command:
            ser.write(chr(byte))
            logging.info("GPS Command %02x HEX to %s" % (byte, device))
        ack = ser.read(10)  # read up to ten bytes

    ack = [ord(c) for c in ack]

    status = cmp(ack, expected_response)
    if status:
         logging.info('SUCCESS: GPS set to flight mode')
    else:
         logging.debug('ERROR: Setting GPS to flight mode failed')

    return status

def get_info():
    global device, baudrate
    if device is None:
        device, baudrate = get_device_settings()
        if device is None:
            return "not available", "no date"
        else:
            #print "listen to serial device '%s' with baud rate %d" %(device, baudrate)
            logging.info("GPS: Listening to serial port '%s' with baud rate %d" %(device, baudrate))
    with serial.Serial(device, baudrate, timeout=1) as ser:
        date = None
        while True:
            line = ser.readline()
            gps_logger(line.rstrip())
            if line.startswith("$GPRMC"):
                # logging.debug(line.rstrip()) # not needed since we log them all
                msg = pynmea2.parse(line)
                date = msg.datestamp
            elif line.startswith("$GPGGA"):
                # logging.debug(line.rstrip()) # same here
                msg = pynmea2.parse(line)
                logging.info("%s lat=%s long=%s alt=%s" %(msg.timestamp, msg.lat, msg.lon, msg.altitude))
                return msg, date

