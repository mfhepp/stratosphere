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
from random import randint
import serial
import serial.tools.list_ports
from picamera import PiCamera
import RPi.GPIO as GPIO
from config import *
import sensors
import gps_info

from shared_memory import *

def init():
    '''This routine initalizes and tests all on-board sensors and equipment.
    The return value is a boolean value: True = OK, False =  Errors. '''
    ok = True
    logging.info("Self-test started.")
    # Set GPIO pins properly, in particular those for the independent camera units
    GPIO.setmode(GPIO.BOARD)

    # All LEDs
    leds = [MAIN_STATUS_LED_PIN,
            MAIN_CAM_STATUS_LED,
            SPARE_STATUS_LED_PIN]
    for led in leds:
        GPIO.setup(led, GPIO.OUT)
    # Turn on one by one
    for led in leds:
        GPIO.output(led,True)
        time.sleep(1)
    # Flash all of them four times
    for status in [False, True]*4:
        for led in leds:
            GPIO.output(led,status)
        time.sleep(0.5)
    # Turn all off
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
            logging.info('Transceiver command: AT+DMOCONNECT')
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
    # We initially use the SSTV frequency in order to make sure that any spurious
    # transmissions are not on the APRS frequency
    command = "AT+DMOSETGROUP=0,%3.4f,%3.4f,0,%i,0\r\n" % (SSTV_FREQUENCY, SSTV_FREQUENCY, SQUELCH)
    tx_ser.write(command)
    logging.info('Transceiver command: %s' % command)
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
    logging.info('Transceiver command: %s' % command)
    tx_response = ser.readline().strip()
    logging.info('Transceiver response: %s' % tx_response)
    if tx_response == "+DMOCONNECT: 0":
         logging.info("Transceiver filter configuration OK")
    else:
        ok = False
        logging.debug("ERROR: Transceiver filter configuration failed")

    # Test Sensors
    internal_temp.value = sensors.get_temperature_DS18B20(config.SENSOR_ID_INTERNAL_TEMP)
    if -5 < internal_temp.value < 40:
        logging.info("Internal temperature: %.2f" % internal_temp.value)
    else:
        ok = False
        logging.debug("WARNING: Internal temperature: %.2f" % internal_temp.value)

    external_temp.value = sensors.get_temperature_DS18B20(config.SENSOR_ID_EXTERNAL_TEMP)
    if -10 < external_temp.value < 40:
        logging.info("External temperature: %.2f" % external_temp.value)
    else:
        ok = False
        logging.debug("WARNING: External temperature: %.2f" % external_temp.value)

    # TBD: Redundant, but nice to have as long as the other sensor functions are just boilerplate code
    battery_temp.value = sensors.get_temperature_DS18B20(config.SENSOR_ID_BATTERY_TEMP)
    if 10 < battery_temp.value < 40:
        logging.info("Battery temperature: %.2f" % battery_temp.value)
    else:
        ok = False
        logging.debug("WARNING: Battery temperature: %.2f" % battery_temp.value)

    cpu_temp.value = sensors.get_temperature_cpu()
    if 10 < cpu_temp.value < 40:
        logging.info("CPU temperature: %.2f" % cpu_temp.value)
    else:
        ok = False
        logging.debug("WARNING: CPU temperature: %.2f" % cpu_temp.value)

    external_temp_ADC.value = sensors.get_temperature_external()
    if -10 < external_temp_ADC.value < 40:
        logging.info("External temperature from ADC: %.2f" % external_temp_ADC.value)
    else:
        ok = False
        logging.debug("WARNING: External temperature from ADC: %.2f" % external_temp_ADC.value)

    atmospheric_pressure.value = get_pressure()
    if 900 < atmospheric_pressure.value < 1200:
        logging.info("Atmospheric pressure: %.2f" % atmospheric_pressure.value)
    else:
        ok = False
        logging.debug("WARNING: Atmospheric pressure: %.2f" % atmospheric_pressure.value)

    # Relative humidity, https://en.wikipedia.org/wiki/Relative_humidity
    humidity_internal.value, humidity_external.value = get_humidity()
    if 0 < humidity_internal.value < 1:
        logging.info("Internal relative humidity: %.2f %%" % humidity_internal.value*100)
    else:
        ok = False
        logging.debug("WARNING: Internal relative humidity: %.2f %%" % humidity_internal.value*100)

    if 0 < humidity_external.value < 1:
        logging.info("External relative humidity: %.2f %%" % humidity_external.value*100)
    else:
        ok = False
        logging.debug("WARNING: External relative humidity: %.2f %%" % humidity_external.value*100)

    motion_sensor_status.value, motion_sensor_message.value = get_motion_sensor_status()
    if motion_sensor_status.value:
            logging.info("Motion sensor OK, current values: %s" % motion_sensor_message.value)
    else:
        ok = False
        logging.debug("WARNING: Motion sensor FAILED, current values: %s" % motion_sensor_message.value)

    # Test Battery Voltage + Current
    battery_voltage.value, discharge_current.value, battery_temp.value = get_battery_status()
    if battery_voltage.value > 11:
        logging.info("Battery voltage: %.2f V" % battery_voltage.value)
    else:
        ok = False
        logging.debug("WARNING: Low battery voltage: %.2f V" % battery_voltage.value)

    if 0.1 < discharge_current.value < 0.75:
        logging.info("Discharge current: %.4f A" % discharge_current.value)
    else:
        ok = False
        logging.debug("WARNING: Discharge current: %.4f A" % discharge_current.value)

    if 10 < battery_temp.value < 40:
        logging.info("Battery temperature: %.2f" % battery_temp.value)
    else:
        ok = False
        logging.debug("WARNING: Battery temperature: %.2f" % battery_temp.value)

    # Test if GPS is available
    for i in range(10):
        device, baud = gps_info.get_device_settings()
        if device != None and baud != None:
            logging.info("GPS found at %s with %4i baud" % (device, baud))
            break
    else:
        ok = False
        logging.debug("CRITICIAL: No GPS device found!")

    # Set GPS to FLIGHT mode so that it will work in high altitudes
    for attempts in range(5):
        if gps_info.set_to_flight_mode():
            break
    else:
        ok = False
        logging.debug('ERROR: Failed to set GPS to flight mode.')
    
    # Test if camera 1 available and returns a reasonable image
    try:
        logging.info("Testing main camera unit.")
        camera = PiCamera()
        camera.start_preview()
        sleep(10)
        camera.stop_preview()
        logging.info("Main camera unit OK.")
    except Exception as msg:
        logging.debug("ERROR: Main camera unit cannot be initialized")
        logging.exception(msg)
        
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
            latitude_direction.value = str(gps_data.lat_dir)
            latitude_outdated.value = 0
        except Exception as msg:
            latitude_outdated.value = 1
            logging.exception(msg)
        try:
            longitude.value = float(gps_data.lon)/100
            longitude_direction.value = str(gps_data.long_dir)
            longitude_outdated.value = 0
        except Exception as msg:
            longitude_outdated.value = 1
            logging.exception(msg)
        # time.sleep(GPS_POLLTIME)
    return


