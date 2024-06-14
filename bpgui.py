# Classes to aid creating a GUI for brewpi in pygame
import pygame

THEME_COLOR1 = 'dodgerblue4'
THEME_COLOR2 = 'white'
THEME_COLOR3 = 'yellow'
PRESSED_COLOR = 'blue'

class BPGui():
    screen = None
    def __init__(self, screen_x, screen_y):
        self.count = None
        #pygame.init() - commening out to initialise components individually so we dont get audio issues
        screen = pygame.display.set_mode((screen_x,screen_y))
        pygame.font.init()
        pygame.mouse.set_visible(False)    # Hide cursor here
        self.screen.fill('black')
        self.clock = pygame.time.Clock()
    def create(self):
        self.home_button = Button(0, 0, 96, 'assets/home.png')
        self.settings_button = Button(0, 96, 96, 'assets/cog.png')
        self.quit_button = Button(0, 384, 96, 'assets/power.png')
        self.mash_up_button = Button(382, 36, 64, 'assets/arrow-up.png')
        self.mash_dn_button = Button(382, 102, 64, 'assets/arrow-down.png')
        self.hlt_up_button = Button(732, 36, 64, 'assets/arrow-up.png')
        self.hlt_dn_button = Button(732, 102, 64, 'assets/arrow-down.png')
        self.mash_panel = Panel(120, 250, 'Mash Tun')
        self.hlt_panel = Panel(470, 250, 'Hot Liquor Tank')

class Button(BPGui):
    def __init__(self, x, y, size, icon):
        self.x = x
        self.y = y
        self.size = size
        self.bg_color = THEME_COLOR1
        self.rect = pygame.Rect(self.x+4, self.y+4, size-8, size-8)
        self.img = pygame.image.load(icon).convert_alpha()
        super().__init__(self)            
    def draw(self):
        pygame.draw.rect(self.screen, self.bg_color, self.rect, border_radius=8)
        img_rect = self.img.get_rect()
        offset = (self.size - img_rect.width) / 2
        self.screen.blit(self.img,(self.x+offset,self.y+offset))
        self.bg_color = THEME_COLOR1
    def is_pressed(self, x, y):
        if self.x < x < (self.x+self.size) and self.y < y < (self.y+self.size):
            self.bg_color = PRESSED_COLOR
            return True
        else:
            return False
    
class Panel(BPGui):
    def __init__(self, x, width, name):
        self.x = x
        self.width = width
        self.sml_font = pygame.font.Font('assets/SQR721B.TTF', 32)     # Square721 BT, Bold
        self.lrg_font = pygame.font.Font('assets/SQR721B.TTF', 64) 
        self.name_text = self.sml_font.render(name, True, THEME_COLOR3)                 
        super().__init__(self)            
    def draw(self, read_temp, target_temp):
        pygame.draw.rect(self.screen, 'black', (self.x, 0, self.width, 160))  # clear panel
        self.screen.blit(self.name_text, (self.x,0))
        text=str('{:5.1f}°c'.format(read_temp))
        reading_text = self.lrg_font.render(text, True, THEME_COLOR2)
        text=str('{:6.0f}°c'.format(target_temp))
        target_text = self.lrg_font.render(text, True, THEME_COLOR1)
        reading_text_rect = reading_text.get_rect()
        target_text_rect = target_text.get_rect()
        reading_text_rect.right = self.x + self.width
        reading_text_rect.top = 32
        target_text_rect.right = self.x + self.width
        target_text_rect.top = 96

        self.screen.blit(reading_text, reading_text_rect)
        self.screen.blit(target_text, target_text_rect)

