# import sys
import pygame

from launch_environment import get_environment
from zs_constants.zs import SCREEN_SIZE, FRAME_RATE, CONTROLLERS, START_ENVIRONMENT
from zs_src.controller import InputManager
from zs_src.game import Game

pygame.init()
pygame.mixer.quit()
pygame.mixer.init(buffer=256)
# sys.stdout = open("output.txt", "w")

start_screen = pygame.display.set_mode(SCREEN_SIZE)
start_env = get_environment(START_ENVIRONMENT)
im = InputManager(*CONTROLLERS)

game = Game(start_env, start_screen, im, FRAME_RATE)
game.main()

# sys.stdout.close()
