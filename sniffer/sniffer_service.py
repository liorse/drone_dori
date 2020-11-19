
# SNIFFER is the active object that has the following specifications:
# 1. It will establish communication with SNIFFER (enter exact model name here)
# 2. It will fail, it will try again endlessly every X seconds (parameter)
# 3. Upon succes it will read the SNIFFER data every Y seconds (parameter)
# 4. Transmit the data over another all subscribed statecharts.
# (the important one is the logger statechart and influxDB)
# 4a. it can also be statechart over the network on a remote pc
# (via RF serial link via PPP)
# 5. It will be able accept control commands to start the laser or the pump
# for example

import time

from miros import Event
from miros import spy_on
from miros import signals
from miros import ActiveObject
from miros import return_status
import logging
import numpy as np
from sniffer_dummy_class import SNIFFER
#from sniffer_class import SNIFFER
import json
import epics

TIMEOUT = 100
OK = 0
logging.basicConfig(format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    level=logging.DEBUG)


@spy_on
def COMMON_BEHAVIOUR(sniffer, e):
    status = return_status.UNHANDLED
    if e.signal == signals.ENTRY_SIGNAL:
        logging.info("Entered COMMON_BEHAVIOUR state")
        status = return_status.HANDLED
    elif e.signal == signals.hook:
        logging.info("hook event")
        status = return_status.HANDLED
    else:
        sniffer.temp.fun = sniffer.top
        status = return_status.SUPER
    return status


@spy_on
def DISABLED(sniffer, e):
    status = return_status.UNHANDLED
    if e.signal == signals.ENTRY_SIGNAL:
        logging.info("Entered DISABLED state")
        sniffer_dev_epics.comm_ON = False
        status = return_status.HANDLED
    elif e.signal == signals.enable_sniffer:
        logging.info("enable sniffer event recieved")
        status = sniffer.trans(ENABLED)
    else:
        sniffer.temp.fun = COMMON_BEHAVIOUR
        status = return_status.SUPER
    return status


@spy_on
def ENABLED(sniffer, e):
    status = return_status.UNHANDLED
    if e.signal == signals.ENTRY_SIGNAL:
        logging.info("Entered ENABLED state")
        sniffer.post_fifo(Event(signal=signals.start_comm))
        status = return_status.HANDLED
    elif e.signal == signals.start_comm:
        logging.info("start communication event")
        status = sniffer.trans(COMM_OFF)
    else:
        sniffer.temp.fun = COMMON_BEHAVIOUR
        status = return_status.SUPER
    return status


@spy_on
def COMM_OFF(sniffer, e):
    status = return_status.UNHANDLED
    if e.signal == signals.ENTRY_SIGNAL:
        logging.info("Entered COMM_OFF state")
        sniffer_dev_epics.comm_ON = False
        sniffer.post_fifo(Event(signal=signals.open_comm))
        status = return_status.HANDLED
    elif e.signal == signals.disable_sniffer:
        logging.info("disable sniffer event recieved")
        status = sniffer.trans(DISABLED)
    elif e.signal == signals.open_comm:
        if sniffer.init_sniffer() == OK:
            logging.info("communication established")
            status = sniffer.trans(COMM_ON)
        else:
            logging.info("trying to establish communication.....")
            sniffer.post_fifo(Event(signal=signals.open_comm))
            status = return_status.HANDLED
    else:
        sniffer.temp.fun = ENABLED
        status = return_status.SUPER
    return status


