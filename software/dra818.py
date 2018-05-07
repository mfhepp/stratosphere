#!/usr/bin/env python
# -*- coding: utf-8 -*-
# dra818.py
# Library for the DRA818 transceiver module
#
import logging
import os
import time
import RPi.GPIO as GPIO
import serial
import subprocess
import config


class DRA818_Error(Exception):
    """A custom Python exception for signaling severe problems with the
    initialization of the DRA818 unit in the __init__ method.
    """
    pass


def send_command(serial_connection, command):
    """Sends a command string to the DRA818 UART and returns the
    response string.

    Args:
        serial_connection: The PySerial connection object.
        command (str): The command string.

    Returns:
        str: The response string.
    """
    serial_connection.write(command)
    logging.info('Transceiver command sent: %s' % command.strip())
    tx_response = serial_connection.readline().strip()
    logging.info('Transceiver response stripped: %s' % tx_response)
    return tx_response


def _play_audio_file(audio_file_path):
    """Plays the audio file at the given path via the RBPi's current
    audio device.

    Args:
        audio_file_path (str): The absolute or relative path of the
        audio file to be played. The file format must be supported by
        the aplay command.

    Returns:
        True if the command was successful, False in case of any error.
    """
    if os.path.isfile(audio_file_path):
        command = "aplay %s" % audio_file_path
        return_code = subprocess.call(command, shell=True)
        if return_code == 0:
            return True
        else:
            return False
    else:
        return False


