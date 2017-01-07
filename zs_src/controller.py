import json
from collections import OrderedDict
from math import sqrt
from os.path import join

import pygame

from zs_constants.controller import FRAME_SLICE_SIZE, INIT_DELAY, HELD_DELAY
from zs_constants.gui import UP, DOWN, LEFT, RIGHT
from zs_constants.paths import CONTROLLER_PROFILES
from zs_src.classes import CacheList
from zs_src.profiles import Profile

pygame.init()
STICK_DEAD_ZONE = .1


class InputMapper:
    AXIS_NEUTRAL = False
    AXIS_MIN = .9
    INPUT_DEVICES = []
    for J in range(pygame.joystick.get_count()):
        joy = pygame.joystick.Joystick(J)
        joy.init()
        INPUT_DEVICES.append(joy)

    class ButtonMappingKey:
        def __init__(self, id_num):
            self.id_num = id_num

        def __repr__(self):
            id_num = "'map_id', {}".format(self.id_num)
            name = "'key_name', '{}'".format(pygame.key.name(self.id_num))
            map_type = "'map_type', 'key'"
            line = "('button_map', ({}), ({}), ({}))".format(
                id_num, name, map_type)

            return line

        def is_pressed(self):
            return pygame.key.get_pressed()[self.id_num]

        @staticmethod
        def get_id(key_string):
            if len(key_string) > 1:
                key = "K_" + key_string.upper()
            else:
                key = "K_" + key_string

            return pygame.__dict__[key]

        def get_profile(self):
            t = eval(repr(self))

            d = {'name': t[0]}
            d.update(dict(t[1:]))

            return d

    class ButtonMappingButton(ButtonMappingKey):
        def __init__(self, id_num, joy_device):
            super(InputMapper.ButtonMappingButton, self).__init__(id_num)
            self.joy_device = joy_device

        def __repr__(self):
            id_num = "'map_id', {}".format(self.id_num)
            name = "'joy_name', '{}'".format(self.joy_device.get_name())
            joy_id = "'joy_id', {}".format(self.joy_device.get_id())
            map_type = "'map_type', 'button'"
            line = "('button_map', ({}), ({}), ({}), ({}))".format(
                id_num, name, joy_id, map_type)

            return line

        def is_pressed(self):
            return self.joy_device.get_button(self.id_num)

    class ButtonMappingAxis(ButtonMappingButton):
        DEAD_ZONE = .1

        def __init__(self, id_num, joy_device, sign):
            super(InputMapper.ButtonMappingAxis, self).__init__(id_num, joy_device)
            self.dead_zone = InputMapper.ButtonMappingAxis.DEAD_ZONE
            self.sign = sign

        def __repr__(self):
            id_num = "'map_id', {}".format(self.id_num)
            name = "'joy_name', '{}'".format(self.joy_device.get_name())
            joy_id = "'joy_id', {}".format(self.joy_device.get_id())
            dead_zone = "'dead_zone', {}".format(self.dead_zone)
            sign = "'sign', {}".format(self.sign)
            map_type = "'map_type', 'axis'"

            line = "('button_map', ({}), ({}), ({}), ({}), ({}), ({}))"
            line = line.format(
                id_num, name, joy_id, dead_zone, sign, map_type)

            return line

        def is_pressed(self):
            axis = self.joy_device.get_axis(self.id_num)

            return axis * self.sign > self.dead_zone

    class ButtonMappingHat(ButtonMappingButton):
        def __init__(self, id_num, joy_device, position, axis):
            super(InputMapper.ButtonMappingHat, self).__init__(id_num, joy_device)
            self.position = position
            self.axis = axis

        def __repr__(self):
            id_num = "'map_id', {}".format(self.id_num)
            name = "'joy_name', '{}'".format(self.joy_device.get_name())
            joy_id = "'joy_id', {}".format(self.joy_device.get_id())
            position = "'position', {}".format(self.position)
            axis = "'axis', {}".format(self.axis)
            map_type = "'map_type', 'hat'"

            line = "('button_map', ({}), ({}),  ({}), ({}), ({}))"
            line = line.format(
                id_num, name, joy_id, position, axis, map_type)

            return line

        def is_pressed(self):
            hat = self.joy_device.get_hat(self.id_num)
            if self.axis != -1:
                return hat[self.axis] == self.position
            else:
                return hat == self.position

    class AxisMapping:
        def __init__(self, id_num, joy_device, sign):
            self.id_num = id_num
            self.sign = sign
            self.joy_device = joy_device

        def __repr__(self):
            id_num = "'map_id', {}".format(self.id_num)
            name = "'joy_name', '{}'".format(self.joy_device.get_name())
            joy_id = "'joy_id', {}".format(self.joy_device.get_id())
            sign = "'sign', {}".format(self.sign)
            line = "('axis_map', ({}), ({}), ({}), ({}))".format(
                id_num, name, joy_id, sign)

            return line

        def get_value(self):
            sign = self.sign

            return self.joy_device.get_axis(self.id_num) * sign

        def get_profile(self):
            t = eval(repr(self))

            d = {'name': t[0]}
            d.update(dict(t[1:]))

            return d

    @staticmethod
    def check_axes():
        axes = []
        for device in InputMapper.INPUT_DEVICES:
            for i in range(device.get_numaxes()):
                axes.append(device.get_axis(i))

        if not InputMapper.AXIS_NEUTRAL:
            InputMapper.AXIS_NEUTRAL = all([axis < .01 for axis in axes])

    @staticmethod
    def get_mapping():
        devices = InputMapper.INPUT_DEVICES

        pygame.event.clear()
        while True:
            InputMapper.check_axes()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit()

                axis, button, hat, key = (
                    event.type == pygame.JOYAXISMOTION,
                    event.type == pygame.JOYBUTTONDOWN,
                    event.type == pygame.JOYHATMOTION,
                    event.type == pygame.KEYDOWN)

                if key:
                    return InputMapper.ButtonMappingKey(event.key)

                if hasattr(event, "joy"):
                    input_device = devices[event.joy]

                    if axis and abs(event.value) > InputMapper.AXIS_MIN:
                        positive = event.value > 0
                        sign = (int(positive) * 2) - 1      # -1 for False, 1 for True

                        if InputMapper.AXIS_NEUTRAL:
                            InputMapper.AXIS_NEUTRAL = False
                            return InputMapper.ButtonMappingAxis(
                                event.axis, input_device, sign)

                    if button:
                        return InputMapper.ButtonMappingButton(
                            event.button, input_device)

                    if hat:
                        x, y = event.value
                        if x != 0 and y == 0:
                            axis = 0
                            value = event.value[0]
                        elif y != 0 and x == 0:
                            axis = 1
                            value = event.value[1]
                        elif x != 0 and y != 0:
                            axis = -1
                            value = event.value
                        else:
                            break

                        return InputMapper.ButtonMappingHat(
                            event.hat, input_device, value, axis)

    @staticmethod
    def get_axis():
        devices = InputMapper.INPUT_DEVICES
        if len(devices) == 0:
            raise IOError("No input devices connected")
        sticks = [device.get_numaxes() > 0 for device in devices]
        if not any(sticks):
            raise IOError("No axes detected for connected devices")

        while True:
            InputMapper.check_axes()

            for event in pygame.event.get():
                if event.type == pygame.JOYAXISMOTION and abs(event.value) > InputMapper.AXIS_MIN:

                    positive = event.value > 0
                    if positive:
                        sign = 1
                    else:
                        sign = -1
                    id_num = event.axis
                    input_device = InputMapper.INPUT_DEVICES[event.joy]

                    if InputMapper.AXIS_NEUTRAL:
                        InputMapper.AXIS_NEUTRAL = False
                        return InputMapper.AxisMapping(
                            id_num, input_device, sign)


