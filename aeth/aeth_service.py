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
import serial

retry_counter = 10
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
        try:
            aeth.init_aeth()
            logging.info("communication established")
            status = aeth.trans(COMM_ON)
        except serial.serialutil.SerialException:
            logging.info("comm to AETH failed. kindly check that USB adapter is connected. " +
                         "trying to establish communication.....")
            aeth.post_fifo(Event(signal=signals.open_comm), period=1, times=1, deferred=True)
            status = return_status.HANDLED
        except IndexError:
            logging.info("communication failed. kindly check that" +
                          " the instrument is connected and powered up")
            status = return_status.HANDLED
            aeth.post_fifo(Event(signal=signals.open_comm), period=1, times=1, deferred=True)
    else:
        aeth.temp.fun = ENABLED
        status = return_status.SUPER
    return status


@spy_on
def COMM_ON(aeth, e):
    status = return_status.UNHANDLED
    if e.signal == signals.ENTRY_SIGNAL:
        logging.info("Entered COMM_ON state")
        #aeth.post_fifo(Event(signal=signals.read_data))
        aeth_dev_epics.sampling_ON = aeth.is_sampling()
        aeth_dev_epics.comm_ON = True
        status = return_status.HANDLED
    elif e.signal == signals.disable_aeth:
        logging.info("disable aeth event recieved")
        status = aeth.trans(DISABLED)
    elif e.signal == signals.start_stop_measurement:
        if e.payload == 1:
            if not aeth.start_measurement():
                aeth.post_fifo(Event(signal=signals.read_data))
            else:
                logging.error('FAILED to start measurement. Please check if the tape had run out.')
                aeth_dev_epics.start_measurement = False
        else:
            aeth.stop_measurement()
            aeth.cancel_events(Event(signal=signals.read_data))
        aeth_dev_epics.sampling_ON = aeth.is_sampling()
        status = return_status.HANDLED        
    elif e.signal == signals.read_data:
        logging.info("reading data from AETH")
        try:
            data = aeth.request_data()
            update_EPICs_var_with_aeth_data(data)
            print(data)
            aeth.post_fifo(Event(signal=signals.read_data), period=1, times=1, deferred=True)
            aeth.retry_counter = 10
            status = return_status.HANDLED
        except serial.serialutil.SerialException:
            status = aeth.trans(COMM_OFF)
        except (IndexError, ValueError):
            if aeth.retry_counter == 0:
                status = aeth.trans(COMM_OFF)
            else:
                aeth.retry_counter = aeth.retry_counter - 1
                aeth.post_fifo(Event(signal=signals.read_data), period=1, times=1, deferred=True)
                status = return_status.HANDLED
    elif e.signal == signals.EXIT_SIGNAL:
        logging.info("closing communication to AETH")
        aeth.close()
        #aeth.cancel_events(Event(signal=signals.read_data))
    else:
        aeth.temp.fun = ENABLED
        status = return_status.SUPER
    return status

