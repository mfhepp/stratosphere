# sensors.py
# Library for accessing the sensors of our probe
# tbd: super-robust error handling
# i2c docs e.g. from http://www.raspberry-projects.com/pi/programming-in-python/i2c-programming-in-python/using-the-i2c-interface-2


import config

def get_temperature_cpu():
    """Returns the temperature of the Raspberry CPU in degree Celsius"""
    # Internal
    return 0.0
    
def get_temperature_DS18B20(sensor_id=''):
    """Returns the temperature of the given DS18B20 sensor in degree Celsius"""
    # see also https://github.com/timofurrer/w1thermsensor
    # One Wire
    return 0.0

def get_temperature_external():
    """Returns the temperature of the external HEL-712-U-0-12-00 sensor in degree Celsius"""
    # see  http://www.mouser.de/ProductDetail/Honeywell/HEL-712-U-0-12-00/?qs=%2Ffq2y7sSKcIJdgTbHPcmcA%3D%3D
    # Analog
    return 0.0

def get_pressure():
    """Returns the pressure from the AP40N-200KG-Stick pressure sensor"""
    # see http://shop.pewatron.com/search/ap40r-200kg-stick-drucksensor.htm
    # I2C Slave Address 0x28
    return 0.0
    
def get_motion_data():
    """Returns all data from the 9 degrees of freedom sensor LSM9DS1"""
    # tbd: Poll rate, format of returned data
    # I2C (or SPI)
    # likely a separate thread with a high polling rate (but mind i2c collisions; maybe use second I2C interface just for this sensor)
    # see https://www.sparkfun.com/products/13284
    # https://cdn.sparkfun.com/assets/learn_tutorials/3/7/3/LSM9DS1_Datasheet.pdf
    
def get_GPS_data():
    """Return GPS position, altitude, meta-data, and raw NMEA details (number of satelites etc.)"""
    # rate of ascent/ descent
    # see http://www.watterott.com/de/ublox-max-6-max-7-GPS-breakout
    # UART or I2C
    return None
    
def get_humidty():
    """Returns data from the HTU21D humidity sensors inside and outside the probe"""
    # see http://www.exp-tech.de/sparkfun-feuchtesensor-breakout-htu21d
    # I2C
    # mind temperature compensation, heating, etc.

def get_adc(channel, gain=0):
    """Returns voltage at ADC, utility method for other methods"""
    # Analog via ADS1115 in the form of a https://www.adafruit.com/product/1085
    # datasheet at http://adafruit.com/datasheets/ads1115.pdf
    # Library at https://github.com/adafruit/Adafruit-Raspberry-Pi-Python-Code
    # see also https://learn.adafruit.com/raspberry-pi-analog-to-digital-converters
    # and https://learn.adafruit.com/raspberry-pi-analog-to-digital-converters/ads1015-slash-ads1115
    return 0.0
        
def get_battery_status():
    """Returns  battery status information, like
    - Voltage
    - Current consumption (before DC-DC converters)
    - Battery temperature (DS18B20)"""
    # Voltage via simple voltage divider and MCP3204 ADC or directly via ADS1115 in the form of a https://www.adafruit.com/product/1085
    # Current via ACS712/714 + OpAmp + MCP3204 ADC or directly via ADS1115 in the form of a https://www.adafruit.com/product/1085
    # TBD calibration    

