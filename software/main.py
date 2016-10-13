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
import multiprocessing as mp
import subprocess
import datetime as dt

import serial
import serial.tools.list_ports
import RPi.GPIO as GPIO

from config import *
import sensors
import gps_info

def init():
    ok = True
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
            ok = False
            logging.critical("CRITICAL: Transceiver NOT found.")

    # Initialize Transceiver
    GPIO.output(DRA818_PTT, GPIO.HIGH)  # Tx/Rx control pin: Low->TX; High->RX
    GPIO.output(DRA818_PD, GPIO.HIGH)  # Power saving control pin: Low->sleep mode; High->normal mode
    GPIO.output(DRA818_HL, TRANSMISSION_POWER_DEFAULT)  # RF Power Selection: Low->0.5W; floated->1W
    time.sleep(1)
    # GROUP SETTING Command
    # T+DMOSETGROUP=GBW,TFV, RFV,Tx_CTCSS,SQ,Rx_CTCSS<CR><LF>
    # We initially use the SSTV frequency in order to have any spurious 
    # emissions not on the APRS frequency
    command = "AT+DMOSETGROUP=0,%3.4f,%3.4f,0,%i,0\r\n" % (SSTV_FREQUENCY, SSTV_FREQUENCY, SQUELCH)
    tx_ser.write(command)
    tx_response = ser.readline().strip()
    logging.info('Transceiver response: %s' % tx_response)
    if tx_response == "+DMOCONNECT: 0":
         logging.info("Transceiver initialization OK")
    else:
        ok = False
        logging.debug("ERROR: Transceiver initialization failed")
    # SETFILTER Command
    # AT+SETFILTER=PRE/DE-EMPH,Highpass,Lowpass <CR><LF>
    # Note: In the datasheet, there is an extra space after the + sign, but I assume this is in error
    command = "AT+SETFILTER=%1i,%1i,%1i\r\n" % (PRE_EMPHASIS, HIGH_PASS, LOW_PASS)
    tx_ser.write(command)
    tx_response = ser.readline().strip()
    logging.info('Transceiver response: %s' % tx_response)
    if tx_response == "+DMOCONNECT: 0":
         logging.info("Transceiver filter configuration OK")
    else:
        ok = False
        logging.debug("ERROR: Transceiver filter configuration failed")

    # Test Sensors
    internal_temp = sensors.get_temperature_DS18B20(config.SENSOR_ID_INTERNAL_TEMP)
    if -5 < internal_temp < 40:
        logging.info("Internal temperature: %.2f" % internal_temp)
    else:
        ok = False
        logging.debug("WARNING: Internal temperature: %.2f" % internal_temp)
        
    external_temp = sensors.get_temperature_DS18B20(config.SENSOR_ID_EXTERNAL_TEMP)
    if -10 < external_temp < 40:
        logging.info("External temperature: %.2f" % external_temp)
    else:
        ok = False
        logging.debug("WARNING: External temperature: %.2f" % external_temp)
    
    # TBD: Redundant, but nice to have as long as the other sensor functions are just boilerplate code
    battery_temp = sensors.get_temperature_DS18B20(config.SENSOR_ID_BATTERY_TEMP)
    if 10 < battery_temp < 40:
        logging.info("Battery temperature: %.2f" % battery_temp)
    else:
        ok = False
        logging.debug("WARNING: Battery temperature: %.2f" % battery_temp)
        
    cpu_temp = sensors.get_temperature_cpu()
    if 10 < cpu_temp < 40:
        logging.info("CPU temperature: %.2f" % cpu_temp)
    else:
        ok = False
        logging.debug("WARNING: CPU temperature: %.2f" % cpu_temp)

    external_temp_ADC = sensors.get_temperature_external()
    if -10 < external_temp_ADC < 40:
        logging.info("External temperature from ADC: %.2f" % external_temp_ADC)
    else:
        ok = False
        logging.debug("WARNING: External temperature from ADC: %.2f" % external_temp_ADC)

    atmospheric_pressure = get_pressure()
    if 900 < atmospheric_pressure < 1200:
        logging.info("Atmospheric pressure: %.2f" % atmospheric_pressure)
    else:
        ok = False
        logging.debug("WARNING: Atmospheric pressure: %.2f" % atmospheric_pressure)
    
    # Relative humidity, https://en.wikipedia.org/wiki/Relative_humidity
    humidity_internal, humidity_external = get_humidity()
    if 0 < humidity_internal < 1:
        logging.info("Internal relative humidity: %.2f %%" % humidity_internal*100)
    else:
        ok = False
        logging.debug("WARNING: Internal relative humidity: %.2f %%" % humidity_internal*100)
        
    if 0 < humidity_external < 1:
        logging.info("External relative humidity: %.2f %%" % humidity_external*100)
    else:
        ok = False
        logging.debug("WARNING: External relative humidity: %.2f %%" % humidity_external*100)
    
    motion_sensor_status, motion_sensor_message = get_motion_sensor_status()
    if motion_sensor_status:
            logging.info("Motion sensor OK, current values: %s" % motion_sensor_message)
    else:
        ok = False
        logging.debug("WARNING: Motion sensor FAILED, current values: %s" % motion_sensor_message)

    # Test Battery Voltage + Current
    battery_voltage, discharge_current, battery_temp = get_battery_status()
    if battery_voltage > 11:
        logging.info("Battery voltage: %.2f V" % battery_voltage)
    else:
        ok = False
        logging.debug("WARNING: Battery voltage: %.2f V" % battery_voltage)
        
    if 0.1 < discharge_current < 0.75
        logging.info("Discharge current: %.4f A" % discharge_current)
    else:
        ok = False
        logging.debug("WARNING: Discharge current: %.4f A" % discharge_current)
        
    if 10 < battery_temp < 40:
        logging.info("Battery temperature: %.2f" % battery_temp)
    else:
        ok = False
        logging.debug("WARNING: Battery temperature: %.2f" % battery_temp)
    
    # Test if GPS is available
    for i in range(10):
        device, baud = gps_info.get_device_settings()
        if device != None and baud != None:
            logging.info("GPS found at %s with %4i baud" % (device, baud))
            break
    else:
        ok = False
        logging.debug("CRITICIAL: No GPS device found!")
        
    # TBD: Set GPS to FLIGHT mode
    for attempts in range(5):
        if gps_infoset_to_flight_mode():
            break
    else:
        ok = False
        logging.debug('ERROR: Failed to set GPS to flight mode.')

    return ok


