# Classes to aid creating a GUI for brewpi in pygame
from importlib.resources import read_text
import brewproc
import pygame
import logging
import asyncio

THEME_COLOR1 = 'dodgerblue4'
THEME_COLOR2 = 'white'
THEME_COLOR3 = 'yellow'
PRESSED_COLOR = 'blue'
DISABLED = (128,128,128)
screen_x = 800
screen_y = 480

class BPGui():
    def __init__(self):
        self.count = None
        self.sensor_task = None
        self.mash_delta = 0
        self.hlt_delta = 0
        self.screen = pygame.display.set_mode((screen_x, screen_y))
        pygame.mouse.set_visible(False)    # Hide cursor here
        self.screen.fill('black')
        pygame.font.init()
        self.clock = pygame.time.Clock()

    def create_home_scrn(self):
        self.home_button = Button(0, 0, 96, 'assets/home.png')
        self.settings_button = Button(0, 96, 96, 'assets/cog.png')
        self.quit_button = Button(0, 384, 96, 'assets/power.png')
        self.mash_up_button = Button(382, 36, 64, 'assets/arrow-up.png')
        self.mash_dn_button = Button(382, 102, 64, 'assets/arrow-down.png')
        self.hlt_up_button = Button(732, 36, 64, 'assets/arrow-up.png')
        self.hlt_dn_button = Button(732, 102, 64, 'assets/arrow-down.png')
        self.mash_panel = Panel(120, 0, 250, 'Mash Tun')
        self.hlt_panel = Panel(470, 0, 250, 'Hot Liquor Tank')
        self.rims_reading = Reading(120, 180, 320, 'RIMS Tube')
        self.boil_reading = Reading(470, 180, 320, 'Boil Kettle')
        self.p1_switch= Switch(650, 224, 'On')
        self.p2_switch= Switch(650, 288, 'On')
        self.rims_switch= Switch(650, 352, 'Auto')
        self.hlt_switch= Switch(650, 416, 'Auto')

    async def update_scrn(self, bp: brewproc.Proc):
        # Read temp probes using a non-blocking task 
        if(self.sensor_task == None):       #  Start read/update task if none defined
            self.sensor_task = asyncio.create_task (bp.async_read_sensors())
        elif(self.sensor_task.done() == True):  # Restart if last read/update finished
            self.sensor_task = asyncio.create_task (bp.async_read_sensors())

        self.mash_panel.draw(self.screen, bp.get_sensor_val('Mash'), bp.mash_target)
        self.hlt_panel.draw(self.screen, bp.get_sensor_val('HLT'), bp.hlt_target)
        self.rims_reading.draw(self.screen, bp.get_sensor_val('RIMS'))
        self.boil_reading.draw(self.screen, bp.get_sensor_val('Boil'))
        self.home_button.draw(self.screen)
        self.settings_button.draw(self.screen)
        self.quit_button.draw(self.screen)
        self.mash_up_button.draw(self.screen)
        self.mash_dn_button.draw(self.screen)
        self.hlt_up_button.draw(self.screen)
        self.hlt_dn_button.draw(self.screen)
        self.p1_switch.draw(self.screen)
        self.p2_switch.draw(self.screen)
        self.rims_switch.draw(self.screen)
        self.hlt_switch.draw(self.screen)
        pygame.display.update()
        await asyncio.sleep(0.223)
        self.clock.tick(0)
        logging.debug("Number ms between last 2 ticks: %d", self.clock.get_time())     
        logging.debug("RIMS Auto = {}, HLT Auto = {}, Relays = {}".format(bp.controllers[0].get('allow_heat'), bp.controllers[1].get('allow_heat'), bp.relay_chans_state))
        
    def event_handeller(self, bp: brewproc.Proc):
        for event in pygame.event.get():
            #print("event: ", event)
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.FINGERUP:
                #print("finger lifted")
                self.mash_delta = self.hlt_delta = 0
                self.count = None
            elif event.type == pygame.FINGERDOWN: 
                finger_x = int (event.x * screen_x + 0.5)
                finger_y = int (event.y * screen_y + 0.5)
                logging.debug("Finger touched the screen at ({},{})".format(finger_x, finger_y)) 
                self.count = 1
                if self.home_button.is_pressed(finger_x, finger_y):
                    settings_screen = False 
                elif self.settings_button.is_pressed(finger_x, finger_y):
                    settings_screen = True
                elif self.quit_button.is_pressed(finger_x, finger_y):
                    return False 
                elif self.mash_up_button.is_pressed(finger_x, finger_y):
                    bp.set_mash_target(bp.mash_target+1)
                    self.mash_delta = 1
                elif self.mash_dn_button.is_pressed(finger_x, finger_y):
                    bp.set_mash_target(bp.mash_target-1)
                    self.mash_delta = -1
                elif self.hlt_up_button.is_pressed(finger_x, finger_y):
                    bp.set_hlt_target(bp.hlt_target+1)
                    self.hlt_delta = 1 
                elif self.hlt_dn_button.is_pressed(finger_x, finger_y):
                    bp.set_hlt_target(bp.hlt_target-1)
                    self.hlt_delta = -1
                elif self.p1_switch.is_pressed(finger_x, finger_y):
                    bp.set_pump_state(1, self.p1_switch.state)
        if(self.count != None):
                self.count += 1
                if(self.count>4):
                    bp.set_mash_target(bp.mash_target + self.mash_delta)
                    bp.set_hlt_target(bp.hlt_target + self.hlt_delta)
        return True

