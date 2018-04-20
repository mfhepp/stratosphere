#!/usr/bin/env python
# -*- coding: utf-8 -*-
# aprs.py
# routines for creating and transmitting APRS messages
# APRS Protocol Reference
# See https://github.com/casebeer/afsk
# and
# https://github.com/rossengeorgiev/aprs-python
# Version 1.0: http://www.aprs.org/doc/APRS101.PDF
# Version 1.1: http://www.aprs.org/aprs11.html
# Version 1.2: http://www.aprs.org/aprs12.html
#
# $ pip install afsk
#

import logging
import os
import datetime
# import aprslib.packets.position
import config
from shared_memory import *
# import ax25


def convert_decimal_to_base91(number):
    """Converts the number value to APRS Base91.APRS
    Based on
    https://github.com/rossengeorgiev/aprs-python/blob/master/aprslib/base91.py

    Args:
        number (float): A value

    Returns:
        A base91 string."""
    text = []
    max_n = ceil(log(number) / log(91))
    for n in _range(int(max_n), -1, -1):
        quotient, number = divmod(number, 91**n)
        text.append(chr(33 + quotient))
    return "".join(text).lstrip('!').rjust(max(1, width), '!')


def DD_to_DMS(lat_or_lon):
    """Converts a GPS coordinate in DD format (e.g. 47.5000) to DMS format
    needed for APRS, i.e. 4730.00."""
    dd = abs(float(lat_or_lon))
    deg = int(dd)
    minsec = dd - deg
    cmin = int(minsec * 60)
    csec = (minsec % 60) / float(60)
    return float(deg * 100 + cmin + csec)


def _compose_message(aprs_info, destination='', ssid=config.APRS_SSID,
                     aprs_path=config.APRS_PATH):
    """Composes a full APRS message string from the given components."""
    return b'{source}>{destination},{digis}:{info}'.format(
        destination=destination,
        source=ssid,
        digis=aprs_path,
        info=aprs_info)


def send_aprs(transceiver, frequency, ssid, aprs_info,
              aprs_path=config.APRS_PATH, aprs_destination='',
              full_power=False):
    """Transmits the given APRS message via the DRA818 transceiver object.

    Args:
        transceiver (DRA818): The DRA818 transceiver object.

        frequency (float): The frequency in MHz. Must be a multiple of
        25 KHz and within the allowed ham radio band allocation.

        ssid (str): The APRS SSID (e.g. 'CALLSIGN-7')

        aprs_info (str): The actual APRS payload.

        aprs_path (str): The APRS path.

        destination (str): The APRS destination. Needed for telemetry
        definitions, since they have to be addressed to the SSID of the
        sender of the telemetry data packages.

        full_power (boolean): True sets the RF power level to the
        maximum of 1 W, False sets it to 0.5W.

    Returns:
        True: Transmission successful.
        False: Transmission failed.
    """
    try:
        # See https://github.com/casebeer/afsk
        if aprs_destination:
            command = 'aprs -c {callsign} --destination {destination} \
            -d {path} -o {usb_path}/aprs.wav "{info}"'.format(
                callsign=ssid,
                destination=aprs_destination,
                path=aprs_path,
                info=aprs_info,
                usb_path=config.USB_DIR)
        else:
            command = 'aprs -c {callsign} -d {path} -o {usb_path}/aprs.wav\
            "{info}"'.format(
                callsign=ssid,
                path=aprs_path,
                info=aprs_info,
                usb_path=config.USB_DIR)
        # TODO: It would be better to play the APRS directly from memory,
        # but setting up PyAudio on Raspbian did not work.info
        # So we take the USB stick instead of the SDCARD in order to
        # minimize wear on the latter.
        # The downside is that failure on the USB stick will break
        # APRS.
        logging.info('Generating APRS wav for [%s]' % command)
        subprocess.call(command, shell=True)
        if not os.path.exists('%s/aprs.py' % config.USB_DIR):
            logging.error('Error: Problem generating APRS wav file.')
            return False
        logging.info('Sending APRS packet from %s via %s [%f MHz]' % (
            ssid, aprs_path, frequency))
        # when converting APRS string to audio using Bell 202, mind the
        # pre-emphasis problems, see pre-emphasis settings, see also
        # http://www.febo.com/packet/layer-one/transmit.html
        transceiver.set_filters(pre_emphasis=config.PRE_EMPHASIS)
        # TODO: Think about software-based volume / modulation control
        # maybe using ALSA via Python wrapper, see e.g.
        # http://larsimmisch.github.io/pyalsaaudio/pyalsaaudio.html#alsa-and-python
        # Also see
        # http://www.forum-raspberrypi.de/Thread-suche-python-befehl-fuer-den-alsa-amixer
        status = transceiver.transmit_audio_file(
            frequency, ['%s/aprs.py' % config.USB_DIR], full_power=full_power)
        try:
            os.remove('%s/aprs.py' % config.USB_DIR)
        except OSError:
            pass
    finally:
        transceiver.stop_transmitter()
    return status


