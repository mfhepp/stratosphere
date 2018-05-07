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
from math import ceil, log
import math
from aprslib import int_type
import dra818
import afsk
import gps_info
import subprocess
import RPi.GPIO as GPIO
import pickle
import audiogen
import utility
import time


def get_sequence_number():
    """Tries to load the most recent sequence number from disk.

    The APRS telemetry sequence number must be incremented if
    there was a test transmission on the same day. Otherwise, aprs.fi
    will reject the packets."""
    sequence_number = 0
    try:
        fn1 = os.path.join(config.USB_DIR, 'sequence_number.dat')
        if os.path.exists(fn1):
            logging.debug('Reading APRS sequence number from %s' % fn1)
            with open(fn1, 'rb') as pickle_handler:
                sequence_number = int(pickle.load(pickle_handler))
                if sequence_number < 0:
                    sequence_number = 0
        sequence_number = (sequence_number + 1) & 0x1FFF
        with open(fn1, 'wb') as pickle_handler:
            pickle.dump(sequence_number, pickle_handler)
        logging.info('New APRS sequence number: %i, %s' % (
            sequence_number, convert_decimal_to_base91(sequence_number)))
    except Exception as msg:
        logging.exception(msg)
    return sequence_number


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
    if number > 0:
        max_n = ceil(log(number) / log(91))
        for n in xrange(int(max_n), -1, -1):
            quotient, number = divmod(number, 91**n)
            text.append(chr(33 + quotient))
    return "".join(text).lstrip('!').rjust(max(1, width), '!')


def DD_to_DMS(lat_or_lon):
    """Converts a GPS coordinate in DD format (e.g. 47.5000) to DMS format
    needed for APRS, i.e. 4730.00."""
    d = math.floor(abs(lat_or_lon))
    min_sec = (lat_or_lon - d) * 60.0
    min_sec = round(min_sec, 2)
    dms = d * 100 + min_sec
    return dms


def clip(val, min_, max_):
    """Returns val, if val if min_ < val < max_, otherwise min_ resp. max_."""
    return min_ if val < min_ else max_ if val > max_ else val


def _compose_message(aprs_info, destination='APRS', ssid=config.APRS_SSID,
                     aprs_path=config.APRS_PATH):
    """Composes a full APRS message string from the given components."""
    return b'{source}>{destination},{digis}:{info}'.format(
        source=ssid,
        destination=destination,
        digis=aprs_path,
        info=aprs_info)


