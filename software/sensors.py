#!/usr/bin/env python
# -*- coding: utf-8 -*-

# sensors.py
# $ sudo apt-get install python-w1thermsensor
# Library for accessing the sensors of our probe
# tbd: super-robust error handling
# i2c docs e.g. from
# http://www.raspberry-projects.com/pi/programming-in-python/i2c-programming-in-python/using-the-i2c-interface-2
#
# BME280
# $ sudo apt-get update
# $ sudo apt-get install build-essential python-pip python-dev python-smbus git
# $ git clone https://github.com/adafruit/Adafruit_Python_GPIO.git
# $ cd Adafruit_Python_GPIO
# $ sudo python setup.py install
# $ cd ..
# $ git clone https://github.com/adafruit/Adafruit_Python_BME280.git
# $ cd Adafruit_Python_BME280/
# $ sudo python setup.py install
import logging
from subprocess import PIPE, Popen
from w1thermsensor import W1ThermSensor
import Adafruit_BME280
import config
import time


def get_temperature_cpu():
    """Returns the temperature of the Raspberry CPU in degree Celsius"""
    # Internal, see
    # https://cae2100.wordpress.com/2012/12/29/reading-cpu-temps-using-python-for-raspberry-pi/
    process = Popen(['vcgencmd', 'measure_temp'], stdout=PIPE)
    output, _error = process.communicate()
    return float(output[output.index('=') + 1:output.rindex("'")])


def get_temperature_DS18B20(sensor_id=''):
    """Returns the temperature of the given DS18B20 sensor in degree Celsius"""
    sensor = W1ThermSensor(W1ThermSensor.THERM_SENSOR_DS18B20, sensor_id)
    return sensor.get_temperature()


def get_temperature_external():
    """Returns the temperature of the external HEL-712-U-0-12-00 sensor
    in degree Celsius"""
    # See
    # http://www.mouser.de/ProductDetail/Honeywell/HEL-712-U-0-12-00/?qs=%2Ffq2y7sSKcIJdgTbHPcmcA%3D%3D
    # Calibrate & convert
    raw_temp = get_adc(config.SENSOR_ADC_CHANNEL_EXTERNAL_TEMPERATURE,
                       gain=0.0)  # gain tbd
    offset = 0.0
    coefficient = 1.0
    exponent = 1.0
    external_temperature = offset + coefficient * raw_temp ** exponent
    # return external_temperature
    return 17.0


def get_pressure_internal_humidity():
    """Returns the atmospheric pressure and the internal relative humidity
    from the BME280 sensor.

    We use this sensor breakout board:
        http://www.watterott.com/index.php?page=product&info=4329
    and this library:
        https://github.com/adafruit/Adafruit_Python_BME280

    Pressure range 300 … 1100 hPa
        (equiv. to +9000…-500 m above/below sea level)
    Relative accuracy ±0.12 hPa, equiv. to ±1 m (950 … 1050hPa @25°C)
    Absolute accuracy typ. ±1 hPa (950 ...1050 hPa, 0 ...+40 °C)

    Returns:
        (pressure (float), humidity(float))
        pressure: The atmospheric pressure in hectopascals (hPa)
        humidity: The relative humidity in percent (0..1)
    """
    sensor = Adafruit_BME280.BME280(
        t_mode=Adafruit_BME280.BME280_OSAMPLE_8,
        p_mode=Adafruit_BME280.BME280_OSAMPLE_8,
        h_mode=Adafruit_BME280.BME280_OSAMPLE_8,
        address=config.SENSOR_ID_PRESSURE)

    # For strange reasons, the library expects reading (1) all three values
    # (2) in the exact order as shown below, even though we just need
    # two of them.
    degrees = sensor.read_temperature()
    pascals = sensor.read_pressure()
    hectopascals = pascals / 100
    humidity = sensor.read_humidity() / 100.0
    return hectopascals, humidity


def get_humidity_external(sensor=None):
    """Returns data from the HTU21D humidity sensor outside
    the probe in percent (1 = 100 %, 0.1 = 10 %)."""
    # see http://www.exp-tech.de/sparkfun-feuchtesensor-breakout-htu21d
    # I2C
    # library in case we use Si7006-A20 Temperature and Humidity sensor
    # instead:
    #     https://github.com/automote/Si7006
    # mind temperature compensation, heating, etc.
    # see also https://github.com/dalexgray/RaspberryPI_HTU21DF
    # SENSOR_ID_HUMIDITY

    return 0.24

def get_motion_sensor_status():
    '''Tests motions sensor'''
    '''Return 0 for False and 1 for True and a short string with
    orientation etc.'''
    # enable
    # read
    # reasonable
    return 0, "Readings as Text, including Compass"


