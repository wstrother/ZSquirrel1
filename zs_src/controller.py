from collections import OrderedDict
from math import sqrt
from sys import maxsize
from zs_constants.controller import FRAME_SLICE_SIZE, INIT_DELAY, HELD_DELAY


class ZsController:
    def __init__(self, name):
        self.name = name
        self.devices = OrderedDict()
        self.commands = {}
        self.input_log = FrameSlice(FRAME_SLICE_SIZE)

    def update(self):
        self.update_devices()
        self.update_commands()

    def update_devices(self):
        frame = []
        for device in self.devices.values():
            frame.append(device.get_frame())
        self.input_log.append(frame)

    def update_commands(self):
        for command in self.commands.values():
            command.update(self.input_log)

    def set_input_log_size(self, size):
        self.input_log = FrameSlice(size)
        for name in self.devices:
            self.input_log.add_device_name(name)

    #
    def add_command(self, command):
        self.commands[command.name] = command

        if command.frame_window > len(self.input_log):
            self.set_input_log_size(command.frame_window)

    def add_button(self, name, mapping):
        button = ZsController.Button(name, mapping)
        self.devices[name] = button

    def add_dpad(self, name, mappings):
        self.devices[name] = ZsController.Dpad(name, mappings)

    def add_thumbstick(self, name, mappings):
        self.devices[name] = ZsController.ThumbStick(name, mappings)

    def add_trigger(self, name, mapping):
        self.devices[name] = ZsController.Trigger(name, mapping)

    class Button:
        def __init__(self, name, mapping):
            self.name = name
            self.ignore = False
            self.held = 0

            self.mapping = mapping
            self.init_delay = INIT_DELAY
            self.held_delay = HELD_DELAY

        def __repr__(self):
            s = self.name + " " + str(self.held) + " " + str(self.held)
            return s

        def get_profile(self):
            name = self.__class__.__name__
            device_name = self.name
            mapping = self.mapping.get_profile()

            d = {'name': name,
                 'device_name': device_name,
                 'mapping': mapping}

            return d

        def get_pressed(self):
            return self.mapping.is_pressed()

        # returns bool to register a 'normal' input on frames when button is down and ignore
        # flag is not True
        def check(self):
            return self.held and not self.ignore

        # when button is pressed down
        def on_down(self):
            if self.held < maxsize:
                self.held += 1
            else:
                self.held = self.init_delay

            # set ignore frames for initial and continuous inputs
            if 1 < self.held < self.init_delay:
                self.ignore = True

            elif self.held >= self.init_delay:
                if (self.held - self.init_delay) % self.held_delay == 0:
                    self.ignore = False
                else:
                    self.ignore = True

        # when button is let go
        def on_up(self):
            self.ignore = False
            self.held = 0

        def get_frame(self):
            pressed = self.mapping.is_pressed()
            if pressed:
                self.on_down()
            else:
                self.on_up()

            output = (self.held, self.ignore)

            return output

    class Dpad:
        def __init__(self, name, mappings):
            self.name = name

            names = "up down left right".split()
            d_buttons = []
            i = 0
            for mapping in mappings:
                button = ZsController.Button(names[i], mapping)
                d_buttons.append(button)
                i += 1

            self.up = d_buttons[0]
            self.down = d_buttons[1]
            self.left = d_buttons[2]
            self.right = d_buttons[3]
            self.buttons = d_buttons

        def get_direction(self):
            x, y = 0, 0
            up, down, left, right = (
                self.up.held,
                self.down.held,
                self.left.held,
                self.right.held)

            if up and not down:
                y -= 1
            if down and not up:
                y += 1
            if left and not right:
                x -= 1
            if right and not left:
                x += 1

            return x, y

        def check(self):
            dominant = self.get_dominant()

            return dominant.check()

        def get_dominant(self):
            u, d, l, r = self.up, self.down, self.left, self.right

            return sorted([u, d, l, r], key=lambda b: b.held * -1)[0]

        def get_frame(self):
            output = (
                self.up.get_frame(),
                self.down.get_frame(),
                self.left.get_frame(),
                self.right.get_frame())

            return output

        def get_profile(self):
            name = self.__class__.__name__
            device_name = self.name
            up, down, left, right = (
                self.up.get_profile(),
                self.down.get_profile(),
                self.left.get_profile(),
                self.right.get_profile())

            d = {'name': name,
                 'device_name': device_name,
                 'up': up,
                 'down': down,
                 'left': left,
                 'right': right}

            return d

    class ThumbStick:
        def __init__(self, name, mappings):
            self.name = name
            self.x_axis = mappings[0]
            self.y_axis = mappings[1]

        def get_x_axis(self):
            return self.x_axis.get_value()

        def get_y_axis(self):
            return self.y_axis.get_value()

        def get_magnitude(self):
            x, y = self.get_x_axis(), self.get_y_axis()
            x **= 2
            y **= 2
            m = round(sqrt(x + y), 3)

            return m

        def get_direction(self):
            x, y = self.get_x_axis(), self.get_y_axis()

            return x, y

        def get_frame(self):
            output = (self.get_direction(), self.get_magnitude())

            return output

        def get_profile(self):
            name = self.__class__.__name__
            device_name = self.name
            x_axis = self.x_axis.get_profile()
            y_axis = self.y_axis.get_profile()

            d = {'name': name,
                 'device_name': device_name,
                 'x_axis': x_axis,
                 'y_axis': y_axis}

            return d

    class Trigger:
        def __init__(self, name, mapping):
            self.name = name
            self.mapping = mapping

        def get_displacement(self):
            return self.mapping.get_value()

        def get_frame(self):
            output = (self.get_displacement(), )

            return output

        def get_profile(self):
            name = self.__class__.__name__
            device_name = self.name
            axis = self.mapping.get_profile()

            d = {'name': name,
                 'device_name': device_name,
                 'axis': axis}

            return d


