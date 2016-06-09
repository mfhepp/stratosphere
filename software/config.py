# config.py
# Configuration settings for the probe and its sensors

# Sensors
SERIAL_PORT_GPS = "/dev/ttyAMA0" # just an example
GPS_ALTITUDE_MODE_CEILING = 10000 # Altitude at which GPS will be switched to Airborne-6 mode with <1g Acceleration; TBD

SERIAL_PORT_TRANSCEIVER = "/dev/ttyAMA0" # just an example
# 3-wire sensors
SENSOR_ID_INTERNAL_TEMP = ""
SENSOR_ID_BATTERY_TEMP = ""
SENSOR_ID_EXTERNAL_TEMP = ""
# I2C sensors
SENSOR_ID_ADC = ""
SENSOR_ID_PRESSURE = ""
SENSOR_ID_HUMIDITY = ""
SENSOR_ID_MOTION = ""
# ADC channels
SENSOR_ADC_CHANNEL_BATTERY_VOLTAGE = 0
SENSOR_ADC_CHANNEL_CURRENT = 1
SENSOR_ADC_CHANNEL_EXTERNAL_TEMPERATURE = 2

# Transceiver
CALLSIGN = "DO1MFH" # insert your mission callsign
APRS_SSID = CALLSIGN + "-11" 
TRANSMISSION_POWER_DEFAULT = 'high' # low = 0.5 W, high = 1 W
APRS_ON = True
APRS_FREQUENCY = 144.800
APRS_RATE = 60 # one transmission per 60 seconds
APRS_PATH = "WIDE2-1" # http://www.arhab.org/aprs
SSTV_ON = True
SSTV_FREQUENCY = 144.600 (?)
SSTV_MODE = "r36" # Robot 36
# Martin 1: m1 / Martin 2: m2 / Scottie 1: s1 / Scottie 2: s2 / Scottie DX: sdx / Robot 36: r36
# Values from https://github.com/hatsunearu/pisstvpp
SSTV_DELAY = 60 # wait 60 seconds after each transmission

# GPIO pin configuration for 1-wire, secondary cameras, power-on, status LEDs, etc.
ONE_WIRE_PIN = 7 # GPIO4 for 1-Wire Devices
POWER_BUTTON_PIN = 37 # GPIO26
MAIN_STATUS_LED_PIN = 40 # GPIO21
SECONDARY_STATUS_LED_PIN = 38 # GPIO20
CAM1_ENABLE_PIN = 29 # GPIO5
CAM1_STATUS_PIN = 31 # GPIO6
CAM2_ENABLE_PIN = 33 # GPIO13
CAM2_STATUS_PIN = 35 # GPIO19
GPS_STATUS_LED_PIN = 11 # GPIO17
PIEZO_SPEAKER_PIN = 13 # GPIO27

# GPIO and UART configuration for DORJI DRA818V transceiver module
SERIAL_PORT_DRA818 = "/dev/ttyAMA1" # just an example
DRA818_SQ = 15 # GPIO22, Squelch detection.. Low -> Audio amplifier on 
DRA818_PTT = 38 # GPIO20, Tx/Rx control pin: Low->TX; High->RX
DRA818_PD = 36 # GPIO16, Power saving control pin: Low->sleep mode; High->normal mode
DRA818_HL = 32 # GPIO12, RF Power Selection: Low->0.5W; floated->1W
# Reserved GPIO pins:
# GPIO2 / 3: SDA1 I2C
# GPIO3 / 5: SCL1 I2C
# GPIO14 / 8: UART TXD
# GPIO15 / 10: UART RXD

# Directories and filenames
LOGFILE_DIR = "/logfiles/"
VIDEO_DIR = "/videos/"
IMAGE_DIR = "/still_images/"
SSTV_DIR = "/sstv/"
DATA_DIR = "/data/"