class DRA818(object):
    """An object for a DRA818 transceiver module connected to a
    Raspberry Pi via GPIO pins and a serial interface.
    """
    def __init__(self, uart='', ptt_pin=0, power_down_pin=0,
                 rf_power_level_pin=0, frequency=0, squelch_level=0,
                 pre_emphasis=True, high_pass=False, low_pass=False):
        """Return a DRA818 transceiver object.

        Args:
            uart (str): The serial port of the DRA818.
            ptt_pin (int): The GPIO pin for activating the transmission
                (in BCM numbering, e.g. 38 for GPIO20).
            power_down_pin (int): The GPIO pin for power saving
                (in BCM numbering).
            rf_power_level_pin (int): The GPIO pin for the power level
            control (in BCM numbering).
            frequency (float): The inital receive and transmit frequency
                in MHz, e.g. 144.800 for the European APRS frequency.
            squelch_level (int): The initial squelch level (0..8).
            pre_emphasis (boolean): Use pre-emphasis for transmitting
            and de-emphasis for receiving.
            high_pass (boolean): Use high-pass filter for receiving.
            low_pass (boolean): Use low-pass filter for receiving.

        Note: Whether or not pre-emphasis should be used for
        transmitting APRS and SSTV mainly depends on whether the
        expected receiving devices use de-emphasis or not.
        See e.g.
        http://www.tapr.org/pipermail/aprssig/2009-October/031608.html
        """
        self.uart = uart
        self.ptt_pin = ptt_pin
        self.power_down_pin = power_down_pin
        self.rf_power_level_pin = rf_power_level_pin
        self.rx_frequency = frequency
        self.tx_frequency = frequency
        self.squelch_level = squelch_level
        self.pre_emphasis = pre_emphasis
        self.high_pass = high_pass
        self.low_pass = low_pass

        GPIO.setmode(GPIO.BOARD)
        # Tx/Rx control pin: Low->TX; High->RX
        GPIO.setup(self.ptt_pin, GPIO.OUT, initial=GPIO.HIGH)
        # Power saving pin: Low->sleep mode; High->normal mode
        GPIO.setup(self.power_down_pin, GPIO.OUT, initial=GPIO.HIGH)
        # RF Power Selection: Low->0.5W; floated->1W
        GPIO.setup(self.rf_power_level_pin, GPIO.OUT,
                   initial=GPIO.LOW)
        logging.info('Searching transceiver at %s' % self.uart)
        time.sleep(1)
        with serial.Serial(self.uart, 9600,
                           bytesize=serial.EIGHTBITS,
                           parity=serial.PARITY_NONE,
                           stopbits=serial.STOPBITS_ONE,
                           timeout=1) as dra818_uart:
            time.sleep(1)
            dra818_uart.reset_output_buffer()
            time.sleep(1)
            dra818_uart.reset_input_buffer()
            time.sleep(2)
            for i in range(10):
                time.sleep(1)
                logging.info('Init command attempt %i of 10' % i)
                response = send_command(dra818_uart, 'AT+DMOCONNECT\r\n')
                if response == '+DMOCONNECT:0':
                    logging.info('Transceiver found.')
                    break
            else:
                logging.critical("CRITICAL: Transceiver NOT found.")
                dra818_uart.close()
                raise DRA818_Error

            # Now initialize and self-test transceiver module.
            # For filter and pre-emphasis settings, see also
            # http://www.febo.com/packet/layer-one/transmit.html
            # Also see
            # https://github.com/LZ1PPL/VSTv2/blob/master/VSTv2.ino
            # and
            # https://github.com/darksidelemm/dra818/blob/master/DRA818/DRA818.cpp
            # https://github.com/darksidelemm/dra818/blob/master/DRA818/examples/DRA818_Basic/DRA818_Basic.ino

            # GROUP SETTING Command
            # AT+DMOSETGROUP=GBW,TFV, RFV,Tx_CTCSS,SQ,Rx_CTCSS<CR><LF>
            command = 'AT+DMOSETGROUP=1,%3.4f,%3.4f,0000,%i,0000\r\n' \
                % (self.tx_frequency, self.rx_frequency,
                   self.squelch_level)
            response = send_command(dra818_uart, command)
            if response == '+DMOSETGROUP:0':
                logging.info('Transceiver initialization OK.')
            else:
                logging.debug('ERROR: Transceiver init failed.')
                dra818_uart.close()
                raise DRA818_Error

            # SETFILTER Command
            # AT+SETFILTER=PRE/DE-EMPH,Highpass,Lowpass <CR><LF>
            # Note: In the datasheet, there is an extra space
            # after the + sign, but I assume this is in error
            # Note: On = 0, Off = 0, so we use int(not <boolean>)
            command = 'AT+SETFILTER=%1i,%1i,%1i\r\n' \
                      % (int(not self.pre_emphasis),
                         int(not self.high_pass),
                         int(not self.low_pass))
            response = send_command(dra818_uart, command)
            if response == '+DMOSETFILTER:0':
                logging.info('Transceiver filter configuration OK.')
            else:
                logging.debug('ERROR: Transceiver filter \
                               configuration failed.')
                dra818_uart.close()
                raise DRA818_Error
            dra818_uart.close()

    def start_transmitter(self, full_power=False):
        """Turns on the transmitter.

        Agrs:
            full_power (boolean): True sets the RF power level to the
            maximum of 1 W, False sets it to 0.5W."""
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.power_down_pin, GPIO.OUT, initial=GPIO.HIGH)
        GPIO.output(self.power_down_pin, GPIO.HIGH)
        if full_power:
            # Set rf_power_level_pin to high impedance / floating for 1W
            GPIO.setup(self.rf_power_level_pin, GPIO.IN)
            logging.info('Transceiver power set to 1W/HIGH.')
        else:
            GPIO.setup(self.rf_power_level_pin, GPIO.OUT)
            GPIO.output(self.rf_power_level_pin, GPIO.LOW)
            logging.info('Transceiver power set to 0.5W/LOW.')
        GPIO.output(self.ptt_pin, GPIO.LOW)
        logging.info('Transceiver ON.')
        return

    def stop_transmitter(self):
        """Turns off the transmitter."""
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.power_down_pin, GPIO.OUT, initial=GPIO.HIGH)
        GPIO.output(self.power_down_pin, GPIO.HIGH)
        GPIO.setup(self.ptt_pin, GPIO.OUT, initial=GPIO.HIGH)
