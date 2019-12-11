#!/usr/bin/python

# GPIO controller
# 1. Implementation of GPIO driver
# 2. Control LED states via GPIO driver
# 3. Define and realize serial communication protocol
# 4. Listen on serial ports and parse incomming packets

from multiprocessing import Process, Manager
import struct
import pprint
import time
import sys
import os

import configure

try:
    import RPi.GPIO as GPIO
    import crcmod.predefined
    import serial
except Exception as e:
    print "Unexpected error when importing modules:\n %s" % (str(e), )

# global variables used for configurations. won't be shared across processes
config_info = {
    "serial": {
        "port": "",
        "baudrate": 115200,
        "bytesize": serial.EIGHTBITS,
        "parity": serial.PARITY_EVEN,
        "stopbits": serial.STOPBITS_ONE,
        "timeout": None,  # read timeout
        "xonxoff": False,  # software flow control
    },
    "pin_map": {
        "node": {
            "norm": 0,
            "err": 0,
            "sync": 0,
        },
        "network": {
            "norm": 0,
            "err": 0,
            "rec": 0
        },
        "storage": {
            "norm": 0,
            "err": 0,
            "rec": 0
        }
    },
    "interval": 1.0,  # global interval as a standard
}

# global variables used for led states. will be shared across processes
manager = Manager()
node_state = manager.dict()
network_state = manager.dict()
storage_state = manager.dict()

node_state["state"] = "norm"

network_state["state"] = "norm"
network_state["err_port"]  = 0

storage_state["state"] = "norm"

LED_LIGHT = True
LED_DARK  = False


def initialization():
    '''
    Read configurations and update the global variable
    '''
    global config_info
    global LED_LIGHT
    global LED_DARK
 
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

    if True == config_info["led_light_voltage"]:
        LED_LIGHT = GPIO.HIGH
    else:
        LED_LIGHT = GPIO.LOW

    if True == config_info["led_dark_voltage"]:
        LED_DARK = GPIO.HIGH
    else:
        LED_DARK = GPIO.LOW
 
    print "Initialization finished, current configuration:"
    print pprint.pformat(config_info)
    return True


def node_led_controller(pin_norm, pin_err, pin_sync, interval = 1.0):
    '''
    poll the status of led_node from serial communication and set
    corresponding GPIO pins
    Args:
        pin_norm: pin number for normal state
        pin_err: pin number for error state
        pin_sync: pin number for sync state
        interval: time period before checking global variables in a loop
    '''
    pin_list = [pin_norm, pin_err, pin_sync]
    GPIO.setup(pin_list, GPIO.OUT, initial = LED_DARK)
    blink_inter = 0.5

    while True:
        last_state_norm = GPIO.input(pin_norm)
        last_state_err = GPIO.input(pin_err)

        if "norm" == node_state["state"]:
            # check if the norm pin is already high
            if LED_DARK == last_state_norm:
                # set low on err pin if necessary
                if LED_LIGHT == last_state_err:
                    GPIO.output(pin_err, LED_DARK)
                GPIO.output(pin_norm, LED_LIGHT)
            time.sleep(interval)

        elif "err" == node_state["state"]:
            # check if the err pin is already high
            if LED_DARK == last_state_err:
                # set low on norm pin if necessary
                if LED_LIGHT == last_state_norm:
                    GPIO.output(pin_norm, LED_DARK)
                GPIO.output(pin_err, LED_LIGHT)
            time.sleep(interval)

        elif "sync" == node_state["state"]:
            # set low on other pins if necessary
            if LED_LIGHT == last_state_norm:
                GPIO.output(pin_norm, LED_DARK)
            if LED_LIGHT == last_state_err:
                GPIO.output(pin_err, LED_DARK)
            # blink sync pin
            GPIO.output(pin_sync, LED_LIGHT)
            time.sleep(blink_inter)
            GPIO.output(pin_sync, LED_DARK)
            time.sleep(blink_inter)