def sensor_recording():
    '''Records time-stamped sensor data for all sensors except for the 9-axis motion sensors'''
    while True:
        try:
            start_time = time.time()
            GPIO.output(SPARE_STATUS_LED_PIN, GPIO.HIGH)
            internal_temp.value = sensors.get_temperature_DS18B20(config.SENSOR_ID_INTERNAL_TEMP)
            external_temp.value = sensors.get_temperature_DS18B20(config.SENSOR_ID_EXTERNAL_TEMP)
            external_temp_ADC.value = sensors.get_temperature_external()
            cpu_temp.value = sensors.get_temperature_cpu()
            battery_voltage.value, discharge_current.value, battery_temp.value = get_battery_status()
            atmospheric_pressure.value = get_pressure()
            humidity_internal.value, humidity_external.value = get_humidity()
            motion_sensor_status.value, motion_sensor_message.value = get_motion_sensor_status()
            data_msg = 'LAT=%.4f,\
                LONG=%.4f,\
                ALT=%.2f,\
                T_INT=%.2f,\
                T_EXT=%.2f,\
                T_EXT_ADC=%.2f,\
                T_CPU=%.2f,\
                BATT_U=%.2f,\
                BATT_I=%.4f,\
                BATT_T=%.2f,\
                ATM=%.2f,\
                HUMID_INT=%.3f,\
                HUMID_EXT=%.3f,\
                ORIENTATION=%s' % (latitude.value, longitude.value, altitude.value,
                internal_temp.value, external_temp.value, external_temp_ADC.value, cpu_temp.value,
                battery_voltage.value, discharge_current.value, battery_temp.value,
                atmospheric_pressure.value, humidity_internal.value, humidity_external.value,
                motion_sensor_message.value)
            datalogger.info(data_msg)
            time.sleep(0.3)
            GPIO.output(SPARE_STATUS_LED_PIN, GPIO.LOW)
            delay = 1.0/POLL_FREQUENCY - (time.time() - start_time)
            if delay>0:
                time.sleep(delay)
        except Exception as msg:
            logging.exception(msg)
    return

