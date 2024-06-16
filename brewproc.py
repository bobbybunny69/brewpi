from w1thermsensor import AsyncW1ThermSensor, W1ThermSensor, Sensor, W1ThermSensorError
import RPi.GPIO as GPIO
import logging
import time

RIMS_delta = 2
temp_delta = 0.5
ON = 1
OFF = 0
OFF_TEMP = 0
NULL_TEMP = 99

"""
    Brew Proc class for brewing control 
    Takes 3 inputs: RIMS pump number, and Mash and HLT temperature targets
    Consists of:
      4 x sensors
      4x relays which can be accessed as a relay list or as atomic elements, which are
          2x pumps as a list
          1x RIMS heater
          1x HLT heater          
   Funtions are included to:
      uodate all sensors and then get individual values via index
      set/get states (NOTE: with RIMS heat/pump overides)
      RIMS and HLT control functions
"""
class Proc:
    def __init__(self, rims_pump):
        logging.info("Brew Proc __init__ called, initializing")
        GPIO.setmode(GPIO.BCM)
        self.relay_chans = [5,6,13,19]
        GPIO.setup(self.relay_chans, GPIO.OUT)
        self.pump_chans = [5,6]
        self.RIMS_heater_chan = 13
        self.HLT_heater_chan = 19
        self.sensors = [{'name':'Mash', 'id':'3c01b5566b49', 'temp':None },
                        {'name':'HLT',  'id':'3c01d0757277', 'temp':None },
                        {'name':'Boil', 'id':'3c01e076e9d7', 'temp':None },
                        {'name':'RIMS', 'id':'3c01e076c825', 'temp':None }]
        self.controllers = [{'name':'Mash', 'allow_heat':'off', 'target_temp':OFF_TEMP },
                        {'name':'HLT', 'allow_heat':'off', 'target_temp':OFF_TEMP }]         
        self.rims_pump = rims_pump    # Note: 1 or 2

    async def async_read_sensors(self):
        for s in self.sensors:
            try:
                sensor = AsyncW1ThermSensor(sensor_type=Sensor.DS18B20, sensor_id=s.get('id'))
                logging.debug("Kick-off sensor read: %s", s.get('name'))
                temperature = await sensor.get_temperature()
                s.update({'temp': temperature})
            except W1ThermSensorError as e:
                logging.warning("%s", e)    #  use sys.stderr.write
                s.update({'temp': None })
                continue

    def get_sensor_val(self, name):
        for s in self.sensors:
            if(s.get('name')==name):
                return s.get('temp')
        logging.warning("Bad sensor name: ", name)

    def get_sensor_name(self, num):
        s=self.sensors[num]
        return s.get('name')

    def get_relay_state(self, num):
        return GPIO.input(self.relay_chans[num])

    def get_pump_state(self, num):
        return GPIO.input(self.pump_chans[num-1])

    def set_pump_state(self, num, state):
        if(num==self.rims_pump and state==OFF and self.get_RIMS_state()==ON):
            logging.error("Trying to turn off RIMS pump with heat on - ignoring!")
        else:
            GPIO.output(self.pump_chans[num-1], state)

    def get_RIMS_state(self):
        return GPIO.input(self.RIMS_heater_chan)

    def set_RIMS_state(self, state):
        if(state==ON and self.get_pump_state(self.rims_pump)==OFF):
            logging.error("Trying to turn on RIMS heater with pump off - ignoring!")
        else:
            GPIO.output(self.RIMS_heater_chan, state)
        
    def get_HLT_state(self):
        return GPIO.input(self.HLT_heater_chan)

    def set_HLT_state(self, state):
        GPIO.output(self.HLT_heater_chan, state)

    # These rely on the sensors being updated using update_sensors() as uses stored values
    def RIMS_heat_ctrl(self):
        if(self.controllers[0].get('allow_heat')=='off'):
            #logging.debug("RIMS heat control called with heat off shutting off heat")
            self.set_RIMS_state(0)
            return()
        mash_target = self.controllers[0].get('target_temp')
        #logging.debug("RIMS heat control called with Mash target %d",mash_target)
        for s in self.sensors:
            if (s.get('name')=='RIMS'):
                RIMS_temp = s.get('temp')
            elif (s.get('name')=='Mash'):
                mash_temp = s.get('temp')

        # Turn on if < target temp-0.5 AND tube < 2 deg C more
        if(mash_temp < (mash_target-temp_delta) and RIMS_temp < (mash_target+RIMS_delta)):
            self.set_HLT_state(0)   # Turn off HLT first to not overload 13A socket
            time.sleep(0.1)
            self.set_RIMS_state(1)
        # Turn off if < target temp+0.5 OR tube > 2 deg C more
        elif(mash_temp > (mash_target+temp_delta) or RIMS_temp > (mash_target+RIMS_delta)):
            self.set_RIMS_state(0)  

    def HLT_heat_ctrl(self):
        if(self.controllers[1].get('allow_heat')=='off'):
            #logging.debug("HLT heat control called with heat off shutting off heat")
            self.set_HLT_state(0)
            return()
        if(self.get_RIMS_state()==1):
            #logging.debug("HLT heat control called with RIMS heat ON shutting off heat")
            self.set_HLT_state(0)
            return()
        self.hlt_target = self.controllers[1].get('target_temp')    
        #logging.debug("HLT heat control called with target %d",self.hlt_target)
 
        for s in self.sensors:
            if (s.get('name')=='HLT'):
                HLT_temp = s.get('temp')
        if(HLT_temp < (self.hlt_target-temp_delta) ):
            self.set_HLT_state(ON)  # Turn on if < target temp-0.5 
        elif(HLT_temp > (self.hlt_target+temp_delta)):
            self.set_HLT_state(OFF)  # Turn off if < target temp+0.5
 
    """
    Gets passsed a step dict of {'Step':i, 'Stage':stage_name, 'Name':step_name, 
    'Type':step_type, 'Time':step_time , 'Value':step_value}      
    """
    def set_target_temps(self, step):
        logging.debug("set_target_temps called with step: %s" ,step)
        if(step.get('Type')=='hlt'):
            logging.debug("hlt step type, with Value: %s" , step.get('Value'))
            self.controllers[1]['target_temp']=step.get('Value')
        elif(step.get('Type')=='mash'):
            logging.debug("mash step type, with Value: %s" , step.get('Value'))
            self.controllers[0]['target_temp']=step.get('Value')
        elif(step.get('Type')=='off'):
            logging.debug("off step type, with Value: %s" , step.get('Value'))
            self.controllers[0]['target_temp']=OFF_TEMP
            self.controllers[1]['target_temp']=OFF_TEMP
        else:
            logging.error("Bad step Type! msut be one of 'hlt', 'rims' or 'off'")            

    def set_mash_target(self, target):
        self.controllers[0].update({'target_temp': target})

    def set_hlt_target(self, target):
        self.controllers[1].update({'target_temp': target})

    @property
    def relay_chans_state(self) -> list:
        relays = []
        for chan in self.relay_chans:
            relays.append(GPIO.input(chan))
        return list(relays)

    @property
    def mash_target(self) -> int:
        return int(self.controllers[0].get('target_temp'))

    @property
    def hlt_target(self):
        return int(self.controllers[1].get('target_temp'))

    @property
    def mash_heater_on(self) -> bool:
        if(self.controllers[0].get('allow_heat')==ON):
            return True
        else:
            return False

    @property
    def hlt_heater_on(self) -> bool:
        if(self.controllers[1].get('allow_heat')==ON):
            return True
        else:
            return False

    def get_controller_state(self, name):
        if(name=="Mash"):
            heat_state = 'off' if self.get_RIMS_state()==0 else 'heat'
        elif(name=="HLT"):
            heat_state = 'off' if self.get_HLT_state()==0 else 'heat'
        else:
            logging.debug("Bad controller name use in get_controller_state: ",name)
            return()
        for c in self.controllers:
            if(c.get('name')==name):
                for s in self.sensors:
                    if(s.get('name')==name):
                        break
                payload = {"temperature": s.get('temp'),
                            "target_temp": c.get('target_temp'),
                            "mode_state": heat_state}
        return(payload)

    def set_controller_state(self, name, state):   #  Set whether to allow heating
        for c in self.controllers:
            if(c.get('name')==name):
                logging.debug("Changing controller %s state: %s", name, state)
                c.update({'allow_heat':state})
                return()
        logging.debug("Bad controller name used set_controller_state: %s",name)

    def toggle_controller_state(self, name):   #  Set whether to allow heating
        for c in self.controllers:
            if(c.get('name')==name):
                if(c.get('allow_heat')=='off'):
                    state = 'heat'
                else:
                    state = 'off'
                logging.debug("Changing controller %s state: %s", name, state)
                c.update({'allow_heat':state})
                return()
        logging.debug("Bad controller name used toggle_controller_state: %s",name)


    def clean_up(self):
        GPIO.output(self.relay_chans, 0)
        GPIO.cleanup(self.relay_chans)
    def __del__(self):
        logging.info("Brew Proc __del__ called:  Shutting off all GPIO")
        self.clean_up()


