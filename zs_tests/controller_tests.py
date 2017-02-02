from collections import OrderedDict
from random import randint, seed

from zs_src.controller import Controller, FrameSlice, Command, Step
from zs_tests.zs_unit_test import ZsUnitTest


class FrameSliceUnitTest(ZsUnitTest):
    def do_tests(self, r=5):
        l = self.log
        l("!s", FrameSlice)

        fs = FrameSlice(r)
        fs.append(None)
        for x in range(r * 2):
            fs.append((x, ))
        assert len(fs) == r
        l("append ok")

        fs = FrameSlice(r)
        items = [(x, ) for x in range(r * 2)]
        fs.add_frames(items)
        assert fs == items[-r:]
        l("add_frames ok")

        fs.add_device_name("test")
        history = [x for x in range(r * 2)]
        assert fs.get_device_history("test") == history[-r:]
        l("add_device_name ok")
        l("get_device_history_ok")

        fs2 = fs.get_frame_slice(1, r)
        assert fs2 == fs[1:r]
        assert fs2.get_device_history("test") == fs.get_device_history("test")[1:r]
        l("get_frame_slice ok")
        l("")
        l("FrameSlice ok")
        l("! ")


class StepUnitTest(ZsUnitTest):
    CF_dict = {
        "a": lambda x: x > 1,
        "b": lambda x: x < 2,
        "c": lambda x: x != 4,
        "d": lambda x: x.is_integer()}
    NAMES = "abcd"

    DESC = {
        NAMES[0]: "greater than 1",
        NAMES[1]: "less than 2",
        NAMES[2]: "not equal to 4",
        NAMES[3]: "is integer"}

    def get_frame_slice(self, names, size, r):
        fs = FrameSlice(size)
        fs.add_frames(self.get_frames(len(names), size, r))
        fs.add_device_names(*names)

        return fs

    @staticmethod
    def get_frames(device_amt, size, r):
        frames = []
        for y in range(size):
            frame = StepUnitTest.get_frame(device_amt, r)
            frames.append(frame)

        return frames

    @staticmethod
    def get_frame(device_amt, r):
        frame = []
        for y in range(device_amt):
            value = randint(1, r) / 2
            frame.append(value)

        return tuple(frame)

    def do_tests(self, r=5):
        l = self.log
        l("!s", Step)
        seed(r)

        self.test_init(r)
        l("! ")

        self.test_conditions(r)
        l("! ")

    def test_init(self, r):
        l = self.log
        l("!m", self.test_init)

        for x in range(r):
            description = "test"
            conditions = "test"
            frame_window = x
            step = Step(description, conditions, frame_window)

            assert step.description == description
            l("description ok")

            assert step.conditions == conditions
            l("conditions ok")

            assert step.frame_window == frame_window
            l("frame_window ok\n")
        l("init ok")

    def test_conditions(self, r):
        l = self.log
        self.log_method_header(self.test_conditions)

        check_funcs = self.CF_dict
        names = self.NAMES

        conditions = []
        for i in range(len(check_funcs)):
            name = names[i]
            cf = check_funcs[name]
            conditions.append((name, cf))

        #
        # MAKE STEP OBJECTS
        for x in range(r):
            l("!r")
            frame_window = (x % round(r / 2)) + 1
            new_conditions = conditions[:(x % len(conditions)) + 1]
            step = Step("test step", new_conditions, frame_window)
            l("step, frame_window: {}".format(frame_window))

            # MAKE FRAME SLICE
            fs = self.get_frame_slice(names, r, r)

            #
            #   PRINT FRAME MATRIX
            l("frame slice:")
            self.log_matrix([fs.device_names], fs, cw=5, co=1)
            l("")

            #
            #   PRINT CHECK MATRIX
            l("check matrix:")
            for con in step.conditions:
                name, check = con
                description = self.DESC[name]

                #
                # ADD CONDITION DESCRIPTIONS
                row = [check(frame) for frame in fs.get_device_history(name)]
                desc = "\t{} for device {}".format(description, name)
                self.log_row(row, desc=desc)
            l("")

            #
            # iterate frame_window sub slices through
            # entire frame_slice object

            matrix = step.get_matrix(fs)
            answer = 0
            for i in range((r - step.frame_window) + 1):
                sub_matrix = step.get_sub_matrix(matrix, i)

                #
                # PRINT SUB MATRICES
                msg = (" " * (3 * i))
                l(msg + "i: {}".format(i))
                self.log_matrix(sub_matrix, co=i, fill=".")

                # break loop if answer found
                if all([any(row) for row in sub_matrix]):
                    answer = i + 1
                    break

            assert answer == step.check(fs)
            #
            # PRINT OUTPUT
            l("!u         output: {}".format(step.check(fs)))
            l("")


