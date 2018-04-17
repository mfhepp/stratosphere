#!/usr/bin/env python
# -*- coding: utf-8 -*-

# camera.py
# Library for handling the three probe cameras.
# The software for the external camera units is at
# https://bitbucket.org/alexstolz/strato_med

import logging
import os
import time
import RPi.GPIO as GPIO
import multiprocessing as mp
import picamera
from shared_memory import *
from config import *
import utility


def _attach_questionmark(value, yes):
    if yes:
        return str(value) + "?"
    else:
        return str(value)


class External_Camera(object):
    """Control handler for external camera modules based on
    https://bitbucket.org/alexstolz/strato_med."""

    def __init__(self, camera_power_on_off_pin,
                 camera_record_start_stop_pin,
                 camera_recording_status_pin, name=''):
        """Initializes the external camera module.

        Args:
        camera_power_on_off_pin (int): The GPIO pin, in GPIO.BOARD counting,
        for the power control of the unit, connected to GPIO3 (pin 5)
        of the OTHER RBPi.

        camera_record_start_stop_pin: The GPIO pin, in GPIO.BOARD counting,
        for starting/stopping the recording, connected to GPIO4
        (pin 7) of the OTHER RBPi.

        camera_recording_status_pin: The GPIO pin, in GPIO.BOARD counting,
        for the monitoring the recording status control of the unit,
        connected to GPIO17 (pin 11) of the OTHER RBPi.

        name (str): A name for the unit (mainly for logging).
        """
        # Functions from the perspective of the other Raspberry:
        # 100 milliseconds LOW on GPIO3 (Pin 5) causes Raspberry to
        # shutdown (or press to start).
        # 1000 milliseconds LOW on GPIO4 (Pin 7) causes Raspberry to
        # start/stop recording.
        # GPIO17 (Pin 11) acknowledges the recording (stays HIGH)
        # GPIO27 (Pin 13) is used for the (blinking) LED.
        self.camera_power_on_off_pin = camera_power_on_off_pin
        self.camera_record_start_stop_pin = camera_record_start_stop_pin
        self.camera_recording_status_pin = camera_recording_status_pin
        self.recording_status = False
        if name:
            self.name = name
        else:
            self.name = 'camera unit @ GPIO (%i,%i,%i)' % (
                camera_power_on_off_pin,
                camera_record_start_stop_pin,
                camera_recording_status_pin)
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
        logging.info('Camera: On/off signal sent to %s (low)' % self.name)
        GPIO.output(self.camera_power_on_off_pin, GPIO.LOW)
        time.sleep(.300)
        GPIO.output(self.camera_power_on_off_pin, GPIO.HIGH)
        logging.info('Camera: On/off signal sent to %s (high)' % self.name)
        return

    def start_recording(self):
        """Starts the recording.

        Returns:
            True: Recording start signal sent.
            False: Recording was already ongoing.

        Note: You should manually check via get_recording_status() if
        the camera unit has actually started the recording."""
        if self.recording_status:
            return False
        else:
            logging.info('Camera: Recording signal sent to %s (low)' %
                         self.name)
            GPIO.output(self.camera_record_start_stop_pin, GPIO.LOW)
            time.sleep(1.500)
            GPIO.output(self.camera_record_start_stop_pin, GPIO.HIGH)
            logging.info('Camera: Recording signal sent to %s (high)' %
                         self.name)
            self.recording_status = True
            return True

    def stop_recording(self):
        """Stops the recording.

        Returns:
            True: Recording stop signal sent.
            False: Recording was not running.

        Note: You should manually check via get_recording_status() if
        the camera unit has actually stopped the recording."""
        if not self.recording_status:
            return False
        else:
            logging.info('Camera: Recording stop signal sent to %s (low)' %
                         self.name)
            GPIO.output(self.camera_record_start_stop_pin, GPIO.LOW)
            time.sleep(1.500)
            GPIO.output(self.camera_record_start_stop_pin, GPIO.HIGH)
            logging.info('Camera: Recording stop signal sent to %s (high)' %
                         self.name)
            self.recording_status = False
            return True

    def get_recording_status(self):
        """Returns the current status of the unit.

        Returns:
            True: Recording ongoing
            False: Not currently recording
        """
        return GPIO.input(self.camera_recording_status_pin)