def motion_sensor_recording():
    '''Records and saves the motion sensor data.
    This is a separate component due to the much higher rate of measurement'''
    return

def transmission():
    sstv = True
    telemetry_meta_data_counter = 10
    while True:
        # add LED
        # Step 1: Send APRS messages (likely two because we have too much data)
        start_time = time.time()
        # Delay tx by random number of 0..10 secs in order to minimize collisions on the APRS frequency
        time.sleep(random.random*10)
        # Create message
        aprs_msg = transmitter.generate_aprs()
        aprs_weather_msg = transmitter.generate_aprs_weather()
        logging.info("APRS message: %s" % aprs_msg)
        logging.info("APRS weather message: %s" % aprs_weather_msg)

        # Every ten APRS transmissions will include telemetry meta-data
        if telemetry_meta_data_counter == 0:
            aprs_telemetry_msg = aprs.generate_aprs_telemetry_config()
            aprs.send_aprs(aprs_telemetry_msg)
            logging.info("APRS telemetry meta-data sent: %s" % aprs_telemetry_msg)
            telemetry_meta_data_counter = 10
        else:
            telemetry_meta_data_counter -= 1

        # Convert APRS messages to sound files and transmit sound files
        aprs.send_aprs(aprs_msg)
        aprs.send_aprs(aprs_weather_msg)

        # Send audio beacon on SSTV frequency
        time.sleep(2)
        sstv.send_audio_beacon()
        time.sleep(2)

        # Step 2: Send latest picture as SSTV every other minute
        if sstv:
            # transmit SSTV
            TBD: send_sstv()
            sstv = False
        else:
            sstv = True

        delay = APRS_RATE - (time.time() - start_time)  # Remaining seconds for a 1-minute cycle
        if delay > 0:
            time.sleep(delay)

    # Reminder to self: Check whether APRS channel is busy (collision) will not work in altitude because of too many stations heard. So rather simply send our data.
    # Possible enhancement: Reduce APRS path setting depending on altitude
    # Possible enhancement: Send APRS on alternate frequency (one transmission every 10 seconds or so)
    # See also http://www.aprs.net/vm/DOS/AIRCRAFT.HTM
    return

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
    # if battery_level <= minimum:
    #    power_saving_mode = True
    pass
    return

def start_secondary_cameras():
    # https://bitbucket.org/alexstolz/strato_media
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
    # Die sekundäre Versorgung (Pufferbetrieb) der S.USV kann über folgenden I2C-Befehl deaktiviert werden:
    # sudo i2cset -y 1 0x0f 0x31 – Der Befehl 0x31 signalisiert der S.USV den sekundären Modus zu beenden und in den primären Modus zu schalten.

    return

