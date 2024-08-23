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
DISABLED_COLOR ='darkslategray4'
OFF_COLOR = 'grey14'

class BPGui():
    def __init__(self, screen_x, screen_y):
        self.count = None
        self.sensor_task = None
        self.mash_delta = 0
        self.hlt_delta = 0
        self.screen_x = screen_x
        self.screen_y = screen_y
        self.display_quit_screen = False
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
        self.rims_reading = Reading(120, 260, 320, 'RIMS Tube')
        self.boil_reading = Reading(470, 260, 320, 'Boil Kettle')
        self.p1_switch= Switch(600, 320, 'On')
        self.p1_ind = Indicator (700, 306, PRESSED_COLOR, ['assets/pump-1.png', 'assets/pump-2.png', 'assets/pump-3.png'])
        self.p2_switch= Switch(600, 400, 'On')
        self.p2_ind = Indicator (700, 386, PRESSED_COLOR, ['assets/pump-1.png', 'assets/pump-2.png', 'assets/pump-3.png'])
        self.rims_switch = Switch(140, 180, 'Auto', disabled=True)
        self.rims_ind = Indicator (240, 166, 'red', ['assets/fire-1.png', 'assets/fire-2.png'])
        self.hlt_switch = Switch(490, 180, 'Auto')
        self.hlt_ind = Indicator (590, 166, 'red', ['assets/fire-1.png', 'assets/fire-2.png'])

    def create_quit_scrn(self):
        x=180
        y=320
        w=320
        h=144
        self.quit_panel = QuitPanel(x, y, w, h, 'Quit...?')
        btn_y = y+h-72
        btn_x = x+8
        self.back_button = Button(btn_x, btn_y, 64, 'assets/back.png')
        btn_x = x+(w/2)-32
        self.continue_button = Button(btn_x, btn_y, 64, 'assets/close.png')
        btn_x = x+w-72
        self.off_button = Button(btn_x, btn_y, 64, 'assets/off.png')

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
        self.p1_ind.draw(self.screen, bp.get_pump_state(1))
        self.p2_switch.draw(self.screen)
        self.p2_ind.draw(self.screen, bp.get_pump_state(2))
        self.rims_switch.draw(self.screen)
        self.rims_ind.draw(self.screen, bp.get_RIMS_state())
        self.hlt_switch.draw(self.screen)
        self.hlt_ind.draw(self.screen, bp.get_HLT_state())
        if self.display_quit_screen:
            self.update_quit_scrn(clear=False)
        else:
            self.update_quit_scrn(clear=True)

        pygame.display.update()
        await asyncio.sleep(0.210)
        self.clock.tick(0)
        logging.debug("Number ms between last 2 ticks: %d", self.clock.get_time())     
        logging.debug("RIMS Auto = {}, HLT Auto = {}, Relays = {}".format(bp.controllers[0].get('allow_heat'), bp.controllers[1].get('allow_heat'), bp.relay_chans_state))
        
    def update_quit_scrn(self, clear=False):
        if clear:
            self.quit_panel.clear(self.screen)
        else:
            self.quit_panel.draw(self.screen)
            self.continue_button.draw(self.screen)
            self.back_button.draw(self.screen)
            self.off_button.draw(self.screen)

    def event_handeller(self, bp: brewproc.Proc):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.FINGERUP:
                self.mash_delta = self.hlt_delta = 0
                self.count = None
            elif event.type == pygame.FINGERDOWN: 
                finger_x = int (event.x * self.screen_x + 0.5)
                finger_y = int (event.y * self.screen_y + 0.5)
                logging.debug("Finger touched the screen at ({},{})".format(finger_x, finger_y)) 
                self.count = 1
                if self.home_button.is_pressed(finger_x, finger_y):
                    settings_screen = False 
                elif self.settings_button.is_pressed(finger_x, finger_y):
                    settings_screen = True
                elif self.quit_button.is_pressed(finger_x, finger_y):
                    self.display_quit_screen = True
                    bp.kill_heat()
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
                elif self.rims_switch.is_pressed(finger_x, finger_y):
                    bp.toggle_controller_state('Mash')
                elif self.hlt_switch.is_pressed(finger_x, finger_y):
                    bp.toggle_controller_state('HLT')
                elif self.p1_switch.is_pressed(finger_x, finger_y):
                    bp.set_pump_state(1, self.p1_switch.state)
                elif self.p2_switch.is_pressed(finger_x, finger_y):
                    bp.set_pump_state(2, self.p2_switch.state)
        if(self.count != None):
                self.count += 1
                if(self.count>4):
                    bp.set_mash_target(bp.mash_target + self.mash_delta)
                    bp.set_hlt_target(bp.hlt_target + self.hlt_delta)
        return True

    def quit_event_handeller(self, bp: brewproc.Proc):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.FINGERUP:
                self.mash_delta = self.hlt_delta = 0
                self.count = None
            elif event.type == pygame.FINGERDOWN: 
                finger_x = int (event.x * self.screen_x + 0.5)
                finger_y = int (event.y * self.screen_y + 0.5)
                logging.debug("Finger touched the screen at ({},{})".format(finger_x, finger_y)) 
                if self.continue_button.is_pressed(finger_x, finger_y):
                    return False 
                elif self.back_button.is_pressed(finger_x, finger_y):
                   self.display_quit_screen = False
                elif self.quit_button.is_pressed(finger_x, finger_y):
                   self.display_quit_screen = False
                elif self.off_button.is_pressed(finger_x, finger_y):
                   return False
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
    def __init__(self, x, y, text_on='On', disabled = False):
        self.x = x
        self.y = y
        self.text_on = text_on
        self.disabled = disabled
        self.state = False
        self.width = 96
        self.bg_color = THEME_COLOR1
        self.sml_font = pygame.font.Font('assets/SQR721B.TTF', 32)     # Square721 BT, Bold
        self.button_rect = pygame.Rect(self.x+4, self.y+4, self.width-8, 56)
    def draw(self, screen: pygame.Surface) :
        pygame.draw.rect(screen, self.bg_color, self.button_rect, border_radius=8)
        text = self.text_on if self.state else 'Off'
        text_color = DISABLED_COLOR if self.disabled else THEME_COLOR2
        screen_text = self.sml_font.render(text, True, text_color) 
        text_rect = screen_text.get_rect(center = self.button_rect.center)
        screen.blit(screen_text, text_rect)
    def is_pressed(self, x, y):
        if self.disabled:
            return False
        if self.x < x < (self.x+self.width) and self.y < y < (self.y+64):
            if self.state == False:
                self.bg_color = PRESSED_COLOR
                self.state = True
                return True
            else:
                self.bg_color = THEME_COLOR1
                self.state = False
                return True