class InputManager:
    def __init__(self, *profile_names):
        self.controller_profiles = OrderedDict()
        self.load_profiles(profile_names)

    @property
    def profile_names(self):
        return list(self.controller_profiles.keys())

    def get_controllers(self):
        controllers = []
        for name in self.controller_profiles:
            try:
                controllers.append(
                    self.make_controller(name))
            except IndexError:
                print(name + " failed to load")

        return controllers

    def make_controller(self, profile_name):
        profile = self.controller_profiles[profile_name]

        return ZsController(profile_name, profile)

    def load_profiles(self, names):
        for name in names:
            path = join(CONTROLLER_PROFILES, name + ".cpf")
            interp = Profile.make_profile

            file = open(path, "r")
            profile = interp(json.load(file))
            file.close()

            profile.devices = [interp(d) for d in profile.devices]

            self.controller_profiles[name] = profile


class ZsInputDevice:
    def __init__(self, name, controller):
        self.name = name
        self.default = None
        self.controller = controller

    def get_frames(self):
        return self.controller.get_frames(self.name)

    def get_value(self):
        if self.get_frames():
            return self.get_frames()[-1]

        else:
            return self.default

    def update(self):
        pass


class Button(ZsInputDevice):
    def __init__(self, *args):
        super(Button, self).__init__(*args)

        self.init_delay = INIT_DELAY
        self.held_delay = HELD_DELAY
        self.held = 0
        self.default = 0

    @property
    def ignore(self):
        ignore = False
        h, i_delay, h_delay = (self.held,
                               self.init_delay,
                               self.held_delay)

        if 1 < h < i_delay:
            ignore = True
        elif h >= i_delay:
            if (h - i_delay) % h_delay != 0:
                ignore = True

        return ignore

    def negative_edge(self):
        frames = self.get_frames()
        current, last = frames[-1], frames[-2]

        return last and not current

    def check(self):
        return self.held and not self.ignore

    @staticmethod
    def get_input(mapping):
        return int(mapping.is_pressed())

    def update(self):
        if self.get_value():
            self.held += 1
        else:
            self.held = 0


