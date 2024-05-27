#
# Rob Saunders 2022
# Assume Python 3.7.x +
# Python Brefather class/object
# Obtain data from Brefather webiste using REST API calls with aim to automate"""

import requests
import logging
import json
from datetime import datetime

OFF = -99
EMPTY = '????'

user_id = 'fqGoLDdBmITgVo7aMIUYeg8n5v62'
api_key = 'C57jUYT4JBogFvDRRethqsbeTbAKmiEOtNTqZP3M9GEmhDO3PxisIV5NZkueYNsi'

class Batch:
    def __init__(self):
        self.user_id = user_id
        self.api_key = api_key
        self.batch_id = None
        self.batch_num = None
        self.title = None
        self.brewer = None
        self.date = None
        self.steps = []

    # Use HTTP GET to setup the object
    def load(self):
        logging.info("Obtain batches being brewed using get")
        payload = {'status': 'Brewing'}    # Payload to get first batch currently being brewed
        r = requests.get('https://api.brewfather.app/v1/batches', auth=(self.user_id, self.api_key), params=payload, timeout=3.2)
        if(r.status_code != 200):
            logging.error("Bad status code returned on HTTP GET: %d", r.status_code)
            return(False)

        for batch in r.json():
            self.batch_id = batch.get('_id')
            self.batch_num = batch.get('batchNo')
            self.title = batch.get('recipe').get('name')
            self.brewer = batch.get('brewer')
            date = batch.get('brewDate')/1000     # Note timestamp in ms
            self.date = datetime.fromtimestamp(date).strftime('%d/%m/%Y')  

        if (self.batch_id == None):
            logging.error("No batches ready for brewing - ensure BF has them in Brewing state")
            return(False)

        logging.info("Proceeding with batch id: %s",self.batch_id)

        """ Now load all steps in to the steps[] array """
        url = 'https://api.brewfather.app/v1/batches/' + self.batch_id + '/brewtracker'
        r = requests.get(url, auth=(self.user_id, self.api_key), timeout=3.2)
        if(r.status_code != 200):
            logging.error("Bad status code returned on HTTP GET: %d", r.status_code)
            return(False)

        """ Get all the steps from all the stages """
        i=0
        for stage in r.json().get("stages"):
            stage_name = stage.get("name")
            for step in stage.get("steps"):
                i+=1
                step_name = step.get("name")
                if (step_name == None):
                    step_name = EMPTY
                step_time = int(step.get("time")/60)   # Convert from seconds to minutes
                step_type = step.get("type")
                temp_value = step.get("value")
                if (temp_value == None):
                    step_value = OFF
                else:
                    step_value = int(temp_value + 0.5) 
                self.steps.append({'Step':i, 'Stage':stage_name, 'Name':step_name, 'Type':step_type, 'Time':step_time , 'Value':step_value})       
        return True

    # Used to make the json file
    def json_print (self):
        return(json.dumps((\
            self.batch_num,
            self.title,
            self.brewer,
            self.date,
            self.steps), indent=4))

    # Use json file to setup the object
    def json_load (self, f):
        try:
            batch = json.load(f)
        except ValueError:  # includes simplejson.decoder.JSONDecodeError
            logging.error("ERROR - Decoding JSON has failed")
        self.batch_num = batch[0]
        self.title = batch[1]
        self.brewer = batch[2]
        self.date = batch[3]
        self.steps = batch[4]

    def step_str (self, i):
        return(str(\
            str(self.steps[i].get('Step')) + ': ' +
            self.steps[i].get('Name') + ', ' +
            self.steps[i].get('Type') + ', ' +
            str(self.steps[i].get('Time')) + 'min, ' +
            str(self.steps[i].get('Value'))))

    def get_title(self):
        return self.title

    def get_date(self):
        return self.date

    def get_brewer(self):
        return self.brewer

    def load_step(self):
        """ Obtain batch tracker for batch """
        url = 'https://api.brewfather.app/v1/batches/' + self.batch_id + '/brewtracker'
        r = requests.get(url, auth=(self.user_id, self.api_key), timeout=3.2)
        if(r.status_code != 200):
            logging.error("Bad status code returned on HTTP GET: %d", r.status_code)
            return(False)

        """ Obtain whether Active although may not need this """    
        active = r.json().get("active")

        """ Get the stage number first asand loop to load correct stage """
        stage_num = r.json().get("stage")
        i=0
        for stage in r.json().get("stages"):
            if i == stage_num:
                break
            i+=1
        stage_name = stage.get("name")
        stage_step = stage.get("step")
        self.paused = stage.get("paused")
        self.time_pos = stage.get("position")
  
        """ Now step theough steps until at correct step then load values """
        i=0
        for step in stage.get("steps"):
            if i == stage_step:
                break
            i+=1
        step_name = step.get("name")
        if (step_name == None):
            step_name = EMPTY
        temp_value = step.get("value")
        if (temp_value == None):
            step_value = OFF
        else:
            step_value = int(temp_value + 0.5) 
        self.target_temp = step_value
        step_time = step.get("time")
        step_type = step.get("type")
        self.step = str(i)+': '+step_name
        
        return True