def generate_aprs_position():
    '''Generate APRS string'''
    # TIME = UTC!!!
    utc = datetime.datetime.utcnow()
    # timestamp_dhm = "%d%02d%02d%z" % (utc.day, utc.hour, utc.minute)
    timestamp_hms = "%02d%02d%02dh" % (utc.hour, utc.minute, utc.second)
    # This format may not be used in Status Reports.
    # All data comes from the shared memory variables
    if config.GPS_OBFUSCATION and altitude_max.value > (altitude.value + 1000):
        lat = latitude.value + config.GPS_OBFUSCATION_DELTA['lat']
        lon = longitude.value + config.GPS_OBFUSCATION_DELTA['lon']
    else:
        lat = latitude.value
        lon = longitude.value
    latitude_string = "%04.2f%s" % (DD_to_DMS(lat), latitude_direction.value)
    longitude_string = "%05.2f%s" % (DD_to_DMS(lon), longitude_direction.value)
    # altitude = "/A=%6i" % altitude.value * 3.28  # in feet
    # Battery voltage, discharge current, battery temperature
# TODO
    speed = 34  # speed in knots from GPS
# TODO
    course = 180  # course from GPS
    comment = 'STRATOSPHERE 2018'
# TODO - weather report could be included
    # comment = "BATT_U=%.2f BATT_I=%.4f BATT_T=%2.2f" % (
    #    battery_voltage.value, discharge_current.value, battery_temp.value)
    info_field = "@%s/%s/%sO%03i/%03i/A=%06i>%s" % (
        timestamp_hms,
        latitude_string,
        longitude_string,
        course,
        speed,
        altitude.value * 3.28,  # in feet
        comment)
    # Extensions
    # Integrate Base91 telemetry directly?
    # - Raw NMEA strings (particular number of satellites)
    # - Ground speed (maybe via NMEA)
    # Ascent / descent rate
    # Orientation (Compass)
    return info_field


def generate_aprs_telemetry_definition():
    '''Creates Base91 Comment Telemetry message (units, labels, ...)'''
    # p. 68 in V 1.1
    # The messages addressee is the callsign of the station transmitting the telemetry data. For example, if N0QBF launches a balloon with the callsign N0QBF-11, then the four messages are addressed to N0QBF-11.
    return ""
# TIME = UTC!!!


def generate_aprs_telemetry_report():
        # increment counter and  make sure that it and all of the telemetry
    # values never get values higher than 8280
    # all data comes from the shared memory variables
    # sequence = (sequence + 1) & 0x1FFF  # see http://he.fi/doc/aprs-base91-comment-telemetry.txt
    # TBD: the newer Base91 telemetry allows for bigger sequence numbers
# TIME = UTC!!!
    global sequence
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
    # T#005,199,000,255,073,123,01101001
    # internal_temp.value
    # external_temp_ADC.value
    # cpu_temp.value
    # battery_voltage.value
    # discharge_current.value
    # battery_temp.value

    # humidity_internal.value
    info_field = "T#%3i,%s,%s,%s,%s,%s,%s" % (sequence, atm, t_int, t_ext, humidity, binary)
    msg = '%s>APRS,%s' % (APRS_SSID, APRS_PATH)
    return info_field


def generate_aprs_weather():
    '''Generate APRS weather message'''
    # For humidity, pressure and outside temperature, also the weather
    # format of APRS could be used (tbc)
# TODO: Check whether aprs.fi will display weather station info for
# balloon SSID
# Otherwise we use two SSIDs
    # humidity_external.value
    # atmospheric_pressure.value
    # external_temp.value

    info_field = ''
    return info_field


if __name__ == '__main__':
    print latitude.value
    logging.basicConfig(level=logging.INFO)
    logging.info('Testing APRS functions.')
    import aprslib
    logging.info('Now generating and parsing APRS messages.')
# TODO: APRSlib expects full message, methods return just info part
    try:
        for messages in [
                generate_aprs_position(),
                generate_aprs_telemetry_definition(),
                generate_aprs_telemetry_report(),
                generate_aprs_weather()]:
            aprs_string = _compose_message(message)
            result = aprslib.parsing.parse(aprs_string)
            logging.info('APRS message: %s' % aprs_string)
            for key, value in result.iteritems():
                logging.info('%s = %s' (key, value))
    except (aprslib.ParseError, aprslib.UnknownFormat) as exp:
        logging.error('Error: Parsing APRS message failed.')
    logging.info('Now starting APRS transmission tests.')
    transceiver = dra818.DRA818(
        uart=config.SERIAL_PORT_TRANSCEIVER,
        ptt_pin=config.DRA818_PTT,
        power_down_pin=config.DRA818_PD,
        rf_power_level_pin=config.DRA818_HL,
        frequency=config.APRS_FREQUENCY,
        squelch_level=1)
    raw_input('Press ENTER to start APRS transmission [CTRL-C for exit].')
    for message in [position_report, telemetry_definition_report,
                    telemetry_report, weather_report]:
        status = send_aprs(transceiver, destination, config.APRS_FREQUENCY,
                           config.APRS_SSID, message)
        logging.info('Transmission status: %s' % status)
        raw_input('Press ENTER to for next transmission [CTRL-C for exit].')
    logging.info('APRS tests completed.')
