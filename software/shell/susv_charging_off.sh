#!/bin/sh
# Turn off battery charging for S.USV

# Ensure script is run as root
if [ $(id -u) -ne 0 ]
then
    echo "Please run as root."
    exit
fi

echo "Turning OFF charging for S.USV."
sudo i2cset -y 1 0x0f 0x27
