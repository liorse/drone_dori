# -*- coding: utf-8 -*-
"""
This is the sniffer4D dummy driver file
Programmer: Lior Segev
Date 12 Nov 2020
Version 0.0.1

"""

from __future__ import print_function
import logging
import sys
from miros import ActiveObject
import re
import time
import json
import numpy as np
from datetime import datetime

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
        
        logging.info('openning serial port to Sniffer ' + self.SNIFFERPORT)
        logging.info('initializing communication with SNIFFER')
        return OK

    def close(self):
        '''
        closing the the SNIFFER serial port
        '''
        logging.info('closing serial port ' + self.SNIFFERPORT)
   
    
    def request_data(self):
        '''
        request data from sniffer. It is currently setup to read in verbose mode and in 5 wavelengths
        '''
        now = datetime.now()
        
        data_dict = {'airData': {'CO(ppm)': np.random.random(), 'NO2(ppm)': np.random.random(), 'Ox(ppm)': np.random.random(), 'PM1.0(ug/m3)': np.random.randint(10), 'PM10(ug/m3)': np.random.randint(10), 
            'PM2.5(ug/m3)': np.random.randint(10), 'SO2(ppm)': np.random.random()}, 'altitude': np.random.random(), 'hdop': np.random.random(), 'humidity': np.random.random(), 
            'latitude': np.random.random(), 'longitude': np.random.random(), 'pressure': np.random.random(), 'sateNum': np.random.random(), 'sequence': np.random.random(), 'serial': '8f9f6532', 
            'temperature': np.random.random(), 'utcTime': now.strftime("%m/%d/%Y-%H:%M:%S")}
                                                
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
