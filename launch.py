# import sys
import pygame
from zs_constants.zs import SCREEN_SIZE, FRAME_RATE, CONTROLLERS, START_ENVIRONMENT
from zs_src.game import Game
from launch_controller import get_controllers
from launch_environment import get_environment

pygame.init()

start_screen = pygame.display.set_mode(SCREEN_SIZE)
start_controller = get_controllers(CONTROLLERS)[0]

start_env = get_environment(START_ENVIRONMENT)

game = Game(start_env, start_screen, [start_controller], FRAME_RATE)

# sys.stdout = open("output.txt", "w")

game.main()

# sys.stdout.close()
