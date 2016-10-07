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

# settings for recording
LENGTH_VIDEO = 60 # in seconds
video_params = (1920, 1080, 30) # initial video params
image_params = (2592, 1944) # initial image params
RESOLUTIONS = (
    # next_threshold video_params image_params
    (10000000, video_params, image_params),
    (2500000, (1440, 960, 24), (1920, 1080)),
    (500000, (1280, 720, 24), (1920, 1080)),
    (50000, (640, 480, 24), (1920, 1080)),
    (10000, (320, 240, 24), (1280, 720)) # stop at ca. 10MB
)
ANNOTATE = 2 # 0 = no annotation, 1 = annotate images only, 2 = annotate both images and videos
IMAGE_TEXT = "Ballonsonde UniBwM %(time)s\nalt=%(alt)s, lat=%(lat)s, lon=%(lon)s"
VIDEO_TEXT = "Ballonsonde UniBwM %(time)s\nalt=%(alt)s, lat=%(lat)s, lon=%(lon)s"
TEXT_SIZE = 40 # 6..160, default=32
GPS_POLLTIME = 30 # in seconds

timestamp = mp.Array("c", "01-01-1970T00:00:00Z")
altitude = mp.Value("d", 0.0)
altitude_outdated = mp.Value("i", 0)
latitude = mp.Value("d", 0.0)
latitude_outdated = mp.Value("i", 0)
longitude = mp.Value("d", 0.0)
longitude_outdated = mp.Value("i", 0)

altitude.value =  0.0
altitude_outdated.value = 0
latitude.value = 0.0
latitude_outdated.value = 0
longitude.value = 0.0
longitude_outdated.value = 0

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
