#!/usr/bin/env python
# -*- coding: utf-8 -*-

# sstv.py
# All routines for generating SSTV images

# TBD
# - set bandwidth / important for narrow-band ham radio transmissions.
# - fine-tune iming as impropper timing results in slanted images
# use https://github.com/hatsunearu/pisstvpp

import logging
import os
import time
import subprocess
import config


def convert_image_to_sstv_wav(image_path, protocol='r36', rate=22050):
    """Creates a WAV file that represents the SSTV modulation for the
    image at the path.

    Args:
        image_path (str): The path of an image in
        PNG or JPG format. Note that the image size should match the
        SSTV mode.

        protocol (str): The SSTV format in the pisstvpp form, like so:
            Martin 1: m1
            Martin 2: m2
            Scottie 1: s1
            Scottie 2: s2
            Scottie DX: sdx
            Robot 36: r36

        rate (int): The sampling rate in Hz (default: 22050 Hz)

    Returns:
        None if a problem occured or a string with the path of the WAV
        file containing the result."""

# TODO: Resize image to Robots 36 or other format
    if os.path.isfile(image_path):
        command = "./pisstvpp/pisstvpp -p %s -r%s %s" % \
                  (protocol, rate, image_path)
        return_code = subprocess.call(command, shell=True)
        if return_code == 0:
            return image_path + '.wav'
        else:
            return False
    else:
        return None


def play_audio_file(audio_file_path):
    """Plays the audio file at the given path via the RBPi's current
    audio device.

    Args:
        audio_file_path (str): The absolute or relative path of the
        audio file to be played. The file format must be supported by
        the aplay command.

    Returns:
        True if the command was successful, False in case of any error.
    """
    if os.path.isfile(audio_file_path):
        command = "aplay %s" % audio_file_path
        return_code = subprocess.call(command, shell=True)
        if return_code == 0:
            return True
        else:
            return False
    else:
        return False


def transmit_audio_file(transceiver, frequency, audio_file_path,
                        full_power=False):
    """Transmits the audio file via the given DRA818 transceiver object.

    Args:
        transceiver (DRA818): The DRA818 transceiver object.

        frequency (float): The frequency in MHz. Must be a multiple of
        25 KHz and within the allowed ham radio band allocation.

        audio_file_path (str): The path of the audio file.

        full_power (bolean): Tx power level. True = 1 W, False = 0.5 W.

    Returns:
        True: Transmission successful.
        False: Transmission failed.
    """
    if transceiver.set_tx_frequency(frequency):
        time.sleep(1)
        transceiver.start_transmitter(full_power=full_power)
        status = play_audio_file(audio_file_path)
        time.sleep(1)
        transceiver.stop_transmitter()
    else:
        return False
    return status


def send_sstv(transceiver, frequency, image_path,
              protocol=config.SSTV_MODE):
    """Transmits the image as SSTV signal.

    Args:
        transceiver (DRA818): The DRA818 transceiver object.

        frequency (float): The frequency in MHz. Must be a multiple of
        25 KHz and within the allowed ham radio band allocation.

        image_path (str): The path of the image file.

        protocol (str): The SSTV mode string.

    Returns:
        True: Transmission successful.
        False: Transmission failed.
    """
    wav = convert_image_to_sstv_wav(image_path,
                                    protocol=protocol,
                                    rate=22050)
    if wav is not None:
        status = transmit_audio_file(transceiver, frequency, wav,
                                     full_power=False)
        return status
    else:
        return False


if __name__ == "__main__":
    import dra818
    logging.basicConfig(level=logging.DEBUG)
    transceiver = dra818.DRA818(
        uart=config.SERIAL_PORT_TRANSCEIVER,
        ptt_pin=config.DRA818_PTT,
        power_down_pin=config.DRA818_PD,
        rf_power_level_pin=config.DRA818_HL,
        frequency=config.SSTV_FREQUENCY,
        squelch_level=1)
    try:
        print 'Now listening at %f MHz. Press CTRL-C to quit.' % \
              config.SSTV_FREQUENCY
        raw_input('Press ENTER to start audio beacon transmission.')
        print 'Transmitting audio message.'
        status = transmit_audio_file(
            transceiver,
            config.SSTV_FREQUENCY,
            'files/beacon-english.wav',
            full_power=False)
        print 'Status: %s' % status
        raw_input('Press ENTER to start SSTV transmission.')
        print 'Starting SSTV transmission.'
        status = send_sstv(
            transceiver,
            config.SSTV_FREQUENCY,
            'files/sstv-testbild-small.png',
            protocol=config.SSTV_MODE)
        print 'Status: %s' % status
    except KeyboardInterrupt:
        print 'CTRL-C detected.'
        transceiver.stop_transmitter()
    finally:
        transceiver.stop_transmitter()
