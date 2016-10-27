#!/usr/bin/env python
# -*- coding: utf-8 -*-

# sensors.py
# Library for accessing the sensors of our probe
# tbd: super-robust error handling
# i2c docs e.g. from http://www.raspberry-projects.com/pi/programming-in-python/i2c-programming-in-python/using-the-i2c-interface-2

from config import *
import picamera

# global imports
import os
import time
import RPi.GPIO as GPIO
import logging
import multiprocessing as mp

from shared_memory import *


def attach_questionmark(value, yes):
    if yes:
        return str(value) + "?"
    else:
        return str(value)

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
        camera.start_recording(os.path.join(USB_DIR, "video_"+t+".h264"))
        if ANNOTATE == 2:
            text_size = int(float(TEXT_SIZE)/1080*video_settings[1])
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
            #camera.annotate_background = picamera.Color('black')
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
    print "Testing Camera Module completed."
