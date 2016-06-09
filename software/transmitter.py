# transmitter.py
# routines for initializing and controlling the DRA818V transceiver module
# see also https://github.com/darksidelemm/dra818/blob/master/DRA818/DRA818.cpp


from config import *

def init():
    '''Initialize and self-test transceiver module'''
    return
    
def send_aprs(aprs_message, power_level = TRANSMISSION_POWER_DEFAULT):
    '''Tunes transceiver to APRS frequency, converts the APRS message to audio, and transmits the audio'''
    transmission_status = False
    # initialize module - set frequency, modulation width, ...
    # DRA818_SQ = None # Squelch detection.. Low -> Audio amplifier on 
    # DRA818_PTT = 1 # Tx/Rx control pin: Low->TX; High->RX
    # DRA818_PD = 1 # Power saving control pin: Low->sleep mode; High->normal mode
    # DRA818_HL = 1 # RF Power Selection: Low->0.5W; floated->1W
    # activate transmission
    # wait (for calibration)
    # send audio
    # wait
    # stop transmission
    return transmission_status 
    
def send_sstv(image_filename, power_level = TRANSMISSION_POWER_DEFAULT):
    '''Tunes transceiver to SSTV frequency and transmits the image from the given filename'''
    transmission_status = False
    # initialize module - set frequency, modulation width, ...
    # DRA818_SQ = None # Squelch detection.. Low -> Audio amplifier on 
    # DRA818_PTT = 1 # Tx/Rx control pin: Low->TX; High->RX
    # DRA818_PD = 1 # Power saving control pin: Low->sleep mode; High->normal mode
    # DRA818_HL = 1 # RF Power Selection: Low->0.5W; floated->1W
    # activate transmission
    # wait (for calibration)
    # send audio
    # wait
    # stop transmission
    # SSTV_ON = True
    # SSTV_FREQUENCY = 144.600
    # SSTV_MODE = "r36" # Robot 36
    # Martin 1: m1 / Martin 2: m2 / Scottie 1: s1 / Scottie 2: s2 / Scottie DX: sdx / Robot 36: r36
    # Values from https://github.com/hatsunearu/pisstvpp
    # SSTV_DELAY = 60 # wait 60 seconds after each transmission
    return transmission_status 

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