@spy_on
def COMM_ON(sniffer, e):
    status = return_status.UNHANDLED
    if e.signal == signals.ENTRY_SIGNAL:
        logging.info("Entered COMM_ON state")
        sniffer.post_fifo(Event(signal=signals.read_data))
        sniffer_dev_epics.comm_ON = True
        status = return_status.HANDLED
    elif e.signal == signals.disable_sniffer:
        logging.info("disable sniffer event recieved")
        status = sniffer.trans(DISABLED)
    elif e.signal == signals.read_data:
        data = sniffer.request_data()
        logging.info(data)
        if not data == -1:
            insert_data_into_epics(data)
            logging.info('data inserted into EPICS')
            sniffer.cancel_events(Event(signal=signals.read_data))
            sniffer.post_fifo(Event(signal=signals.read_data), period=1, times=1, deferred=True)
            status = return_status.HANDLED
        else:
            logging.info("comm failed !!!")
            status = sniffer.trans(COMM_OFF)
    elif e.signal == signals.EXIT_SIGNAL:
        logging.info("closing communication to SNIFFER")
        sniffer.close()
    else:
        sniffer.temp.fun = ENABLED
        status = return_status.SUPER
    return status


def insert_data_into_epics(data):
    '''
    {'airData': {'CO(ppm)': 0.5567, 'NO2(ppm)': 0.0085, 'Ox(ppm)': 0.0301, 'PM1.0(ug/m3)': 4, 'PM10(ug/m3)': 6, 
    'PM2.5(ug/m3)': 5, 'SO2(ppm)': 0.0002}, 'altitude': 17.3662, 'hdop': 99.99, 'humidity': 35.0078, 
    'latitude': -90, 'longitude': -180, 'pressure': 101117, 'sateNum': 0, 'sequence': 2419, 'serial': '8f9f6532', 
    'temperature': 24.1017, 'utcTime': '1970-01-01-00-40-21'}
    '''
    
    if isinstance(data, dict):
        sniffer_dev_epics.CO = data['airData']['CO(ppm)']
        sniffer_dev_epics.NO2 = data['airData']['NO2(ppm)']
        sniffer_dev_epics.Ox = data['airData']['Ox(ppm)']
        sniffer_dev_epics.PM1 = data['airData']['PM1.0(ug/m3)']
        sniffer_dev_epics.PM10 = data['airData']['PM10(ug/m3)'] 
        sniffer_dev_epics.PM2dot5 = data['airData']['PM2.5(ug/m3)']
        sniffer_dev_epics.SO2 = data['airData']['SO2(ppm)']
        sniffer_dev_epics.altitude = data['altitude']
        sniffer_dev_epics.hdop = data['hdop']
        sniffer_dev_epics.humidity = data['humidity']
        sniffer_dev_epics.latitude = data['latitude']
        sniffer_dev_epics.longitude = data['longitude']
        sniffer_dev_epics.pressure = data['pressure']
        sniffer_dev_epics.sateNum = data['sateNum']
        sniffer_dev_epics.sequence = data['sequence']
        sniffer_dev_epics.serial = data['serial']
        sniffer_dev_epics.temperature = data['temperature']
        sniffer_dev_epics.utcTime = data['utcTime']
    

def on_sniffer_enable(value, **kw):
    if value == True:
        sniffer.post_fifo(Event(signal=signals.enable_sniffer))
    else:
        sniffer.post_fifo(Event(signal=signals.disable_sniffer))

if __name__ == "__main__":

    # set an active object
    sniffer = SNIFFER(sniffer_name="Sniffer4d",
              sniffer_port="/dev/ttyUSB1",
              sniffer_location="drone")
    
    sniffer.live_trace = True
    sniffer.live_spy = True

    time.sleep(0.1)

    
    # establish EPICS variable connection
    sniffer_dev_epics = epics.Device('sniffer:',
                                 attrs=[
                                     'comm_ON','enable', 'CO', 'NO2', 'Ox', 'PM1', 'PM10',
                                     'PM2dot5', 'SO2', 'altitude', 'hdop', 'humidity','latitude', 'longitude', 'pressure',
                                     'sateNum', 'serial', 'temperature', 'utcTime'
                                 ])
                                 
    sniffer_dev_epics.add_callback('enable', on_sniffer_enable)
    sniffer.start_at(DISABLED)
        
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    '''
    sniffer.establish_comm()
    sniffer.read_data_from_sniffer()
    sniffer.set_fan(True)
    sniffer.set_fan(False)
    sniffer.set_laser(True)
    sniffer.set_laser(False)
    '''
