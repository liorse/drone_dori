# AETH is the active object that has the following specifications:
# 1. It will establish communication with AETH (enter exact model name here)
# 2. It will fail, it will try again endlessly every X seconds (parameter)
# 3. Upon succes it will read the AETH data every Y seconds (parameter)
# 4. Transmit the data over another all subscribed statecharts.
# (the important one is the logger statechart and influxDB)
# 4a. it can also be statechart over the network on a remote pc
# (via RF serial link via PPP)

import time

from miros import Event
from miros import spy_on
from miros import signals
#from miros import ActiveObject
from miros import return_status
import logging
from aeth_class import AETH
import epics

TIMEOUT = 100
OK = 0
logging.basicConfig(format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    level=logging.DEBUG)

@spy_on
def COMMON_BEHAVIOUR(aeth, e):
    status = return_status.UNHANDLED
    if e.signal == signals.ENTRY_SIGNAL:
        logging.info("Entered COMMON_BEHAVIOUR state")
        status = return_status.HANDLED
    elif e.signal == signals.hook:
        logging.info("hook event")
        status = return_status.HANDLED
    else:
        aeth.temp.fun = aeth.top
        status = return_status.SUPER
    return status


@spy_on
def DISABLED(aeth, e):
    status = return_status.UNHANDLED
    if e.signal == signals.ENTRY_SIGNAL:
        logging.info("Entered DISABLED state")
        aeth_dev_epics.comm_ON = False
        status = return_status.HANDLED
    elif e.signal == signals.enable_aeth:
        logging.info("enable aeth event recieved")
        status = aeth.trans(ENABLED)
    else:
        aeth.temp.fun = COMMON_BEHAVIOUR
        status = return_status.SUPER
    return status


@spy_on
def ENABLED(aeth, e):
    status = return_status.UNHANDLED
    if e.signal == signals.ENTRY_SIGNAL:
        logging.info("Entered ENABLED state")
        aeth.post_fifo(Event(signal=signals.start_comm))
        status = return_status.HANDLED
    elif e.signal == signals.start_comm:
        logging.info("start communication event")
        status = aeth.trans(COMM_OFF)
    else:
        aeth.temp.fun = COMMON_BEHAVIOUR
        status = return_status.SUPER
    return status


@spy_on
def COMM_OFF(aeth, e):
    status = return_status.UNHANDLED
    if e.signal == signals.ENTRY_SIGNAL:
        logging.info("Entered COMM_OFF state")
        aeth_dev_epics.comm_ON = False
        aeth.post_fifo(Event(signal=signals.open_comm))
        status = return_status.HANDLED
    elif e.signal == signals.disable_aeth:
        logging.info("disable aeth event recieved")
        status = aeth.trans(DISABLED)
    elif e.signal == signals.open_comm:
        if aeth.init_aeth() == OK:
            logging.info("communication established")
            status = aeth.trans(COMM_ON)
        else:
            logging.info("trying to establish communication.....")
            aeth.post_fifo(Event(signal=signals.open_comm))
            status = return_status.HANDLED
    else:
        aeth.temp.fun = ENABLED
        status = return_status.SUPER
    return status


@spy_on
def COMM_ON(aeth, e):
    status = return_status.UNHANDLED
    if e.signal == signals.ENTRY_SIGNAL:
        logging.info("Entered COMM_ON state")
        aeth.post_fifo(Event(signal=signals.read_data))
        aeth_dev_epics.comm_ON = True
        status = return_status.HANDLED
    elif e.signal == signals.disable_aeth:
        logging.info("disable aeth event recieved")
        if aeth.stop_measurement():
            status = aeth.trans(DISABLED)
    elif e.signal == signals.set_gain:
            status = return_status.HANDLED
    elif e.signal == signals.read_data:
        logging.info("reading data from AETH")    
        data = aeth.request_data()
        print(data)
        aeth.post_fifo(Event(signal=signals.read_data), period=1, times=1, deferred=True)
    elif e.signal == signals.EXIT_SIGNAL:
        logging.info("closing communication to AETH")
        aeth.close()
        #aeth.cancel_events(Event(signal=signals.read_data))
    else:
        aeth.temp.fun = ENABLED
        status = return_status.SUPER
    return status


def on_aeth_enable(value, **kw):
    if value == True:
        aeth.post_fifo(Event(signal=signals.enable_aeth))
    else:
        aeth.post_fifo(Event(signal=signals.disable_aeth))
'''
def on_aeth_set_laser(value, **kw):
    aeth.post_fifo(Event(signal=signals.set_laser, payload=value))

def on_aeth_set_fan(value, **kw):
    aeth.post_fifo(Event(signal=signals.set_fan, payload=value))

def on_aeth_set_gain(value, **kw):
    aeth.post_fifo(Event(signal=signals.set_gain, payload=value))
'''

if __name__ == "__main__":

    # set an active object
    aeth = AETH(aeth_name="MicroAeth",
              aeth_port="/dev/ttyUSB0",
              aeth_location="drone")
    

    # establish EPICS variable connection
    aeth_dev_epics = epics.Device('aeth:',
                                 attrs=[
                                     'enable', 'comm_ON', 'period', 'set_period'
                                 ])
                                 
    aeth_dev_epics.add_callback('enable', on_aeth_enable)
    #aeth_dev_epics.add_callback('set_laser', on_aeth_set_laser)
    #aeth_dev_epics.add_callback('set_fan', on_aeth_set_fan)
    #aeth_dev_epics.add_callback('toggle_gain', on_aeth_set_gain)
    #aeth_dev_epics.set_period = 0

    aeth.live_spy = True
    aeth.live_trace = True
    aeth.start_at(ENABLED)
    
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        aeth_dev_epics.remove_callback('enable')
