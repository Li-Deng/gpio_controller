default_config_info = {
    "serial": {
        "port": "/dev/serial0",
        "port_pc": "/dev/tty.usbserial-14240",
        "baudrate": 115200,
        "bytesize": 8,
        "parity": "even",
        "stopbits": 1,
        "timeout": None,
        "xonxoff": False,
    },
    "pin_map": {
        "node": {
            "norm": 29,
            "err": 31,
            "sync": 33,
        },
        "network": {
            "norm": 35,
            "err": 37,
            "rec": 32
        },
        "storage": {
            "norm": 36,
            "err": 38,
            "rec": 40
        }
    },
    "interval": 0.5,
    "led_light_voltage": False,
    "led_dark_voltage": True
}