class Button(BPGui):
    def __init__(self, x, y, size, icon):
        self.x = x
        self.y = y
        self.size = size
        self.bg_color = THEME_COLOR1
        self.rect = pygame.Rect(self.x+4, self.y+4, size-8, size-8)
        self.img = pygame.image.load(icon).convert_alpha()
    def draw(self, screen: pygame.Surface):
        pygame.draw.rect(screen, self.bg_color, self.rect, border_radius=8)
        img_rect = self.img.get_rect()
        offset = (self.size - img_rect.width) / 2
        screen.blit(self.img,(self.x+offset,self.y+offset))
        self.bg_color = THEME_COLOR1
    def is_pressed(self, x, y):
        if self.x < x < (self.x+self.size) and self.y < y < (self.y+self.size):
            self.bg_color = PRESSED_COLOR
            return True
        else:
            return False

class Switch(BPGui):
    def __init__(self, x, y, text_on='On'):
        self.x = x
        self.y = y
        self.state = False
        self.size = 64
        self.text = 'Off'
        self.disabled = False
        self.icon_on = 'assets/toggle-switch-on.png'
        self.icon_off = 'assets/toggle-switch-off.png'
        self.img = pygame.image.load(self.icon_off).convert_alpha()
    def draw(self, screen: pygame.Surface) :
        pygame.draw.rect(screen, 'black', (self.x, self.y, self.size, self.size))  # clear
        if self.disabled:
            pygame.PixelArray(self.img).replace((255,255,255), DISABLED)
        else:
            pygame.PixelArray(self.img).replace(DISABLED, (255,255,255))
        screen.blit(self.img,(self.x, self.y))
    def is_pressed(self, x, y):
        if self.disabled:
            return False
        if self.x < x < (self.x+self.size) and self.y < y < (self.y+self.size):
            if self.state == False:
                self.img = pygame.image.load(self.icon_on).convert_alpha()
                self.state = True
                return True
            else:
                self.img = pygame.image.load(self.icon_off).convert_alpha()
                self.state = False
                return True

class Indicator(BPGui):
    def __init__(self, x, y, icons):
        self.x = x
        self.y = y
        self.on = False
        self.i = 0
        self.img = pygame.image.load(icons[self.i]).convert_alpha()
        self.state = False
        self.size = self.img.get_rect().width
        self.icons = icons
    def draw(self, screen: pygame.Surface) :
        if self.on:
            self.i += 1
            if self.i==len(self.icons):
                self.i = 0
        else:
            self.i = 0
        self.img = pygame.image.load(self.icons[self.i]).convert_alpha()
        screen.blit(self.img,(self.x, self.y))

class Panel(BPGui):
    def __init__(self, x, y, width, name):
        self.x = x
        self.y = y
        self.width = width
        self.sml_font = pygame.font.Font('assets/SQR721B.TTF', 32)     # Square721 BT, Bold
        self.lrg_font = pygame.font.Font('assets/SQR721B.TTF', 64) 
        self.name_text = self.sml_font.render(name, True, THEME_COLOR3)                 
    def draw(self, screen: pygame.Surface, read_temp, target_temp):
        pygame.draw.rect(screen, 'black', (self.x, self.y, self.width, 160))  # clear panel
        screen.blit(self.name_text, (self.x,self.y))
        if(read_temp==None):
            text = "-----"
        else:
            text=str('{:5.1f}°c'.format(read_temp))
        reading_text = self.lrg_font.render(text, True, THEME_COLOR2)
        text=str('{:6.0f}°c'.format(target_temp))
        target_text = self.lrg_font.render(text, True, THEME_COLOR1)
        reading_text_rect = reading_text.get_rect()
        target_text_rect = target_text.get_rect()
        reading_text_rect.right = self.x + self.width
        reading_text_rect.top = self.y+32
        target_text_rect.right = self.x + self.width
        target_text_rect.top = self.y+96
        screen.blit(reading_text, reading_text_rect)
        screen.blit(target_text, target_text_rect)

class Reading(BPGui):
    def __init__(self, x, y, width, name):
        self.x = x
        self.y = y
        self.width = width
        self.sml_font = pygame.font.Font('assets/SQR721B.TTF', 32)     # Square721 BT, Bold
        self.name_text = self.sml_font.render(name+':', True, THEME_COLOR3)                 
    def draw(self, screen: pygame.Surface, read_temp):
        pygame.draw.rect(screen, 'black', (self.x, self.y, self.width, 32))  # clear panel
        screen.blit(self.name_text, (self.x,self.y))
        if(read_temp==None):
            text = "-----"
        else:
            text=str('{:5.1f}°c'.format(read_temp))
        reading_text = self.sml_font.render(text, True, THEME_COLOR2)
        reading_text_rect = reading_text.get_rect()
        reading_text_rect.right = self.x + self.width
        reading_text_rect.top = self.y
        screen.blit(reading_text, reading_text_rect)

