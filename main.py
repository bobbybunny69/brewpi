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
import logging, os
import asyncio

# ==== START USER INPUT ====
MQTT_HOST = "spklns04.speckly"     # host of your MQTT Broker
MQTT_PORT = 1883            # port of your MQTT Broker
json_file = "brewpi.json"
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

# Define the elements globally
RIMS_PUMP = 1
sensors = ["Mash", "HLT", "Boil", "RIMS"]
controllers = ["Mash", "HLT"]
switches = [{'name':'Pump-1', 'on_mode':'On', 'disabled':False },
            {'name':'Pump-2', 'on_mode':'On', 'disabled':False },
            {'name':'RIMS',   'on_mode':'Auto', 'disabled':True },
            {'name':'HLT',    'on_mode':'Auto', 'disabled':False }]

# Set-up the brewing process and define which input channel is the RIMS pump to protect heater
bproc = brewproc.Proc(RIMS_PUMP)
bp_mqttc=None

bpg = bpgui.BPGui(800, 480)
bpg.create_home_scrn()
bpg.create_quit_scrn()

def control_logic():
    if bproc.get_pump_state(RIMS_PUMP)==True:
        bpg.rims_switch.disabled = False
    else:
        bpg.rims_switch.disabled = True
    if bproc.controllers[0].get('allow_heat')=='off':
        bpg.p1_switch.disabled = False
    else:
        bpg.p1_switch.disabled = True

async def game_loop():
    running = True
    while running:
        if bpg.display_quit_screen:
            running = bpg.quit_event_handeller(bproc)
        else:
            running = bpg.event_handeller(bproc)
            control_logic()
            
        if bpg.display_quit_screen==False:
            bproc.RIMS_heat_ctrl()
            bproc.HLT_heat_ctrl()
        
        await bpg.update_scrn(bproc)

asyncio.run(game_loop())

logging.info("Exiting BREWPI task")
if bpg.shutdown_flag:
    logging.info("... and sgutting down")
    os.system("sleep 2 && sudo shutdown -P now")