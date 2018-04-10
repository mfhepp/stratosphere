#!/usr/bin/env python
# -*- coding: utf-8 -*-

# camera.py
# Library for handling the three probe cameras

from config import *
import picamera
# global imports
import os
import time
import RPi.GPIO as GPIO
import logging
import multiprocessing as mp
from shared_memory import *

def _attach_questionmark(value, yes):
    if yes:
        return str(value) + "?"
    else:
        return str(value)


class External_Camera(object):
    """Control handler for external camera module based on
    https://bitbucket.org/alexstolz/strato_med."""

    def __init__(self, camera_power_on_off_pin,
                 camera_record_start_stop_pin,
                 camera_recording_status_pin):
        """Initializes the external camera module.

        Args:
        camera_power_on_off_pin (int): The GPIO pin, in BCM counting,
        for the power control of the unit, connected to GPIO3 (pin 5)
        of the OTHER RBPi.

        camera_record_start_stop_pin: The GPIO pin, in BCM counting,
        for starting/stopping the recording, connected to GPIO4
        (pin 7) of the OTHER RBPi.

        camera_recording_status_pin: The GPIO pin, in BCM counting,
        for the monitoring the recording status control of the unit,
        connected to GPIO17 (pin 11) of the OTHER RBPi.
        """
        # Functions from the perspective of the other Raspberry:
        # 100 milliseconds LOW on GPIO3 (Pin 5) causes Raspberry to
        # shutdown (or press to start)
        # 1000 milliseconds LOW on GPIO4 (Pin 7) causes Raspberry to
        # start/stop recording
        # GPIO17 (Pin 11) acknowledges the recording (stays HIGH)
        # GPIO27 (Pin 13) is used for the (blinking) LED
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(camera_power_on_off_pin, GPIO.OUT, initial=GPIO.HIGH)
        GPIO.setup(camera_record_start_stop_pin, GPIO.OUT,
                   initial=GPIO.HIGH)
        GPIO.setup(camera_recording_status_pin, GPIO.IN,
                   pull_up_down=GPIO.PUD_DOWN)
        logging.info('Camera unit attached to pins (%i, %i, %i).' %
                     (camera_power_on_off_pin,
                      camera_record_start_stop_pin,
                      camera_recording_status_pin))

    def power_on_off(self):
        """Shutdown or restart the unit.

        Note: Calling this function toggles between on and off.
        You cannot check the actual status."""
        pass
        time.sleep(8)
        return

    def start_recording(self):
        """Starts the recording.

        Returns:
            True: Recording started.
            False: Recording was already ongoing.
        """
        # start blink process
        # gpio
        pass
        return

    def stop_recording(self):
        """Stops the recording.

        Returns:
            True: Recording stopped.
            False: Recording was already stopped.
        """
        # check status
        # stop blink process
        # gpio
        pass
        return

    def get_recording_status(self):
        """Returns the current status of the unit.

        Returns:
            True: Recording ongoing
            False: Not currently recording
        """
        pass
        return


def video_recording(duration=10, video_settings=(1920, 1080, 30)):
    # From Alex Stolz, https://bitbucket.org/alexstolz/strato_media
    # logging.info("recording video with a duration of %d seconds, %s" % (duration, video_settings))
    # p = mp.Process(target=blink, args=(1,))
    # p.start()
    t = time.strftime("%Y-%m-%d_%H-%M-%S")
    with picamera.PiCamera() as camera:
        camera.resolution = video_settings[:2]
        camera.framerate = video_settings[2]
        camera.start_preview()
        camera.preview.alpha = 128
        camera.start_recording(os.path.join(
            config.USB_DIR, "video_"+t+".h264"))
        if ANNOTATE == 2:
            text_size = int(float(config.TEXT_SIZE)/1080 * video_settings[1])
            if text_size > 6 and text_size < 160:
                camera.annotate_text_size = text_size
            else:
                camera.annotate_text_size = TEXT_SIZE
            camera.annotate_text = VIDEO_TEXT % {"time": timestamp.value, "alt": attach_questionmark(altitude.value, altitude_outdated.value), "lat": attach_questionmark(latitude.value, latitude_outdated.value),
            "lon": attach_questionmark(longitude.value, longitude_outdated.value)}
            camera.wait_recording(duration)
        else:
            camera.wait_recording(duration)
        camera.stop_recording()
    # p.terminate()
    return

def take_snapshot(image_resolution=(1920, 1080)):
    # From Alex Stolz, https://bitbucket.org/alexstolz/strato_med
    # logging.info("taking snapshot, %s" % str(image_resolution))
    # p = mp.Process(target=blink, args=(10,))
    # p.start()
    t = time.strftime("%Y-%m-%d_%H-%M-%S")
    with picamera.PiCamera() as camera:
        camera.resolution = image_resolution
        if ANNOTATE >= 1:
            # camera.annotate_background = picamera.Color('black')
            text_size = int(float(TEXT_SIZE)/1080*image_resolution[1])
            if text_size > 6 and text_size < 160:
                camera.annotate_text_size = text_size
            else:
                camera.annotate_text_size = TEXT_SIZE
            camera.annotate_text = IMAGE_TEXT % {"time": timestamp.value, "alt": altitude.value, "lat": latitude.value, "lon": longitude.value}
        camera.exif_tags['IFD0.Copyright'] = 'Copyright (c) 2016 Universitaet der Bundeswehr Muenchen'
        camera.capture(os.path.join(USB_DIR, "image_"+t+".jpg"))
    # p.terminate()
    return


if __name__ == "__main__":
    print "Testing Camera Module"
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(MAIN_CAM_STATUS_LED, GPIO.OUT)
    GPIO.output(MAIN_CAM_STATUS_LED, True)
    video_recording()
    GPIO.output(MAIN_CAM_STATUS_LED, False)
    for status in [True, False]*4:
        GPIO.output(MAIN_CAM_STATUS_LED, status)
        time.sleep(0.5)
    take_snapshot()
    # maybe show image on monitor
    print "Testing Camera Module completed."