def get_motion_data():
    """Returns all data from the 9 degrees of freedom sensor LSM9DS1"""
    # tbd: Poll rate, format of returned data
    # I2C (or SPI)
    # likely a separate thread with a high polling rate
    # (but mind i2c collisions; maybe use second I2C interface just for
    # this sensor)
    # see https://www.sparkfun.com/products/13284
    # https://cdn.sparkfun.com/assets/learn_tutorials/3/7/3/LSM9DS1_Datasheet.pdf
    # SENSOR_ID_MOTION
    # See also here for converting IMU data to yaw, pitch and roll
    #     https://github.com/micropython-IMU/micropython-fusion
    # and
    #    https://github.com/micropython-IMU (but MicroPython)
    # LSM9DS1 Library:
    #     https://github.com/hgonzale/PiCar/blob/master/src/picar/IMU.py
    # Also interesting library:
    #     https://github.com/mwilliams03/BerryIMU
    # Update 2017-06: The best solution seems to be
    #     https://github.com/hoihu/projects/blob/master/raspi-hat/lsm9ds1.py
    # in combination with
    #     https://github.com/hoihu/projects/blob/master/raspi-hat/fusion.py
    return {}





def get_adc(channel, gain=0):
    """Returns voltage at ADC, utility method for other methods"""
    # Analog via ADS1115 in the form of a https://www.adafruit.com/product/1085
    # datasheet at http://adafruit.com/datasheets/ads1115.pdf
    # Library at https://github.com/adafruit/Adafruit-Raspberry-Pi-Python-Code
    # see also
    # https://learn.adafruit.com/raspberry-pi-analog-to-digital-converters
    # and
    # https://learn.adafruit.com/raspberry-pi-analog-to-digital-converters/ads1015-slash-ads1115
    # SENSOR_ID_ADC
    return 0.0


def get_battery_status():
    """Returns  battery status information, like
    - Voltage in V
    - Current consumption (before DC-DC converters) in A
    - Battery temperature (DS18B20)"""
    # Voltage via simple voltage divider and MCP3204 ADC or directly
    # via ADS1115 in the form of a
    # https://www.adafruit.com/product/1085
    # Current via ACS712/714 + OpAmp + MCP3204 ADC or directly via
    # ADS1115 in the form of a https://www.adafruit.com/product/1085
    # TBD calibration, see also
    # https://cdn-learn.adafruit.com/downloads/pdf/calibrating-sensors.pdf
    raw_voltage = get_adc(config.SENSOR_ADC_CHANNEL_BATTERY_VOLTAGE, gain=0)
    # Simple Exponential Regression model for calibration
    voltage_offset = 0.0
    voltage_coefficient = 1.0
    voltage_exponent = 1.0
    battery_voltage = voltage_offset + voltage_coefficient *\
        raw_voltage ** voltage_exponent
    raw_current = get_adc(config.SENSOR_ADC_CHANNEL_CURRENT, gain=0.0)
    current_offset = 0.0
    current_coefficient = 1.0
    current_exponent = 1.0
    discharge_current = current_offset + current_coefficient *\
        raw_current ** current_exponent
    battery_temperature = get_temperature_DS18B20(
        sensor_id=config.SENSOR_ID_BATTERY_TEMP)
#    return (battery_voltage, discharge_current, battery_temperature)
    return (11.8, 0.36, 32.5)


if __name__ == '__main__':
    # add tests / reasonable value check
    logging.basicConfig(level=logging.DEBUG)
    logging.info('Testing sensors.')
    logging.info('Internal temperature: %f °C' % get_temperature_DS18B20(
        sensor_id=config.SENSOR_ID_INTERNAL_TEMP))
    logging.info('External temperature: %f °C' % get_temperature_DS18B20(
        sensor_id=config.SENSOR_ID_EXTERNAL_TEMP))
    logging.info('External temperature via ADC: %f °C' %
                 get_temperature_external())
    logging.info('Battery temperature: %f °C' % get_temperature_DS18B20(
        sensor_id=config.SENSOR_ID_BATTERY_TEMP))
    logging.info('CPU temperature: %f °C' % get_temperature_cpu())
    pressure, humidity_internal = get_pressure_internal_humidity()
    logging.info('Humidity internal: %f %%' % (humidity_internal * 100))
    logging.info('Atmospheric pressure: %f hPa' % pressure)
    logging.info('Humidity external: %f' % get_humidity_external())
    u, i, t = get_battery_status()
    logging.info('Battery status: U=%fV, I=%fA, T=%f°C' % (u, i, t))
    a, b = get_motion_sensor_status()
    logging.info('Motion sensor status: %s - %s' % (a, b))
    raw_input('Press ENTER to start motion sensor test.')
    while True:
        try:
            logging.info('Motion sensor data: %s [CTRL-C for exit]' %
                         get_motion_data())
            time.sleep(0.5)
        except KeyboardInterrupt:
            print 'CTRL-C detected.'
            break

