#!/usr/bin/env python
# -*- coding: utf-8 -*-

# sstv.py
# all routines for generating SSTV images

# TBD
# - set bandwidth / important for narrow-band ham radio transmissions.
# - fine-tune iming as impropper timing results in slanted images

# use https://github.com/hatsunearu/pisstvpp

import subprocess

def convert_image(filename, protocol='r36', rate ='22050'):
    command = "./pisstvpp -p %s -r%s %s" % (protocol, rate, filename)
    subprocess.call(command, shell=True)
    return filename+".wav"

def play_file(filename):
    command = "aplay %s" % filename
    subprocess.call(command, shell=True)
    return

if __name__ == "__main__":
    for rate in ['8000', '16000', '22050', '44100']:
        tmp_file = convert_image('files/sstv-testbild-small.png', rate=rate, protocol='r36')
        play_file(tmp_file)
