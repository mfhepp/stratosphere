#!/usr/bin/env python
# -*- coding: utf-8 -*-

# main.py
# main routines for balloon probe
# very early, pseudocode-style sketch at this point
# basically just a notepad of requirements and ideas
# logging - very important for post-mission analysis

import os
import sys
import time
import threading
import multiprocessing as mp
import subprocess
import datetime as dt

import serial
import gps_info

import serial.tools.list_ports
import RPi.GPIO as GPIO

from config import *
import sensors


def init():
    logging.info("Self-test started.")
    # Set GPIO pins properly, in particular those for the camera satellite units
    GPIO.setmode(GPIO.BOARD)
    
    # all LEDs
    leds = [MAIN_STATUS_LED_PIN,
            MAIN_CAM_STATUS_LED,
            SPARE_STATUS_LED_PIN]
    for led in leds:
        GPIO.setup(led, GPIO.OUT)
    # turn on one by one
    for led in leds:
        GPIO.output(led,True)
        time.sleep(1)
    # flash all four times
    for status in [False, True]*4:
        for led in leds:
            GPIO.output(led,status)
        time.sleep(0.5)
    # turn off
    for led in leds:
        GPIO.output(led,False)
    
    # Power button
    GPIO.setup(POWER_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    current_status = GPIO.input(POWER_BUTTON_PIN)
    logging.info("Power button status: %s" % current_status)

    # Camera unit control pins
    GPIO.setup(CAM1_PWR, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(CAM1_REC, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(CAM1_STATUS, GPIO.IN)
    logging.info("Camera 1 status: %s" % GPIO.input(CAM1_STATUS))
    
    GPIO.setup(CAM2_PWR, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(CAM2_REC, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(CAM2_STATUS, GPIO.IN)
    logging.info("Camera 2 status: %s" % GPIO.input(CAM2_STATUS))

    # Transceiver pins
    GPIO.setup(DRA818_PTT, GPIO.OUT, initial=GPIO.HIGH)  # Tx/Rx control pin: Low->TX; High->RX
    GPIO.setup(DRA818_PD, GPIO.OUT, initial=GPIO.HIGH)  # Power saving control pin: Low->sleep mode; High->normal mode
    GPIO.setup(DRA818_HL, GPIO.OUT, initial=GPIO.LOW)  # RF Power Selection: Low->0.5W; floated->1W
    
    # Initialize and self-test transceiver module
    # Filter and pre-emphasis settings, see also http://www.febo.com/packet/layer-one/transmit.html
    # Also see https://github.com/LZ1PPL/VSTv2/blob/master/VSTv2.ino
    # and https://github.com/darksidelemm/dra818/blob/master/DRA818/DRA818.cpp
    # and https://github.com/darksidelemm/dra818/blob/master/DRA818/examples/DRA818_Basic/DRA818_Basic.ino
   
    ports = list(serial.tools.list_ports.comports())
    logging.info("%i serial ports found:" % len(ports))
    ports_names = "\n\t".join([p.device for p in ports])
    logging.info(ports_names)
    with serial.Serial(SERIAL_PORT_TRANSCEIVER, 9600, bytesize=serial.EIGHTBITS, 
                       parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=1) as tx_ser:
                       
        for i in range(10):
            tx_ser.reset_input_buffer()
            time.sleep(1)
            tx_ser.write("AT+DMOCONNECT\r\n")
            tx_response = ser.readline().strip()
            logging.info('Transceiver response: %s (%i of 10 attempts)' % (tx_response, i))
                if tx_response == "+DMOCONNECT: 0":
                    logging.info("Transceiver found.")
                    break
        else:
            logging.critical("CRITICAL: Transceiver NOT found.")

    # TBD: Initialize Transceiver
    # GROUP SETTING Command (SSTV Frequency)
    # SETFILTER Command
    
    # TBD Test Sensors
    
    # TBD Test Battery Voltage + Current

    return



# GPIO and UART configuration for DORJI DRA818V transceiver module
# OK, checked
SERIAL_PORT_TRANSCEIVER = "/dev/ttyAMA0" # just an example
DRA818_PTT = 38 # GPIO20, Tx/Rx control pin: Low->TX; High->RX
DRA818_PD = 36 # GPIO16, Power saving control pin: Low->sleep mode; High->normal mode
DRA818_HL = 32 # GPIO12, RF Power Selection: Low->0.5W; floated->1W


    
    # Check volume for data (USB)
    # Check / create working directories
    # Search for GPS device on all serial ports at 4800 and 9600 bps
    # Search for UART of DRA818V transceiver on remaining ports
    # Power-On-Self-Test
    # - Turn on logging (sequential number for each run, since we do not have a reliable date at this point)
    # - CPU Temperature
    # - Sensors available
    # - Battery voltage, current, temperature
    # - Sensor readings in reasonable intervals
    # - Transmitter available
    # - GPS available + signal
    # - Set system Time / Date according to GPS, see also http://www.lammertbies.nl/comm/info/GPS-time.html
    # - Camera 1 available and reasonable image
    # - Camera 2 power on and wait for handshake
        # CAM1_ENABLE_PIN = 29 # GPIO5, low for > 1 sec.
        # CAM1_STATUS_PIN = 31 # GPIO6, high = running
    # - Camera 3 power on and wait for handshake
        # CAM2_ENABLE_PIN = 33 # GPIO13, low for > 1 sec.
        # CAM2_STATUS_PIN = 35 # GPIO19, high = running
    # - Send start-up message via APRS twice with no digipeating (No path)
    pass
    return

# run in child process
def update_gps_info(timestamp, altitude, latitude, longitude):
    while continue_gps:
        gps_data, datestamp = gps_info.get_info()
        try:
            if datestamp is not None:
                timestamp.value = datestamp.strftime("%Y-%m-%dT")+str(gps_data.timestamp)+"Z"
            else:
                timestamp.value = str(gps_data.timestamp)
            try:
                os.system("sudo date --set '%s'" % timestamp.value)
            except Exception as msg_time:
                logging.debug("could not set the system time")
                logging.exception(msg_time)
        except Exception as msg:
            timestamp.value = "01-01-1970T00:00:00Z"
            logging.exception(msg)
        try:
            altitude.value = gps_data.altitude
            altitude_outdated.value = 0
        except Exception as msg:
            altitude_outdated.value = 1
            logging.exception(msg)
        try:
            latitude.value = float(gps_data.lat)/100
            latitude_outdated.value = 0
        except Exception as msg:
            latitude_outdated.value = 1
            logging.exception(msg)
        try:
            longitude.value = float(gps_data.lon)/100
            longitude_outdated.value = 0
        except Exception as msg:
            longitude_outdated.value = 1
            logging.exception(msg)
        time.sleep(GPS_POLLTIME)
    return


def gps_monitoring():
    '''Reads GPS device and keeps last position and other data up to date.
    Also updates system clock from GPS time stamp.'''
    
    # Also log all raw NMEA packets with system timestamp in file
    # Also use LED indicator when GPS has receiption (condition tbd; maybe blink whenever new valid position is received)
    return

def image_recording():
# initialize and test equipment
    while True:
        pass
    # record HD video for 1 minute and save
    # see http://picamera.readthedocs.io/en/release-1.10/recipes1.html#overlaying-text-on-the-output
    # see also http://www.netzmafia.de/skripten/hardware/RasPi/RasPi_Kamera.html
    # take HiRes static image and save
    # add basic telemetry data (and save under new filename?)
    # take lowres SSTV Robot 36 image and save
    # add callsign + telemetry data
    # use cv2.rectangle() + cv2.putText() for that or
    ## for SSTV loop, see https://github.com/hatsunearu/pisstvpp/blob/master/sstvcatch.py
    # maybe change camera position for SSTV (e.g. ground, horizon, top)
    # check for disk space and power saving
    # add SSTV to telemetry queue
    return

def sensor_recording():
    # add LED, like so
    # import RPi.GPIO as GPIO ## Import GPIO library
    # GPIO.setmode(GPIO.BOARD) ## Use board pin numbering
    # GPIO.setup(7, GPIO.OUT) ## Setup GPIO Pin 7 to OUT
    # GPIO.output(7,True)
    # time.sleep (0.3)
    # GPIO.output(7,False)
    
    while True:
        Timestamp = currentTime
        # set LED1 = ON
        data_all = ""
        for sensor in sensors:
            data = measure(sensor)
            timedelta = currentTime - Timetstamp
            write (sensor.name, data, timedelta)
            data_all.append(sensor.name, + ":" +" /" +str(data,timedelta))
        # add data to telemetry queue
        
        if battery_level <= minimum:
            power_saving_mode = True
        # set LED1= OFF
    return

def motion_sensor_recording():
    '''Records and saves the motion sensor data.
    This is a separate component due to the much higher rate of measurement'''
    return

def transmission():
    # add LED
    if len(data_queue) >0:
        fetch(element)
        sendAPRS(header, element)
        delay
    if sstv_queue not empty:
        fetch image
        send_sstv(image)
    # tbd: better syncing so that the frequency of transmission does not depend on timing of the execution, i.e. that the delay evens that out.
    # tbd: if queue grows faster than transmission, drop older elements from queue (but keep them on storage device, e.g. while Queue.qsize() > 5: element = Queue.get() )
    # Reminder to self: Check whether APRS channel is busy (collision) will not work in altitude because of too many stations heard. So rather simply send our data.
    # Delay tx by random number of secs after 0:0:0, maybe even vary
    # Reduce APRS path setting depending on altitude
    # Maybe backup high rate APRS on alternate frequency (one transmission every 10 seconds or so)
    # See also http://www.aprs.net/vm/DOS/AIRCRAFT.HTM

def power_monitoring():
    # turn off optional components and tasks if power goes down (tbd: the main Pi can't actually turn off devices)
    # maybe in several steps (first reduce SSTV power, then SSTV rate, then turn SSTV off, then reduce data frequency, then reduce data power, then only GPS with high power every 15 minutes, then shut down all systems
    # also handle power on / off button, maybe use events, see http://raspi.tv/2013/how-to-use-interrupts-with-python-on-the-raspberry-pi-and-rpi-gpio-part-3
    # and http://stackoverflow.com/questions/16143842/raspberry-pi-gpio-events-in-python
    # monitor system health and indicate errors via LED and / or piezo buzzer
    # shut down system in worst case
    # think about how to implement terminate functions for all threads
    # see http://stackoverflow.com/questions/323972/is-there-any-way-to-kill-a-thread-in-python
    # http://stackoverflow.com/questions/6524459/stopping-a-thread-after-a-certain-amount-of-time

def start_secondary_cameras():
    # https://bitbucket.org/alexstolz/strato_media
    return

def main():
    logging.info("System turned on.")
    power_saving_mode = False
    # Test of USB stick is writeable
    try:
        filehandle = open(USB_DIR+"test.txt", 'w' )
    except IOError:
        # this will only be shown on the screen
        logging.info("ERROR: USB Media missing or write-protected")
        logging.info("Trying to mount media.")
        try:
            os.system("sudo ./shell/detect_and_mount_usb.sh")
        except Exception as msg_time:
            logging.debug("FATAL: Could not mount USB media")
            logging.exception(msg_time)
    finally:
        logging.debug("Shutting down system.")
        os.system("sudo shutdown -h now")

    # Test if USB stick has at least 30 GB free capacity
    # TBD
    
    status_ok = init()
    logging.info("Self-test status success: %s")
    if status_ok:
        # start blink process for main LED
        
        # Turn on GPS process
        
        # Turn on power monitoring and down process
        # (will shut down non-essential functionality in case of near battery failure and monitor power button)
        power_monitoring_stop = threading.Event()
        # see also https://pymotw.com/2/threading/
        threading.Thread(target=power_monitoring, args=(1, power_monitoring_stop)).start()
                
        # Turn on both camera modules
        
        # TBC - Okay, up to date
        """DONE 4. CTL CAM TOP und CTL CAM BOTTOM verdrahten
        GPIO17 weiss -> BLACK PIN_BUTTON = 5 # start and shutdown signal
        GPIO27 gelb --> RED PIN_REC = 7 # start/stop recording
        GPIO18 grau -> BROWN PIN_ACK = 11 # acknowledge recording state
        DONE CTL CAM BOTTOM verdrahten
        GPIO22 weiss -> BLACK PIN_BUTTON = 5 # start and shutdown signal
        GPIO24 gelb --> RED PIN_REC = 7 # start/stop recording
        GPIO23 grau -> BROWN PIN_ACK = 11 # acknowledge recording state"""

        CAM1_PWR = 11 # GPIO17
        CAM1_REC = 13 # GPIO13
        CAM1_STATUS = 12 # GPIO18
        CAM2_PWR = 15 # GPIO22
        CAM2_REC = 18 # GPIO14
        CAM2_STATUS = 16 # GPIO23

        threading.Thread(target=gps_monitoring).start()
        
        # start image_recording (save in intervals of 5 minutes) thread
        threading.Thread(target=image_recording).start()

        # start measurement thread
        threading.Thread(target=sensor_recording).start()
        
        # start motion measurement process

        # start telemetry and sstv thread
        threading.Thread(target=transmission).start()

    else:
        while True:
            # Fatal Error LED signal
            # Beep
            # shutdown upon keypress or after time interval
    return
try:
    p = mp.Process(target=update_gps_info, args=(timestamp, altitude, latitude, longitude))
    p.start()
    while True:
        if do_recording:
            # 1. record video
            try:
                video_recording(LENGTH_VIDEO, video_params)
            except Exception as recording_msg:
                logging.exception(recording_msg)
            # 2. capture snapshot
            try:
                take_snapshot(image_params)
            except Exception as capturing_msg:
                logging.exception(capturing_msg)
            # 3. monitor free space left
            try:
                monitor_freespace()
            except Exception as monit_msg:
                logging.exception(monit_msg)
        else: # do not stress CPU
            if do_shutdown:
                bye()
            time.sleep(1)
    p.terminate()
except Exception as msg:
    logging.exception(msg)
    GPIO.cleanup()
    sys.exit(1)

GPIO.cleanup()

logging.debug("clean exit")


if __name__ == "__main__":
    main()
