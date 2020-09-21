#!/usr/bin/env python
# -*- coding: utf-8 -*-
from miros import ActiveObject
import numpy as np
import logging
OK = 0
logging.basicConfig(format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    level=logging.DEBUG)


class OPC(ActiveObject):
    '''
    The following methods are the actual interface:
    init_opc()
    laz_ctrl(bool) to start or stop the opc lazer
    fan_ctrl(bool) to start or stop the opc fan
    read_data() to read data from the opc - returns a dict with all the information
    '''
    def __init__(self,
                 opc_name="TEstOPC",
                 opc_port="/dev/ttyACM0",
                 opc_location="some_location"):
        self.OPCNAME = opc_name
        self.OPCPORT = opc_port
        self.LOCATION = opc_location
        logging.info("Instantiated OPC class on port " + self.OPCPORT)
        super().__init__()

    def init_opc(self):

        if np.random.random() > 0.5:
            logging.info('established communication')
            return OK  # error code that everything went fine
        else:
            logging.info('communication failed')
            return -1

    def close_opc(self):
        logging.info('closing communication with OPC')
        return OK

    def read_data(self):
        if np.random.random() > 0.5:
            data = np.random.random()
            logging.info('reading data from OPC' + str(data))
            return data
        else:
            return -1

    def fan_ctrl(self, state=False):
        logging.info('setting the fan to ' + str(state))
        return OK

    def laz_ctrl(self, state=False):
        logging.info('setting the laser to ' + str(state))


