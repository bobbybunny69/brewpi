"""
Class for GUI for brewpi - needs to be passed in a brewproc Proc class and a brewfather Batch class

"""

from datetime import datetime
import time
import logging, os
import asyncio
import tkinter as tk
from tkinter import font, Button, scrolledtext, messagebox

timer = 'MM:SS'
log_file = "brewpi.csv"

OFF = 0
COUNT = 140  # Aiming for 30s:  each senor read takes ~200ms so 30*5


class App:
    def __init__(self, brewproc, batch, bpmqttc, sensors, controllers, pumps, ipaddr, ssid):
        self.bp = brewproc    # These are just to pass through (probably better way to do this)
        self.batch = batch
        self.bpmqttc =  bpmqttc   # brewproc mqtt clients
        self.sensors = sensors
        self.controllers = controllers
        self.pumps = pumps
        self.ipaddr = ipaddr
        self.ssid = ssid

    async def exec(self):
        self.window = GUI(asyncio.get_event_loop(), self.bp, self.batch, self.bpmqttc, self.sensors, self.controllers, self.pumps, self.ipaddr, self.ssid)
        await self.window.show_update();

class GUI(tk.Tk):
    def __init__(self, loop, brewproc, batch, bpmqttc, sensors, controllers, pumps, ipaddr, ssid):
        super().__init__()
        self.loop = loop

        self.bp = brewproc
        self.batch = batch
        self.bpmqttc = bpmqttc
        self.sensors = sensors
        self.controllers = controllers
        self.pumps = pumps
        self.ipaddress = ipaddr
        self.ssid = ssid

        self.f = open(log_file, "a")
        self.mash_ctrl = False
        self.hlt_ctrl = False
        self.step = 0
        self.title_str = None
        self.exit = False
        self.powerdown = False

        self.resizable(False, False)
        self.geometry("800x480")
        # Set default font
        default_font = tk.font.nametofont("TkDefaultFont")
        default_font.configure(family="Liberation Sans", size=16)
        self.option_add("*Font", default_font)
        # Create the main frames
        self.create_title_frame()
        self.create_center_frames()
        self.create_proc_frame()
        self.create_quit_frame()

    """
    Funtion to show all the updates in the window
    """
    async def show_update(self):
        count=COUNT-20     # -20 to allow enough time to read all sensors  
        sensor_task = None
        while not self.exit:
            # Read temp probes using a non-blocking task
            if(sensor_task == None):       #  Start read/update task if none defined
                sensor_task = asyncio.create_task (self.bp.async_update_sensors())
            elif(sensor_task.done() == True):  # Restart if last read/update finished
                sensor_task = asyncio.create_task (self.bp.async_update_sensors())
    
            # Update sensor fields on GUI
            sensors_log_str = ""
            i=0
            for s in self.sensors:
                temperature = self.bp.get_sensor_val(s)
                sensors_log_str += "{:0.1f}, ".format(temperature)
                if(temperature < -90):
                    self.sensor_text_vals[i].set('-----')
                else:
                    self.sensor_text_vals[i].set('{:5.1f}'.format(temperature))
                i+=1

            # Update controller target temps on GUI
            self.mash_target_text.set('{:5.1f}'.format(self.bp.controllers[0].get('target_temp')))
            self.hlt_target_text.set('{:5.1f}'.format(self.bp.controllers[1].get('target_temp')))
                
            # Run the Brewproc control loops
            self.bp.RIMS_heat_ctrl()
            self.bp.HLT_heat_ctrl()
    
            # Update the relay status text fields 
            relays_log_str = ""
            for i in range(1,5):
                relays_log_str += "{}, ".format(self.bp.get_relay_state(i))    
                if(self.bp.get_relay_state(i)==1):
                    self.relay_text_vals[i].set('*ON*')
                else:
                    self.relay_text_vals[i].set('....')
            logging.debug("Relays (P1, P2, Rims, HLT): %s",relays_log_str)

            # Update the Pump button colors according to state 
            if(self.bp.get_pump_state(1)==1):
                self.button_p1.config(bg='blue', activebackground='blue')
            else:
                self.button_p1.config(bg='white', activebackground='white')
            if(self.bp.get_pump_state(2)==1):
                self.button_p2.config(bg='blue', activebackground='blue')
            else:
                self.button_p2.config(bg='white', activebackground='white')

            # Update the Heater button colors according to Allow Heat state
            if(self.bp.controllers[0].get('allow_heat')=='heat'):
                self.button_h1.config(bg='red', activebackground='red')
            else:
                self.button_h1.config(bg='white', activebackground='white')
            if(self.bp.controllers[1].get('allow_heat')=='heat'):
                self.button_h2.config(bg='red', activebackground='red')
            else:
                self.button_h2.config(bg='white', activebackground='white')

            #  Update the logfile and MQTT sensor every COUNT iterations
            count+=1
            if(count>COUNT):
                count=0
                timestamp_str = time.strftime('%H:%M:%S') + ': '
                target_temp_str = "{:0.1f}, ".format(self.bp.mash_target)
                log_str = timestamp_str + str(self.batch.steps[self.step].get('Step')) + ", " + target_temp_str + sensors_log_str + relays_log_str
                self.f.write(log_str+'\n')
                logging.debug(log_str)
                #  Publish MQTT data to home assistant
                for s in self.sensors:
                    self.bpmqttc.publish_sensor_temp(s)
                for c in self.controllers:
                    self.bpmqttc.publish_controller_status(c)
                for p in self.pumps:
                    self.bpmqttc.publish_switch_state(p)
        
            self.update()
            await asyncio.sleep(0.2)

        ###  Quitting...  close file
        self.f.close()
        self.bpmqttc.offline()   #  Publish to HA gone offline
        #  Close GUI
        self.destroy()
        if(self.powerdown==True):
            os.system("sleep 2 && sudo shutdown -h now")
                 
    def create_title_frame(self):
        title_frame = tk.Frame(self, bg='blue', width=800, height=40)
        title_frame.grid(row=0)
        self.title_str = tk.StringVar()
        self.title_str.set('-----')
        
        if(self.batch.batch_num == None):
            self.title_str.set('Batch file not loaded!')
            title_str = 'Batch file not loaded!\n'
        else:
            self.title_str.set(self.batch.title + ',  ' + self.batch.brewer + ',  ' + self.batch.date)
            title_str = self.batch.title + ',  ' + self.batch.brewer + ',  ' + self.batch.date +'\n'
                         
        tk.Label(title_frame, textvar=self.title_str, fg='white', bg='blue').pack(expand=True, fill='both', side='left', ipadx=20, ipady=5)
        self.f.write(title_str)
    
    def create_proc_frame(self):
        global ipaddress, ssid
        proc_frame = tk.Frame(self, width=800, height=150)
        proc_frame.grid(row=2)
        button_next = Button(proc_frame, text='Next', bg='yellow', command= self.next )
        button_next.grid(column=0, row=0, padx=20, pady=5)
        button_prev = Button(proc_frame, text='Previous', bg='yellow', command= self.prev )
        button_prev.grid(column=0, row=2, padx=20, pady=5)
        tk.Label(proc_frame, text=timer, fg='white', bg='blue').grid(column=0, row=1, padx=5, pady=5)
        self.text_area = scrolledtext.ScrolledText(proc_frame, wrap=tk.WORD, width=50, height=5)
        self.text_area.grid(column=1, row =0, rowspan=3, pady=5, padx=5)
        now = datetime.now()
        status_str = now.strftime('%d/%b/%y') + ':  ' + self.ipaddress.strip() + ' on ' + self.ssid
        self.text_area.insert(tk.END, status_str)
        self.text_area.insert(tk.END, self.batch.step_str(self.step) +'\n')

    def create_quit_frame(self):
        quit_frame = tk.Frame(self, bg='red', width=800, height=40)
        quit_frame.grid(row=3, sticky='e')
        button_q = Button(quit_frame, text = 'Quit', command= self.quit ).grid(column=0, row=0, padx=50, pady=10)
        button_s = Button(quit_frame, text = 'Shutdown!', command= self.shutdown ).grid(column=1, row=0, padx=50, pady=10)

    def create_center_frames(self):        
        center_frame = tk.Frame(self, width=800, height=250)
        center_frame.grid(row=1, sticky='w')

        ctr_left = tk.Frame(center_frame, width=500, height=250)
        ctr_left.grid_columnconfigure(0, weight=1)
        ctr_right = tk.Frame(center_frame, width=300, height=250)
        ctr_left.grid(row=0, column=0, sticky='w')
        ctr_right.grid(row=0, column=1, padx=50)

        # Display temp sensors in a grid - using textvars to update the readings
        self.sensor_text_vals = []
        for i in range(0,4):
            self.sensor_text_vals.append(tk.StringVar())
            self.sensor_text_vals[i].set('-----')
            tk.Label(ctr_left, text=self.bp.get_sensor_name(i), width=10).grid(column=0, row=i, sticky='w', pady=10)
            tk.Label(ctr_left, textvar=self.sensor_text_vals[i], relief=tk.RIDGE, width=10).grid(column=1, row=i, sticky='w')
            
        # Display the target temps (Mash and HLT) with up/down buttons 
        self.button_rims_up=tk.Button(ctr_left, text= "+", bg='white', command= self.rims_up_button)
        self.button_rims_up.grid(row=0, column=4, pady=0)
        self.button_rims_dn=tk.Button(ctr_left, text= "-", bg='white', command= self.rims_dn_button)
        self.button_rims_dn.grid(row=0, column=2, pady=0)
        self.mash_target_text= tk.StringVar()
        self.mash_target_text.set('{:5.1f}'.format(self.bp.controllers[0].get('target_temp')))
        tk.Label(ctr_left, textvar=self.mash_target_text, bg="green", relief=tk.RIDGE, width=8).grid(column=3, row=0, sticky='w')

        self.button_hlt_up=tk.Button(ctr_left, text= "+", bg='white', command= self.hlt_up_button)
        self.button_hlt_up.grid(row=1, column=4, pady=0)
        self.button_hlt_dn=tk.Button(ctr_left, text= "-", bg='white', command= self.hlt_dn_button)
        self.button_hlt_dn.grid(row=1, column=2, pady=0)
        self.hlt_target_text= tk.StringVar()
        self.hlt_target_text.set('{:5.1f}'.format(self.bp.controllers[1].get('target_temp')))
        tk.Label(ctr_left, textvar=self.hlt_target_text, bg="green", relief=tk.RIDGE, width=8).grid(column=3, row=1,  sticky='w')

        # Pump buttons
        self.button_p1=tk.Button(ctr_right, text= "PUMP 1", bg='white', command= self.PUMP1button)
        self.button_p1.grid(row=0, column=0, pady=10)
        self.button_p2=tk.Button(ctr_right, text= "PUMP 2", bg='white', command= self.PUMP2button)
        self.button_p2.grid(row=1, column=0, pady=10)
        # Heater buttons
        self.button_h1=tk.Button(ctr_right, text= "RIMS HEAT", bg='white', command= self.HEAT1button)
        self.button_h1.grid(row=2, column=0, pady=10)
        self.button_h2=tk.Button(ctr_right, text= " HLT HEAT", bg='white', command= self.HEAT2button)
        self.button_h2.grid(row=3, column=0, pady=10)

        # Relay status labels
        self.relay_text_vals = []   # Bogus inital tk.StringVar entry to align array with numbers
        self.relay_text_vals.append(tk.StringVar())
        for i in range (1,5):
            self.relay_text_vals.append(tk.StringVar())
            self.relay_text_vals[i].set('....')
            tk.Label(ctr_right, textvar=self.relay_text_vals[i], bg="green", width=6).grid(row=i-1, column=1, padx=10)

    def PUMP1button(self):
        logging.debug("PUMP1 Button pressed - State %d", self.bp.get_pump_state(1))
        if self.bp.get_pump_state(1) == 0:
            self.bp.set_pump_state(1, 1)
            self.button_p1.config(bg='blue', activebackground='blue')
        else:
            self.bp.set_pump_state(1, 0)
            self.button_p1.config(bg='white', activebackground='white')
        time.sleep(0.2)   #  Pause to show button hit then update with actual state
        if self.bp.get_pump_state(1) == 1:
            self.button_p1.config(bg='blue', activebackground='blue')
            self.relay_text_vals[1].set('*ON*')
        else:
            self.button_p1.config(bg='white', activebackground='white')
            self.relay_text_vals[1].set('....')
        self.bpmqttc.publish_switch_state('pump1')   
           
    def PUMP2button(self):
        logging.debug("PUMP2 Button pressed - State %d", self.bp.get_pump_state(2))
        if self.bp.get_pump_state(2) == 0:
            self.bp.set_pump_state(2, 1)
            self.button_p2.config(bg='blue', activebackground='blue')
        else:
            self.bp.set_pump_state(2, 0)
            self.button_p2.config(bg='white', activebackground='white')
        time.sleep(0.2)   #  Pause to show button hit then update with actual state
        if self.bp.get_pump_state(2) == 1:
            self.button_p2.config(bg='blue', activebackground='blue')
            self.relay_text_vals[2].set('*ON*')
        else:
            self.button_p2.config(bg='white', activebackground='white')
            self.relay_text_vals[2].set('....')
        self.bpmqttc.publish_switch_state('pump2')   

    def HEAT1button(self):
        logging.debug("HEAT1 Button pressed - State %s", self.bp.controllers[0].get('allow_heat'))
        self.bp.toggle_controller_state('Mash')
        self.bp.RIMS_heat_ctrl()
        self.bpmqttc.publish_controller_status('Mash')

    def HEAT2button(self):
        logging.debug("HEAT2 Button pressed - State %s", self.bp.controllers[1].get('allow_heat'))
        self.bp.toggle_controller_state('HLT')
        self.bp.HLT_heat_ctrl()
        self.bpmqttc.publish_controller_status('HLT')

    def rims_up_button(self):
        logging.debug("RIMS up Button pressed")
        self.bp.controllers[0]['target_temp'] += 1
        self.mash_target_text.set('{:5.1f}'.format(self.bp.controllers[0].get('target_temp')))
        self.bpmqttc.publish_controller_status('Mash')   

    def rims_dn_button(self):
        logging.debug("RIMS down Button pressed")
        if(self.bp.controllers[0]['target_temp'] != OFF):
            self.bp.controllers[0]['target_temp'] -= 1
        self.mash_target_text.set('{:5.1f}'.format(self.bp.controllers[0].get('target_temp')))
        self.bpmqttc.publish_controller_status('Mash')   

    def hlt_up_button(self):
        logging.debug("HLT up Button pressed")
        self.bp.controllers[1]['target_temp'] += 1
        self.hlt_target_text.set('{:5.1f}'.format(self.bp.controllers[1].get('target_temp')))
        self.bpmqttc.publish_controller_status('HLT')   
           
    def hlt_dn_button(self):
        logging.debug("HLT down Button pressed")
        if(self.bp.controllers[1]['target_temp'] != OFF):
            self.bp.controllers[1]['target_temp'] -= 1
        self.hlt_target_text.set('{:5.1f}'.format(self.bp.controllers[1].get('target_temp')))
        self.bpmqttc.publish_controller_status('HLT')   

    def shutdown(self):
        MsgBox = tk.messagebox.askquestion ('Shutdown!!','Are you sure you want to shutdown BrewPi',icon = 'warning')
        if MsgBox == 'yes':
            logging.info("Shutting Down - shutting all relays and cleaning-up GPIO")
            self.exit = True
            self.powerdown = True

    def quit(self):
        MsgBox = tk.messagebox.askquestion ('Exit Application','Are you sure you want to exit the application',icon = 'warning')
        if MsgBox == 'yes':
            logging.info("Exiting - shutting all relays and cleaning-up GPIO")
            self.exit = True
        
    def next(self):
        logging.debug("Next hit")
        if(self.step == len(self.batch.steps)-1):
            logging.debug("No next step!")
            return()
        self.step+=1
        self.text_area.insert(tk.END, self.batch.step_str(self.step) +'\n')
        self.text_area.see("end")
        self.bp.set_target_temps(self.batch.steps[self.step]) 
        self.mash_target_text.set('{:5.1f}'.format(self.bp.controllers[0].get('target_temp')))
        self.hlt_target_text.set('{:5.1f}'.format(self.bp.controllers[1].get('target_temp')))
        self.bpmqttc.publish_controller_status('Mash')   
        self.bpmqttc.publish_controller_status('HLT')   
        
    def prev(self):
        logging.debug("Previous hit")
        if(self.step == 0):
            logging.debug("No previous step!")
            return()
        self.step-=1
        self.text_area.insert(tk.END, self.batch.step_str(self.step) +'\n')
        self.text_area.see("end")
        self.bp.set_target_temps(self.batch.steps[self.step]) 
        self.mash_target_text.set('{:5.1f}'.format(self.bp.controllers[0].get('target_temp')))
        self.hlt_target_text.set('{:5.1f}'.format(self.bp.controllers[1].get('target_temp')))
        self.bpmqttc.publish_controller_status('Mash')   
        self.bpmqttc.publish_controller_status('HLT')   
        
