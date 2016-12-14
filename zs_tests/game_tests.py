from zs_tests.zs_unit_test import ZsUnitTest
from zs_src.game import Game


class GameUnitTest(ZsUnitTest):
    def do_tests(self):
        l = self.log
        l("!s", Game)

        class MockScreen:
            def __init__(self):
                self.fill_color = None

            def fill(self, color):
                self.fill_color = color

        class MockController:
            def __init__(self):
                self.get_inputs_called = False

            def get_inputs(self):
                self.get_inputs_called = True

        class MockEnvironment:
            def __init__(self, controller):
                self.controllers = [controller]
                self.main_called = False
                self.transition_to = None

            def main(self, dt, screen):
                self.main_called = dt, screen

        fr = 60
        cont = MockController()
        env, scr = MockEnvironment(cont), MockScreen()
        g = Game(env, scr, fr)

        assert g.environment is env
        l("environment ok")

        assert g.screen is scr
        l("screen ok")

        assert g.frame_rate == fr
        l("frame_rate ok")

        g.main_routine()
        assert env.main_called == (1, scr)
        assert cont.get_inputs_called
        l("main_routine ok")

        env.transition_to = "test"
        g.main_routine()
        assert g.environment == "test"
        assert env.transition_to is None
        l("transition ok")

        l("! ")


def do_tests():
    GameUnitTest().do_tests()

