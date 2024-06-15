#!/usr/bin/python3
"""
Initial Brew Pi start function - little in it
  v4:  Version that went off to internet and got brewfather data
  v5:  Use a brewpi.json file to load the steps to make robust to internet failure
  v6:  Use Asyncio for non-blocking reading of sensors to make UI more repsonsive
  v7:  Use MQTT sensors to get temperature data in to home assistant
  v8:  Update to use better MQTT used in brew-pico
  v9:  Switch to pygame
"""
from bp2mqtt import bp2mqtt
import bpgui
import brewproc
import logging
import asyncio

# ==== START USER INPUT ====
MQTT_HOST = "spklns04.speckly"     # host of your MQTT Broker
MQTT_PORT = 1883            # port of your MQTT Broker
json_file = "brewpi.json"
RIMS_pump = 1
screen_x = 800
screen_y = 480
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

# Set-up the brewing process and define which input channel is the RIMS pump to protect heater
sensors = ["Mash", "HLT", "Boil", "RIMS"]
controllers = sensors[:2]
pumps = ["pump1", "pump2"]
RIMS_PUMP = 1
bproc = brewproc.Proc(RIMS_PUMP)
bp_mqttc=None

bpg = bpgui.BPGui(screen_x, screen_y)
bpg.create_home_scrn()

async def game_loop():
    running = True
    while running:
        running = bpg.event_handeller(bproc)
        bproc.RIMS_heat_ctrl()
        bproc.HLT_heat_ctrl()
        await bpg.update_scrn(bproc)

asyncio.run(game_loop())

logging.info("Exiting BREWPI task")
