# -*- coding: utf-8 -*-
"""
This is the sniffer4D driver file
Programmer: Lior Segev
Date 12 Nov 2020
Version 0.0.1

"""

from __future__ import print_function
import logging
import sys
from miros import ActiveObject
import serial
import re
import time
import json

integration = 5

# NAMING VARIABLES
SNIFFERNAME = "MICROSNIFFER-MA200"
SNIFFERPORT = "/dev/ttyUSB0"
LOCATION = "Drone"
wait = 100e-06
OK = 0

log_format = '%(asctime)s %(filename)s: %(message)s'
logging.basicConfig(format=log_format, level=logging.INFO)

class Error(Exception):
    '''
    Base class for other exceptions
    '''
    pass

class NoNewDataRecieved(Error):
    '''
    This is raised when no new data is available when polling the microSNIFFER
    '''
    pass

class FailedCommunication(Error):
    '''
    failed communication exception
    '''
    pass
    
class SNIFFER(ActiveObject):
    '''
    The following methods are the actual interface:
    init_sniffer()
    '''
    def __init__(self,
                 sniffer_name="TestSNIFFER",
                 sniffer_port="/dev/ttyUSB1",
                 sniffer_location="some_location"):
        self.SNIFFERNAME = sniffer_name
        self.SNIFFERPORT = sniffer_port
        self.LOCATION = sniffer_location
        self.first_id = 0
        self.next_id = 0
        self.current_id = 0
        self.retry_counter = 10;
        logging.info("Instantiated SNIFFER class on port " + self.SNIFFERPORT)
        super().__init__()

    def init_sniffer(self):
        '''
        establish communication with SNIFFER return OK if succedded and -1 if failed
        '''

        serial_opts = {
            "port": self.SNIFFERPORT,
            "baudrate": 115200,
            "parity": serial.PARITY_NONE,
            "bytesize": serial.EIGHTBITS,
            "stopbits": serial.STOPBITS_ONE,
            "xonxoff": False,
            "timeout": 5
        }

        logging.info('openning serial port to Sniffer ' + self.SNIFFERPORT)
        logging.info('initializing communication with SNIFFER')
        self.ser = serial.Serial(**serial_opts)
        return OK

    def close(self):
        '''
        closing the the SNIFFER serial port
        '''
        logging.info('closing serial port ' + self.SNIFFERPORT)
        self.ser.close()
   
    
    def request_data(self):
        '''
        request data from sniffer. It is currently setup to read in verbose mode and in 5 wavelengths
        '''
        while True:
            array_strings =[]    
            while True:
                data_string_line = self.ser.readline()
                if data_string_line == b'\n':
                    break
                else:
                    try:
                        array_strings.append(data_string_line.decode('utf-8'))
                    except UnicodeDecodeError:
                        logging.error('decoding of string failed. will try again')
                        break

            sep = ''
            json_string = sep.join(array_strings)
            try:
                data_dict = json.loads(json_string)
                print('data start')
                print(data_dict)
                print('data end')
                break
            except json.decoder.JSONDecodeError:
                logging.error('json read exception occured, retrying next data frame....')
                
                                                
        return data_dict       
                       
if __name__ == '__main__':
    sniffer = SNIFFER(sniffer_name="Sniffer4d",
              sniffer_port="/dev/ttyUSB1",
              sniffer_location="drone")
    if not sniffer.init_sniffer() == OK:
        sys.exit()
    
    while True:
        data = sniffer.request_data()
        print(data)
        time.sleep(0.01)
    
    sniffer.close()
