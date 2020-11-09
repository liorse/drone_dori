# -*- coding: utf-8 -*-
"""
This is the microaeth-MA200 driver file
Programmer: Lior Segev
Date 05 Nov 2020
Version 0.0.1

"""

from __future__ import print_function
import logging
import sys
from miros import ActiveObject
import serial
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
        self.retry_counter = 10;
        logging.info("Instantiated AETH class on port " + self.AETHPORT)
        super().__init__()

    def init_aeth(self):
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
        logging.info('initializing communication with AETH')
        self.ser = serial.Serial(**serial_opts)
        logging.info('updating measurements IDs..')
        self.update_measurment_ids()
        return OK

    def close(self):
        '''
        closing the the AETH serial port
        '''
        logging.info('closing serial port ' + self.AETHPORT)
        self.ser.close()

    def is_sampling(self):
        '''
        return True if sampling is on going and False otherwise
        '''
        self.ser.write(b'cs\r')
        self.ser.readline()
        status_str = self.ser.readline()
        self.ser.readline()
        status_re = re.findall('[0-9]+', status_str.decode('utf-8'))
        return True if int(status_re[3])==1 else False
        
    def update_measurment_ids(self):
        '''
        update measurements ids by checking status of AETH
        command: cs
        udpates state variables  firstid = , nextId=, currentId= , sampling = 0 or 1 
        '''
        self.ser.write(b'cs\r')
        self.ser.readline()
        status_str = self.ser.readline()
        self.ser.readline()

        status_re = re.findall('[0-9]+', status_str.decode('utf-8'))

        self.first_id = int(status_re[0])
        self.next_id = int(status_re[1])
        self.current_id = int(status_re[2])
        
        return 0

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
            self.update_measurment_ids()
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
        start measurement - returns True if sampling started
        '''
        if not self.is_sampling():
            self.ser.write(b'ms\r')

            while True:
                status_text = self.ser.readline()
                if status_text != b'':
                    logging.info(status_text)
                else:
                    return self.is_sampling() == True
        else:
            return True

    def stop_measurement(self):
        '''
        stop measurement - return True if sampling stopped
        '''
        if self.is_sampling():
            self.ser.write(b'ms\r')

            while True:
                status_text = self.ser.readline()
                if status_text != b'':
                    logging.info(status_text)
                else:
                    return self.is_sampling() == False
        else:
            return True
                       
if __name__ == '__main__':
    aeth = AETH(aeth_name="MicroAeth",
              aeth_port="/dev/ttyUSB0",
              aeth_location="drone")
    if not aeth.init_aeth() == OK:
        sys.exit()
    
    logging.info(aeth.request_data())
    logging.info(aeth.check_battery())
    logging.info(aeth.start_measurement())
    logging.info(aeth.stop_measurement())
    aeth.close()
