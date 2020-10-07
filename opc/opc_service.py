# OPC is the active object that has the following specifications:
# 1. It will establish communication with OPC (enter exact model name here)
# 2. It will fail, it will try again endlessly every X seconds (parameter)
# 3. Upon succes it will read the OPC data every Y seconds (parameter)
# 4. Transmit the data over another all subscribed statecharts.
# (the important one is the logger statechart and influxDB)
# 4a. it can also be statechart over the network on a remote pc
# (via RF serial link via PPP)
# 5. It will be able accept control commands to start the laser or the pump
# for example

import time

import paho.mqtt.client as mqtt
from miros import Event
from miros import spy_on
from miros import signals
from miros import ActiveObject
from miros import return_status
import logging
import numpy as np
#from opc_dummy_class import OPC
from opc_class import OPC
import json

TIMEOUT = 100
OK = 0
logging.basicConfig(format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    level=logging.DEBUG)


@spy_on
def COMMON_BEHAVIOUR(opc, e):
    status = return_status.UNHANDLED
    if e.signal == signals.ENTRY_SIGNAL:
        logging.info("Entered COMMON_BEHAVIOUR state")
        status = return_status.HANDLED
    elif e.signal == signals.hook:
        logging.info("hook event")
        status = return_status.HANDLED
    else:
        opc.temp.fun = opc.top
        status = return_status.SUPER
    return status


@spy_on
def DISABLED(opc, e):
    status = return_status.UNHANDLED
    if e.signal == signals.ENTRY_SIGNAL:
        logging.info("Entered DISABLED state")
        status = return_status.HANDLED
    elif e.signal == signals.enable_opc:
        logging.info("enable opc event recieved")
        status = opc.trans(ENABLED)
    else:
        opc.temp.fun = COMMON_BEHAVIOUR
        status = return_status.SUPER
    return status


@spy_on
def ENABLED(opc, e):
    status = return_status.UNHANDLED
    if e.signal == signals.ENTRY_SIGNAL:
        logging.info("Entered ENABLED state")
        opc.post_fifo(Event(signal=signals.start_comm))
        status = return_status.HANDLED
    elif e.signal == signals.start_comm:
        logging.info("start communication event")
        status = opc.trans(COMM_OFF)
    else:
        opc.temp.fun = COMMON_BEHAVIOUR
        status = return_status.SUPER
    return status


@spy_on
def COMM_OFF(opc, e):
    status = return_status.UNHANDLED
    if e.signal == signals.ENTRY_SIGNAL:
        logging.info("Entered COMM_OFF state")
        opc.post_fifo(Event(signal=signals.open_comm))
        status = return_status.HANDLED
    elif e.signal == signals.disable_opc:
        logging.info("disable opc event recieved")
        opc.laz_ctrl(False)
        opc.fan_ctrl(False)
        status = opc.trans(DISABLED)
    elif e.signal == signals.open_comm:
        if opc.init_opc() == OK:
            logging.info("communication established")
            status = opc.trans(COMM_ON)
        else:
            logging.info("trying to establish communication.....")
            opc.post_fifo(Event(signal=signals.open_comm))
            status = return_status.HANDLED
    else:
        opc.temp.fun = ENABLED
        status = return_status.SUPER
    return status


@spy_on
def COMM_ON(opc, e):
    status = return_status.UNHANDLED
    if e.signal == signals.ENTRY_SIGNAL:
        logging.info("Entered COMM_ON state")
        opc.post_fifo(Event(signal=signals.read_data))

        #opc.post_fifo(Event(signal=signals.read_data),
        #              times=0,
        #              period=1,
        #              deferred=True)
        status = return_status.HANDLED
    elif e.signal == signals.disable_opc:
        logging.info("disable opc event recieved")
        opc.laz_ctrl(False)
        opc.fan_ctrl(False)
        status = opc.trans(DISABLED)
    elif e.signal == signals.read_data:
        data = opc.read_data()
        print(data)
        data_json_string = json.dumps(data)
        if not data == -1:
            mqttc.publish("opc/data", payload=data_json_string, qos=2)
            opc.post_fifo(Event(signal=signals.read_data))
            status = return_status.HANDLED
        else:
            logging.info("comm failed !!!")
            status = opc.trans(COMM_OFF)
    elif e.signal == signals.EXIT_SIGNAL:
        logging.info("closing communication to OPC")
        opc.close_opc()
        #opc.cancel_events(Event(signal=signals.read_data))
    else:
        opc.temp.fun = ENABLED
        status = return_status.SUPER
    return status


def on_message(client, userdata, message):

    if message.payload == b'1':
        opc.post_fifo(Event(signal=signals.enable_opc))
    elif message.payload == b'0':
        opc.post_fifo(Event(signal=signals.disable_opc))
    else:
        print("doing nothing")
    return 0
    # print("Received message '" + str(message.payload) + "' on topic '"
    #     + message.topic + "' with QoS " + str(message.qos))


if __name__ == "__main__":

    # set an active object
    #opc = OPC(name='OPC', serial_port='/tty/USB0')
    opc = OPC(opc_name="some_opc",
              opc_port="/dev/ttyACM0",
              opc_location="the_forest")

    opc.live_trace = True
    # opc.live_spy = True

    mqttc = mqtt.Client(client_id=str(np.random.random()),
                        clean_session=True,
                        userdata=None)
    # opc.mqttc = mqttc
    opc.start_at(DISABLED)

    host = "localhost"
    port_num = 1883
    mqttc.connect_async(host, port=port_num, keepalive=60, bind_address="")
    mqttc.loop_start()
    time.sleep(0.1)
    mqttc.subscribe("opc/cmd", qos=2)
    mqttc.on_message = on_message

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        mqttc.loop_stop()
        mqttc.disconnect()
        print("Disconnected from Mosquitto broker")
    '''
    opc.establish_comm()
    opc.read_data_from_opc()
    opc.set_fan(True)
    opc.set_fan(False)
    opc.set_laser(True)
    opc.set_laser(False)
    '''
