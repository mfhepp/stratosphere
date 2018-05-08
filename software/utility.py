# utility.py
# Utility functions

# run in child process

import logging
import time
import os
import subprocess
import RPi.GPIO as GPIO
import config


def blink(led_pin, frequency):
    """Method for child process that lets an LED blink.LED

    Args:
        led_pin (int): The GPIO pin (in BCM counting) of the LED.

        frequency (int or float): The blink frequency in Hz.
    """
    try:
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(led_pin, GPIO.OUT)
        period = 1. / frequency
        while True:
            GPIO.output(led_pin, GPIO.HIGH)
            time.sleep(period / 2)
            GPIO.output(led_pin, GPIO.LOW)
            time.sleep(period / 2)
    finally:
        GPIO.output(led_pin, GPIO.LOW)
    return


def check_and_initialize_USB():
    """Checks and initializes the USB media."""
    # Test if USB stick is writeable
    try:
        fn = os.path.join(config.USB_DIR + 'test.txt')
        filehandle = open(fn, 'w')
        filehandle.close()
    except IOError:
        # This will only be shown on the screen
        logging.error('ERROR: USB Media missing or write-protected.')
        logging.info('Trying to mount USB media.')
        try:
            os.system("sudo ./home/pi/shell/detect_and_mount_usb.sh")
            filehandle = open(fn, 'w')
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
                config.DATA_DIR]:
            path_string = os.path.join(config.USB_DIR + folder)
            if not os.path.exists(path_string):
                os.makedirs(path_string)
                logging.info('Created directory %s' % path_string)
            else:
                logging.info('Found directory %s' % path_string)
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


def check_free_disk_space(minimum=None):
    """Checks whether the USB drive has sufficient free space.

    Args:
        minimum (int): The minimum in bytes.
        If None, config.DISK_SPACE_MINIMUM will be used.
    """
    # http://stackoverflow.com/questions/4260116/find-size-and-free-space-of-the-filesystem-containing-a-given-file
    if minimum is None:
        minimum = config.DISK_SPACE_MINIMUM
    st = os.statvfs(config.USB_DIR)
    free = st.f_bavail * st.f_frsize
    logging.info('Available space on USB stick: %s GB ' %
                 format(float(free) / (1024 * 1024 * 1024), ','))
    if free > minimum:
        return True
    else:
        return False


def disable_usv_charging():
    """Turns of the charging of the S.USV backup power supply, because we
    do not want to charge this emergency unit from the onboard batteries
    during flight."""
    subprocess.call('sudo i2cset -y 1 0x0f 0x29', shell=True)

