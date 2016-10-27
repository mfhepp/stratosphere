#!/usr/bin/env python
# -*- coding: utf-8 -*-

# sstv.py
# all routines for generating SSTV images

# TBD
# - set bandwidth / important for narrow-band ham radio transmissions.
# - fine-tune iming as impropper timing results in slanted images

# use https://github.com/hatsunearu/pisstvpp

import subprocess
from shared_memory import *


def convert_image(filename, protocol='r36', rate='22050'):
    '''Createas a WAV file that represents the SSTV modulation for the image at the filename.'''
    #tbd: scale to Robots 36 or other format
    #tbd: test image / try /except
    command = "./pisstvpp -p %s -r%s %s" % (protocol, rate, filename)
    subprocess.call(command, shell=True)
    return filename+".wav"

def play_file(filename):
    #tbd: test if file exists, otherwise skip
    command = "aplay %s" % filename
    subprocess.call(command, shell=True)
    return

def send_audio_beacon():
    # tune to SSTV frequency
    # turn transmitter on
    # wait
    play.file(AUDIO_BEACON)
    # turn transmitter off
    return

def send_sstv(image_filename, power_level = TRANSMISSION_POWER_DEFAULT):
    '''Tunes transceiver to SSTV frequency and transmits the image from the given filename'''
    transmission_status = False
    # initialize module - set frequency, modulation width, ...
    # DRA818_SQ = None # Squelch detection.. Low -> Audio amplifier on
    # DRA818_PTT = 1 # Tx/Rx control pin: Low->TX; High->RX
    # DRA818_PD = 1 # Power saving control pin: Low->sleep mode; High->normal mode
    # DRA818_HL = 1 # RF Power Selection: Low->0.5W; floated->1W
    # activate transmission
    # wait (for calibration)
    # send audio
    # wait
    # stop transmission
    # SSTV_ON = True
    # SSTV_FREQUENCY = 144.600
    # SSTV_MODE = "r36" # Robot 36
    # Martin 1: m1 / Martin 2: m2 / Scottie 1: s1 / Scottie 2: s2 / Scottie DX: sdx / Robot 36: r36
    # Values from https://github.com/hatsunearu/pisstvpp
    # SSTV_DELAY = 60 # wait 60 seconds after each transmission
    return transmission_status

if __name__ == "__main__":
    for rate in ['8000', '16000', '22050', '44100']:
        tmp_file = convert_image('files/sstv-testbild-small.png', rate=rate, protocol='r36')
        play_file(tmp_file)
