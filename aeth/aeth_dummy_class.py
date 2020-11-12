# -*- coding: utf-8 -*-
"""
This is the microaeth-MA200 dummy class file
Programmer: Lior Segev
Date 05 Nov 2020
Version 0.0.1

"""

from __future__ import print_function
import logging
import sys
from miros import ActiveObject
import re
import time
import numpy as np

integration = 5

# NAMING VARIABLES
AETHNAME = "MICROAETH-MA200"
AETHPORT = "/dev/ttyUSB0"
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
    This is raised when no new data is available when polling the microAETH
    '''
    pass

class FailedCommunication(Error):
    '''
    failed communication exception
    '''
    pass
    
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

        logging.info('openning serial port to OPC ' + self.AETHPORT)
        logging.info('initializing communication with AETH')
        logging.info('updating measurements IDs..')
        return OK

    def close(self):
        '''
        closing the the AETH serial port
        '''
        logging.info('closing serial port ' + self.AETHPORT)

    def is_sampling(self):
        '''
        return True if sampling is on going and False otherwise
        '''
        return True if np.random.random()>0.5 else False
        
   
    def request_data(self):
        '''
        request data from aeth. It is currently setup to read in verbose mode and in 5 wavelengths
        '''

        data = [str(np.random.randint(10)) for i in range(71)]

        return data        

    def check_battery(self):
        '''
        request battery status
        '''

        return np.random.randint(100)

    def start_measurement(self):
        '''
        start measurement - returns True if sampling started
        '''
        return True

    def stop_measurement(self):
        '''
        stop measurement - return True if sampling stopped
        '''
        return True
                       
if __name__ == '__main__':
    aeth = AETH(aeth_name="MicroAeth",
              aeth_port="/dev/ttyUSB0",
              aeth_location="drone")
    if not aeth.init_aeth() == OK:
        sys.exit()
    
    #logging.info(aeth.request_data())
    #logging.info(aeth.check_battery())
    logging.info(aeth.is_sampling())
    logging.info(aeth.start_measurement())
    logging.info(aeth.is_sampling())
    
    while True:
        try:
            data = aeth.request_data()
            print(data)
            break
        except:
            time.sleep(1)

    logging.info(aeth.stop_measurement())
    aeth.close()
