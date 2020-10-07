# -*- coding: utf-8 -*-
"""
This is the OPC driver file
Programmer: Lior Segev
Date 03 September 2020
Version 0.0.1
Based on code by Daniel Jarvis

"""

from __future__ import print_function

#import datetime
#import sys
#import os.path
import logging
import struct
import time
import sys
from miros import ActiveObject
import serial

integration = 5

# NAMING VARIABLES
OPCNAME = "TestOPC"
OPCPORT = "/dev/ttyACM0"
LOCATION = "Lab2"
wait = 100e-06
OK = 0

log_format = '%(asctime)s %(filename)s: %(message)s'
logging.basicConfig(format=log_format, level=logging.INFO)


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
        self.comm = False
        self.laser_status = False
        self.fan_status = False
        logging.info("Instantiated OPC class on port " + self.OPCPORT)
        super().__init__()

    def init_opc(self):
        '''
        establish communication with OPC return OK if succedded and -1 if failed
        '''

        serial_opts = {
            "port": self.OPCPORT,
            "baudrate": 9600,
            "parity": serial.PARITY_NONE,
            "bytesize": serial.EIGHTBITS,
            "stopbits": serial.STOPBITS_ONE,
            "xonxoff": False,
            "timeout": 1
        }

        # wait for opc to boot
        time.sleep(2)

        logging.info('openning serial port to OPC ' + self.OPCPORT)
        try:
            self.ser = serial.Serial(**serial_opts)
            self.comm = True
        except serial.serialutil.SerialException:
            logging.info(
                'communication failed - check USB connection to raspberry PI host'
            )
            self.comm = False
            return -1
        logging.info('initializing communication with OPC')
        # print("Init:")
        time.sleep(1)
        self.ser.write(bytearray([0x5a, 0x01]))
        nl = self.ser.read(3)
        time.sleep(wait)
        self.ser.write(bytearray([0x5a, 0x03]))
        nl = self.ser.read(9)
        time.sleep(wait)

        # spi conncetion
        self.ser.write(bytearray([0x5a, 0x02, 0x92, 0x07]))
        nl = self.ser.read(2)
        time.sleep(wait)

        # turn on Lazer and Fan for the correct operation of the OPC
        self.laz_ctrl(True)
        self.fan_ctrl(True)

        return OK

    def close_opc(self):
        logging.info('closing serial port ' + self.OPCPORT)
        self.ser.close()

    def fan_ctrl(self, ctrl_flag=False):
        '''
        opc fan control by sending true to turn it on and false to turn it off
        '''
        T = 0
        while True:
            self.ser.write(bytearray([0x61, 0x03]))
            nl = self.ser.read(2)
            T = T + 1
            if nl == (b"\xff\xf3" or b"xf3\xff"):
                time.sleep(wait)
                if ctrl_flag:
                    # fan on
                    logging.info("Request Fan to turn ON")
                    self.ser.write(bytearray([0x61, 0x03]))
                    nl = self.ser.read(2)
                    self.fan_status = True
                    logging.info("Fan ON")
                    time.sleep(2)
                    return 0  # success
                else:
                    logging.info("Request Fan to turn OFF")
                    self.ser.write(bytearray([0x61, 0x02]))
                    nl = self.ser.read(2)
                    self.fan_status = False
                    logging.info("Fan OFF")
                    time.sleep(2)
                    return 0  # success
            elif T > 20:
                logging.info("Reset SPI")
                time.sleep(3)  # time for spi buffer to reset
                # reset SPI  conncetion
                self.init_opc()
                T = 0
            else:
                time.sleep(wait * 10)

    # Lazer on   0x07 is SPI byte following 0x03 to turn laser ON.
    def laz_ctrl(self, laser_flag=False):
        '''
        opc fan control by sending true to turn it on and false to turn it off
        '''

        T = 0  # Triese counter
        while True:
            self.ser.write(bytearray([0x61, 0x03]))
            nl = self.ser.read(2)
            T = T + 1
            if nl == (b"\xff\xf3" or b"xf3\xff"):
                time.sleep(wait)
                if laser_flag:
                    # Lazer on
                    logging.info("Request laser to turn ON")
                    self.ser.write(bytearray([0x61, 0x07]))
                    nl = self.ser.read(2)
                    time.sleep(wait)
                    self.laser_status = True
                    logging.info("Laser is ON")
                    return 0  # 0 error means success
                else:
                    # Lazer off
                    logging.info("Request laser to turn OFF")
                    self.ser.write(bytearray([0x61, 0x06]))
                    nl = self.ser.read(2)
                    time.sleep(wait)
                    self.laser_status = False
                    logging.info("Laser is OFF")
                    return 0  # 0 error means success
            elif T > 20:
                logging.info("Reset SPI")
                time.sleep(3)  # time for spi buffer to reset
                # reset SPI  conncetion
                self.init_opc()
                T = 0
            else:
                time.sleep(wait * 10)  # wait 1e-05 before next commnad

    def rightbytes(self, response):
        '''
        Get ride of the 0x61 byeste responce from the hist data,
        returning just the wanted data
        '''
        hist_response = []
        for j, k in enumerate(response):
            # Each of the 86 bytes we expect to be returned is prefixed
            # by 0xFF.
            if ((j + 1) % 2) == 0:  # Throw away 0th, 2nd, 4th, 6th bytes, etc.
                hist_response.append(k)
        return hist_response

    def RHcon(self, ans):
        '''
        ans is  combine_bytes(ans[52],ans[53])
        '''
        RH = 100 * (ans / (2**16 - 1))
        return RH

    def Tempcon(self, ans):
        '''
        ans is  combine_bytes(ans[52],ans[53])
        '''
        Temp = -45 + 175 * (ans / (2**16 - 1))
        return Temp

    def combine_bytes(self, LSB, MSB):
        return (MSB << 8) | LSB

    def Histdata(self, ans):
        '''
        function to read all the hist data, to break up the getHist
        '''

        data = {}
        data['Bin 0'] = self.combine_bytes(ans[0], ans[1])
        data['Bin 1'] = self.combine_bytes(ans[2], ans[3])
        data['Bin 2'] = self.combine_bytes(ans[4], ans[5])
        data['Bin 3'] = self.combine_bytes(ans[6], ans[7])
        data['Bin 4'] = self.combine_bytes(ans[8], ans[9])
        data['Bin 5'] = self.combine_bytes(ans[10], ans[11])
        data['Bin 6'] = self.combine_bytes(ans[12], ans[13])
        data['Bin 7'] = self.combine_bytes(ans[14], ans[15])
        data['Bin 8'] = self.combine_bytes(ans[16], ans[17])
        data['Bin 9'] = self.combine_bytes(ans[18], ans[19])
        data['Bin 10'] = self.combine_bytes(ans[20], ans[21])
        data['Bin 11'] = self.combine_bytes(ans[22], ans[23])
        data['Bin 12'] = self.combine_bytes(ans[24], ans[25])
        data['Bin 13'] = self.combine_bytes(ans[26], ans[27])
        data['Bin 14'] = self.combine_bytes(ans[28], ans[29])
        data['Bin 15'] = self.combine_bytes(ans[30], ans[31])
        data['Bin 16'] = self.combine_bytes(ans[32], ans[33])
        data['Bin 17'] = self.combine_bytes(ans[34], ans[35])
        data['Bin 18'] = self.combine_bytes(ans[36], ans[37])
        data['Bin 19'] = self.combine_bytes(ans[38], ans[39])
        data['Bin 20'] = self.combine_bytes(ans[40], ans[41])
        data['Bin 21'] = self.combine_bytes(ans[42], ans[43])
        data['Bin 22'] = self.combine_bytes(ans[44], ans[45])
        data['Bin 23'] = self.combine_bytes(ans[46], ans[47])
        data['MToF'] = struct.unpack('f', bytes(
            ans[48:52]))[0]  # MTof is in 1/3 us, value of 10=3.33us
        data['period'] = self.combine_bytes(ans[52], ans[53])
        data['FlowRate'] = self.combine_bytes(ans[54], ans[55])
        data['OPC-T'] = self.Tempcon(self.combine_bytes(ans[56], ans[57]))
        data['OPC-RH'] = self.RHcon(self.combine_bytes(ans[58], ans[59]))
        data['pm1'] = struct.unpack('f', bytes(ans[60:64]))[0]
        data['pm2.5'] = struct.unpack('f', bytes(ans[64:68]))[0]
        data['pm10'] = struct.unpack('f', bytes(ans[68:72]))[0]
        data['Check'] = self.combine_bytes(ans[84], ans[85])
        data['comm'] = self.comm
        data['laser_status'] = self.laser_status
        data['fan_status'] = self.fan_status

        return (data)

    # get hist data
    def read_data(self):
        '''
        Read all data from OPC
        '''
        T = 0  # attemt varaible
        while True:
            logging.info("Request data from OPC")

            # request the hist data set
            self.ser.write([0x61, 0x30])
            # time.sleep(wait*10)
            nl = self.ser.read(2)
            T = T + 1
            if nl == (b'\xff\xf3' or b'\xf3\xff'):
                for i in range(86):  # Send bytes one at a time
                    self.ser.write([0x61, 0x01])
                    time.sleep(0.000001)

                time.sleep(wait)  # delay
                ans = bytearray(self.ser.readall())
                ans = self.rightbytes(ans)  # get the wanted data bytes
                data = self.Histdata(ans)
                logging.info("Read all data from the OPC")
                return data
            if T > 20:
                logging.info("Reset SPI")
                time.sleep(wait)  # time for spi buffer to reset
                self.init_opc()
                return -999  # error data was not read from the OPC
            else:
                time.sleep(wait * 10)  # wait 1e-05 before next commn


if __name__ == '__main__':
    opc = OPC(opc_name="some_opc",
              opc_port="/dev/ttyACM0",
              opc_location="the_forest")
    if not opc.init_opc() == OK:
        sys.exit()
    time.sleep(2)
    opc.fan_ctrl(True)
    opc.laz_ctrl(True)
    for i in range(10):
        print(opc.read_data())
    opc.fan_ctrl(False)
    opc.laz_ctrl(False)
    opc.close_opc()
