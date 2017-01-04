from sys import exit

import pygame


class Game:
    def __init__(self, start_env, screen, input_manager, frame_rate):
        self.environment = start_env()
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
        self.environment.reset_spawn()

        clock = pygame.time.Clock()
        while True:
            self.poll_events()
            self.controllers[0].update()
            self.main_routine(clock)
            pygame.display.flip()

    def main_routine(self, clock=None):
        if clock:
            dt = clock.tick(self.frame_rate) / 1000
        else:
            dt = 1

        environment = self.environment

        if not self.controllers[0].devices["start"].held:
            self.screen.fill((0, 0, 0))
            environment.main(dt, self.screen)
        elif self.controllers[0].devices["start"].check():
            self.screen.fill((0, 0, 0))
            environment.main(dt, self.screen)

        t = environment.transition_to
        if t:
            t.reset_spawn()
            environment.transition_to = None
            return_value = environment.get_value("_return")
            print(return_value)

            self.environment = t
            self.environment.controllers = self.input_manager.get_controllers()
            self.environment.set_value("_return", return_value)
