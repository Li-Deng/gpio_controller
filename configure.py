default_config_info = {
    "serial": {
        "port": "/dev/serial0",
        "port_pc": "/dev/tty.usbserial-0001",
        "baudrate": 115200, 
        "bytesize": 8,
        "parity": "even",
        "stopbits": 1,
        "timeout": None,
        "xonxoff": False,
    },
    "pin_map": {
        "node": {
            "norm": 33,
            "err": 31,
            "sync": 29,
        },
        "network": {
            "norm": 32,
            "err": 37,
            "rec": 35
        },
        "storage": {
            "norm": 40,
            "err": 38,
            "rec": 36
        }
    },
    "interval": 0.5,
    "led_light_voltage": False,
    "led_dark_voltage": True
}
