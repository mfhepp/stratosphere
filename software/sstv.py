#!/usr/bin/env python
# -*- coding: utf-8 -*-

# sstv.py
# All routines for generating and transmitting SSTV images
#
# $ git clone https://github.com/hatsunearu/pisstvpp
# $ sudo apt-get install build-essential libgd-dev libmagic-dev
# $ make make pisstvpp  (in the directory where PiSSTV resides in)
# $

import logging
import os
import subprocess
import config
from PIL import Image, ImageOps, ImageDraw, ImageFont


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
    if os.path.isfile(image_path):
        command = "./pisstvpp/pisstvpp -p %s -r%s %s" % \
                  (protocol, rate, image_path)
        logging.debug('Command: %s' % command)
        return_code = subprocess.call(command, shell=True)
        if return_code == 0:
            return image_path + '.wav'
        else:
            return False
    else:
        return None


def resize_image(image_path, protocol='r36'):
    """Resizes and crops the image so that it matches the required size
    for the given SSTV protocol. The new image will be written to a new file.

    Args:
        image_path (str): The path of an image in PNG or JPG format.

        protocol (str): The SSTV format in the pisstvpp form, like so:
            Martin 1: m1
            Martin 2: m2
            Scottie 1: s1
            Scottie 2: s2
            Scottie DX: sdx
            Robot 36: r36

    Returns:
            filename (str): The path and filename of the resized image.
    """
    if protocol not in ['m1', 'm2', 's1', 's2', 'sdx', 'r36']:
        raise ValueError('Invalid SSTV protocol string.')
    # All modes except Robot 36 can only accept 320x256 sized images
    # without cropping, whereas Robot 36 can only accept 320x240 sized
    # images without cropping.
    if protocol == 'r36':
        width, height = (320, 240)
    else:
        width, height = (320, 256)
    image = Image.open(open(image_path, 'rb'))
    # image = PIL.Image.open(image_path)
    sstv_image = ImageOps.fit(image, (width, height))
    fn, extension = os.path.splitext(image_path)
    output_path = os.path.join(fn + '_sstv' + extension)
    sstv_image.save(output_path, 'JPEG')
    logging.info('Wrote %ix%i SSTV image to %s.' %
                 (width, height, output_path))
    return output_path


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
    logging.debug('Return of SSTV: %s' % wav)
    if wav is not None:
        status = transceiver.transmit_audio_file(frequency, [wav],
                                                 full_power=False)
        return status
    else:
        return False


if __name__ == "__main__":
    import dra818
    import camera

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
        status = transceiver.transmit_audio_file(
            config.SSTV_FREQUENCY,
            [config.AUDIO_BEACON],
            full_power=False)
        print 'Status: %s' % status
        raw_input('Press ENTER to start SSTV transmission.')
        print 'Starting SSTV transmission.'
        status = send_sstv(
            transceiver,
            config.SSTV_FREQUENCY,
            config.SSTV_TEST_IMAGE,
            protocol=config.SSTV_MODE)
        print 'Status: %s' % status
        raw_input('Press ENTER to take still image.')
        print 'Taking still image.'
        fn = camera.InternalCamera.take_snapshot(annotate=False)
        fn_sstv = resize_image(fn, protocol=config.SSTV_MODE)
        print fn_sstv
        image = Image.open(open(fn_sstv, 'rb'))
        text_field = ImageDraw.Draw(image)
        font = ImageFont.truetype(
            '/usr/share/fonts/truetype/freefont/FreeMono.ttf', 18)
        print config.CALLSIGN
        text_field.text((10, 10), config.MISSION_TEXT, font=font)
        image.save(fn_sstv)
        print 'Showing SSTV image preview. Press ESC to proceed.'
        os.system('sudo fbi -a %s' % fn_sstv)
        print 'Starting SSTV transmission.'
        status = send_sstv(
            transceiver,
            config.SSTV_FREQUENCY,
            fn_sstv,
            protocol=config.SSTV_MODE)
        print 'Status: %s' % status
    except KeyboardInterrupt:
        print 'CTRL-C detected.'
    finally:
        transceiver.stop_transmitter()