class Dpad(ZsInputDevice):
    FIRST = 0

    def __init__(self, *args):
        super(Dpad, self).__init__(*args)
        if not Dpad.FIRST:
            Dpad.FIRST = id(self)

        def get_d(d):
            return self.controller.devices[self.name + "_" + d]
        self.last_direction = (1, 0)
        self.default = (0, 0)
        self.buttons = (get_d("up"),
                        get_d("down"),
                        get_d("left"),
                        get_d("right"))

    def get_direction(self):
        return self.get_value()

    def get_dominant(self):
        u, d, l, r = self.buttons

        return sorted([u, d, l, r], key=lambda b: b.held * -1)[0]

    def check(self):
        return self.get_dominant().check()

    def update(self):
        if self.get_value():
            x, y = self.get_value()
            if (x, y) in (UP, DOWN, LEFT, RIGHT):
                if self.last_direction != (x, y):
                    if id(self) == Dpad.FIRST:
                        print(x, y)
                self.last_direction = x, y

    @staticmethod
    def get_input(mappings):
        u, d, l, r = [m.is_pressed() for m in mappings]

        x, y = 0, 0
        x -= int(l)
        x += int(r)
        y += int(d)
        y -= int(u)

        return x, y


class ThumbStick(ZsInputDevice):
    def __init__(self, *args, dead_zone=STICK_DEAD_ZONE):
        super(ThumbStick, self).__init__(*args)
        self.dead_zone = dead_zone
        self.default = (0, 0)

    @property
    def x_axis(self):
        return self.get_value()[0]

    @property
    def y_axis(self):
        return self.get_value()[1]

    def get_direction(self):
        return self.get_value()

    def get_magnitude(self):
        x, y = self.x_axis, self.y_axis
        x **= 2
        y **= 2
        m = round(sqrt(x + y), 3)

        return m

    def is_neutral(self):
        return self.get_magnitude() < self.dead_zone

    def check(self):
        return not self.is_neutral()

    @staticmethod
    def get_input(mappings):
        x, y = [m.get_value() for m in mappings]

        return x, y


class Trigger(ZsInputDevice):
    def __init__(self, *args):
        super(Trigger, self).__init__(*args)

        self.button = self.controller.devices[self.name + "_button"]
        self.default = 0

    @property
    def get_displacement(self):
        return self.get_value()

    def check(self):
        return self.button.check()

    @staticmethod
    def get_input(mapping):
        return mapping.get_value()


