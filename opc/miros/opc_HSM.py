# OPC is the active object that has the following specifications:
# 1. It will establish communication with OPC (enter exact model name here)
# 2. It will fail, it will try again endlessly every X seconds (parameter)
# 3. Upon succes it will read the OPC data every Y seconds (parameter)
# 4. Transmit the data over another all subscribed statecharts. (the important one is the logger statechart and influxDB)
# 4a. it can also be statechart over the network on a remote pc (via RF serial link via PPP)
# 5. It will be able accept control commands to start the laser or the pump for example

from PyQt5.QtWidgets import QApplication, QMainWindow, \
    QPushButton, QVBoxLayout, QWidget

import time

from miros import Event
from miros import spy_on
from miros import signals
from miros import ActiveObject
from miros import return_status
import logging
import numpy as np

TIMEOUT = 100
OK = 0 
logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.DEBUG)

class OPC(ActiveObject):
  def __init__(self, name, serial_port='/tty/USB0'):
    self.serial_port = serial_port
    super().__init__(name)

  def establish_comm(self):
    logging.info('established communication')
    return OK # error code that everything went fine

  def read_data_from_opc(self):
    logging.info('reading data from OPC')
    data = 1
    return data

  def set_fan(self, state=False):
    logging.info('setting the fan to ' + str(state))
    return OK

  def set_laser(self, state=False):
    logging.info('setting the laser to ' + str(state))

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
      status = opc.trans(DISABLED) 
  elif e.signal == signals.open_comm:
    time.sleep(0.1)
    if np.random.random() > 0.9:
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
    opc.post_fifo(
          Event(signal=signals.read_data),
          times=0,
          period=1,
          deferred=True)
    status = return_status.HANDLED
  elif e.signal == signals.disable_opc:
      logging.info("disable opc event recieved")
      status = opc.trans(DISABLED) 
  elif e.signal == signals.read_data:
    if np.random.random() > 0.2:
      logging.info("reading data from OPC...")
      status = return_status.HANDLED
    else:
      logging.info("comm failed !!!")
      status = opc.trans(COMM_OFF)
  elif e.signal == signals.EXIT_SIGNAL:
    logging.info("closing communication to OPC")
    opc.cancel_events(Event(signal=signals.read_data)) 
  else:
    opc.temp.fun = ENABLED
    status = return_status.SUPER
  return status

def btn_enable_opc_evt():
    print("sent enable event to OPC")
    opc.post_fifo(Event(signal=signals.enable_opc))

def btn_disable_opc_evt():
    print("sent disable event to OPC")
    opc.post_fifo(Event(signal=signals.disable_opc))
  
if __name__ == "__main__":
  
  # set an active object
  opc = OPC(name='OPC', serial_port='/tty/USB0')
  opc.live_trace = True
  #opc.live_spy = True
  opc.start_at(DISABLED)
  
  '''
  opc.establish_comm()
  opc.read_data_from_opc()
  opc.set_fan(True)
  opc.set_fan(False)
  opc.set_laser(True)
  opc.set_laser(False)
  '''


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