def network_led_controller(pin_norm, pin_err, pin_rec, interval = 1.0):
    '''
    poll the status of network_node from serial communication and
    set corresponding GPIO pins
    Args:
        pin_norm: pin number for normal state
        pin_err: pin number for error state
        pin_rec: pin number for recover state
        interval: time period before checking global variables in a loop
    '''
    pin_list = [pin_norm, pin_err, pin_rec]
    GPIO.setup(pin_list, GPIO.OUT, initial = LED_DARK)
    blink_inter = 0.5
    # the display of network error requires longer duration
    blink_inter_short = 0.2

    while True:
        last_state_norm = GPIO.input(pin_norm)
        last_state_err = GPIO.input(pin_err)

        if "norm" == network_state["state"]:
            if LED_DARK == last_state_norm:
                GPIO.output(pin_norm, LED_LIGHT)
            time.sleep(interval)
        elif "err" == network_state["state"]:
            if LED_LIGHT == last_state_norm:
                GPIO.output(pin_norm, LED_DARK)
            if 1 == network_state["err_port"]:
                GPIO.output(pin_err, LED_LIGHT)
                time.sleep(blink_inter_short)
                GPIO.output(pin_err, LED_DARK)
                time.sleep(interval)
            elif 2 == network_state["err_port"]:
                for i in range(2):
                    GPIO.output(pin_err, LED_LIGHT)
                    time.sleep(blink_inter_short)
                    GPIO.output(pin_err, LED_DARK)
                    time.sleep(blink_inter_short)
                time.sleep(interval)

            elif 3 == network_state["err_port"]:
                for i in range(3):
                    GPIO.output(pin_err, LED_LIGHT)
                    time.sleep(blink_inter_short)
                    GPIO.output(pin_err, LED_DARK)
                    time.sleep(blink_inter_short)
                time.sleep(interval)

            elif 4 == network_state["err_port"]:
                for i in range(4):
                    GPIO.output(pin_err, LED_LIGHT)
                    time.sleep(blink_inter_short)
                    GPIO.output(pin_err, LED_DARK)
                    time.sleep(blink_inter_short)
                time.sleep(interval)

        elif "rec" == network_state["state"]:
            if LED_LIGHT == last_state_norm:
                GPIO.output(pin_norm, LED_DARK)
            GPIO.output(pin_rec, LED_LIGHT)
            time.sleep(blink_inter)
            GPIO.output(pin_rec, LED_DARK)
            time.sleep(blink_inter)


def storage_led_controller(pin_norm, pin_err, pin_rec, interval = 1):
    '''
    poll the status of led_storage from serial communication and set
    corresponding GPIO pins
    Args:
        pin_norm: pin number for normal state
        pin_err: pin number for error state
        pin_rec: pin number for sync state
        interval: time period before checking global variables in a loop
    '''
    pin_list = [pin_norm, pin_err, pin_rec]
    GPIO.setup(pin_list, GPIO.OUT, initial = LED_DARK)
    blink_inter = 0.5

    while True:
        last_state_norm = GPIO.input(pin_norm)
        last_state_err = GPIO.input(pin_err)

        if "norm" == storage_state["state"]:
            # check if the norm pin is already high
            if LED_DARK == last_state_norm:
                # set low on err pin if necessary
                if LED_LIGHT == last_state_err:
                    GPIO.output(pin_err, LED_DARK)
                GPIO.output(pin_norm, LED_LIGHT)
            time.sleep(interval)

        elif "err" == storage_state["state"]:
            # check if the err pin is already high
            if LED_DARK == last_state_err:
                # set low on norm pin if necessary
                if LED_LIGHT == last_state_norm:
                    GPIO.output(pin_norm, LED_DARK)
                GPIO.output(pin_err, LED_LIGHT)
            time.sleep(interval)

        elif "rec" == storage_state["state"]:
            # set low on other pins if necessary
            if LED_LIGHT == last_state_norm:
                GPIO.output(pin_norm, LED_DARK)
            if LED_LIGHT == last_state_err:
                GPIO.output(pin_err, LED_DARK)
            # blink sync pin
            GPIO.output(pin_rec, LED_LIGHT)
            time.sleep(blink_inter)
            GPIO.output(pin_rec, LED_DARK)
            time.sleep(blink_inter)


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