class FrameSlice(list):
    def __init__(self, size):
        super(FrameSlice, self).__init__()
        self.device_names = []
        self.size = size

    def append(self, p_object):
        super(FrameSlice, self).append(p_object)
        if len(self) > self.size:
            for i in range(len(self) - 1):
                self[i] = self[i + 1]
            self.pop()

    def add_frames(self, frames):
        for frame in frames:
            self.append(frame)

    def add_device_name(self, name):
        self.device_names.append(name)

    def add_device_names(self, *names):
        for name in names:
            self.add_device_name(name)

    def get_device_history(self, name):
        i = self.device_names.index(name)

        return [frame[i] for frame in self]

    def get_frame_slice(self, start, stop):
        fs = FrameSlice(stop - start)
        fs.add_frames(self[start:stop])

        for name in self.device_names:
            fs.add_device_name(name)

        return fs


class Command:
    def __init__(self, name, steps, frame_window=0):
        self.name = name
        self.steps = steps
        if not frame_window:
            frame_window = sum([step.frame_window for step in steps])
        self.frame_window = frame_window
        self.frames = None

    def update(self, frames):
        l = len(frames)
        window = l - self.frame_window
        self.frames = frames.get_frame_slice(window, l)

    def check(self):
        frames = self.frames
        l = len(frames)
        i = 0
        for step in self.steps:
            sub_slice = frames.get_frame_slice(i, l)
            j = step.check(sub_slice)
            i += j
            if j == 0:
                return False

        return True

    def __repr__(self):
        return self.name


class Step:
    # condition: tuple(name, check_function)
    # check_function: function(frame) => Bool

    def __init__(self, description, conditions, frame_window=1):
        self.description = description
        self.conditions = conditions
        self.frame_window = frame_window

    def get_matrix(self, frames):
        frame_matrix = []
        conditions = self.conditions

        for con in conditions:
            name, check = con
            history = frames.get_device_history(name)
            row = [check(frame) for frame in history]
            frame_matrix.append(row)

        return frame_matrix

    def get_sub_matrix(self, frame_matrix, i):
        conditions = self.conditions
        fw = self.frame_window
        sub_matrix = []

        for con in conditions:
            row_i = conditions.index(con)
            row = frame_matrix[row_i][i:i + fw]
            sub_matrix.append(row)

        return sub_matrix

    def check(self, frames):
        frame_matrix = self.get_matrix(frames)
        fw = self.frame_window
        fl = len(frames)

        for i in range((fl - fw) + 1):
            sub_matrix = self.get_sub_matrix(frame_matrix, i)
            truth = all([any(row) for row in sub_matrix])

            if truth:
                return i + 1
        return 0

    def __repr__(self):
        d, fw = self.description, self.frame_window

        return "{}, frame window: {}".format(d, fw)


