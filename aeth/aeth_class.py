# -*- coding: utf-8 -*-
"""
This is the microaeth-MA200 driver file
Programmer: Lior Segev
Date 05 Nov 2020
Version 0.0.1

"""

from __future__ import print_function

#import datetime
#import sys
#import os.path
import logging
import struct
import time
import sys
from miros import ActiveObject
import serial
import numpy as np
import re

integration = 5

# NAMING VARIABLES
AETHNAME = "MICROAETH-MA200"
AETHPORT = "/dev/ttyUSB0"
LOCATION = "Drone"
wait = 100e-06
OK = 0

log_format = '%(asctime)s %(filename)s: %(message)s'
logging.basicConfig(format=log_format, level=logging.INFO)


class AETH(ActiveObject):
    '''
    The following methods are the actual interface:
    init_aeth()
    '''
    def __init__(self,
                 aeth_name="TEstAETH",
                 aeth_port="/dev/ttyUSB0",
                 aeth_location="some_location"):
        self.AETHNAME = aeth_name
        self.AETHPORT = aeth_port
        self.LOCATION = aeth_location
        self.first_id = 0
        self.next_id = 0
        self.current_id = 0
        self.sampling = False
        self.comm = False
        logging.info("Instantiated AETH class on port " + self.AETHPORT)
        super().__init__()

    def init(self):
        '''
        establish communication with AETH return OK if succedded and -1 if failed
        '''

        serial_opts = {
            "port": self.AETHPORT,
            "baudrate": 1000000,
            "parity": serial.PARITY_NONE,
            "bytesize": serial.EIGHTBITS,
            "stopbits": serial.STOPBITS_ONE,
            "xonxoff": False,
            "timeout": 1
        }

        logging.info('openning serial port to OPC ' + self.AETHPORT)
        try:
            self.ser = serial.Serial(**serial_opts)
            self.comm = True
        except serial.serialutil.SerialException:
            logging.info(
                'communication failed to MICROAETH-MA200- check USB connection to raspberry PI host'
            )
            self.comm = False
            return -1
        logging.info('initializing communication with AETH')
        self.check_status()
        return OK

    def close(self):
        logging.info('closing serial port ' + self.AETHPORT)
        self.ser.close()

    def check_status(self):
        '''
        check status of AETH
        command: cs
        returns: firstid = , nextId=, currentId= , sampling = 0 or 1 
        '''
        self.ser.write(b'cs\r')
        self.ser.readline()
        status_str = self.ser.readline()
        self.ser.readline()

        status_re = re.findall('[0-9]+', status_str.decode('utf-8'))

        self.first_id = int(status_re[0])
        self.next_id = int(status_re[1])
        self.current_id = int(status_re[2])
        self.sampling = True if int(status_re[3])==1 else False
        
        return status_re

    def request_data(self):
        '''
        request data from aeth. It is currently setup to read in verbose mode and in 5 wavelengths
        '''

        self.ser.write(b'dr\r')

        data = self.ser.readline().decode('utf-8').split(',')[1:-1]

        if int(data[0]) != self.current_id:
            return 0 # no new data present
        else:
            # update the new ID
            self.check_status()
            return data        

    def check_battery(self):
        '''
        request battery status
        '''

        self.ser.write(b'cb\r')
        re_battery_search = re.search('\d+', self.ser.readline().decode('utf-8') )
        return int(re_battery_search.group(0))

    def start_measurement(self):
        '''
        start measurement
        '''
        if not self.sampling:
            self.ser.write(b'ms\r')

            while True:
                status_text = self.ser.readline()
                if status_text != b'':
                    logging.info(status_text)
                else:
                    self.check_status()
                    return self.sampling == True
        else:
            return True

    def stop_measurement(self):
        '''
        stop measurement
        '''
        if self.sampling:
            self.ser.write(b'ms\r')

            while True:
                status_text = self.ser.readline()
                if status_text != b'':
                    logging.info(status_text)
                else:
                    self.check_status()
                    return self.sampling == False
        else:
            return True
                       
if __name__ == '__main__':
    aeth = AETH(aeth_name="MicroAeth",
              aeth_port="/dev/ttyUSB0",
              aeth_location="drone")
    if not aeth.init() == OK:
        sys.exit()
    
    logging.info(aeth.check_status())
    logging.info(aeth.request_data())
    logging.info(aeth.check_battery())
    logging.info(aeth.start_measurement())
    logging.info(aeth.stop_measurement())
    aeth.close()