class CommandUnitTest(StepUnitTest):
    @staticmethod
    def get_frame(device_amt, r):
        frame = []
        for y in range(device_amt):
            value = randint(1, 5) / 2
            frame.append(value)

        return tuple(frame)

    def do_tests(self, r=5):
        l = self.log
        l("!s", Command)
        seed(r)

        self.test_init(r)
        l("! ")

        self.test_update(r)
        l("! ")

        self.test_check(r)
        l("! ")

    def test_init(self, r):
        self.log_method_header(self.test_init)
        l = self.log

        class MockStep:
            def __init__(self):
                self.frame_window = 1

        # CREATE COMMAND OBJECTS
        for x in range(r):
            name = "test command"
            fw = x + 1
            steps = [MockStep()] * randint(1, r)
            command = Command(name, steps, fw)

            assert command.name == name
            l("name ok")

            assert command.steps == steps
            l("steps ok")

            assert command.frame_window == fw
            l("frame_window ok")
            l("")
        l("init ok")

    def test_update(self, r):
        l = self.log
        l("!m ", self.test_update)

        class MockStep:
            def __init__(self):
                self.frame_window = 1

        # CREATE COMMAND OBJECT
        name = "test command"
        steps = [MockStep()] * randint(1, r)
        buffer = 0
        command = Command(name, steps, buffer)
        fw = command.frame_window

        fs = self.get_frame_slice(["test device"], r * 2, r)

        # TEST UPDATE METHOD
        max_i = len(fs) - fw
        for i in range(max_i):
            sub_slice = fs.get_frame_slice(0, i + fw)
            command.update(sub_slice)

            assert command.frames[0] == sub_slice[-fw]
            assert command.frames[-1] == sub_slice[-1]
            l("frames adjusted ok")
        l("update ok")

    def get_steps(self, r):
        check_funcs = self.CF_dict

        steps = []
        for x in range(randint(1, r)):
            conditions = []
            for i in range(randint(1, len(check_funcs))):
                cf = check_funcs[self.NAMES[i]]
                conditions.append((self.NAMES[i], cf))

            step = Step("test step", conditions, randint(1, 3))
            steps.append(step)
        return steps

    def test_check(self, r):
        l = self.log
        self.log_method_header(self.test_check)
        CELL_WIDTH = 5

        #
        # TEST COMMANDS
        for x in range(r):
            name = "test command"
            steps = self.get_steps(r)
            buffer = randint(1, 3)
            command = Command(name, steps, buffer * len(steps))

            #
            # PRINT COMMAND OBJECT
            l("!u {}, frame_window: {}, buffer: {}, {} steps".format(
                name, command.frame_window, buffer, len(steps)
            ))

            #
            # PRINT FRAME SLICE
            l("        frame_slice:")
            fs = self.get_frame_slice(self.NAMES, command.frame_window, r)
            command.update(fs)
            self.log_matrix([fs.device_names], command.frames, ro=8, cw=CELL_WIDTH)

            i = 0
            step_n = 0
            full_length = len(command.frames)
            step_fail = False

            #
            # TEST STEPS
            for step in command.steps:
                fw = step.frame_window

                #
                # PRINT STEP
                l("step {}, frame_window: {}, conditions:".format(step_n + 1, fw))

                #
                # PRINT CONDITIONS
                for c in step.conditions:
                    name, cf = c
                    msg = "\tdevice {}: {}".format(name, self.DESC[name])
                    l(msg)

                sub_slice = command.frames.get_frame_slice(i, full_length)
                check_matrix = step.get_matrix(sub_slice)
                assert len(check_matrix[0]) == len(sub_slice)

                output = step.check(sub_slice)
                i += output
                if output:
                    step_n += 1

                #
                # PRINT CHECK MATRIX
                self.log_matrix(check_matrix, cw=CELL_WIDTH, ro=2)

                #
                # PRINT OUTPUT
                if output:
                    lhs = ("." * 6) * (output - 1)
                    inside = ("^" * 6) * (fw - 1)
                    inside += "^"
                    pointer = "....{}[{}]".format(lhs[:-1], inside)
                else:
                    pointer = "[^]"
                l(pointer + " output: {}".format(output))
                l("")

                # BREAK IF STEP FAILS
                if output == 0:
                    step_fail = True
                    break

            assert command.check() == (not step_fail)

            #
            # PRINT COMMAND.CHECK RESULT

            l("!u steps completed: {} {}/{}".format(not step_fail, step_n, len(steps)))
            l("!r")
            l("")
        l("check ok")


class ZsControllerUnitTest(ZsUnitTest):
    class MockDevice:
        def __init__(self, name):
            self.name = name

        def get_frame(self):
            return self.name

    class MockCommand:
        def __init__(self, name, fw):
            self.name = name
            self.frame_window = fw
            self.frames = None

        def update(self, frames):
            self.frames = frames

    class MockButton:
        def __init__(self):
            self.on_down_calls = 0
            self.on_up_calls = 0

        def is_pressed(self):
            return bool(randint(0, 1))

        def on_up(self):
            self.on_up_calls += 1

        def on_down(self):
            self.on_down_calls += 1

    def do_tests(self, r=5):
        l = self.log
        l("!s", Controller)
        seed(r)

        name = "test controller"
        controller = Controller(name)
        assert controller.name == name
        l("name ok")

        size = randint(1, r)
        controller.set_input_log_size(size)
        controller.input_log.add_frames([None] * (size * 2))
        assert len(controller.input_log) == size
        l("set_input_log_size ok")
        l("")

        self.test_update_methods(r)
        l("update methods ok")

        l("! ")

    def test_update_methods(self, r):
        l = self.log
        l("!m", self.test_update_methods)

        names = "abcde"
        devices, commands, buttons = OrderedDict(), {}, []
        for name in names:
            device = self.MockDevice(name)
            fw = randint(1, r)
            command = self.MockCommand(name, fw)
            button = self.MockButton()
            devices[name] = device
            commands[name] = command
            buttons.append(button)

        name = "test controller"
        controller = Controller(name)

        # UPDATE DEVICES TEST

        controller.devices = devices
        controller.update_devices()

        assert controller.input_log[-1] == list(names)
        l("update_devices ok")

        # UPDATE COMMANDS TEST

        controller.commands = commands
        controller.update_commands()

        for command in commands.values():
            assert command.frames[-1] == list(names)
        l("update_commands ok")


#
TESTS = ZsControllerUnitTest, FrameSliceUnitTest, StepUnitTest, CommandUnitTest


def do_tests(r=5):
    for t in TESTS:
        t().do_tests(r)
