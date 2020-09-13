# -*- coding: utf-8 -*-
"""
This is the OPC driver file
Programmer: Lior Segev
Date 03 September 2020
Version 0.0.1
Based on code by Daniel Jarvis
"""

from __future__ import print_function

#import struct
#import datetime
#import sys
#import os.path
import logging
import time

import serial

integration = 5

# NAMING VARIABLES
OPCNAME = "TestOPC"
OPCPORT = "/dev/ttyACM0"
LOCATION = "Lab2"
wait = 100e-06

log_format = '%(asctime)s %(filename)s: %(message)s'
logging.basicConfig(format=log_format, level=logging.INFO)


class OPC():
    def __init__(self,
                 opc_name="TEstOPC",
                 opc_port="/dev/ttyACM0",
                 opc_location="some_location"):
        self.OPCNAME = opc_name
        self.OPCPORT = opc_port
        self.LOCATION = opc_location
        logging.info("Instantiated OPC class on port " + self.OPCPORT)

    def init_opc(self):

        serial_opts = {
            "port": self.OPCPORT,
            "baudrate": 9600,
            "parity": serial.PARITY_NONE,
            "bytesize": serial.EIGHTBITS,
            "stopbits": serial.STOPBITS_ONE,
            "xonxoff": False,
            "timeout": 1
        }

        # wait for opc to boot
        time.sleep(2)

        logging.info('openning serial port to OPC ' + self.OPCPORT)
        self.ser = serial.Serial(**serial_opts)

    def close_opc(self):
        logging.info('closing serial port ' + self.OPCPORT)
        self.ser.close()

    def fan_ctrl(self, ctrl_flag=False):
        '''
        opc fan control by sending true to turn it on and false to turn it off
        '''
        T = 0
        while True:
            self.ser.write(bytearray([0x61, 0x03]))
            nl = self.ser.read(2)
            T = T + 1
            if nl == (b"\xff\xf3" or b"xf3\xff"):
                time.sleep(wait)
                if ctrl_flag:
                    # fan on
                    logging.info("Request Fan to turn ON")
                    self.ser.write(bytearray([0x61, 0x03]))
                    nl = self.ser.read(2)
                    logging.info("Fan ON")
                    time.sleep(2)
                    return 0  # success
                else:
                    logging.info("Request Fan to turn OFF")
                    self.ser.write(bytearray([0x61, 0x02]))
                    nl = self.ser.read(2)
                    logging.info("Fan OFF")
                    time.sleep(2)
                    return 0  # success
            elif T > 20:
                logging.info("Reset SPI")
                time.sleep(3)  # time for spi buffer to reset
                # reset SPI  conncetion
                self.init_opc()
                T = 0
            else:
                time.sleep(wait * 10)


if __name__ == '__main__':
    opc = OPC(opc_name="some_opc",
              opc_port="/dev/ttyACM0",
              opc_location="the_forest")
    opc.init_opc()
    time.sleep(2)
    opc.fan_ctrl(True)
    opc.fan_ctrl(False)
    opc.close_opc()
