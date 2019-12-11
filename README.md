# gpio_controller
A gpio controller on Raspberry PI platform

### Raspbian configuration

#### OS type

Raspbian-buster-lite

#### Libraries

* Python
  * pyserial
  * RPi.GPIO
  * crcmod

#### PI configurations

* SSH: Enabled
* serial console: disabled
* serial hardware support: enabled
* swap UART hardware channel
  * Add **enable_uart=1** and **dtoverlay=pi3-miniuart-bt** at the end of `/boot/config.txt`
  * sudo systemctl stop serial-getty@ttyAMA0.service
  * sudo systemctl disable serial-getty@ttyAMA0.service
  * Remove `console=...` in `/boot/cmdline.txt`



**Note** server should be little endian

### Deploy methods

* [Create a custom Raspbian OS image for production](https://medium.com/platformer-blog/creating-a-custom-raspbian-os-image-for-production-3fcb43ff3630)
