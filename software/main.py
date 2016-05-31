# main.py
# main routines for balloon probe
# very early, pseudocode-style sketch at this point
# basically just a notepad of requirements and ideas


import config

def init():
# Power-On-Self-Test
# - Battery
# - Transmiter
# - Sensors
# Set Time / Date
# Logging
	pass
	return

def run():
    power_saving_mode = False
    # start videoRecording (save in intervals of 5 minutes) thread
    # start measurement thread
    # start telemetry and sstv thread
    # start power monitoring thread (will shut down non-essential functionality in case of near battery failure)
	pass
	return

def image_recording():
# initialize and test equipment
	while True:
	# record HD video for 1 minute and save
    ## see also http://www.netzmafia.de/skripten/hardware/RasPi/RasPi_Kamera.html
	# take HiRes static image and save
    # add basic telemetry data (and save under new filename?)
	# take lowres SSTV Robot 36 image and save
    # add callsign + telemetry data
    # use cv2.rectangle() + cv2.putText() for that
    ## for SSTV loop, see https://github.com/hatsunearu/pisstvpp/blob/master/sstvcatch.py
    # maybe change camera position for SSTV (e.g. ground, horizon, top)
	# check for disk space and power saving
	# add SSTV to telemetry queue
	return

def sensor_recording():
	# add LED
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