def update_EPICs_var_with_aeth_data(data):
    '''
    copy all data originating from verbose mode - dual point measurement - 5 wavelengths
    any other data will not fit and will cause a run time error
    '''
    aeth_dev_epics.datum_id = data[0]
    aeth_dev_epics.session_id = data[1]
    aeth_dev_epics.data_format_ver = data[2]
    aeth_dev_epics.firmware_version = data[3]
    aeth_dev_epics.date_time_GMT = data[4]
    aeth_dev_epics.timezone_offset = data[5]
    aeth_dev_epics.gps_lat = data[6]
    aeth_dev_epics.gps_long = data[7]
    aeth_dev_epics.gps_speed = data[8]
    aeth_dev_epics.timebase = data[9]
    aeth_dev_epics.status = data[10]
    aeth_dev_epics.battery = data[11]
    aeth_dev_epics.accel_x = data[12]
    aeth_dev_epics.accel_y = data[13]
    aeth_dev_epics.accel_z = data[14]
    aeth_dev_epics.tape_pos = data[15]
    aeth_dev_epics.flow_setpoint = data[16]
    aeth_dev_epics.flow_total = data[17]
    aeth_dev_epics.flow1 = data[18]
    aeth_dev_epics.flow2 = data[19]
    aeth_dev_epics.sample_temp = data[20]
    aeth_dev_epics.sample_RH = data[21]
    aeth_dev_epics.sample_dewpoint = data[22]
    aeth_dev_epics.int_pressure = data[21]
    aeth_dev_epics.int_temp = data[22]
    aeth_dev_epics.optical_config = data[23]
    '''
    aeth_dev_epics.UV_sen1 = data[24]
    aeth_dev_epics.UV_sen2 = data[25]
    aeth_dev_epics.UV_ref = data[26]
    aeth_dev_epics.UV_ATN1 = data[27]
    aeth_dev_epics.UV_ATN2 = data[28]
    aeth_dev_epics.UV_K = data[29]
    aeth_dev_epics.blue_sen1 = data[30]
    aeth_dev_epics.blue_sen2 = data[31]
    aeth_dev_epics.blue_ref = data[32]
    aeth_dev_epics.blue_ATN1 = data[33]
    aeth_dev_epics.blue_ATN2 = data[34]
    
    aeth_dev_epics.blue_K = data[35]
    aeth_dev_epics.green_sen1 = data[36]
    aeth_dev_epics.green_sen2 = data[37]
    aeth_dev_epics.green_ref = data[38]
    aeth_dev_epics.green_ATN1 = data[39]
    aeth_dev_epics.green_ATN2 = data[40]
    aeth_dev_epics.green_K = data[41]
    aeth_dev_epics.red_sen1 = data[42]
    aeth_dev_epics.red_sen2 = data[43]
    aeth_dev_epics.red_ref = data[44]
    aeth_dev_epics.red_ATN1 = data[45]
    aeth_dev_epics.red_ATN2 = data[46]
    aeth_dev_epics.red_K = data[47]
    aeth_dev_epics.IR_sen1 = data[48]
    aeth_dev_epics.IR_sen2 = data[49]
    aeth_dev_epics.IR_ref = data[50]
    aeth_dev_epics.IR_ATN1 = data[51]
    aeth_dev_epics.IR_ATN2 = data[52]
    aeth_dev_epics.IR_K = data[53]
    aeth_dev_epics.UV_BC1 = data[54]
    aeth_dev_epics.UV_BC2 = data[55]
    aeth_dev_epics.UV_BCc = data[56]
    aeth_dev_epics.blue_BC1 = data[57]
    aeth_dev_epics.blue_BC2 = data[58]
    aeth_dev_epics.blue_BCc = data[59]
    aeth_dev_epics.greeen_BC1 = data[60]
    aeth_dev_epics.green_BC2 = data[61]
    aeth_dev_epics.green_BCc = data[62]
    aeth_dev_epics.red_BC1 = data[63]
    aeth_dev_epics.red_BC2 = data[64]
    aeth_dev_epics.red_BCc = data[65]
    aeth_dev_epics.IR_BC1 = data[66]
    aeth_dev_epics.IR_BC2 = data[67]
    aeth_dev_epics.IR_BCc = data[68]
    '''
def on_aeth_enable(value, **kw):
    if value == True:
        aeth.post_fifo(Event(signal=signals.enable_aeth))
    else:
        aeth.post_fifo(Event(signal=signals.disable_aeth))

def on_aeth_start_stop_measurement(value, **kw):
    aeth.post_fifo(Event(signal=signals.start_stop_measurement, payload=value))
    
'''

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
                                     'enable', 'comm_ON', 'sampling_ON',
                                     'start_measurement', 'datum_id', 'session_id',
                                     'data_format_ver', 'firmware_version', 'date_time_GMT',
                                     'timezone_offset', 'gps_lat', 'gps_long', 'gps_speed',
                                     'timebase', 'status', 'battery', 'accel_x', 'accel_y',
                                     'accel_z', 'tape_pos', 'flow_setpoint', 'flow_total',
                                     'flow1', 'flow2', 'sample_temp', 'sample_RH', 'sample_dewpoint',
                                     'int_pressure', 'int_temp', 'optical_config', 'UV_sen1',
                                     'UV_sen2', 'UV_ref', 'UV_ATN1', 'UV_ATN2', 'UV_K','blue_sen1',
                                     'blue_sen2', 'blue_ref', 'blue_ATN1', 'blue_ATN2', 'blue_K','green_sen1',
                                     'green_sen2', 'green_ref', 'green_ATN1', 'green_ATN2', 'green_K', 'red_sen1',
                                     'red_sen2', 'red_ref', 'red_ATN1', 'red_ATN2', 'red_K', 'IR_sen1',
                                     'IR_sen2', 'IR_ref', 'IR_ATN1', 'IR_ATN2', 'IR_K', 'UV_BC1', 'UV_BC2', 'UV_BCc',
                                     'blue_BC1', 'blue_BC2', 'blue_BCc', 'green_BC1', 'green_BC2', 'green_BCc',
                                     'red_BC1', 'red_BC2', 'red_BCc', 'IR_BC1', 'IR_BC2', 'IR_BCc'
                                 ])
                                 
    aeth_dev_epics.add_callback('enable', on_aeth_enable)
    aeth_dev_epics.add_callback('start_measurement', on_aeth_start_stop_measurement)
    #aeth_dev_epics.add_callback('set_fan', on_aeth_set_fan)
    #aeth_dev_epics.add_callback('toggle_gain', on_aeth_set_gain)
    #aeth_dev_epics.set_period = 0

    #aeth.live_spy = True
    aeth.live_trace = True
    aeth.start_at(DISABLED)
    
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        aeth_dev_epics.remove_callback('enable')
