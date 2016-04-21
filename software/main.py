# main.py
# main routines for balloon probe
# very early, pseudocode-style sketch at this point
# basically just a notepad of requirements and ideas

def init():
# Power-On-Self-Test
# - Battery
# - Transmiter
# - Sensors
# Set Time / Date
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
	# take HiRes static image and save
	# take lowres SSTV Robot 36 image and save
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

def power_monitoring():
	# turn off optional components and tasks if power goes down
	# maybe in several steps (first reduce SSTV power, then SSTV rate, then turn SSTV off, then reduce data frequency, then reduce data power, then only GPS with high power every 15 minutes, then shut down all systems 
