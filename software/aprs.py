#!/usr/bin/env python
# -*- coding: utf-8 -*-

# aprs.py
# routines for initializing and controlling the DRA818V transceiver module
# see also https://github.com/darksidelemm/dra818/blob/master/DRA818/DRA818.cpp
# APRS Protocol Reference
#
# Version 1.0: http://www.aprs.org/doc/APRS101.PDF
# Version 1.1: http://www.aprs.org/aprs11.html
# Version 1.2: http://www.aprs.org/aprs12.html

import aprslib.packets.position

from config import *
from shared_memory import *

def convert_decimal_to_base91(number):
    '''Converts the number value to APRS Base91'''
    # Based on https://github.com/rossengeorgiev/aprs-python/blob/master/aprslib/base91.py
    text = []
    max_n = ceil(log(number) / log(91))
    for n in _range(int(max_n), -1, -1):
        quotient, number = divmod(number, 91**n)
        text.append(chr(33 + quotient))
    return "".join(text).lstrip('!').rjust(max(1, width), '!')


def send_aprs(aprs_message, power_level = TRANSMISSION_POWER_DEFAULT):
    '''Tunes transceiver to APRS frequency, converts the APRS message to audio, and transmits the audio'''
    # - nach PTT-Tastung liegt Vorlaufzeit bis zum Erreichen der vollen TX-Sendebereitschaft bei etwa 1 Sekunde
    transmission_status = False
    # when comverting APRS string to audio using Bell 202, mind the
    # pre-emphasis problems, see pre-emphasis settings, see also http://www.febo.com/packet/layer-one/transmit.html
    # also think about software-based volume / modulation control
    # maybe using ALSA via Python wrapper, see e.g. http://larsimmisch.github.io/pyalsaaudio/pyalsaaudio.html#alsa-and-python
    # also see http://www.forum-raspberrypi.de/Thread-suche-python-befehl-fuer-den-alsa-amixer
    # initialize module - set frequency, modulation width, ...
    # DRA818_SQ = None # Squelch detection.. Low -> Audio amplifier on
    # DRA818_PTT = 1 # Tx/Rx control pin: Low->TX; High->RX
    # DRA818_PD = 1 # Power saving control pin: Low->sleep mode; High->normal mode
    # DRA818_HL = 1 # RF Power Selection: Low->0.5W; floated->1W
    # activate transmission
    # wait (for calibration)
    # send audio
    # ---> direct with aprs --callsign DK3IT-11  WIDE2-1  ":EMAIL    :test@example.com Test email"
    command = 'aprs --callsign %s -d %s "%s"' % (APRS_SSID, APRS_PATH, aprs_message)
    subprocess.call(command, shell=True)

    # more elegant: directly invoke library, see
    # https://github.com/casebeer/afsk/blob/master/afsk/ax25.py

    # wait
    # stop transmission
    return transmission_status


def generate_aprs_telemetry_definition():
    '''Creates Base91 Comment Telemetry message (units, labels, ...)'''
    # p. 68 in V 1.1
    # The messages addressee is the callsign of the station transmitting the telemetry data. For example, if N0QBF launches a balloon with the callsign N0QBF-11, then the four messages are addressed to N0QBF-11.
    return ""


def generate_aprs_telemetry_report():
    # all data comes from the shared memory variables
    # sequence = (sequence + 1) & 0x1FFF  # see http://he.fi/doc/aprs-base91-comment-telemetry.txt
    # TBD: the newer Base91 telemetry allows for bigger sequence numbers
    if sequence < 999:
        sequence += 1
    else:
        sequence = 0
    # For now, we cut it down to 1 - 999

    # All values must be mapped to a 8-Bit unsigned integer
    # Channel 1: Pressure: 0 - 1500 -> divide by 5
    atm = "%3i" % atmospheric_pressure.value/5
    # Channel 2: Temperature inside -> 128 + 128 -> add 100
    t_int = "%3i" % internal_temp.value + 100
    # Channel 3: Temperature outside -> 128 + 128 -> add 100
    t_ext = "%3i" % external_temp.value + 100
    # Channel 4: Humidity 0.0 - 1.0 -> multiply by 200
    humidity = "%3i" % humidity_external.value * 200
    binary = "00000000"

    # Nice to have:
    # Channel 5: Compass / orientation
    # Binary 1: Camera 1 on/on
    # Binary 2: Camera 2 on/off
    # Binary 3 - 8: tbd
    # T#005,199,000,255,073,123,01101001
    # internal_temp.value
    # external_temp_ADC.value
    # cpu_temp.value
    # battery_voltage.value
    # discharge_current.value
    # battery_temp.value
    # atmospheric_pressure.value
    # humidity_internal.value
    # humidity_external.value
    # motion_sensor_status.value
    # motion_sensor_message.value
    info_field = "T#%3i,%s,%s,%s,%s,%s,%s" % (sequence, atm, t_int, t_ext, humidity, binary)
    msg = '%s>APRS,%s' % (APRS_SSID, APRS_PATH)


def generate_aprs_position():
    '''Generate APRS string'''
    # increment counter and  make sure that it and all of the telemetry values never get values higher than 8280

    utc = datetime.utcnow()
    timestamp_dhm = "%d%02d%02d%z" % (utc.day, utc.hour, utc.minute)
    timestamp_hms = "%d%02d%02d%h" % (utc.hour, utc.minute, utc.second)  # This format may not be used in Status Reports.
    # all data comes from the shared memory variables
    latitude = "%04.2f%s" % (latitude.value, latitude_direction.value)
    longitude = "%05.2f%s" % (longitude.value, longitude_direction.value)
    altitude = "/A=%6i" % altitude.value*3.28  # in feet

    # Battery voltage, discharge current, battery temperature
    comment = "BATT_U=%.2f BATT_I=%.4f BATT_T=%2.2f" % (battery_voltage.value, discharge_current.value, battery_temp.value)

    info_field = "/%s/%s/%s>%s" % (timestamp_hms, latitude, longitude, comment)

    # Extensions
    # Intetegrate Base91 telemetry directly?
    # - Raw NMEA strings (particular number of satellites)
    # - Ground speed (maybe via NMEA)
    # Ascent / descent rate
    # Orientation (Compass)

    return info_field


def generate_aprs_weather():
    '''Generate APRS weather message'''
    # For humidity, pressure and outside temperature, also the weather format of APRS could be used (tbc)
    info_field = ""
    return info_field
