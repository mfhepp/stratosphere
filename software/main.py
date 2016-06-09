# main.py
# main routines for balloon probe
# very early, pseudocode-style sketch at this point
# basically just a notepad of requirements and ideas
# logging - very important for post-mission analysis

import threading
import config

def init():
    # Check / create working directories
    # Power-On-Self-Test
    # - Turn on logging (sequential number for each run, since we do not have a reliable datetime at this point)
    # - CPU Temperature
    # - Sensors available
    # - Battery voltage, current, temperature
    # - Sensor readings in reasonable intervals    
    # - Transmitter available
    # - GPS available + signal
    # - Set system Time / Date according to GPS, see also http://www.lammertbies.nl/comm/info/GPS-time.html
    # - Camera 1 available and reasonable image
    # - Camera 2 power on and wait for handshake
    # - Camera 3 power on and wait for handshake
    # - Send start-up message via APRS twice with no digipeating (No path)
	pass
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
		set LED1 = ON
		data_all = ""
		for sensor in sensors:
			data = measure(sensor)
			timedelta = currentTime - Timetstamp
			write (sensor.name, data, timedelta)
			data_all.append(sensor.name, + ":" +" /" +str(data,timedelta))
		# add data to telemetry queue

		If battery_level <= minimum:
			power_saving_mode = True
		set LED1= OFF
	return

def motion_sensor_recording():
    '''Records and saves the motion sensor data.
    This is a separate component due to the much higher rate of measurement'''
    return

def	transmission():
	# add LED
	if data_queue not empty:
		fetch element
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
	# turn off optional components and tasks if power goes down
	# maybe in several steps (first reduce SSTV power, then SSTV rate, then turn SSTV off, then reduce data frequency, then reduce data power, then only GPS with high power every 15 minutes, then shut down all systems 
    # also handle power on / off button, maybe use events, see http://raspi.tv/2013/how-to-use-interrupts-with-python-on-the-raspberry-pi-and-rpi-gpio-part-3
    # and http://stackoverflow.com/questions/16143842/raspberry-pi-gpio-events-in-python
    # monitor system health and indicate errors via LED and / or piezo buzzer
    # shut down system in worst case
    # think about how to implement terminate functions for all threads
    # see http://stackoverflow.com/questions/323972/is-there-any-way-to-kill-a-thread-in-python
    # http://stackoverflow.com/questions/6524459/stopping-a-thread-after-a-certain-amount-of-time

if __name__ == "__main__":
    power_saving_mode = False
    if init():
        # start power monitoring thread 
        # (will shut down non-essential functionality in case of near battery failure and monitor power button)
        power_monitoring_stop = threading.Event()
        # see also https://pymotw.com/2/threading/
        threading.Thread(target=power_monitoring, args=(1, power_monitoring_stop)).start()
        threading.Thread(target=gps_monitoring).start()
        # start image_recording (save in intervals of 5 minutes) thread
        threading.Thread(target=image_recording).start()
        # start measurement thread
        threading.Thread(target=sensor_recording).start()
        # start telemetry and sstv thread
        threading.Thread(target=transmission).start()
    else:
        while True:
            # Fatal Error LED signal
            # Beep
            # shutdown upon keypress or after time interval