# check why the GPIO status is not preserved????
        GPIO.output(self.ptt_pin, GPIO.HIGH)
        logging.info('Transceiver OFF.')
        return

    def set_tx_frequency(self, frequency):
        """Sets the transmission frequency.

        Args:
            frequency (float): The transmit frequency in MHz,
            e.g. 144.800 for the European APRS frequency.
        """
        frequency_old = self.tx_frequency
        self.tx_frequency = frequency
        with serial.Serial(self.uart, 9600,
                           bytesize=serial.EIGHTBITS,
                           parity=serial.PARITY_NONE,
                           stopbits=serial.STOPBITS_ONE,
                           timeout=1) as dra818_uart:
            time.sleep(1)
            dra818_uart.reset_output_buffer()
            time.sleep(1)
            dra818_uart.reset_input_buffer()
            time.sleep(2)
            for i in range(10):
                time.sleep(1)
                logging.info('Init command attempt %i of 10' % i)
                response = send_command(dra818_uart, 'AT+DMOCONNECT\r\n')
                if response == '+DMOCONNECT:0':
                    logging.info('Transceiver found.')
                    break
            else:
                logging.critical("CRITICAL: Transceiver NOT found.")
                dra818_uart.close()
                return False
            # GROUP SETTING Command
            # T+DMOSETGROUP=GBW,TFV, RFV,Tx_CTCSS,SQ,Rx_CTCSS<CR><LF>
            command = 'AT+DMOSETGROUP=1,%3.4f,%3.4f,0000,%i,0000\r\n' \
                      % (self.tx_frequency, self.rx_frequency,
                         self.squelch_level)
            response = send_command(dra818_uart, command)
            if response == '+DMOSETGROUP:0':
                logging.info('Tx frequency set to %f MHz.' %
                             self.tx_frequency)
                dra818_uart.close()
                return True
            else:
                logging.debug('ERROR: Setting Tx frequency failed.')
                self.tx_frequency = frequency_old
                dra818_uart.close()
                return False

    def set_rx_frequency(self, frequency):
        """Sets the receive frequency.

        Args:
            frequency (float): The receive frequency in MHz,
            e.g. 144.800 for the European APRS frequency.
        """
        frequency_old = self.rx_frequency
        self.rx_frequency = frequency
        with serial.Serial(self.uart, 9600,
                           bytesize=serial.EIGHTBITS,
                           parity=serial.PARITY_NONE,
                           stopbits=serial.STOPBITS_ONE,
                           timeout=1) as dra818_uart:
            time.sleep(1)
            dra818_uart.reset_output_buffer()
            time.sleep(1)
            dra818_uart.reset_input_buffer()
            time.sleep(2)
            for i in range(10):
                time.sleep(1)
                logging.info('Init command attempt %i of 10' % i)
                response = send_command(dra818_uart,
                                        'AT+DMOCONNECT\r\n')
                if response == '+DMOCONNECT:0':
                    logging.info('Transceiver found.')
                    break
            else:
                logging.critical("CRITICAL: Transceiver NOT found.")
                dra818_uart.close()
                return False
            # GROUP SETTING Command
            # T+DMOSETGROUP=GBW,TFV, RFV,Tx_CTCSS,SQ,Rx_CTCSS<CR><LF>
            command = 'AT+DMOSETGROUP=1,%3.4f,%3.4f,0000,%i,0000\r\n' \
                      % (self.tx_frequency, self.rx_frequency,
                         self.squelch_level)
            response = send_command(dra818_uart, command)
            if response == '+DMOSETGROUP:0':
                logging.info('Rx frequency set to %f MHz.' %
                             self.rx_frequency)
                dra818_uart.close()
                return True
            else:
                logging.debug('ERROR: Setting Rx frequency failed.')
                self.rx_frequency = frequency_old
                dra818_uart.close()
                return False

    def set_squelch(self, squelch_level):
        """Sets the squelch level.

        Args:
            squelch_level (int): The initial squelch level (0..8).
        """
        if squelch_level > 8 or squelch_level < 0:
            return False
        squelch_old = self.squelch_level
        self.squelch_level = squelch_level
        with serial.Serial(self.uart, 9600,
                           bytesize=serial.EIGHTBITS,
                           parity=serial.PARITY_NONE,
                           stopbits=serial.STOPBITS_ONE,
                           timeout=1) as dra818_uart:
            time.sleep(1)
            dra818_uart.reset_output_buffer()
            time.sleep(1)
            dra818_uart.reset_input_buffer()
            time.sleep(2)
            for i in range(10):
                time.sleep(1)
                logging.info('Init command attempt %i of 10' % i)
                response = send_command(dra818_uart,
                                        'AT+DMOCONNECT\r\n')
                if response == '+DMOCONNECT:0':
                    logging.info('Transceiver found.')
                    break
            else:
                logging.critical("CRITICAL: Transceiver NOT found.")
                dra818_uart.close()
                return False
            # GROUP SETTING Command
            # T+DMOSETGROUP=GBW,TFV, RFV,Tx_CTCSS,SQ,Rx_CTCSS<CR><LF>
            command = 'AT+DMOSETGROUP=1,%3.4f,%3.4f,0000,%i,0000\r\n' \
                      % (self.tx_frequency, self.rx_frequency,
                         self.squelch_level)
            response = send_command(dra818_uart, command)
            if response == '+DMOSETGROUP:0':
                logging.info('Squelch level to %i.' %
                             self.squelch_level)
                dra818_uart.close()
                return True
            else:
                logging.debug('ERROR: Setting squelch level failed.')
                self.squelch_level = squelch_old
                dra818_uart.close()
                return False

    def set_filters(self, pre_emphasis=None, high_pass=None,
                    low_pass=None):
        """Sets the filter configuration of the DRA818.the

        Args:
            pre_emphasis (boolean): Use pre-emphasis for transmitting
            and de-emphasis for receiving.
            high_pass (boolean): Use high-pass filter for receiving.
            low_pass (boolean): Use low-pass filter for receiving.
        """
        if pre_emphasis is None:
            pre_emphasis = self.pre_emphasis
        if high_pass is None:
            high_pass = self.high_pass
        if low_pass is None:
            low_pass = self.low_pass
        # SETFILTER Command
        # AT+SETFILTER=PRE/DE-EMPH,Highpass,Lowpass <CR><LF>
        # Note: In the datasheet, there is an extra space
        # after the + sign, but I assume this is in error
        with serial.Serial(self.uart, 9600,
                           bytesize=serial.EIGHTBITS,
                           parity=serial.PARITY_NONE,
                           stopbits=serial.STOPBITS_ONE,
                           timeout=1) as dra818_uart:
            time.sleep(1)
            dra818_uart.reset_output_buffer()
            time.sleep(1)
            dra818_uart.reset_input_buffer()
            time.sleep(2)
            for i in range(10):
                time.sleep(1)
                logging.info('Init command attempt %i of 10' % i)
                response = send_command(dra818_uart,
                                        'AT+DMOCONNECT\r\n')
                if response == '+DMOCONNECT:0':
                    logging.info('Transceiver found.')
                    break
            else:
                logging.critical("CRITICAL: Transceiver NOT found.")
                dra818_uart.close()
                return False
            # Note: On = 0, Off = 0, so we use int(not <boolean>)
            command = 'AT+SETFILTER=%1i,%1i,%1i\r\n' \
                      % (int(not pre_emphasis),
                         int(not high_pass),
                         int(not low_pass))
            response = send_command(dra818_uart, command)
            if response == '+DMOSETFILTER:0':
                logging.info('Transceiver filter configuration OK.')
                dra818_uart.close()
                return True
            else:
                logging.debug('ERROR: Transceiver filter \
                              configuration failed.')
                dra818_uart.close()
                return False

    def transmit_audio_file(self, frequency, audio_files,
                            full_power=False):
        """Transmits the audio file via the DRA818 transceiver object.

        Args:
            frequency (float): The frequency in MHz. Must be a multiple of
            25 KHz and within the allowed ham radio band allocation.

            audio_files (list): A list of strings with the path of audio
            files.

            full_power (bolean): Tx power level. True = 1 W, False = 0.5 W.

        Returns:
            True: Transmission successful.
            False: Transmission failed.
        """
        try:
            for i in range(10):
                if self.set_tx_frequency(frequency):
                    break
                else:
                    time.sleep(0.5)
            else:
                return False
            self.start_transmitter(full_power=full_power)
            time.sleep(1)
            status = True
            logging.debug('WAV list: %s' % audio_files)
            for audio_file_path in audio_files:
                logging.debug('WAV path: %s' % audio_file_path)
                status = status and _play_audio_file(audio_file_path)
            time.sleep(1)
            self.stop_transmitter()
        finally:
            self.stop_transmitter()
        return status


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    transceiver = DRA818(
        uart=config.SERIAL_PORT_TRANSCEIVER,
        ptt_pin=config.DRA818_PTT,
        power_down_pin=config.DRA818_PD,
        rf_power_level_pin=config.DRA818_HL,
        frequency=145.525,
        squelch_level=0)
    print 'Now listening at 145.525 MHz. Press CTRL-C to quit.'
    print 'Testing Squelch setings.'
    for squelch_level in [0, 2, 8]:
        print 'Setting squelch to %i' % squelch_level
        status = transceiver.set_squelch(squelch_level)
        print '--> Status: %s' % status
        time.sleep(1)
    transceiver.set_squelch(1)
    print 'Testing filter settings.'
    for pe, hp, lp in [(False, False, False), (True, False, True),
                       (True, True, True)]:
        print 'pre_emphasis: %s, high_pass: %s, low_pass: %s' % (pe, hp, lp)
        status = transceiver.set_filters(pre_emphasis=pe, high_pass=hp,
                                         low_pass=lp)
        print '--> Status: %s' % status
        time.sleep(1)
    transceiver.set_filters(pre_emphasis=True, high_pass=False, low_pass=False)
    while True:
        try:
            raw_input('Press ENTER to start transmission.')
            print 'Now sending.'
            list_of_files = [config.AUDIO_BEACON,
                             config.AUDIO_APRS_TEST_SIGNAL,
                             config.AUDIO_SELFTEST_OK]
            transceiver.transmit_audio_file(transceiver.tx_frequency,
                                            list_of_files)
            time.sleep(0.5)
            print 'Back to receive'
        except KeyboardInterrupt:
            print 'CTRL-C detected.'
            break
        finally:
            transceiver.stop_transmitter()
