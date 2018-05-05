#!/usr/bin/env python
# -*- coding: utf-8 -*-
# shutdown_test.py

import logging
import os
import time
import RPi.GPIO as GPIO
import subprocess
import config


def main():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(config.POWER_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    try:
        while True:
            switch = GPIO.input(config.POWER_BUTTON_PIN)
            if not switch:
                counter = 0
                while not GPIO.input(config.POWER_BUTTON_PIN):
                    counter += 1
                    time.sleep(0.1)
                    if counter > 50:
                        logging.info('Shutting down now.')
                        subprocess.call('sudo shutdown -h now', shell=True)
                counter = 0
            else:
                time.sleep(0.1)
            logging.info('Power switch status: %s [CTRL-C to stop]' % switch)

    except KeyboardInterrupt:
        logging.info('CTRL-C detected.')


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    main()
