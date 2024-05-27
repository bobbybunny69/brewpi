#!/usr/bin/python3.9

"""
Read all thermos and benchmark time taken
"""

import brewproc
import asyncio
import time
import logging, os

async def main():
    loglevel = 'INFO'
    #logfile = 'brewpi.log'
    #loglevel = 'DEBUG'
    logfile = None
    numeric_level = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_level, int):
       raise ValueError('Invalid log level: %s' % loglevel)
    if(logfile == None):
        logging.basicConfig(format='%(asctime)s %(message)s', level=numeric_level)
    else:
        logging.basicConfig(filename=logfile, filemode='w', format='%(asctime)s %(message)s', level=numeric_level)

    RIMS_pump = 1
    mash_target = 28
    sparge_target = 28
 
    bp=brewproc.Proc(RIMS_pump)
    bp.set_pump_state(1,1)

    sensor_task = asyncio.create_task (bp.async_update_sensors())
    while(1):
        tic = time.perf_counter()

        print(sensor_task.done())
        if(sensor_task.done() == True):
            print('Finished reading')
            sensor_task = asyncio.create_task (bp.async_update_sensors())

        for i in range(1,5):
            print('Sensor {} = {:5.1f}'.format(i,bp.get_sensor_val(i)))
        
        bp.RIMS_heat_ctrl()
        bp.HLT_heat_ctrl()

        for i in range(1,5):
            print('Relay {} = {:5.1f}'.format(i,bp.get_relay_state(i)))
  
        await asyncio.sleep(1)
        toc = time.perf_counter()
        print(f"Time taken: {toc - tic:0.4f} seconds")
        
asyncio.run(main())

logging.info("Exiting")

