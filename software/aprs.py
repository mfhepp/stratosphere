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
import config
from shared_memory import *

sequence_number = 1


def timestamp_hms():
    """Returns the current UTC time in the HMS format for APRS."""
    utc = datetime.datetime.utcnow()
    return '%02d%02d%02dh' % (utc.hour, utc.minute, utc.second)


def timestamp_dhm():
    """returns the current UTC time in the DHM format for APRS."""
    utc = datetime.datetime.utcnow()
    return '%d%02d%02d%z' % (utc.day, utc.hour, utc.minute)


def convert_decimal_to_base91(number, width=1):
    """Converts the number value to APRS Base91.APRS
    Based on
    https://github.com/rossengeorgiev/aprs-python/blob/master/aprslib/base91.py

    Args:
        number (float): A value

    Returns:
        A base91 string."""
    if not isinstance(number, int_type):
        raise TypeError("Value must be int, got %s", type(number))
    if not 0 <= number <= 8280:
        raise ValueError('Value must be between 0 and 8280.')
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


def clip(val, min_, max_):
    return min_ if val < min_ else max_ if val > max_ else val


def _compose_message(aprs_info, destination='', ssid=config.APRS_SSID,
                     aprs_path=config.APRS_PATH):
    """Composes a full APRS message string from the given components."""
    return b'{source}>{destination},{digis}:{info}'.format(
        source=ssid,
        destination=destination,
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
        # but setting up PyAudio on Raspbian did not work.
        # So we take the USB stick instead of the SDCARD in order to
        # minimize wear-off on the latter.
        # The downside is that failure of the USB stick will break
        # APRS completely.
        logging.info('Generating APRS wav for [%s]' % command)
        subprocess.call(command, shell=True)
        if not os.path.exists('%s/aprs.py' % config.USB_DIR):
            logging.error('Error: Problem generating APRS wav file.')
            return False
        logging.info('Sending APRS packet from %s via %s [%f MHz]' % (
            ssid, aprs_path, frequency))
        # When converting APRS string to audio using Bell 202, mind the
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


def generate_aprs_position(telemetry=False):
    '''Generate APRS string for an APRS Position Report.

    Args:
        telemetry (boolean): Adds Base 91 telemetry to the comment if True

    All data comes from the shared memory variables.'''
    global sequence_number
    if config.GPS_OBFUSCATION and altitude_max.value > (altitude.value + 1000):
        lat = latitude.value + config.GPS_OBFUSCATION_DELTA['lat']
        lon = longitude.value + config.GPS_OBFUSCATION_DELTA['lon']
        logging.info('GPS obfuscation used for APRS with (%f, %f) at %fm.' %
                     (config.GPS_OBFUSCATION_DELTA['lat'],
                      config.GPS_OBFUSCATION_DELTA['lon'], altitude.value))
    else:
        lat = latitude.value
        lon = longitude.value
    latitude_string = '%04.2f%s' % (DD_to_DMS(lat), latitude_direction.value)
    longitude_string = '%05.2f%s' % (DD_to_DMS(lon), longitude_direction.value)
    if telemetry:
        # Channel 1: Pressure: 0 - 1500 -> * 4
        atm = int(clip(atmospheric_pressure.value, 0, 1500) * 4)
        # Channel 2: Temperature inside -128...+128 °C -> add 128 and
        t_int = int(clip(internal_temp.value, -128, 128) + 128) * 32
        # Channel 3: Temperature outside -> 128 + 128 -> add 100
        t_ext = int(clip(external_temp.value, -128, 128) + 128) * 32
        # Channel 4: Humidity 0.0 - 1.0 -> multiply by 8000
        humidity = humidity_external.value * 8000
        # Channel 5: Battery voltage 0.0 - 15 V -> multiply by 256
        voltage = battery_voltage.value * 256
        sequence_number = (sequence_number + 1) & 0x1FFF
        comment = '|%s%s%s%s%s%s|' % (
            convert_decimal_to_base91(sequence_number),
            convert_decimal_to_base91(atm),
            convert_decimal_to_base91(t_int),
            convert_decimal_to_base91(t_ext),
            convert_decimal_to_base91(humidity),
            convert_decimal_to_base91(voltage))
    else:
        comment = "B_U=%2.2f B_T=%2.2f" % (
            battery_voltage.value, battery_temp.value)
    # See pp. 32f. in the APR 1.01 spec for the message format.
    # The 'O' is the APRS symbol code for a balloon ('>' would be car)
    info_field = "/%s/%s/%sO%03i/%03i/A=%06i %s" % (
        timestamp_hms(),
        latitude_string,
        longitude_string,
        course.value,
        speed.value,
        altitude.value * 3.28,
        comment)
    # Possible extensions
    # - weather report could be included
    # - Raw NMEA strings (particular number of satellites)
    # - Ascent / descent rate
    # - Orientation (Compass)
    return info_field


def generate_aprs_telemetry_report(sequence_number):
    """DEPRECATED. ONLYE KEPT AS A BACKUP FOR NOW.

    Generate an APRS telemetry payload string.

    All data comes from the shared memory variables.
    See http://www.aprs.net/vm/DOS/TELEMTRY.HTM for the official definition."""

    # All values must be mapped to a 8-Bit unsigned integer
    # Channel 1: Pressure: 0 - 1500 -> divide by 5
    atm = int(atmospheric_pressure.value / 5.0)
    # Channel 2: Temperature inside -> 128 + 128 -> add 100
    t_int = int(internal_temp.value + 100)
    # Channel 3: Temperature outside -> 128 + 128 -> add 100
    t_ext = int(external_temp.value + 100)
    # Channel 4: Humidity 0.0 - 1.0 -> multiply by 200
    humidity = humidity_external.value * 200
    # Channel 5: Battery voltage 0.0 - 15 V -> multiply by 16
    voltage = battery_voltage.value * 16
    binary = "00000000"
    # Nice to have:
    # external_temp_ADC.value
    # cpu_temp.value
    # discharge_current.value
    # battery_temp.value
    # humidity_internal.value
    # T#sss,111,222,333,444,555,xxxxxxxx
    info_field = "T#%3i,%3i,%3i,%3i,%3i,%s" % (
        sequence, atm, t_int, t_ext, humidity, voltage, binary)
    return info_field


def generate_aprs_telemetry_definition():
    '''Creates Base91 Comment Telemetry message (units, labels, ...)'''
    # p. 68 in V 1.1
    # The messages addressee is the callsign of the station transmitting the telemetry data. For example, if N0QBF launches a balloon with the callsign N0QBF-11, then the four messages are addressed to N0QBF-11.
    return ""
# TIME = UTC!!!


if __name__ == '__main__':
    print latitude.value
    logging.basicConfig(level=logging.INFO)
    logging.info('Testing APRS functions.')
    import aprslib
    logging.info('Now generating and parsing APRS messages.')
# TODO: APRSlib expects full message, methods return just info part
    test_messages = [generate_aprs_position(),
                     generate_aprs_position(telemetry=True),
                     generate_aprs_telemetry_definition()]
    try:
# TODO: telemetry definition must be sent to balloon SSID
        for messages in test_messages:
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
    logging.info('Sending position report without telemetry.')
    status = send_aprs(transceiver, config.APRS_FREQUENCY, config.APRS_SSID,
                       generate_aprs_position(telemetry=False),
                       aprs_path=config.APRS_PATH, aprs_destination='',
                       full_power=False)
    logging.info('Transmission status: %s' % status)
    raw_input('Press ENTER to for next transmission [CTRL-C for exit].')
    logging.info('Sending position report with telemetry.')
    status = send_aprs(transceiver, config.APRS_FREQUENCY, config.APRS_SSID,
                       generate_aprs_position(telemetry=True),
                       aprs_path=config.APRS_PATH, aprs_destination='',
                       full_power=False)
    logging.info('Transmission status: %s' % status)
    raw_input('Press ENTER to for next transmission [CTRL-C for exit].')
# Send telemetry definition messages
    logging.info('APRS tests completed.')
