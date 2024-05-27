#!/bin/bash
# Copy files to brewpi.speckly

mountpoint -q /mnt/brewpi || sshfs rob@brewpi.speckly:/home/rob /mnt/brewpi

files='bp_start.py bpgui.py brewfather.py brewproc.py bp2mqtt.py brewpi.service brewpi.json'

for file in $files
do
cp -v -u $file /mnt/brewpi
done
echo All done
