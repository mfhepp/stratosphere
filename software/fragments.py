#!/usr/bin/env python
# -*- coding: utf-8 -*-

while True:
     GPIO.output(DRA818_PTT, GPIO.HIGH)
     GPIO.output(DRA818_PD, GPIO.HIGH)
     GPIO.output(DRA818_HL, GPIO.HIGH)
     time.sleep(1)
     GPIO.output(DRA818_HL, GPIO.LOW)
     time.sleep(1)
     GPIO.output(DRA818_PD, GPIO.LOW)
     time.sleep(1)
     GPIO.output(DRA818_PTT, GPIO.LOW)
     time.sleep(1)


while True:
	for sensor in W1ThermSensor.get_available_sensors():
    	print("Sensor %s has temperature %.2f" % (sensor.id, sensor.get_temperature()))

T EXT 		Sensor 0000077147fe has temperature 33.19

BATT 	Sensor  000007717589 has temperature 31.81

T INET Sensor 00000771bf4e has temperature 25.31



		Sensor 00000771bf4e has temperature 25.31

		Sensor 000007717589 has temperature 24.06
		