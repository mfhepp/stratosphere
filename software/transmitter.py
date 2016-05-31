# transmitter.py
# routines for initializing and controlling the DRA818V transceiver module
# see also https://github.com/darksidelemm/dra818/blob/master/DRA818/DRA818.cpp


from config import *

def init():
    '''Initialize and self-test transceiver module'''
    return
    
def send_aprs(filename, power_level = TRANSMISSION_POWER_DEFAULT):
    '''Tunes transceiver to APRS frequency and transmits the audio from the given filename'''
    # initialize module - set frequency, modulation width, ...
    # activate transmission
    # wait (for calibration)
    # send audio
    # wait
    # stop transmission
    return
    
def send_sstv(filename, power_level = TRANSMISSION_POWER_DEFAULT):
    '''Tunes transceiver to SSTV frequency and transmits the audio from the given filename'''
    # initialize module - set frequency, modulation width, ...
    # activate transmission
    # wait (for calibration)
    # send audio
    # wait
    # stop transmission
    return

def generate_aprs_telemetry_config():
    '''Creates Base91 Comment Telemetry message (units, labels, ...)'''
    return ""
    
def generate_aprs(tbd):
    '''Generate APRS string'''
    # increment counter and  make sure that it and all of the telemetry values never get values higher than 8280
    
    # Position lat, long, altitude
    # Raw NMEA strings (particular number of satellites)
    # Ground speed (maybe via NMEA)
    # Channel 1: Pressure
    # Channel 2: Temperature inside
    # Channel 3: Temperature outside
    # Channel 4: Humidity
    # Channel 5: Compass / orientation
    # Binary 1: Camera 1 on/on
    # Binary 2: Camera 2 on/off
    # Binary 3 - 8: tbd
    # TBD
    # Battery voltage
    # Discharge current
    # Ascent / descent rate
    # Battery temperature
    # Maybe motion data (albeit likely to dynamic for APRS)
    # Some data could go into plain comment (e.g. battery voltage, current, battery temperature )
    # For humidity, pressure and outside temperature, also the weather format of APRS could be used (tbc)
    return ""