class InternalCamera(object):
    """Represents the internal RBPi camera.

    Based on https://bitbucket.org/alexstolz/strato_media."""

    def video_recording(duration=10, video_settings=(1920, 1080, 30),
                        anotate=True, rotation=0, preview=False):
        """Starts a video recording with the given settings.
        The h264-encoded result will be written to the path set in
        config.USB_DIR/config.VIDEO_DIR. The LED attached to
        config.MAIN_CAM_STATUS_LED will blink at 4 Hz during the recording.

        Args:
            duration (float): The duration of the recording in seconds.
            video_settings (tuple): (image_width, image_height, framerate)
            annotate (boolean): True adds annotation text to the video.
            rotation (int): Rotates the image by 90, 180 or 270 degrees.
            preview (boolean): If True, the recording will be shown on
            the screen.

        Returns:
            filename (str): The path and filename of the recorded video.
        """
        # TODO: Add option for capturing motion vector data:
        # http://picamera.readthedocs.io/en/release-1.10/recipes2.html#recording-motion-vector-data
        if rotation not in [0, 90, 180, 270]:
            raise ValueError('Rotation must be 0, 90, 180 or 270 degrees.')
        t = time.strftime("%Y-%m-%d_%H-%M-%S")
        logging.info("Recording video with a duration of %d seconds [%s]." %
                     (duration, video_settings))
        with picamera.PiCamera() as camera:
            camera.resolution = video_settings[:2]
            camera.framerate = video_settings[2]
            camera.rotation = rotation
            if preview:
                camera.start_preview(alpha=128)  # alpha sets the transparency
            fn = os.path.join(config.USB_DIR, config.VIDEO_DIR, "video_" +
                              t + ".h264")
            camera.start_recording(fn)
            logging.info('Writing to %s.' % fn)
            if annotate:
                text_size = int(float(config.TEXT_SIZE) / 1080 *
                                video_settings[1])
                if text_size > 6 and text_size < 160:
                    camera.annotate_text_size = text_size
                else:
                    camera.annotate_text_size = config.TEXT_SIZE
                camera.annotate_text = VIDEO_TEXT % {
                    "time": timestamp.value,
                    "alt": _attach_questionmark(altitude.value,
                                                altitude_outdated.value),
                    "lat": _attach_questionmark(latitude.value,
                                                latitude_outdated.value),
                    "lon": _attach_questionmark(longitude.value,
                                                longitude_outdated.value)}
            cam_led_process = mp.Process(target=utility.blink,
                                         args=(config.MAIN_CAM_STATUS_LED, 4))
            cam_led_process.start()
            camera.wait_recording(duration)
            camera.stop_recording()
            cam_led_process.terminate()
            cam_led_process.join()
        return fn

    def take_snapshot(image_resolution=(1920, 1080), annotate=True):
        """Takes a still image of the given resolution and writes it as
        a JPG image to config.USB_DIR/config.IMAGE_DIR/image_*.jpg.

        Args:
            image resolution (tuple): The width and height of the image.
            annotate (boolean): True adds annotation text to the video.

        Returns:
            filename (str): The path and filename of the image.
        """
        t = time.strftime("%Y-%m-%d_%H-%M-%S")
        with picamera.PiCamera() as camera:
            camera.resolution = image_resolution
            if annotate:
                # camera.annotate_background = picamera.Color('black')
                text_size = int(float(config.TEXT_SIZE) / 1080 *
                                image_resolution[1])
                if text_size > 6 and text_size < 160:
                    camera.annotate_text_size = text_size
                else:
                    camera.annotate_text_size = config.TEXT_SIZE
                camera.annotate_text = config.IMAGE_TEXT % {
                    "time": timestamp.value,
                    "alt": altitude.value,
                    "lat": latitude.value,
                    "lon": longitude.value}
            camera.exif_tags['IFD0.Copyright'] = config.COPYRIGHT_TEXT
            fn = os.path.join(config.USB_DIR, config.IMAGE_DIR, 'image_' +
                              t + '.jpg')
            logging.info('Capturing %s still image to %s.' %
                         (image_resolution, fn))
            camera.capture(fn)
        return fn


if __name__ == "__main__":
    logging.info('Testing camera modules.')
    cam_top = camera.ExternalCamera(
        config.CAM1_PWR,
        config.CAM1_REC,
        config.CAM1_STATUS)
    status_ok = cam_top.start_recording()
    if status_ok:
        logging.info('Top camera recording started.')
    else:
        logging.error('Problem: Top camera recording already running.')
    for i in range(60):
        if cam_top.get_recording_status():
            logging.info('Top camera recording acknowledgment received.')
            break
        logging.info('Waiting for top camera recording acknowledgment' +
                     ' (%i).' % i)
        time.sleep(1)
    else:
        logging.error('Problem: Top camera recording could not be started.')

    cam_bottom = camera.ExternalCamera(
        config.CAM2_PWR,
        config.CAM2_REC,
        config.CAM2_STATUS)
    status_ok = cam_bottom.start_recording()
    if status_ok:
        logging.info('Bottom camera recording started.')
    else:
        logging.error('Problem: Bottom camera recording already running.')
    for i in range(60):
        if cam_bottom.get_recording_status():
            logging.info('Bottom camera recording acknowledgment received.')
            break
        logging.info('Waiting for bottom camera recording acknowledgment' +
                     ' (%i).' % i)
        time.sleep(1)
    else:
        logging.error('Problem: Bottom camera recording could not be started.')

    logging.info('Starting main camera recording, d = 10 sec.')
    fn = InternalCamera.video_recording(duration=10, preview=True)
    logging.info('Main camera recording saved to %s.' % fn)
    logging.info('Main camera still image capture started.')
    fn = InternalCamera.take_snapshot()
    logging.info('Main camera still image saved to %s.' % fn)
    print "Testing camera modules completed."

