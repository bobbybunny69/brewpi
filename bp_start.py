#!/usr/bin/python3
"""
Initial Brew Pi start function - little in it
  v4:  Version that went off to internet and got brewfather data
  v5:  Use a brewpi.json file to load the steps to make robust to internet failure
  v6:  Use Asyncio for non-blocking reading of sensors to make UI more repsonsive
  v7:  Use MQTT sensors to get temperature data in to home assistant
  v8:  Update to use better MQTT used in brew-pico
"""
import brewfather as bf
import bpgui
from brewproc import Proc
from bp2mqtt import bp2mqtt

import logging, os, uuid
import asyncio

# ==== START USER INPUT ====
MQTT_HOST = "spklns04.speckly"     # host of your MQTT Broker
MQTT_PORT = 1883            # port of your MQTT Broker

json_file = "brewpi.json"
RIMS_pump = 1
# ======== END USER INPUT ==========

#loglevel = 'INFO'
loglevel = 'DEBUG'
logfile = None
#logfile = 'brewpi.log'

numeric_level = getattr(logging, loglevel.upper(), None)
if not isinstance(numeric_level, int):
    raise ValueError('Invalid log level: %s' % loglevel)
if(logfile == None):
    logging.basicConfig(format='%(asctime)s %(message)s', level=numeric_level)
else:
    logging.basicConfig(filename=logfile, filemode='w', format='%(asctime)s %(message)s', level=numeric_level)

# Get the os data for SSID being used and ipaddress to display on screen
ipaddress = os.popen('hostname -I').read()
ssid = os.popen('iwgetid --raw').read()
mac = hex(uuid.getnode())[2:]

# Load in the batch data using a json file (i.e. using json_load() function of class)
batch = bf.Batch() 
f = open(json_file, "r")
batch.json_load(f)
f.close()
#print(batch.json_print())

# Set-up the brewing process and define which input channel is the RIMS pump to protect heater
sensors = ["Mash", "HLT", "Boil", "RIMS"]
controllers = sensors[:2]
pumps = ["pump1", "pump2"]
RIMS_PUMP = 1
bproc = Proc(RIMS_PUMP)
bp_mqttc=None

# Start MQTT clients for HA publishing for each sensor in the brewproc
bp_mqttc=bp2mqtt("Brew Pi", mac, MQTT_HOST, MQTT_PORT, bproc)  # MAC used as unique ID
for s in sensors:
    bp_mqttc.create_sensor(s)
for c in controllers:
    bp_mqttc.create_controller(c)
for p in pumps:
    bp_mqttc.create_switch(p)

# Kickoff the tkinter loop with the breproc, batch and mqtt clients
asyncio.run(bpgui.App(bproc, batch, bp_mqttc, sensors, controllers, pumps, ipaddress, ssid).exec())

logging.info("Exiting BREWPI task")