class Indicator(BPGui):
    def __init__(self, x, y, on_color, icons):
        self.x = x
        self.y = y
        self.state = False
        self.on_color = on_color
        self.i = 0
        self.img = pygame.image.load(icons[0])  # just to get size
        self.size = self.img.get_rect().width
        self.icons = icons
    def draw(self, screen: pygame.Surface, state=False) :
        if state:
            self.i += 1
            if self.i==len(self.icons):
                self.i = 0
            img_color = self.on_color
        else:
            self.i = 0
            img_color = OFF_COLOR
        pygame.draw.rect(screen, 'black', (self.x, self.y, self.size, self.size)) # clear
        image = pygame.image.load(self.icons[self.i]).convert_alpha()
        color_image = pygame.Surface(image.get_size()).convert_alpha()
        color_image.fill(img_color)
        image.blit(color_image, (0,0), special_flags = pygame.BLEND_RGBA_MULT)
        screen.blit(image,(self.x, self.y))
        #logging.debug("State: {},  Index: {}, Img color: {}".format(state, self.i, img_color))

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

class QuitPanel(BPGui):
    def __init__(self, x, y, width, height, name):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.font = pygame.font.Font('assets/SQR721B.TTF', 48)     # Square721 BT, Bold
        self.name_text = self.font.render(name, True, 'black')                 
    def draw(self, screen: pygame.Surface):
        pygame.draw.rect(screen, 'white', (self.x, self.y, self.width, self.height))  # clear panel
        text_rect = self.name_text.get_rect()
        text_rect.centerx = self.x+(self.width/2)
        text_rect.y = self.y + 4
        screen.blit(self.name_text, text_rect)
    def clear(self, screen: pygame.Surface):
        pygame.draw.rect(screen, 'black', (self.x, self.y, self.width, self.height))  # clear panel
        