def update_gps_info(timestamp, altitude, latitude, longitude):
    '''Method for child process that fetches the GPS data, stores the most recent in global variables, 
    and writes the raw NMEA data to a separate log'''
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
                logging.debug("ERROR: Could not set the system time")
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
    # - Camera 1 available and reasonable image
    # - Camera 2 power on and wait for handshake
        # CAM1_ENABLE_PIN = 29 # GPIO5, low for > 1 sec.
        # CAM1_STATUS_PIN = 31 # GPIO6, high = running
    # - Camera 3 power on and wait for handshake
        # CAM2_ENABLE_PIN = 33 # GPIO13, low for > 1 sec.
        # CAM2_STATUS_PIN = 35 # GPIO19, high = running
    # - Send start-up message via APRS twice with no digipeating (No path)
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
    return True, True
    
def turn_off_usv_charging():
    '''Turns of the charging function of the S.USV backup, because we do not want to 
    charge this secondary backup from our primary cells.'''
    return

def led_blink_process(led_pin, frequency):
    '''Subprocess for blinking LED '''
    period = 1./frequency
    while True:
        GPIO.output(led_pin, GPIO.HIGH)
        time.sleep(0.1)
        GPIO.output(led_pin, GPIO.LOW)
        time.sleep(period)
    return

def main():
    logging.info("System turned on.")
    if not DEBUG:
        turn_off_usv_charging()
        logging.info("USV charging disabled (ok for actual mission)")
    else:
        logging.debug("WARNING: USV charging ENABLED (don't use this for an actual mission")

    power_saving_mode = False
    # Test of USB stick is writeable
    try:
        filehandle = open(USB_DIR+"test.txt", 'w' )
    except IOError:
        # this will only be shown on the screen
        logging.debug("ERROR: USB Media missing or write-protected")
        logging.info("Trying to mount media.")
        try:
            os.system("sudo ./shell/detect_and_mount_usb.sh")
        except Exception as msg_time:
            logging.debug("FATAL: Could not mount USB media")
            logging.exception(msg_time)
    finally:
        logging.debug("Shutting down system.")
        os.system("sudo shutdown -h now")
    # Check / create working directories

    folders = [LOGFILE_DIR, VIDEO_DIR, IMAGE_DIR, SSTV_DIR, DATA_DIR]
    try:
        for folder in folders:
            if not os.path.exists(USB_DIR+folder):
                os.makedirs(USB_DIR+folder)
                logging.info("Created directory %s" % USB_DIR+folder)
            else:
                logging.info("Found directory %s" % USB_DIR+folder)
    except Exception as msg_time:
        logging.debug("FATAL: Could not create directories")
        logging.exception(msg_time)
    finally:
        logging.debug("Shutting down system.")
        os.system("sudo shutdown -h now")
        
    # Test if USB stick has at least 30 GB free capacity
    # http://stackoverflow.com/questions/4260116/find-size-and-free-space-of-the-filesystem-containing-a-given-file
    st = os.statvfs(path)
    free = st.f_bavail * st.f_frsize
    if free > DISK_SPACE_MINIMUM:
        logging.info("Available space on USB stick: %s GB " % format(float(free)/(1024*1024*1024),',')
    else:
        logging.debug("Warning: Available space on USB stick below limit: %s GB " % format(float(free)/(1024*1024*1024),',')
        
    # Run power-on-self-test and initialize peripherals
    status_ok = init()
    logging.info("Self-test status success: %s")
    
    # Wait for GPS to receive signal
    # GPS signal
    # - Set system Time / Date according to GPS, see also http://www.lammertbies.nl/comm/info/GPS-time.html
    
    if status_ok:
        # start second and third camera
        cam1, cam2 = start_secondary_cameras()
        
        # start blink process for main LED
        
        # led_blink_process(led_pin, frequency)
        p = mp.Process(target=led_blink_process, args=(MAIN_STATUS_LED_PIN, 1))
        p.start()
        
        try:
            # Start GPS process
            gps_process = mp.Process(target=update_gps_info, args=(timestamp, altitude, latitude, longitude))
            gps_process.start()
            
            # Start data collection
            data_collection_process = mp.Process(target=data_collection, args=())
            data_collection_process.start()
            
            # start
            motion_recording_process = mp.Process(target=motion_recording, args=())
            motion_recording_process.start()
            
            # start power management and power_down switch
            pwr_management_process = mp.Process(target=pwr_management, args=())
            pwr_management_process.start()
            GPIO.add_event_detect(PIN_REC, GPIO.FALLING, bouncetime=500)
            GPIO.add_event_callback(PIN_REC, start_stop_recording)
            
            
            while True:
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


        
        # Turn on GPS process
        
        # Turn on power monitoring and down process
        # (will shut down non-essential functionality in case of near battery failure and monitor power button)
        power_monitoring_stop = threading.Event()
        # see also https://pymotw.com/2/threading/
        threading.Thread(target=power_monitoring, args=(1, power_monitoring_stop)).start()
                
        # Turn on both camera modules
        start_secondary_cameras():
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
