#!/bin/bash

caput opc:set_period 1
caput opc:enable 1
caput logger:enable 1
caput logger:save_interval 5
caput sniffer:enable 1
caput aeth:enable 1
