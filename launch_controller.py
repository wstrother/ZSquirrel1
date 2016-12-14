from sys import exit
from os.path import join
import json
import pygame

from zs_src.events import Event
from zs_src.controller import ZsController
from zs_constants.paths import CONTROLLER_PROFILES

pygame.joystick.init()


class InputMapper:
    AXIS_SET = False
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
            line = "('axis_mapping', ({}), ({}), ({}))".format(
                id_num, name, joy_id)

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
    def get_mapping():
        get_device = lambda x: InputMapper.INPUT_DEVICES[x]
        pygame.event.clear()
        while True:
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
                    input_device = get_device(event.joy)

                    if axis and abs(event.value) < .1:
                        InputMapper.AXIS_SET = False

                    if axis and abs(event.value) > .5:
                        positive = event.value > 0
                        if positive:
                            sign = 1
                        else:
                            sign = -1

                        if not InputMapper.AXIS_SET:
                            InputMapper.AXIS_SET = True
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
            for event in pygame.event.get():
                if event.type == pygame.JOYAXISMOTION and abs(event.value) > .1:
                    InputMapper.AXIS_SET = False

                if event.type == pygame.JOYAXISMOTION and abs(event.value) > .5:

                    positive = event.value > 0
                    if positive:
                        sign = 1
                    else:
                        sign = -1
                    id_num = event.axis
                    input_device = InputMapper.INPUT_DEVICES[event.joy]

                    if not InputMapper.AXIS_SET:
                        InputMapper.AXIS_SET = True
                        return InputMapper.AxisMapping(
                            id_num, input_device, sign)

#


def interpret_profile(profile):
    interp = Event.interpret

    p = interp(profile)
    for key in p.__dict__:
        value = p.__dict__[key]
        if type(value) == dict:
            p.set(key, interpret_profile(value))

    return p


def build_controller(*profiles):
    controller = ZsController("test_controller")

    for profile in profiles:
        cls = profile.name
        name = profile.device_name

        if cls == "Dpad":
            m_profiles = (
                profile.up.mapping,
                profile.down.mapping,
                profile.left.mapping,
                profile.right.mapping
            )
            mappings = []
            for mp in m_profiles:
                mappings.append(build_button_map(mp))
            controller.add_dpad(name, mappings)

        if cls == "Button":
            mapping = build_button_map(profile.mapping)
            controller.add_button(name, mapping)

        if cls == "Thumbstick":
            x_axis = profile.x_axis.mapping
            y_axis = profile.y_axis.mapping
            controller.add_thumbstick(name, (x_axis, y_axis))

        if cls == "Trigger":
            axis = profile.axis.mapping
            controller.add_trigger(name, axis)

    return controller


def build_button_map(profile):
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


def build_axis_map(profile):
    id_num = profile.map_id
    sign = profile.sign
    joy_device = InputMapper.INPUT_DEVICES[profile.joy_id]
    assert joy_device.get_name() == profile.joy_name

    return InputMapper.AxisMapping(id_num, joy_device, sign)


def get_controllers(profile_names):
    controllers = []

    for name in profile_names:
        path = join(CONTROLLER_PROFILES, name + ".cpf")

        file = open(path, "r")
        cpf = json.load(file)
        file.close()

        devices = []
        for device_name in cpf:
            devices.append(cpf[device_name])

        profiles = [interpret_profile(device) for device in devices]

        try:
            controller = build_controller(*profiles)
            controllers.append(controller)
        except (IndexError, AssertionError):
            print("{} failed to load".format(name))

    return controllers
