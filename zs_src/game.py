from sys import exit
import pygame


class Game:
    def __init__(self, start_env, screen, controllers, frame_rate):
        self.environment = start_env()
        self.screen = screen
        self.frame_rate = frame_rate

        self.controllers = controllers
        self.environment.controllers = controllers

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
            self.main_routine(clock)
            pygame.display.flip()

    def main_routine(self, clock=None):
        if clock:
            dt = clock.tick(self.frame_rate) / 1000
            # print(dt)
        else:
            dt = 1

        environment = self.environment

        for controller in environment.controllers:
            controller.update()

        # cont = environment.controllers[0]
        # if cont.devices["a"].held:
        #     self.screen.fill((0, 0, 0))
        #     environment.main(dt, self.screen)
        self.screen.fill((0, 0, 0))
        environment.main(dt, self.screen)

        t = environment.transition_to
        if t:
            t.reset_spawn()
            environment.transition_to = None

            self.environment = t
            self.environment.controllers = self.controllers
