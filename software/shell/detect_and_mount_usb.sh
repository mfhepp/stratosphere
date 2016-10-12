#!/bin/sh

# ensure script is run as root
if [ $(id -u) -ne 0 ]
then
    echo "Please run as root"
    exit
fi


sda=$(blkid | awk '{print substr($1, 1, length($1)-1)}' | grep /dev/sd)

for volume in $sda
do
    size=$(sudo fdisk -l $volume | grep $volume | awk -F', ' '{print substr($2, 1, length($2)-6)}')
    echo $size
    # assume the usb partition is bigger than 30GB
    if [ "$size" -gt "30000000000" ]
    then
       echo $volume" is bigger"
       mount -t vfat -o uid=pi -o gid=pi $volume /media/usbstick
       if mount | grep $volume > /dev/null
       then
	   echo $volume" has been mounted"
       fi
    fi       
done