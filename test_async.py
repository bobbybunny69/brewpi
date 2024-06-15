#!/usr/bin/python
"""
Test async sensor access and play around with it
"""
import time
import logging
from w1thermsensor import AsyncW1ThermSensor, Sensor, W1ThermSensorError
import asyncio
import brewproc

loglevel = 'DEBUG'
numeric_level = getattr(logging, loglevel.upper(), None)
if not isinstance(numeric_level, int):
    raise ValueError('Invalid log level: %s' % loglevel)
logging.basicConfig(format='%(asctime)s %(message)s', level=numeric_level)
                         
async def update():
    sensors = ["Mash", "HLT", "Boil", "RIMS"]
    bp = brewproc.Proc(1)

    tic = time.perf_counter()
    task = None
    i = 0
    while i<10:
        await bp.async_read_sensor(sensors[0])
        toc = time.perf_counter()
        logging.info(task)
        logging.info(f"Time taken: {toc - tic:0.4f} seconds")
        logging.info(bp.sensors)
        await asyncio.sleep(0.5)
        i+=1

asyncio.run(update())