def main():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False) # DEBUG

    if False == initialization():
        print "Initialization failed! Abort execution."
        return

    ser_conf = config_info["serial"]
    pin_conf = config_info["pin_map"]
    # create process objects
    p_node = Process(target = node_led_controller,
                    args = (pin_conf["node"]["norm"], 
                            pin_conf["node"]["err"], 
                            pin_conf["node"]["sync"], 
                            config_info["interval"]))
    p_network = Process(target = network_led_controller,
                    args = (pin_conf["network"]["norm"], 
                            pin_conf["network"]["err"], 
                            pin_conf["network"]["rec"],
                            config_info["interval"]))
    p_storage = Process(target = storage_led_controller,
                    args = (pin_conf["storage"]["norm"], 
                            pin_conf["storage"]["err"], 
                            pin_conf["storage"]["rec"], 
                            config_info["interval"]))

    process_list = [
        {
            "name": "node_led",
            "object": p_node
        },
        {
            "name": "network_led",
            "object": p_network
        },
        {
            "name": "storage_led",
            "object": p_storage
        }
    ]

    # start processes
    for item in process_list:
        item["object"].start()
        print "Controller %s started!" % (item["name"], )

    # create the crc function
    crc8_func = crcmod.predefined.mkCrcFun('crc-8')
    # read buffer
    data_frame = bytearray(4)
    data_frame[0] = 0x55
    data_frame[1] = 0xaa
    rd_byte = 0
    crc_input = ""
    frame_crc_checksum = 0

    with serial.Serial(ser_conf["port"],
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
            # read incoming byte stream
            if ser.inWaiting() > 0:
                # check if the header is valid
                rd_byte = unpack(ser.read())
                if 0x55 != rd_byte:
                    continue
                rd_byte = unpack(ser.read())
                if 0xaa != rd_byte:
                    continue
            else:
                time.sleep(config_info["interval"])
                continue

            # read the remaining bytes
            data_frame[2] = unpack(ser.read())
            data_frame[3] = unpack(ser.read())

            # checksum verification
            crc_input = "%d%d%d" % (data_frame[0], data_frame[1], data_frame[2], )
            frame_crc_checksum = crc8_func(crc_input)
            if frame_crc_checksum != data_frame[3]:
                # checksum byte is not valid. drop this packet
                continue

            # parse frame body
            node_seg = data_frame[2] & 192    # extract bits 6, 7
            storage_seg = data_frame[2] & 48  # extract bits 4, 5
            network_seg = data_frame[2] & 15  # extract bits 0, 1, 2, 3

            # set global states according to the communication protocol
            if 0 == node_seg:
                node_state["state"] = "norm"
            elif 64 == node_seg:
                node_state["state"] = "sync"
            elif 192 == node_seg:
                node_state["state"] = "err"

            if 0 == storage_seg:
                storage_state["state"] = "norm"
            elif 16 == storage_seg:
                storage_state["state"] = "rec"
            elif 48 == storage_seg:
                storage_state["state"] = "err"

            if 0 == network_seg:
                network_state["state"] = "norm"
            elif 15 == network_seg:
                network_state["state"] = "rec"
            elif 1 == network_seg:
                network_state["state"] = "err"
                network_state["err_port"] = 1
            elif 2 == network_seg:
                network_state["state"] = "err"
                network_state["err_port"] = 2
            elif 4 == network_seg:
                network_state["state"] = "err"
                network_state["err_port"] = 3
            elif 8 == network_seg:
                network_state["state"] = "err"
                network_state["err_port"] = 4

            # TODO: check if each of the 3 processes is alive. Reboot system otherwise (os.system("reboot"))

        ser.close()

    for item in process_list:
        item["object"].join()
        print "Controller %s ended!" % (item["name"], )

    GPIO.cleanup()
    return


if "__main__" == __name__:
    try:
        main()
    except KeyboardInterrupt:
        GPIO.cleanup()
        sys.exit()
    except Exception as e:
        print "Unexpected error: %s" % (str(e))
        GPIO.cleanup()
        sys.exit()
