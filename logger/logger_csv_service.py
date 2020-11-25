
# Logger is the active object that has the following specifications:
# 1. enable or disable logging
# 2. on data ready signal from various instrument services, the logger will update its local state variable
# 3. on a specific interval chosen by an epic variable, it will save the mean number of samples for each measurment. 
#    it will record the count number of samples for each type of instrument

import time

from miros import Event
from miros import spy_on
from miros import signals
from miros import ActiveObject
from miros import return_status
import logging
import numpy as np
#from logger_dummy_class import LOGGER
#from logger_class import LOGGER
import json
import epics
import pandas as pd

OK = 0
logging.basicConfig(format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    level=logging.DEBUG)

class LOGGER(ActiveObject):
    '''
    LOGGER class will include methods for updating its local 
    state measurements from all instruments
    '''

    def __init__(self, save_folder='/home/pi/data', save_interval_s=5):
        self.save_folder = save_folder
        self.save_interval_s = save_interval_s # 5 seconds default interval
        self.thread_save_to_file_id = None
        logging.info("Instantiated Logger class!")
        super().__init__()
        
@spy_on
def LOGGER_COMMON_BEHAVIOUR(logger, e):
    status = return_status.UNHANDLED
    if e.signal == signals.ENTRY_SIGNAL:
        status = return_status.HANDLED
    elif e.signal == signals.disable_logger:
        status = logger.trans(LOGGER_DISABLED)
    elif e.signal == signals.enable_logger:
        status = logger.trans(LOGGER_ENABLED)
    else:
        logger.temp.fun = logger.top
        status = return_status.SUPER
    return status


@spy_on
def LOGGER_DISABLED(logger, e):
    status = return_status.UNHANDLED
    if e.signal == signals.ENTRY_SIGNAL:
        status = return_status.HANDLED
    else:
        logger.temp.fun = LOGGER_COMMON_BEHAVIOUR
        status = return_status.SUPER
    return status


@spy_on
def LOGGER_ENABLED(logger, e):
    status = return_status.UNHANDLED
    if e.signal == signals.ENTRY_SIGNAL:
        #logger.post_fifo(Event(signal=signals.start_comm))
        status = return_status.HANDLED
    elif e.signal == signals.INIT_SIGNAL:
        # setup a recurring signal to keep saving data to file every logger.save_interval_s
        
        logger.thread_save_to_file_id = logger.post_fifo(
                                                            Event(signal=signals.SAVE_TO_FILE),
                                                            period=logger.save_interval_s,
                                                            deferred=False
                                                        )
        logging.info('created periodic thread id' + str(logger.thread_save_to_file_id))
        status = logger.trans(LOGGER_IDLE)
    elif e.signal == signals.SAVE_INTERVAL_VALUE_UPDATE:
        logger.save_interval_s = e.payload
        status = logger.trans(LOGGER_ENABLED)
    elif e.signal == signals.EXIT_SIGNAL:
        logging.info('cancelling thread id' + str(logger.thread_save_to_file_id))
        logger.cancel_event(logger.thread_save_to_file_id)
        status = return_status.HANDLED
    else:
        logger.temp.fun = LOGGER_COMMON_BEHAVIOUR
        status = return_status.SUPER
    return status


@spy_on
def LOGGER_IDLE(logger, e):
    status = return_status.UNHANDLED
    if e.signal == signals.ENTRY_SIGNAL:
        status = return_status.HANDLED
    elif e.signal == signals.SAVE_TO_FILE:
        logging.info('writing to file')
        status = return_status.HANDLED
    elif e.signal == signals.OPC_DATA_READY:
        logging.info('new OPC data recieved - updating internal dataframe')
        status = return_status.HANDLED
    elif e.signal == signals.AETH_DATA_READY:
        logging.info('new AETH data recieved - updating internal dataframe')
        status = return_status.HANDLED
    elif e.signal == signals.SNIFFER_DATA_READY:
        logging.info('new SNIFFER data recieved - updating internal dataframe')
        status = return_status.HANDLED
    else:
        logger.temp.fun = LOGGER_ENABLED
        status = return_status.SUPER
    return status


def on_logger_enable(value, **kw):
    if value == True:
        logger.post_fifo(Event(signal=signals.enable_logger))
    else:
        logger.post_fifo(Event(signal=signals.disable_logger))

def on_save_interval_value_change(value, **kw):
    logger.post_fifo(Event(signal=signals.SAVE_INTERVAL_VALUE_UPDATE, payload=value))

def on_opc_data_ready(value, **kw):
    logger.post_lifo(Event(signal=signals.OPC_DATA_READY))

def on_aeth_data_ready(value, **kw):
    logger.post_lifo(Event(signal=signals.AETH_DATA_READY))

def on_sniffer_data_ready(value, **kw):
    logger.post_lifo(Event(signal=signals.SNIFFER_DATA_READY))
    
if __name__ == "__main__":

    # establish EPICS variable connection
    #logger_dev_epics = epics.Device('logger:',
    #                             attrs=[
    #                                 'comm_ON','enable', 'CO', 'NO2', 'Ox', 'PM1', 'PM10',
    #                                 'PM2dot5', 'SO2', 'altitude', 'hdop', 'humidity','latitude', 'longitude', 'pressure',
    #                                 'sateNum', 'serial', 'temperature', 'utcTime'
    #                             ])

    logger_dev_epics = epics.Device('logger:')
    opc_dev_epics = epics.Device('opc:')
    aeth_dev_epics = epics.Device('aeth:')
    sniffer_dev_epics = epics.Device('sniffer:')
    
    # set an active object
    logger = LOGGER(save_interval_s=logger_dev_epics.save_interval)
    logger.live_trace = True
    #logger.live_spy = True
    time.sleep(0.1)

    logger_dev_epics.add_callback('enable', on_logger_enable)
    logger_dev_epics.add_callback('save_interval', on_save_interval_value_change)
    opc_dev_epics.add_callback('data_ready', on_opc_data_ready)
    aeth_dev_epics.add_callback('data_ready', on_aeth_data_ready)
    sniffer_dev_epics.add_callback('data_ready', on_sniffer_data_ready)
    
    logger.start_at(LOGGER_DISABLED)
        
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    '''
    logger.establish_comm()
    logger.read_data_from_logger()
    logger.set_fan(True)
    logger.set_fan(False)
    logger.set_laser(True)
    logger.set_laser(False)
    '''