def led_blink_process(led_pin, frequency=1):
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
        logging.info("USV charging disabled (OK for actual mission)")
    else:
        logging.debug("WARNING: USV charging ENABLED (Don't use this for an actual mission")

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
        logging.info("Available space on USB stick: %s GB " % format(float(free)/(1024*1024*1024),','))
    else:
        logging.debug("Warning: Available space on USB stick below limit: %s GB " % format(float(free)/(1024*1024*1024),','))

    # Run power-on-self-test and initialize peripherals
    status_ok = init()
    if status_ok:
        logging.info("="*60+"\nSelf-test status: OK\n"+"="*60)
        GPIO.output(MAIN_STATUS_LED_PIN, GPIO.HIGH)
        aprs.send_aprs('%s>%s:>Self-test status: OK') % (APRS_SSID, APRS_SSID)
        for in range(3):
            sstv.send_audio_beacon(file='files/selftest-ok.wav')
            time.sleep(2)
    else:
        logging.debug("="*60+"\nFATAL: Self-test status: FAILURE\n"+"="*60)
        # The following would be nice, but since we do not know the state of the transceiver,
        # this is risky (it might have been tuned to a wrong frequency)
        # sstv.send_audio_beacon(file='files/selftest-failed.wav')
        # aprs.send_aprs('%s>%s:>Self-test status: FAILURE') % (APRS_SSID, APRS_SSID)
        logging.debug("Shutting down system.")
        os.system("sudo shutdown -h now")

    # Wait for GPS to receive signal
    logging.info("Waiting for valid GPS position data (this may take up to several minutes)")

    # GPS signal
    for i in range(300):  # time-out after 300 secs / 5 minutes
        gps_msg, gps_date = gps_info.get_info()
        if 47 <= msg.lat <= 49 and 7 <= msg.lon <= 11 and 0 <= msg.altitude <= 800:
            info.logging('Valid GPS position detected')
            break
        time.sleep(1)
    else:
        info.debug('FATAL: No valid GPS position detected after 300 seconds.')
        sstv.send_audio_beacon(file='files/selftest-failed.wav')
        time.sleep(2)
        aprs.send_aprs('%s>%s:>FATAL: No valid GPS position detected after 300 seconds.') % (APRS_SSID, APRS_SSID)
        logging.debug("Shutting down system.")
        os.system("sudo shutdown -h now")

    # Set system Time / Date according to GPS, see also http://www.lammertbies.nl/comm/info/GPS-time.html
    update_gps_info()

    # Start second and third camera
    cam1, cam2 = start_secondary_cameras()

    # Start blink process for main LED
    p = mp.Process(target=led_blink_process, args=(MAIN_STATUS_LED_PIN, 1))
    p.start()

    try:
        # Start GPS process
        gps_process = mp.Process(target=update_gps_info, args=(timestamp, altitude, latitude, longitude))
        gps_process.start()

        # Start data collection
        data_collection_process = mp.Process(target=data_collection, args=())
        data_collection_process.start()

        # Start motion data recording
        motion_recording_process = mp.Process(target=motion_recording, args=())
        motion_recording_process.start()

        # Start transmission process
        transmission_process = mp.Process(target=motion_recording, args=())
        motion_recording_process.start()

        # Start power management and power_down switch
        # (will shut down non-essential functionality in case of near battery failure and monitor power button)
        pwr_management_process = mp.Process(target=pwr_management, args=())
        pwr_management_process.start()
        GPIO.add_event_detect(POWER_BUTTON_PIN, GPIO.FALLING, bouncetime=500)
        GPIO.add_event_callback(POWER_BUTTON_PIN, power_down_system)

        while True:
            # 1. record video
            # see http://picamera.readthedocs.io/en/release-1.10/recipes1.html#overlaying-text-on-the-output
            # see also http://www.netzmafia.de/skripten/hardware/RasPi/RasPi_Kamera.html
            # take HiRes static image and save
            # add basic telemetry data (and save under new filename?)
            # take lowres SSTV Robot 36 image and save
            # add callsign + telemetry data
            # use cv2.rectangle() + cv2.putText() for that or
            ## for SSTV loop, see https://github.com/hatsunearu/pisstvpp/blob/master/sstvcatch.py
            # check for disk space and power saving
            # add SSTV to telemetry queue
            try:
                camera.video_recording(LENGTH_VIDEO, video_params)
            except Exception as recording_msg:
                logging.exception(recording_msg)
            # 2. capture snapshot
            try:
                camera.take_snapshot(image_params)
            except Exception as capturing_msg:
                logging.exception(capturing_msg)
    except Exception as msg:
        logging.exception(msg)
        power_down_system()

def power_down_system():
    # Try to kill all subprocesses
    try:
        for p in [gps_process, data_collection_process, motion_recording_process, transmission_process, pwr_management_process]:
            logging.info('Trying to shut down %s' % p)
            p.kill()
    except Exception as shutdown_msg:
        logging.debug(shutdown_msg)

    # Turn off transceiver
    GPIO.output(DRA818_PTT, GPIO.HIGH)  # Tx/Rx control pin: Low->TX; High->RX
    GPIO.output(DRA818_PD, GPIO.LOW)  # Power saving control pin: Low->sleep mode; High->normal mode
    GPIO.output(DRA818_HL, GPIO.LOW)  # RF Power Selection: Low->0.5W; floated->1W

    if not DEBUG:
        logging.debug("Shutting down system.")
        os.system("sudo shutdown -h now")
    # GPIO.cleanup() better avoid that so that we can rest assured that the transmitter remains off
    sys.exit(1)  # redundant

if __name__ == "__main__":
    main()
