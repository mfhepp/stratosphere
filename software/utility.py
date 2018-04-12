# utility.py
# Utility functions

# run in child process

import logging
import time
import os
import RPi.GPIO as GPIO
import config


def blink(led_pin, frequency):
    """Method for child process that lets an LED blink.LED

    Args:
        led_pin (int): The GPIO pin (in BCM counting) of the LED.

        frequency (int or float): The blink frequency in Hz.
    """
    period = 1. / frequency
    while True:
        GPIO.output(led_pin, GPIO.HIGH)
        time.sleep(period / 2)
        GPIO.output(led_pin, GPIO.LOW)
        time.sleep(period / 2)
    return


def check_and_initialize_USB():
    """Checks and initializes the USB media."""
    # Test if USB stick is writeable
    try:
        filehandle = open(config.USB_DIR + 'test.txt', 'w')
        filehandle.close()
    except IOError:
        # This will only be shown on the screen
        logging.error('ERROR: USB Media missing or write-protected.')
        logging.info('Trying to mount USB media.')
        try:
            os.system("sudo ./shell/detect_and_mount_usb.sh")
            filehandle = open(config.USB_DIR + 'test.txt', 'w')
            filehandle.close()
        except Exception as msg_time:
            logging.critical('FATAL: Could not mount USB media.')
            logging.exception(msg_time)
            logging.error('FATAL: Shutting down system.')
            os.system('sudo shutdown -h now')
    except Exception as msg_time:
        logging.critical('FATAL: Unknown problem with USB media.')
        logging.exception(msg_time)
        logging.error('FATAL: Shutting down system.')
        os.system('sudo shutdown -h now')
    # Check / create working directories
    try:
        for folder in [
                config.LOGFILE_DIR,
                config.VIDEO_DIR,
                config.IMAGE_DIR,
                config.SSTV_DIR,
                config.DATA_DIR]:
            if not os.path.exists(config.USB_DIR + folder):
                os.makedirs(config.USB_DIR + folder)
                logging.info('Created directory %s' %
                             config.USB_DIR + folder)
            else:
                logging.info('Found directory %s' %
                             config.USB_DIR + folder)
    except Exception as msg_time:
        logging.error('FATAL: Could not create directories.')
        logging.exception(msg_time)
        logging.error('FATAL: Shutting down system.')
        os.system('sudo shutdown -h now')
    # Test if USB stick has at least 16 GB free capacity
    # http://stackoverflow.com/questions/4260116/find-size-and-free-space-of-the-filesystem-containing-a-given-file
    st = os.statvfs(config.USB_DIR)
    free = st.f_bavail * st.f_frsize
    if free > config.DISK_SPACE_MINIMUM:
        logging.info('Available space on USB stick: %s GB ' %
                     format(float(free) / (1024 * 1024 * 1024), ','))
    else:
        logging.error(
            'FATAL: Available space on USB stick below limit:\
            %s GB.' % format(float(free) / (1024 * 1024 * 1024), ','))
        logging.error('FATAL: Shutting down system.')
        os.system('sudo shutdown -h now')