class ZsController:
    Button, Dpad, ThumbStick, Trigger = Button, Dpad, ThumbStick, Trigger

    def __init__(self, name, profile):
        self.name = name
        self.frames = CacheList(FRAME_SLICE_SIZE)
        self.commands = []

        self.devices = {}
        self.mapping_dict = {}
        self.profile = profile
        self.get_devices(profile)

    def get_devices(self, profile):
        for device in profile.devices:
            if device:
                cls = device.type

                {
                    "Button": self.add_button,
                    "Dpad": self.add_dpad,
                    "ThumbStick": self.add_thumbstick,
                    "Trigger": self.add_trigger
                }[cls](device)

    def add_button(self, device):
            m = device.mapping.make_object(
                self.get_button_mapping)
            self.add_device(
                Button(device.name, self), m)

    def add_dpad(self, device):
            name = device.name
            mappings = []
            for direction in ("up", "down", "left", "right"):
                button_name = name + "_" + direction

                m = device.get(direction).get("mapping").make_object(
                    self.get_button_mapping)
                mappings.append(m)

                self.add_device(
                    Button(button_name, self), m)
            self.add_device(Dpad(name, self), mappings)

    def add_thumbstick(self, device):
        f = self.get_axis_mapping
        m = (device.x_axis.make_object(f),
             device.y_axis.make_object(f))
        self.add_device(
            ThumbStick(device.name, self), m)

    def add_trigger(self, device):
        name = device.name
        self.add_device(
            Button(name + "_button", self),
            device.mapping.make_object(
                self.get_button_mapping))

        m = device.axis.make_object(
            self.get_axis_mapping)
        self.add_device(
            Trigger(name, self), m)

    def add_device(self, device, mappings):
        self.mapping_dict[device.name] = mappings
        self.devices[device.name] = device

    def get_frames(self, device_name):
        output = []
        i = list(self.devices.keys()).index(device_name)

        for frame in self.frames:
            output.append(frame[i])

        return output

    def update(self):
        self.update_frames()
        for device in self.devices.values():
            device.update()

        for command in self.commands:
            device_frames = [self.get_frames(n) for n in command.devices]
            frames = list(zip(*device_frames))
            command.update(frames[-1])

        if self.commands:
            if self.commands[0].active and self.devices["dpad"].last_direction == (1, 0):
                print(" fuck")

    def update_frames(self):
        frame = []

        for device in self.devices.values():
            m = self.mapping_dict[device.name]

            frame.append(device.get_input(m))
        self.frames.append(frame)

    def save_profile(self):
        cpf = self.profile.get_json_dict()
        path = join(CONTROLLER_PROFILES, self.name + ".cpf")
        file = open(path, "w")

        json.dump(cpf, file, indent=2)
        print(json.dumps(cpf, indent=2))
        file.close()

    @staticmethod
    def get_button_mapping(profile):
        id_num = profile.map_id
        m_type = profile.map_type

        m = None
        if m_type == "key":
            m = InputMapper.ButtonMappingKey(id_num)

        else:
            joy_device = InputMapper.INPUT_DEVICES[profile.joy_id]
            assert joy_device.get_name() == profile.joy_name

            if m_type == "button":
                m = InputMapper.ButtonMappingButton(
                    id_num, joy_device)

            if m_type == "axis":
                m = InputMapper.ButtonMappingAxis(
                    id_num, joy_device, profile.sign)

            if m_type == "hat":
                m = InputMapper.ButtonMappingHat(
                    id_num, joy_device, profile.position, profile.axis)

        return m

    @staticmethod
    def get_axis_mapping(profile):
        id_num = profile.map_id
        sign = profile.sign
        joy_device = InputMapper.INPUT_DEVICES[profile.joy_id]
        assert joy_device.get_name() == profile.joy_name

        return InputMapper.AxisMapping(id_num, joy_device, sign)


class Command:
    def __init__(self, name, steps, device_names, frame_window=0):
        self.name = name
        self.steps = steps
        if not frame_window:
            frame_window = sum([step.frame_window for step in steps])
        self.frame_window = frame_window
        self.frames = CacheList(frame_window)
        self.devices = device_names
        self.active = False

    def check(self):
        frames = self.frames
        l = len(frames)
        i = 0
        for step in self.steps:
            sub_slice = frames[i:l]
            j = step.check(sub_slice)
            step.last = j
            i += j
            if j == 0:
                return False

        return True

    def update(self, frame):
        self.frames.append(frame)
        c = self.check()
        self.active = c

        if c:
            self.frames.clear()

    def __repr__(self):
        return self.name


class Step:
    # condition: device_name, check_func
    # check_func: function(frame) => Bool

    def __init__(self, description, conditions, frame_window=1):
        self.description = description
        self.conditions = conditions
        self.frame_window = frame_window
        self.last = 0

    def get_matrix(self, frames):
        frame_matrix = []
        conditions = self.conditions

        for con in conditions:
            check = con
            row = [check(frame) for frame in frames]
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


