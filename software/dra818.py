#!/usr/bin/env python
# -*- coding: utf-8 -*-
# dra818.py
# Module for the DRA818 transceiver module
#
import logging
import time
import RPi.GPIO as GPIO
import serial
import config


class DRA818_Error(Exception):
    """A custom Python exception for signaling severe problems with the
    initialization of the DRA818 unit in the __init__ method.
    """
    pass


def send_command(self, serial_connection, command):
    """Sends a command string to the DRA818 UART and returns the
    response string.

    Args:
        serial_connection: The PySerial connection object.
        command (str): The command string.

    Returns:
        str: The response string.
    """
    serial_connection.write(command)
    logging.info('Transceiver command sent: %s' % command)
    tx_response = serial_connection.readline().strip()
    logging.info('Transceiver response: %s' % tx_response)
    return tx_response


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
            for i in range(10):
                dra818_uart.reset_input_buffer()
                time.sleep(1)
                logging.info('Init command attempt %i of 10' % i)
                response = send_command(dra818_uart,
                                        'AT+DMOCONNECT\r\n')
                if response == '+DMOCONNECT: 0':
                    logging.info('Transceiver found.')
                    break
            else:
                logging.critical("CRITICAL: Transceiver NOT found.")
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
            # T+DMOSETGROUP=GBW,TFV, RFV,Tx_CTCSS,SQ,Rx_CTCSS<CR><LF>
            command = 'AT+DMOSETGROUP=0,%3.4f,%3.4f,0,%i,0\r\n' \
                % (self.tx_frequency, self.rx_frequency,
                   self.squelch_level)
            response = send_command(dra818_uart, command)
            if response == '+DMOCONNECT: 0':
                logging.info('Transceiver initialization OK.')
            else:
                logging.debug('ERROR: Transceiver init failed.')
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
            if response == '+DMOCONNECT: 0':
                logging.info('Transceiver filter configuration OK.')
            else:
                logging.debug('ERROR: Transceiver filter \
                               configuration failed.')
                raise DRA818_Error

    def start_transmitter(self, full_power=False):
        """Turns on the transmitter.

        Agrs:
            full_power (boolean): True sets the RF power level to the
            maximum of 1 W, False sets it to 0.5W."""

        return True

    def stop_transmitter(self):
        """Turns off the transmitter."""
        return True

    def set_tx_frequency(self, frequency):
        """Sets the transmission frequency.

        Args:
            frequency (float): The transmit frequency in MHz,
            e.g. 144.800 for the European APRS frequency.
        """
        return True

    def set_rx_frequency(self, frequency):
        """Sets the receive frequency.

        Args:
            frequency (float): The receive frequency in MHz,
            e.g. 144.800 for the European APRS frequency.
        """
        return True

    def set_squelch(self, squelch_level):
        """Sets the squelch level.

        Args:
            squelch_level (int): The initial squelch level (0..8).
        """
        return True

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
            # Note: On = 0, Off = 0, so we use int(not <boolean>)
            command = 'AT+SETFILTER=%1i,%1i,%1i\r\n' \
                      % (int(not pre_emphasis),
                         int(not high_pass),
                         int(not low_pass))
            response = send_command(dra818_uart, command)
            if response == '+DMOCONNECT: 0':
                logging.info('Transceiver filter configuration OK.')
                return True
            else:
                logging.debug('ERROR: Transceiver filter \
                              configuration failed.')
                return False


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
    print 'Testing filter settings.'
    import itertools
    for pe, hp, lp in list(itertools.product([True, False], repeat=3)):
        print 'pre_emphasis: %s, high_pass: %s, low_pass: %s' % (pe, hp, lp)
        transceiver.set_filters(pre_emphasis=pe, high_pass=hp,
                                low_pass=lp)
        time.sleep(1)
    transceiver.set_filters(pre_emphasis=True, high_pass=False, low_pass=False)
    while True:
        try:
            raw_input('Press ENTER to start transmission.')
            print 'Now sending.'
            transceiver.start_transmitter()
            raw_input('Press ENTER to stop transmission.')
            transceiver.stop_transmitter()
            print 'Back to receive'
        finally:
            transceiver.stop_transmitter()
