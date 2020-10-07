import paho.mqtt.client as mqtt
import time
import numpy as np
import json
import pandas as pd

def on_message(client, userdata, message):
    #print("Received message '" + str(message.payload) + "' on topic '" +
    #      message.topic + "' with QoS " + str(message.qos))

    # transform data into a dictionary
    opc_dict = json.loads(message.payload)
    print(opc_dict)

mqttc = mqtt.Client(client_id=str(np.random.random()),
                    clean_session=True,
                    userdata=None)
host = "localhost"
port_num = 1883
mqttc.connect_async(host, port=port_num, keepalive=60, bind_address="")
mqttc.loop_start()
time.sleep(0.1)
mqttc.subscribe("opc/data", qos=2)
mqttc.on_message = on_message

# Read from config file which 
try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    mqttc.loop_stop()
    mqttc.disconnect()
    print("Disconnected from Mosquitto broker")


