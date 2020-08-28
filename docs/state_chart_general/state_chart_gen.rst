*****************************
trying statecharts as devices
*****************************

I am going to try a few statecharts to test if they are suitable for this project.
specifically I am going to need a thread that will be

1. Read from a device every X seconds
2. be responsive to commands

To be able to do that I will need a statechart that will the following states

1. init
2. idle
3. reading_status
4. setting_parameter
5. error

Now let's start with the init state. entering into the init state will

1. init the communication with instrument
2. init the parameters for outside communication using the MQTT mosquitto
3. if failed goto to the error state, inform the outside world and decide what to do next depending on the error.

Connecting the serial over RF to the raspberry:
dmesg | grep ttyUSB
[14785.320310] usb 1-1.3: FTDI USB Serial Device converter now attached to ttyUSB0
pppd proxyarp mtu 1280 persist nodeflate noauth lcp-echo-interval 10 crtscts lock 10.10.1.2:10.10.1.1 /dev/ttyUSB0 115200
the line that worked:
sudo pppd  -detach  noauth crtscts lock 10.10.1.1:10.10.1.2 /dev/ttyUSB0 115200 &
sudo kill pppd

to install pyqt on raspberry
sudo apt-get install qt5-default pyqt5-dev pyqt5-dev-tools
pip install --upgrade pip
pip install PyQt5

how to instlal rabbitmq-miros on raspberry:
sudo apt install libffi-dev
sudo apt install rabbitmq-server
pip install miros-rabbitmq

to configue rabbit-mq - run ansible
sudo apt install ansible
and follow this page:
https://aleph2c.github.io/miros-rabbitmq/html/installing_infrastructure.html#installing-infrastructure-installing-required-programs
