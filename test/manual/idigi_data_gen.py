#!/usr/bin/python2.7
'''
A test tool to generate a stream of idigi_data test samples.
'''

import sys
import random
import time

sys.path.insert(0, "../../src/library/ext")

import serial

def idigi_data_generator(num_channels=1, generations=-1):
    CHANNEL_TEMPLATE="test_channel_%d"
    UNIT_TEMPLATE="unit_%d"
    while 1:
        if generations == 0:
            break
        str = "idigi_data:names="
        str += ','.join([ CHANNEL_TEMPLATE % i for i in range(num_channels) ])
        str += "&values="
        str += ','.join([ "%.2f" % random.uniform(1,10) for i in range(num_channels) ])
        str += "&units="
        str += ','.join([ UNIT_TEMPLATE % i for i in range(num_channels) ])
        str += "\r\n"
        yield str
        generations -= 1

def main():
    port=serial.Serial(port=sys.argv[1], baudrate=115200, rtscts=True)
    for s in idigi_data_generator(5):
        print "Sending: %s" % (repr(s.strip()))
        port.write(s)
        time.sleep(0.500)
    port.close()
    
    return 0

if __name__ == "__main__":
    ret = main()
    sys.exit(ret)

        
