import paho.mqtt.client as mqtt
import time
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, \
    QPushButton, QVBoxLayout, QWidget


def on_message(client, userdata, message):
   print("Received message '" + str(message.payload) + "' on topic '"
        + message.topic + "' with QoS " + str(message.qos))

def btn_enable_opc_evt():
    print("sent enable event to OPC")
    mqttc.publish("opc/cmd", payload="1", qos=2)
    

def btn_disable_opc_evt():
    print("sent disable event to OPC")
    mqttc.publish("opc/cmd", payload="0", qos=2)


mqttc = mqtt.Client(client_id=str(np.random.random()), clean_session=True, userdata=None)
host="localhost"
port_num = 1883
mqttc.connect_async(host, port=port_num, keepalive=60, bind_address="")
mqttc.loop_start()
time.sleep(0.1)
mqttc.subscribe("opc/data", qos=2)
mqttc.on_message = on_message

app = QApplication([])
win = QMainWindow()
central_widget = QWidget()
btn_enable_opc = QPushButton('Enable OPC', central_widget)
btn_disable_opc = QPushButton('Disable OPC', central_widget)

btn_enable_opc.clicked.connect(btn_enable_opc_evt)
btn_disable_opc.clicked.connect(btn_disable_opc_evt)

layout = QVBoxLayout(central_widget)
layout.addWidget(btn_enable_opc)
layout.addWidget(btn_disable_opc)
win.setCentralWidget(central_widget)
win.show()
app.exit(app.exec_())
mqttc.loop_stop()
mqttc.disconnect()