def send_aprs(aprs_info, frequency=config.APRS_FREQUENCY,
              ssid=config.APRS_SSID, aprs_path=config.APRS_PATH,
              aprs_destination=b'APRS', full_power=False):
    """Transmits the given APRS message via the DRA818 transceiver object.

    Args:
        transceiver (DRA818): The DRA818 transceiver object.
        aprs_info (str): The actual APRS payload.
        frequency (float): The frequency in MHz. Must be a multiple of
        25 KHz and within the allowed ham radio band allocation.
        ssid (str): The APRS SSID (e.g. 'CALLSIGN-7')
        aprs_path (str): The APRS path.
        aprs_destination (str): The APRS destination. Needed for telemetry
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
        packet = afsk.ax25.UI(
            destination=aprs_destination,
            source=ssid,
            info=aprs_info,
            digipeaters=aprs_path.split(b','))
        logging.info(r"APRS packet content: '{0}'".format(packet))
        fn = os.path.join(config.USB_DIR, 'aprs.wav')
        logging.info('Now generating file %s for APRS packet.' % fn)
        audio = afsk.encode(packet.unparse())
        with open(fn, 'wb') as f:
            audiogen.sampler.write_wav(f, audio)
        # TODO: It would be better to play the APRS directly from memory,
        # but setting up PyAudio on Raspbian did not work.
        # So we take the USB stick instead of the SDCARD in order to
        # minimize wear-off on the latter.
        # The downside is that failure of the USB stick will break
        # APRS completely.
        if not os.path.exists(fn):
            logging.error('Error: Problem generating APRS wav file.')
            return False
        logging.info('Sending APRS packet from %s via %s [%f MHz]' % (
            ssid, aprs_path, frequency))
        # When converting APRS string to audio using Bell 202, mind the
        # pre-emphasis problems, see pre-emphasis settings, see also
        # http://www.febo.com/packet/layer-one/transmit.html
        # but this is already done:
        # transceiver.set_filters(pre_emphasis=config.PRE_EMPHASIS)
        # TODO: Think about software-based volume / modulation control
        # maybe using ALSA via Python wrapper, see e.g.
        # http://larsimmisch.github.io/pyalsaaudio/pyalsaaudio.html#alsa-and-python
        # Also see
        # http://www.forum-raspberrypi.de/Thread-suche-python-befehl-fuer-den-alsa-amixer
        transceiver = dra818.DRA818(
            uart=config.SERIAL_PORT_TRANSCEIVER,
            ptt_pin=config.DRA818_PTT,
            power_down_pin=config.DRA818_PD,
            rf_power_level_pin=config.DRA818_HL,
            frequency=frequency,
            squelch_level=config.SQUELCH)
        status = transceiver.transmit_audio_file(
            frequency, [fn], full_power=full_power)
        try:
            os.remove(fn)
        except OSError:
            pass
    except Exception as msg:
        logging.exception(msg)
    finally:
        transceiver.stop_transmitter()
    return status


def send_telemetry_definitions(frequency=config.APRS_FREQUENCY,
                               ssid=config.APRS_SSID,
                               aprs_path=config.APRS_PATH,
                               aprs_destination='',
                               full_power=False):
    """Transmits the APRS telemetry definition messages via the DRA818
    transceiver object.The five channel definitions are hard-wired in the code.

    Note: APRS telemetry definitions must be addressed to the SSID of the
    beaconing station, i.e. the SSID of the balloon.

    Args:
        frequency (float): The frequency in MHz. Must be a multiple of
        25 KHz and within the allowed ham radio band allocation.
        ssid (str): The APRS SSID (e.g. 'CALLSIGN-7')
        aprs_path (str): The APRS path.
        aprs_destination (str): The APRS destination. Telemetry
        definitions have to be addressed to the SSID of the
        sender of the telemetry data packets.
        full_power (boolean): True sets the RF power level to the
        maximum of 1 W, False sets it to 0.5W.

    Returns:
        True: Transmission successful.
        False: Transmission failed.
    """
    # Check that all four files exist, otherwise regenerate all four
    ok = True
    wav_files = ['aprs_telemetry_%i.wav' % i for i in range(4)]
    for fn in wav_files:
        ok = ok and os.path.exists(fn)
    if not ok:
        for idx, msg in enumerate(generate_aprs_telemetry_definition()):
            # command = 'aprs -c {callsign} --destination {destination} \
            command = 'aprs -c {callsign} -d {path} -o aprs_telemetry_{i}.wav \
"{info}"'.format(
                callsign=ssid,
                destination=aprs_destination,
                path=aprs_path,
                i=idx,
                info=msg)
            logging.info('Generating APRS wav for [%s]' % command)
            subprocess.call(command, shell=True)
            if not os.path.exists('aprs_telemetry_%i.wav' % idx):
                logging.error(
                    'Error: Problem generating aprs_telemetry_%i.wav' % idx)
                return False
    # Transmit all four messages in one turn, i.e. without turning off
    # the transceiver.
    transceiver = dra818.DRA818(
        uart=config.SERIAL_PORT_TRANSCEIVER,
        ptt_pin=config.DRA818_PTT,
        power_down_pin=config.DRA818_PD,
        rf_power_level_pin=config.DRA818_HL,
        frequency=frequency,
        squelch_level=config.SQUELCH)
    transceiver.set_filters(pre_emphasis=config.PRE_EMPHASIS)
    status = transceiver.transmit_audio_file(
        frequency, wav_files, full_power=full_power)
    return status


def generate_aprs_position(telemetry=False):
    '''Generate APRS string for an APRS Position Report.

    Args:
        telemetry (boolean): Adds Base 91 telemetry to the comment if True

    All data comes from the shared memory variables.'''
    if config.GPS_OBFUSCATION and altitude_max.value > (altitude.value + 1000):
        lat = latitude.value + config.GPS_OBFUSCATION_DELTA['lat']
        lon = longitude.value + config.GPS_OBFUSCATION_DELTA['lon']
        logging.info('GPS obfuscation used for APRS with (%f, %f) at %fm.' %
                     (config.GPS_OBFUSCATION_DELTA['lat'],
                      config.GPS_OBFUSCATION_DELTA['lon'], altitude.value))
        GpO = 1
    else:
        lat = latitude.value
        lon = longitude.value
        GpO = 0
    latitude_string = '%07.2f%s' % (DD_to_DMS(lat), latitude_direction.value)
    longitude_string = '%08.2f%s' % (DD_to_DMS(lon), longitude_direction.value)
    if telemetry:
        # Channel 1: Pressure: 0 - 1500 -> * 4
        atm = int(clip(atmospheric_pressure.value, 0, 1500) * 4)
        # Channel 2: Temperature inside -128...+128 °C -> add 128 and
        t_int = int(clip(internal_temp.value, -128, 128) + 128) * 32
        # Channel 3: Temperature outside -> 128 + 128 -> add 100
        t_ext = int(clip(external_temp.value, -128, 128) + 128) * 32
        # Channel 4: Humidity 0.0 - 1.0 -> multiply by 8000
        humidity = int(humidity_external.value * 8000)
        # Channel 5: Battery voltage 0.0 - 15 V -> multiply by 256
        voltage = int(battery_voltage.value * 256)
        # Binary channels
        # CamT - Top camera recording
        CamT = cam_top_recording.value
        # CamB - Bottom camera recording
        CamB = cam_bottom_recording.value
        # GpO - future feature: see above
        # Dsk - USB disk okay / enough memory
        Dsk = int(utility.check_free_disk_space())
        # gA - GPS lat outdated
        gA = latitude_outdated.value
        # gO - GPS lon outdated
        gO = longitude_outdated.value
        # Al - GPS alt outdated
        Al = altitude_outdated.value
        # Binary values are put into a single Base91 encoded integer,
        # where the LSB (least significant bit) corresponds
        # to B1 of the traditional Telemetry specification,
        # the 8th bit corresponds to B8.
        binary_channels = CamT + CamB * 2 + Dsk * 4 + gA * 8 + gO * 16 + \
            Al * 32
        sequence_number = get_sequence_number()
        comment = b'|%s%s%s%s%s%s%s|' % (
            convert_decimal_to_base91(sequence_number, width=2),
            convert_decimal_to_base91(atm, width=2),
            convert_decimal_to_base91(t_int, width=2),
            convert_decimal_to_base91(t_ext, width=2),
            convert_decimal_to_base91(humidity, width=2),
            convert_decimal_to_base91(voltage, width=2),
            convert_decimal_to_base91(binary_channels, width=2))
    else:
        comment = "B_U=%2.2f B_T=%2.2f" % (
            battery_voltage.value, battery_temp.value)
    # See pp. 32f. in the APR 1.01 spec for the message format.
    # The 'O' is the APRS symbol code for a balloon ('>' would be car)
    info_field = "/%s%s/%sO/A=%06i %s" % (
        timestamp_hms(),
        latitude_string,
        longitude_string,
        altitude.value * 3.28,
        comment)
    # Possible extensions
    # - course and speed
    # - weather report could be included
    # - Raw NMEA strings (particular number of satellites)
    # - Ascent / descent rate
    # - Orientation (Compass)
    return info_field


def generate_aprs_telemetry_definition(target_station=config.APRS_SSID):
    """Creates a list of  APRS telemetry definition messages, namely the
    names, units, and equation coefficients.
    See p. 68 in V 1.1 spec.

    Args:
        target_station (str): The SSID of the balloon."""
    # Binary Fields:
    # CamT - Top camera recording
    # CamB - Bottom camera recording
    # GpO - future feature
    # Dsk - USB disk okay / enough memory
    # gA - GPS lat outdated
    # gO - GPS lon outdated
    # Al - GPS alt outdated
    parameters_name_message = ':%s:PARM.ATM,T_Int,T_Ext,Humid,Batt' %\
        target_station.ljust(9, ' ') + ',CamT,CamB,GpO,Dsk,gA,gO,Al'
    parameters_unit_message = ':%s:UNIT.mBar,degC,degC,%%,V' %\
        target_station.ljust(9, ' ') + ',on,on,on,ok,ok,ok,ok'
    # Equation coefficients (a,b,c) = a * value^2 + b * value + c
    # Hard-wired, cf. generate_aprs_position(telemetry=True)
    c1 = '0,0.25,0'  # Channel 1: Pressure: 0 - 1500 -> * 4
    # Channels 2 and 3: Temperature -128...+128 °C -> add 128 and * 32
    c2 = '0,0.03125,-128'
    c3 = '0,0.03125,-128'
    # Channel 4: Humidity 0.0 - 1.0 -> multiply by 8000
    # Because we want %, we divide just by 80
    c4 = '0,0.0125,0'
    # Channel 5: Battery voltage 0.0 - 15 V -> multiply by 256
    c5 = '0,0.00390625,0'
    parameters_equation_coefficients_message = \
        ':{}:EQNS.{},{},{},{},{}'.format(
            target_station.ljust(9, ' '), c1, c2, c3, c4, c5)
    bit_sense_project_name_message = ':%s:BITS.11111111,%s' % \
        (target_station.ljust(9, ' '), config.APRS_COMMENT[:22])
    return [parameters_name_message, parameters_unit_message,
            parameters_equation_coefficients_message,
            bit_sense_project_name_message]


if __name__ == '__main__':
    import stratosphere
    logging.basicConfig(level=logging.INFO)
    gps_logger = logging.getLogger('gps')
    gps_logger.setLevel(logging.ERROR)
    nmea_logger = logging.getLogger('nmea')
    nmea_logger.setLevel(logging.ERROR)
    # Initialize GPS subprocess / thread
    continue_gps.value = 1
    p_gps = mp.Process(target=gps_info.update_gps_info,
                       args=(gps_logger, nmea_logger))
    p_gps.start()
    # Wait for valid GPS position and time, and sync time
    logging.info('Waiting for valid initial GPS position.')
    while longitude_outdated.value > 0 or latitude_outdated.value > 0:
        time.sleep(1)
    # Initialize sensors thread
    sensors_active.value = 1
    logging.info('Starting sensors logging.')
    p_sensors = mp.Process(target=stratosphere.sensors_handler)
    p_sensors.start()
    logging.info('Sensors logging OK.')
    logging.info('Testing APRS functions.')
    import aprslib
    logging.info('Now generating and parsing APRS messages.')
    aprs_strings = [_compose_message(message) for message in [
        generate_aprs_position(), generate_aprs_position(telemetry=True)]]
    aprs_strings.extend([_compose_message(message) for message in
                         generate_aprs_telemetry_definition()])
    try:
        for message in aprs_strings:
            logging.info('Trying to parse APRS: %s' % message)
            result = aprslib.parsing.parse(message)
            logging.info('APRS message: %s parsing OK:' % message)
            for key in result:
                logging.debug('\t%s = %s' % (key, result[key]))
    except (aprslib.ParseError, aprslib.UnknownFormat) as exp:
        logging.error('Error: Parsing APRS message failed.')
        logging.exception(msg)

    logging.info('Now starting APRS transmission tests.')
    raw_input('Press ENTER to start APRS transmission [CTRL-C for exit].')
    logging.info('Sending four telemetry definition messages.')
    status = send_telemetry_definitions(full_power=True)
    logging.info('Transmission status: %s' % status)
    while True:
        try:
            raw_input('Press ENTER to for next transmission' +
                      ' [CTRL-C for exit].')
            logging.info('Sending position report with telemetry.')
            info_msg = generate_aprs_position(telemetry=True)
            logging.info('----> INFO: %s' % info_msg)
            status = send_aprs(info_msg, full_power=True)
            logging.info('Transmission status: %s' % status)
        except KeyboardInterrupt:
            logging.info('APRS tests completed.')
            break
    p_gps.join(10)
    p_sensors.join(10)
    GPIO.cleanup()
