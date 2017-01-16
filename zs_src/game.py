from sys import exit

import pygame


class Game:
    def __init__(self, start_env, screen, input_manager, frame_rate):
        self.environment = start_env()
        self.environment.game_environment = True
        self.screen = screen
        self.frame_rate = frame_rate

        self.input_manager = input_manager
        self.controllers = input_manager.get_controllers()
        self.environment.controllers = input_manager.get_controllers()

    @staticmethod
    def poll_events():
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()

    def main(self):
        self.environment.handle_event("spawn")

        clock = pygame.time.Clock()
        while True:
            self.poll_events()
            self.controllers[0].update()
            self.main_routine(clock)
            pygame.display.flip()

    def main_routine(self, clock=None):
        if clock:
            dt = clock.tick(self.frame_rate) / 1000
            # print(dt)
        else:
            dt = 1

        environment = self.environment

        self.screen.fill((15, 15, 25))
        environment.main(dt, self.screen)

        t = environment.transition_to
        if t:
            environment.transition_to = None
            environment.game_environment = False
            return_value = environment.get_value("_return")
            print(return_value)

            t.controllers = self.input_manager.get_controllers()
            t.set_value("_return", return_value)
            t.handle_event("spawn")
            t.game_environment = True
            self.environment = t
