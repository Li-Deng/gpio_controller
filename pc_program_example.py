#!/usr/bin/python

# PC program example
# provide an example of interacting
# prerequisties:
#    1. python 2.7
#    2. pyserial
#    3. crcmod 

from multiprocessing import Process, Manager
import struct
import pprint
import time
import sys
import os

import configure

try:
    import crcmod.predefined
    import serial
except Exception as e:
    print "Unexpected error when importing modules:\n %s" % (str(e), )

# global variables used for configurations. won't be shared across processes
config_info = {
    "serial": {
        "port_pc": "",
        "baudrate": 115200,
        "bytesize": serial.EIGHTBITS,
        "parity": serial.PARITY_EVEN,
        "stopbits": serial.STOPBITS_ONE,
        "timeout": None,  # read timeout
        "xonxoff": False,  # software flow control
    },
    "interval": 1.0,  # global interval as a standard
}

# create the crc function
crc8_func = crcmod.predefined.mkCrcFun('crc-8')

# example bytes array which will be used in the 3rd byte position and
# indicate each individual LED states
test_data = [
    192,
    64,
    48,
    16,
    15,
    8,
    4,
    2,
    1,
    0
]

def initialization():
    '''
    Read configurations and update the global variable
    '''
    global config_info
 
    # check if the configurations are valid
    if not configure.default_config_info:
        print "Error: the configuration file is empty!"
        return False

    config_info = configure.default_config_info
    if "even" == config_info["serial"]["parity"]:
        config_info["serial"]["parity"] = serial.PARITY_EVEN
    elif "odd" == config_info["serial"]["parity"]:
        config_info["serial"]["parity"] = serial.PARITY_ODD

    if 1 == config_info["serial"]["stopbits"]:
        config_info["serial"]["stopbits"] = serial.STOPBITS_ONE
    elif 1.5 == config_info["serial"]["stopbits"]:
        config_info["serial"]["stopbits"] = serial.STOPBITS_ONE_POINT_FIVE
    elif 2 == config_info["serial"]["stopbits"]:
        config_info["serial"]["stopbits"] = serial.STOPBITS_TWO

    if 8 == config_info["serial"]["bytesize"]:
        config_info["serial"]["bytesize"] = serial.EIGHTBITS
    elif 7 == config_info["serial"]["bytesize"]:
        config_info["serial"]["bytesize"] = serial.SEVENBITS
    elif 6 == config_info["serial"]["bytesize"]:
        config_info["serial"]["bytesize"] = serial.SIXBITS
    elif 5 == config_info["serial"]["bytesize"]:
        config_info["serial"]["bytesize"] = serial.FIVEBITS
 
    print "Initialization finished, current configuration:"
    print pprint.pformat(config_info)
    return True


def unpack(input):
    '''
    convert the byte string value read from serial to integer
    '''
    if 1 != len(input):
        return 0

    val = struct.unpack('<B', input)
    if len(val) < 1:
        return 0
    else:
        return val[0]


def create_data_frame(control_byte = 0):
    '''
    create a frame data based on control_byte
    '''
    # checksum verification
    crc_input = "%d%d%d" % (0x55, 0xaa, control_byte, )
    frame_crc_checksum = crc8_func(crc_input)
    return bytearray([0x55, 0xaa, control_byte, frame_crc_checksum])


def main():
    if False == initialization():
        print "Initialization failed! Abort execution."
        return

    ser_conf = config_info["serial"]

    # read buffer
    data_frame = bytearray(4)

    with serial.Serial(ser_conf["port_pc"],
                       ser_conf["baudrate"],
                       bytesize = ser_conf["bytesize"],
                       parity = ser_conf["parity"],
                       stopbits = ser_conf["stopbits"],
                       timeout = ser_conf["timeout"],
                       xonxoff = ser_conf["xonxoff"]) as ser:
        # open the serial port
        if False == ser.is_open:
            ser.open()

        while True:
            for s in test_data:
                data_frame = create_data_frame(s)
                ser.write(data_frame)
                time.sleep(3)

        ser.close()

    return


if "__main__" == __name__:
    try:
        main()
    except KeyboardInterrupt:
        sys.exit()
    except Exception as e:
        print "Unexpected error: %s" % (str(e))
        sys.exit()
