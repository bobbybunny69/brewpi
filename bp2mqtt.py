"""
BP2MQTT Publish the Brew-Pi device on HASS with all sensors, buttons and controllers (Thermostats)
"""
import json
import logging
import paho.mqtt.client as mqtt

class bp2mqtt(object):
    def __init__(self, name, client_id, mqtt_host, mqtt_port, brewproc):
        self.client_id = client_id
        logging.debug("Creating BP2MQTT client class with client_id: %s", self.client_id)
        self.device_name = name
        self.device_config = {
                "identifiers": self.client_id,
                "name": name,
                "model": "Brew Pi",
                "sw": "0.8",
                "manufacturer": "robby" }
        self.availability_topic = 'homeassistant/brewpi/availability'
        self.rims_heat_state = 0
        self.hlt_heat_state = 0
        self.mash_target = 0.0
        self.hlt_target = 0.0
        self.bproc = brewproc
 
        mqttc=mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id)
        mqttc.on_connect = self.on_connect
        mqttc.on_message = self.on_message
        mqttc.on_log = self.on_log
        self.client = mqttc
        self.client.will_set(self.availability_topic, 'offline')
        
        result = self.client.connect(mqtt_host, mqtt_port, 60)
        logging.debug('MQTT connect to server result %s', result)
        
        self.client.loop_start()

    """ Callback for when the client receives a CONNACK response from the server """
    def on_connect(self, mqttc, userdata, flags, rc, properties):
        if rc.is_failure:
            logging.warning(f"Failed to connect: {rc}. loop_forever() will retry connection")
        else:
            logging.debug("subscribing: homeassistant/status") # Birth/will messages from HA
            self.client.subscribe('homeassistant/status')
            
            subscribe_topic = "homeassistant/+/" + self.client_id + "/+/set/#" 
            logging.debug("subscribing: %s", subscribe_topic)
            self.client.subscribe(subscribe_topic)   # subscribe to commands for thermo from HA       
            
    """ Callback for when a PUBLISH message is received from the server """
    def on_message(self, mqttc, userdata, msg):
        tpc_str = str(msg.topic)
        data_str = str(msg.payload.decode("utf-8"))
        logging.debug ("Topic received: %s", tpc_str )
        logging.debug ("Data received: %s", data_str )

        climate_topic = "homeassistant/climate/"+self.client_id
        switch_topic = "homeassistant/switch/"+self.client_id

        if (tpc_str == climate_topic+"/Mash/set/temp"):
            logging.debug("Setting Mash target: %s", data_str)
            self.bproc.set_mash_target(float(data_str))
            self.bproc.RIMS_heat_ctrl()
            self.publish_controller_status("Mash")
        elif (tpc_str == climate_topic+"/HLT/set/temp"):
            logging.debug("Setting HLT target: %s", data_str)
            self.bproc.set_hlt_target(float(data_str))
            self.bproc.HLT_heat_ctrl()
            self.publish_controller_status("HLT")
        elif (tpc_str == climate_topic+"/Mash/set/mode"):
            logging.debug("Setting Mash mode: %s", data_str)
            self.bproc.set_controller_state("Mash", data_str.decode("utf-8"))
            self.bproc.RIMS_heat_ctrl()
            self.publish_controller_status("Mash")
        elif (tpc_str == climate_topic+"/HLT/set/mode"):
            logging.debug("Setting HLT mode: %", data_str)
            self.bproc.set_controller_state("HLT", data_str.decode("utf-8"))
            self.bproc.HLT_heat_ctrl()
            self.publish_controller_status("HLT")
        elif (tpc_str == switch_topic+"/pump1/set"):
            logging.debug("Setting pump1 state: %s", data_str)
            if(data_str==b'ON'):
                self.bproc.set_pump_state(1,1)   # Turn pump 1 on
            else:
                self.bproc.set_pump_state(1,0)   # Turn pump 1 off
            self.publish_switch_state("pump1")
        elif (tpc_str == switch_topic+"/pump2/set"):
            logging.debug("Setting pump1 state: %s", data_str)
            if(data_str==b'ON'):
                self.bproc.set_pump_state(2,1)   # Turn pump 2 on
            else:
                self.bproc.set_pump_state(2,0)   # Turn pump 2 off
            self.publish_switch_state("pump2")
        else:
            logging.warning("Command not actioned - don't know what to do")

    """ on log callback (used by PAHO to catch exceptions) """
    def on_log(self, mqttc, userdata, level, buff):
        logging.debug(buff)

    def offline(self):
        logging.debug("Going offline with %s", self.availability_topic)
        self.client.publish(self.availability_topic, 'offline', retain=True)
        self.client.disconnect()
        self.client.loop_stop()

