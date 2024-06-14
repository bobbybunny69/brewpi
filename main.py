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

import pygame
import bpgui

screen_x = 800
screen_y = 480
mash_target = hlt_target = 0
mash_delta = hlt_delta = 0
count = None

bpg = bpgui.BPGui(screen_x, screen_y)

home_button = bpgui.Button(0, 0, 96, 'assets/home.png')
settings_button = bpgui.Button(0, 96, 96, 'assets/cog.png')
quit_button = bpgui.Button(0, 384, 96, 'assets/power.png')

mash_up_button = bpgui.Button(382, 36, 64, 'assets/arrow-up.png')
mash_dn_button = bpgui.Button(382, 102, 64, 'assets/arrow-down.png')
hlt_up_button = bpgui.Button(732, 36, 64, 'assets/arrow-up.png')
hlt_dn_button = bpgui.Button(732, 102, 64, 'assets/arrow-down.png')

mash_panel = bpgui.Panel(120, 250, 'Mash Tun')
hlt_panel = bpgui.Panel(470, 250, 'Hot Liquor Tank')

running = True
while running:
    for event in pygame.event.get():
        #print("event: ", event)
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.FINGERUP:
            #print("finger lifted")
            mash_delta = hlt_delta = 0
            count = None
        elif event.type == pygame.FINGERDOWN: 
            finger_x = int (event.x * screen_x + 0.5)
            finger_y = int (event.y * screen_y + 0.5)
            #print("Finger touched the screen at ({},{})".format(finger_x, finger_y)) 
            count = 1
            if home_button.is_pressed(finger_x, finger_y):
                settings_screen = False 
            elif settings_button.is_pressed(finger_x, finger_y):
                settings_screen = True
            elif quit_button.is_pressed(finger_x, finger_y):
                running = False 
            elif mash_up_button.is_pressed(finger_x, finger_y):
                mash_target += 1
                mash_delta = 1
            elif mash_dn_button.is_pressed(finger_x, finger_y):
                mash_target -= 1
                mash_delta = -1
            elif hlt_up_button.is_pressed(finger_x, finger_y):
                hlt_target += 1
                hlt_delta = 1 
            elif hlt_dn_button.is_pressed(finger_x, finger_y):
                hlt_target -= 1
                hlt_delta = -1 
    if(count != None):
        count += 1
        if(count>4):
            mash_target += mash_delta
            hlt_target += hlt_delta

    # draw all our elements
    mash_panel.draw(45.6, mash_target)
    hlt_panel.draw(67.8, hlt_target)

    home_button.draw()
    settings_button.draw()
    quit_button.draw()
    mash_up_button.draw()
    mash_dn_button.draw()
    hlt_up_button.draw()
    hlt_dn_button.draw()
    # update everything
    pygame.display.update()
    bpg.clock.tick(4)

pygame.quit()
