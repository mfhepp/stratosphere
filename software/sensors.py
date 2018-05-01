#!/usr/bin/env python
# -*- coding: utf-8 -*-

# sensors.py
# $ sudo apt-get install python-w1thermsensor
# Library for accessing the sensors of our probe
# tbd: super-robust error handling
# i2c docs e.g. from
# http://www.raspberry-projects.com/pi/programming-in-python/i2c-programming-in-python/using-the-i2c-interface-2
#
# I. BME280
# $ sudo apt-get update
# $ sudo apt-get install build-essential python-pip python-dev python-smbus git
# $ git clone https://github.com/adafruit/Adafruit_Python_GPIO.git
# $ cd Adafruit_Python_GPIO
# $ sudo python setup.py install
# $ cd ..
# $ git clone https://github.com/adafruit/Adafruit_Python_BME280.git
# $ cd Adafruit_Python_BME280/
# $ sudo python setup.py install
# II. HTU21D
# I2C overlay fix needed, see issue #828:
# https://github.com/raspberrypi/firmware/issues/828
# 1. Download the old module from
# https://drive.google.com/file/d/0B_P-i4u-SLBXb3VlN0N5amVBb1k/view?usp=sharing
# 2. Copy that file into /boot/overlays.
# 3. In /boot/config.txt add the line dtoverlay=i2c1-bcm2708 at the end.
# III. ADC
# sudo apt-get install git build-essential python-dev
# $ cd ~
# $ git clone https://github.com/adafruit/Adafruit_Python_ADS1x15.git
# $ cd Adafruit_Python_ADS1x15
# $ sudo python setup.py install
# IV. IMU
# https://github.com/akimach/LSM9DS1_RaspberryPi_Library
# a) WiringPi
# $ sudo apt-get install libi2c-dev
# $ git clone git://git.drogon.net/wiringPi
# $ cd wiringPi
# $ git pull origin
# $ ./build
# $ cd ..
# b) library
# $ git clone https://github.com/akimach/LSM9DS1_RaspberryPi_Library.git
# $ cd LSM9DS1_RaspberryPi_Library
# $ make
# $ sudo make install


import logging
import config
from shared_memory import *
import time
import datetime
from smbus import SMBus
from subprocess import PIPE, Popen
from w1thermsensor import W1ThermSensor
import Adafruit_BME280
import Adafruit_ADS1x15
import lsm9ds1


class HTU21D():
    """Class for accessing HTU21D sensors via I2C.

    Code taken from https://github.com/jasiek/HTU21D.

    Args:
        busno (int): The I2C bus (0 or 1, default is 1).
        address (byte): The I2C address of the sensor.
    """
    CMD_TRIG_TEMP_HM = 0xE3
    CMD_TRIG_HUMID_HM = 0xE5
    CMD_TRIG_TEMP_NHM = 0xF3
    CMD_TRIG_HUMID_NHM = 0xF5
    CMD_WRITE_USER_REG = 0xE6
    CMD_READ_USER_REG = 0xE7
    CMD_RESET = 0xFE

    def __init__(self, busno=1, address=config.SENSOR_ID_HUMIDITY_EXT):
        self.bus = SMBus(busno)
        self.i2c_address = address

    def read_temperature(self):
        self.reset()
        msb, lsb, crc = self.bus.read_i2c_block_data(
            self.i2c_address, self.CMD_TRIG_TEMP_HM, 3)
        return -46.85 + 175.72 * (msb * 256 + lsb) / 65536

    def read_humidity(self):
        self.reset()
        msb, lsb, crc = self.bus.read_i2c_block_data(
            self.i2c_address, self.CMD_TRIG_HUMID_HM, 3)
        return -6 + 125 * (msb * 256 + lsb) / 65536.0

    def reset(self):
        self.bus.write_byte(self.i2c_address, self.CMD_RESET)


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