##### PICO

    def create_sensor(self, name):
        sensor_name = self.device_name+ " " + name
        unique_id = self.client_id + "_" + name
        base_topic = "homeassistant/sensor/" + self.client_id + "/" + name 

        topic = base_topic + "/config"
        payload = { "device_class": "temperature",
            "name": sensor_name,
            "state_topic": base_topic+"/state",
            "availability_topic": self.availability_topic,
            "unit_of_measurement": "°C",
            "value_template": "{{ value_json.temperature }}",
            "unique_id": unique_id,
            "device": self.device_config,
            }
        logging.debug(json.dumps(payload))
        self.client.publish(topic, bytes(json.dumps(payload), 'utf-8'))
        self.client.publish(self.availability_topic, 'online')

    def publish_sensor_temp(self, name):
        base_topic = "homeassistant/sensor/" + self.client_id + "/" + name 
        temperature = self.bproc.get_sensor_val(name)
        payload = { "temperature": "{:.1f}".format(temperature) }
        logging.debug(json.dumps(payload))
        self.client.publish(base_topic+"/state", bytes(json.dumps(payload), 'utf-8'))
        self.client.publish(self.availability_topic, 'online')

    def create_controller(self, name):
        sensor_name = self.device_name + " " + name + " Controller"
        unique_id = self.client_id + "_" + name
        base_topic = "homeassistant/climate/" + self.client_id + "/" + name 
        
        topic = base_topic + "/config"
        payload = { "name": sensor_name,
                    "unique_id": unique_id,
                    "temperature_command_topic": base_topic+"/set/temp",
                    "mode_command_topic": base_topic+"/set/mode",
                    "current_temperature_topic": base_topic+"/state",
                    "current_temperature_template": "{{ value_json.temperature }}",
                    "temperature_state_topic": base_topic+"/state",
                    "temperature_state_template": "{{ value_json.target_temp }}",
                    "mode_state_topic": base_topic+"/state",
                    "mode_state_template": "{{ value_json.mode_state }}",
                    "temperature_unit": "C",
                    "min_temp" : 20.0,
                    "max_temp" : 99.0,
                    "modes": ["heat", "off"],
                    "device": self.device_config,
                    "availability_topic": self.availability_topic
            }
        logging.debug(json.dumps(payload))
        self.client.publish(topic, bytes(json.dumps(payload), 'utf-8'))
        self.client.publish(self.availability_topic, 'online')

    def publish_controller_status(self, name):
        unique_id = self.client_id+"_"+name+"_controller"
        base_topic = "homeassistant/climate/" + self.client_id + "/" + name 

        payload = self.bproc.get_controller_state(name)
        
        logging.debug("Publishing state = %s", payload)  
        self.client.publish(base_topic+"/state", bytes(json.dumps(payload), 'utf-8'))
        self.client.publish(self.availability_topic, 'online')

    def create_switch(self, name):
        switch_name = self.device_name+ " " + name
        unique_id = self.client_id + "_" + name
        base_topic = "homeassistant/switch/" + self.client_id + "/" + name 

        topic = base_topic + "/config"
        payload = { "name": switch_name,
            "state_topic": base_topic+"/state",
            "command_topic": base_topic+"/set",
            "availability_topic":  self.availability_topic,
            "icon": "mdi:pump",
            "unique_id": unique_id,
            "device": self.device_config,
            }
        logging.debug(json.dumps(payload))
        self.client.publish(topic, bytes(json.dumps(payload), 'utf-8'))
        self.client.publish(self.availability_topic, 'online')

    def publish_switch_state(self, name):
        base_topic = "homeassistant/switch/" + self.client_id + "/" + name 
        if(name=='pump1'):
            onoff_state = 'OFF' if self.bproc.get_pump_state(1)==0 else 'ON'
        elif(name=="pump2"):
            onoff_state = 'OFF' if self.bproc.get_pump_state(2)==0 else 'ON'
        else:
            logging.debug("Bad pump name use in set_switch_state: %s",name)
            return()
        self.client.publish(base_topic+"/state", onoff_state )
        self.client.publish(self.availability_topic, 'online')