def get_adc(channel, gain=1):
    """Returns voltage at from 4-channel ADC ADS115.0

    See https://www.adafruit.com/product/1085.
    Datasheet at http://adafruit.com/datasheets/ads1115.pdf.
    Library at https://github.com/adafruit/Adafruit_Python_ADS1x15
    See also
    https://learn.adafruit.com/raspberry-pi-analog-to-digital-converters/ads1015-slash-ads1115
    Args:
        channel(int): The number of the ADC channel (0..3)
        gain(float): The ADC gain according to the following table:
            1 for reading voltages from 0 to 4.09V.
            2/3 = +/-6.144V
            1 = +/-4.096V
            2 = +/-2.048V
            4 = +/-1.024V
            8 = +/-0.512V
            16 = +/-0.256V
        See table 3 in the ADS1015/ADS1115 datasheet for more info on gain.
    """
    # Create an ADS1115 ADC (16-bit) instance.
    adc = Adafruit_ADS1x15.ADS1115(address=config.SENSOR_ID_ADC)
    return adc.read_adc(channel, gain=gain)


def get_battery_status():
    """Returns  battery status information, i.e.
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
    #
    raw_voltage = get_adc(config.SENSOR_ADC_CHANNEL_BATTERY_VOLTAGE, gain=2)
    # The voltage is measured through a 10k:1k voltage divider,
    # so it will be in 1/11th of the actual voltage and thus in the range
    # from 0V and ca. 1.6 V
    # convert 16 bit integer to float
    raw_voltage = raw_voltage * 2.048 / 32767.0
    # input is just 1/11th of actual voltage
    # 1.017 is a small correction factor
    battery_voltage = raw_voltage * 11.0 * 1.017
    # The current drain from the battery is measured via ACS 712
    # and a 2.2k : 10k voltage divider.
    # At 0 A, the voltage is 2.5 V (1/2 of 5V). For each A of current,
    # this is being increased or decreased by 185 mV.
    raw_voltage = get_adc(config.SENSOR_ADC_CHANNEL_CURRENT, gain=1)
    raw_voltage = raw_voltage * 4.096 / 32767.0
    raw_voltage = raw_voltage * 12.2 / 10  # compensate for voltage divider
    raw_voltage -= 2.5
    # The 5A version of the sensor has a sensitivity of 185mV/A
    discharge_current = raw_voltage / 0.185 * -1
    # Correction factor
    # discharge_current = discharge_current * 442 / 495
    battery_temperature = get_temperature_DS18B20(
        sensor_id=config.SENSOR_ID_BATTERY_TEMP)
    return (battery_voltage, discharge_current, battery_temperature)


def get_temperature_external():
    """Returns the temperature of the external HEL-712-U-0-12-00 sensor
    in degree Celsius"""
    # See
    # http://www.mouser.de/ProductDetail/Honeywell/HEL-712-U-0-12-00/?qs=%2Ffq2y7sSKcIJdgTbHPcmcA%3D%3D
    # The sensor is connected to 3.3V via a 1k resistor.
    # It has a resistance between 500 Ohms at - 100 °C and 3000 Ohms
    # at + 500 °C.
    # The realistic range is between 500R and less than 2k, so the
    # voltage range is between 1.1V and 2.048 V.
    # Calibrate & convert
# TODO: use proper Steinhart-Hart Formula
    # https://arduinodiy.wordpress.com/2015/11/10/measuring-temperature-with-ntc-the-steinhart-hart-formula/
    # https://www.maximintegrated.com/en/app-notes/index.mvp/id/1753
    # https://www.mouser.de/datasheet/2/187/honeywell-sensing-hel-700-series-thin-film-platinu-1137676.pdf
    raw_voltage = get_adc(
        config.SENSOR_ADC_CHANNEL_EXTERNAL_TEMPERATURE, gain=1)
    # raw_voltage = raw_voltage * 2.048 / 32767.0
    r_ptc = 200 / ((32767.0 / raw_voltage) - 1)
    temperature = r_ptc / 1000.0 / 0.0375
    # return external_temperature
    return temperature


def log_IMU_data(logger, sample_rate):
    """Logs the data from the 9-DoF sensor LSM9DS1 to the given logger.

    Args:
        logger: A logger object.
        sample_rate(float): The sample rate in Hz
    """
    duration_of_cycle = 1.0 / sample_rate
    imu = lsm9ds1.lib.lsm9ds1_create()
    lsm9ds1.lib.lsm9ds1_begin(imu)
    if lsm9ds1.lib.lsm9ds1_begin(imu) == 0:
        logging.error('ERROR: IMU LSM9DS1 unit not found.')
        return
    lsm9ds1.lib.lsm9ds1_calibrate(imu)

    while imu_logging_active.value:
        start_time = time.time()
        while lsm9ds1.lib.lsm9ds1_gyroAvailable(imu) == 0:
            pass
        lsm9ds1.lib.lsm9ds1_readGyro(imu)
        while lsm9ds1.lib.lsm9ds1_accelAvailable(imu) == 0:
            pass
        lsm9ds1.lib.lsm9ds1_readAccel(imu)
        while lsm9ds1.lib.lsm9ds1_magAvailable(imu) == 0:
            pass
        lsm9ds1.lib.lsm9ds1_readMag(imu)

        gx = lsm9ds1.lib.lsm9ds1_getGyroX(imu)
        gy = lsm9ds1.lib.lsm9ds1_getGyroY(imu)
        gz = lsm9ds1.lib.lsm9ds1_getGyroZ(imu)

        ax = lsm9ds1.lib.lsm9ds1_getAccelX(imu)
        ay = lsm9ds1.lib.lsm9ds1_getAccelY(imu)
        az = lsm9ds1.lib.lsm9ds1_getAccelZ(imu)

        mx = lsm9ds1.lib.lsm9ds1_getMagX(imu)
        my = lsm9ds1.lib.lsm9ds1_getMagY(imu)
        mz = lsm9ds1.lib.lsm9ds1_getMagZ(imu)

        cgx = lsm9ds1.lib.lsm9ds1_calcGyro(imu, gx)
        cgy = lsm9ds1.lib.lsm9ds1_calcGyro(imu, gy)
        cgz = lsm9ds1.lib.lsm9ds1_calcGyro(imu, gz)

        cax = lsm9ds1.lib.lsm9ds1_calcAccel(imu, ax)
        cay = lsm9ds1.lib.lsm9ds1_calcAccel(imu, ay)
        caz = lsm9ds1.lib.lsm9ds1_calcAccel(imu, az)

        cmx = lsm9ds1.lib.lsm9ds1_calcMag(imu, mx)
        cmy = lsm9ds1.lib.lsm9ds1_calcMag(imu, my)
        cmz = lsm9ds1.lib.lsm9ds1_calcMag(imu, mz)
        # CSV Format:
        # datetime, gyro_x, gyro_y, gyro_z, accel_x, accel_y, accel_z, mag_x, mag_y, mag_z
        # Units: Gyro: deg/s, Accel: Gs, Mag: gauss
        msg = '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s' % (
            datetime.datetime.utcnow().isoformat(),
            cgx, cgy, cgz, cax, cay, caz, cmx, cmy, cmz)
        if logger is not None:
            logger.info(msg)
        else:
            logging.debug(msg)
        delay = duration_of_cycle - (time.time() - start_time)
        if delay > 0:
            time.sleep(delay)


if __name__ == '__main__':
    # add tests / reasonable value check
    logging.basicConfig(level=logging.INFO)
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
    sensor = HTU21D(busno=1, address=config.SENSOR_ID_HUMIDITY_EXT)
    logging.info('Humidity external: %f' % sensor.read_humidity())
    u, i, t = get_battery_status()
    logging.info('Battery status: U=%fV, I=%fA, T=%f°C' % (u, i, t))
    raw_input('Press ENTER to start motion sensor test.')
    imu_logger = logging.getLogger('imu')
    imu_logger.setLevel(logging.DEBUG)
    try:
        p = mp.Process(target=log_IMU_data, args=(imu_logger, 10.0))
        p.start()
        time.sleep(5)
        logging.info('Halting IMU thread.')
        imu_logging_active.value = 0
        time.sleep(1)
        p.join()
    except KeyboardInterrupt:
        logging.info('CTRL-C detected. Halting IMU thread.')
        imu_logging_active.value = 0
        time.sleep(1)
        p.join()
