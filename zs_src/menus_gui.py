from sys import exit

import pygame

from zs_constants.gui import LEFT_RIGHT, UP_DOWN_LEFT_RIGHT, ADVANCE, BACK, DPAD
from zs_src.classes import StateMeter
from zs_src.gui import TextSprite, ContainerSprite


class SelectableInterface:
    EVENT_NAMES = "select", "deselect", "activate", "return"

    def __init__(self):
        self.selectable = True
        self.active = False

        self.add_event_methods(*SelectableInterface.EVENT_NAMES)

    def toggle_active(self):
        if not self.active:
            self.active = True

        else:
            self.active = False

        e = self.event
        if e and e.name == "activate":
            e.set("active", self.active)

        return self.active

    def on_select(self):
        if not self.event.get("no_sound", False):
            self.play_sound("select")

    def on_deselect(self):
        pass

    def on_activate(self):
        if not self.event.get("no_sound", False):
            self.play_sound("activate")

    def on_return(self):
        if not self.event.get("no_sound", False):
            self.play_sound("activate")

    def handle_controller(self, controller):
        activate = any([controller.devices[name].check() for name in ADVANCE])

        if activate:
            self.queue_events("activate")


class MenuBlockInterface:
    EVENT_NAMES = "show_sub_block", "hide_sub_block", "change_active_block", "return"

    def __init__(self):
        self.add_event_methods(*MenuBlockInterface.EVENT_NAMES)
        self.return_command_names = ADVANCE + BACK

    def on_show_sub_block(self):
        pass

    def on_hide_sub_block(self):
        pass

    def on_change_active_block(self):
        pass

    def on_return(self):
        pass

    def handle_controller(self, controller):
        names = self.return_command_names
        b = any([controller.devices[name].check() for name in names])

        if b:
            self.handle_event("return")

        return b


# Option Sprites


class TextOption(SelectableInterface, TextSprite):
    def __init__(self, *args, **kwargs):
        TextSprite.__init__(self, *args, **kwargs)
        SelectableInterface.__init__(self)

    def on_select(self):
        color = self.style.colors["selected"]
        self.change_color("text", color)

        super(TextOption, self).on_select()

    def on_deselect(self):
        color = self.style.colors["unselected"]
        self.change_color("text", color)


class ChangeBlockOption(TextOption):
    def __init__(self, block, menu, *args, **kwargs):
        super(ChangeBlockOption, self).__init__(*args, **kwargs)
        show_block = ("show_sub_block",
                      ("block", block))
        change_block = ("change_active_block",
                        ("block", block),
                        ("to_child", True))
        self.set_event_listener("activate", show_block, menu)
        self.set_event_listener("activate", change_block, menu)

        menu.add_block(block)
        block.set_event_listener("return", "die")
        self.block = block


class SwitchOption(TextOption):
    def __init__(self, switches, **kwargs):
        super(SwitchOption, self).__init__(switches[0], **kwargs)
        self.switch = StateMeter("", switches)
        self.add_event_methods("change_switch")

    def on_activate(self):
        if self.toggle_active():
            self.turn_on_cycling()

        else:
            self.turn_off_cycling()

    def on_select(self):
        if not self.active:
            super(SwitchOption, self).on_select()

    def set_switch(self, state):
        self.switch.set_state(state)
        self.set_text_to_switch()

    def set_text_to_switch(self):
        if self.text != self.switch.state:
            self.handle_event("change_switch text=" + self.switch.state)
        self.change_text(self.switch.state)

    def turn_on_cycling(self):
        self.ui_directions = LEFT_RIGHT
        self.control_freeze = True

        color = self.style.colors["active"]
        self.change_color("text", color)

    def turn_off_cycling(self):
        self.ui_directions = []
        self.control_freeze = False

        color = self.style.colors["selected"]
        self.change_color("text", color)

    def handle_controller(self, controller):
        super(SwitchOption, self).handle_controller(controller)

        r_names = self.return_command_names
        b = any([controller.devices[name].check() for name in r_names])
        if b and self.active:
            self.handle_event("activate")

        dpad = controller.devices["dpad"]
        button = dpad.get_dominant()
        move = button.check() or button.held > button.init_delay
        x_direction = dpad.get_direction()[0]

        left = x_direction == -1
        right = x_direction == 1

        if move and self.active:
            if left:
                self.switch.prev()

            if right:
                self.switch.next()

            self.set_text_to_switch()

    def on_change_switch(self):
        pass


class MeterOption(SwitchOption):
    def __init__(self, span, offset=0, **kwargs):
        switches = []
        for x in range(span):
            switches.append(str(x + offset))
        super(MeterOption, self).__init__(switches, **kwargs)


class BoxOption(SelectableInterface, ContainerSprite):
    def __init__(self, *args, **kwargs):
        ContainerSprite.__init__(self, *args, **kwargs)
        SelectableInterface.__init__(self)
        self.bg_color = self.style.colors["bg"]

    def on_select(self):
        color = self.style.colors["selected"]
        self.change_color("bg", color)

    def on_deselect(self):
        color = self.bg_color
        self.change_color("bg", color)


class CheckBox(BoxOption):
    def __init__(self, name, **kwargs):
        super(CheckBox, self).__init__(name, [TextSprite(" ")], **kwargs)
        self.return_command_names = ""

    @property
    def text(self):
        if self.active:
            return "True"
        else:
            return "False"

    def on_activate(self):
        if self.toggle_active():
            self.members[0][0].change_text("X")

        else:
            self.members[0][0].change_text(" ")


class TextField(TextOption):
    def __init__(self, length, **kwargs):
        super(TextField, self).__init__("", **kwargs)
        self.input_length = length
        self.prompt = ""

    def on_spawn(self):
        super(TextField, self).on_spawn()
        self.change_text(self.prompt)

    def handle_controller(self, controller):
        waiting = True
        while waiting:

            event = pygame.event.poll()
            if event.type == pygame.KEYDOWN:
                key = event.key
                shift = key == pygame.K_RSHIFT or key == pygame.K_LSHIFT

                if key == pygame.K_RETURN:
                    waiting = False

                    return_input = ("return",
                                    ("text", self.text),
                                    ("do_response", True))
                    self.handle_event(return_input)

                elif not shift:
                    waiting = False

                    length = len(self.text)
                    keyboard_cutoff = 127

                    if key == pygame.K_BACKSPACE:
                        if length > 0:
                            if pygame.key.get_mods() & pygame.KMOD_CTRL:
                                last_word = self.text.split()[-1]
                                self.text = self.text.rpartition(last_word)[0]
                            else:
                                self.text = self.text[:-1]
                            self.reset_image()

                    elif key <= keyboard_cutoff and length < self.input_length:
                        letter = chr(key)

                        if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                            letter = str(letter).capitalize()
                            alt = "1234567890-=[];',./\\"
                            alt_shift = '!@#$%^&*()_+{}:"<>?|'

                            for i in range(len(alt)):
                                if alt[i] == letter:
                                    letter = alt_shift[i]

                        self.change_text(self.text + letter)
                        self.reset_image()

            elif event.type == pygame.QUIT:
                exit()


class TextFieldOption(TextField):
    def __init__(self, prompt, length, **kwargs):
        super(TextFieldOption, self).__init__(length, **kwargs)
        self.prompt = prompt
        self.set_event_listener("return", "activate")

    def on_activate(self):
        if self.toggle_active():
            color = self.style.colors["active"]
            self.control_freeze = True
        else:
            color = self.style.colors["selected"]
            self.control_freeze = False

        self.play_sound("activate")
        self.change_color("text", color)
        self.reset_image()

    def handle_controller(self, controller):
        if not self.active:
            SelectableInterface.handle_controller(self, controller)

        if self.active:
            super(TextFieldOption, self).handle_controller(controller)
            self.prompt = self.text


class PromptOption(TextOption):
    def __init__(self, text, input_block, menu, prompt=None, **kwargs):
        super(PromptOption, self).__init__(text, **kwargs)

        response_event = kwargs.get("response_event")
        response_target = kwargs.get("response_target")

        input_dialog = ("show_dialog",
                        ("block", input_block),
                        ("response_event", response_event),
                        ("response_target", response_target))
        self.set_event_listener("activate", input_dialog, menu)

        if not prompt:
            prompt = text
        change_prompt = ("change_prompt",
                         ("text", prompt))
        self.set_event_listener("activate", change_prompt, input_block)

        input_block.set_event_passer("return", self)

# Block sprites


class MenuBlock(MenuBlockInterface, ContainerSprite):
    def __init__(self, *args, **kwargs):
        ContainerSprite.__init__(self, *args, **kwargs)
        MenuBlockInterface.__init__(self)

    def add_sub_sprite(self, sprite, menu):
        for name in "show_sub_block", "hide_sub_block":
            if name not in sprite.event_handler.event_methods:
                sprite.add_event_methods(name)

        menu.set_event_passer("show_sub_block", sprite)
        menu.set_event_passer("hide_sub_block", sprite)
        self.sub_sprites.append(sprite)

    @staticmethod
    def make_sub_box(group, name, members, **kwargs):
        return SubBox(group, name, members, **kwargs)

    @staticmethod
    def make_entry_box(group, name, entries, **kwargs):
        return EntryBox(group, name, entries, **kwargs)


class SubBox(MenuBlockInterface, ContainerSprite):
    def __init__(self, menu, name, members, **kwargs):
        ContainerSprite.__init__(self, name, members, **kwargs)
        MenuBlockInterface.__init__(self)
        self.menu = menu
        self.add_event_methods("add_member", "clear_members")

    @property
    def menu_group(self):
        return self.menu.menu_group

    def change_text(self, text):
        member = self.members[0][0]
        if hasattr(member, "change_text"):
            member.change_text(text)

    def on_show_sub_block(self):
        block = self.event.block
        if self in block.sub_sprites:
            if not self.event.get("trigger.no_show", False):
                spawn = ("spawn",
                         ("group", self.menu_group))
                self.handle_event(spawn)

    def on_hide_sub_block(self):
        block = self.event.block
        if self in block.sub_sprites:
            if not self.event.get("trigger.no_hide", False):
                self.handle_event("die")

    def on_add_member(self):
        sprite = self.event.sprite
        args = self.event.get("args", [])
        self.add_member_sprite(sprite, *args)

    def on_clear_members(self):
        for sprite in self.member_list:
            sprite.kill()

        self.member_table.members = [[]]


class EntryBox(SubBox):
    def __init__(self, menu, name, entries, **kwargs):
        members = [TextSprite(entry) for entry in entries]
        kwargs.update({"table_style": "column"})
        super(EntryBox, self).__init__(menu, name, members, **kwargs)

    def on_add_member(self):
        entry = self.event.entry
        sprite = TextSprite(entry)
        self.add_member_sprite(sprite)


# Option blocks


class FunctionBlock(MenuBlock):
    def __init__(self, name, function, **kwargs):
        super(FunctionBlock, self).__init__(name, [TextSprite("")], **kwargs)
        self.function = function
        self.function_called = False
        self.return_command_names = ""

    def on_spawn(self):
        super(FunctionBlock, self).on_spawn()
        self.function_called = False

    def change_text(self, text):
        self.members[0][0].change_text(text)

    def update(self, dt):
        super(FunctionBlock, self).update(dt)
        if self.get_state() == "alive" and not self.function_called:
            output = self.function()
            self.function_called = True
            self.queue_events(("return",
                               ("text", output),
                               ("do_response", True)))


class InputBlock(MenuBlock):
    def __init__(self, text, length, **kwargs):
        prompt = TextSprite(text)
        field = TextField(length)
        super(InputBlock, self).__init__("input box", [prompt, field], **kwargs)

        field.set_event_passer("return", self)
        self.add_event_methods("change_prompt")
        self.return_command_names = ""

    @property
    def text(self):
        return self.members[1][0].text

    @property
    def prompt(self):
        return self.members[0][0].text

    def change_prompt(self, value):
        self.members[0][0].change_text(value)

    @property
    def active_option(self):
        return self.members[1][0]

    def handle_controller(self, controller):
        self.members[1][0].handle_controller(controller)

    def on_change_prompt(self):
        prompt = self.event.text
        self.change_prompt(prompt)


class OptionBlock(MenuBlock):
    def __init__(self, *args, **kwargs):
        super(OptionBlock, self).__init__(*args, **kwargs)

        self.pointer = [0, 0]
        self.pointer_origin = [0, 0]
        self.ui_directions = UP_DOWN_LEFT_RIGHT
        self.return_command_names = BACK

        self.add_event_methods("change_option")

    def on_spawn(self):
        super(OptionBlock, self).on_spawn()

        self.pointer = self.pointer_origin
        ao = self.active_option
        if ao:
            self.queue_events(("change_option",
                               ("option", ao)))

    @property
    def options(self):
        return self.members

    @property
    def active_option(self):
        i, j = self.pointer
        try:
            ao = self.options[i][j]
        except IndexError:
            ao = None
        return ao

    def add_option(self, text, *args):
        option = TextOption(text)
        self.add_member_sprite(option, *args)

        return option

    def remove_member_sprite(self, sprite):
        super(OptionBlock, self).remove_member_sprite(sprite)
        self.pointer = self.pointer_origin
        if self.active_option:
            self.active_option.handle_event("select")

    def remove_member_row(self, index):
        super(OptionBlock, self).remove_member_row(index)
        self.pointer = self.pointer_origin
        if self.active_option:
            self.active_option.handle_event("select")

    def handle_controller(self, controller):
        parent = self.parent
        ao = self.active_option
        if ao:
            if hasattr(ao, "handle_controller"):
                ao.handle_controller(controller)

            if not ao.control_freeze:
                if super(OptionBlock, self).handle_controller(controller):
                    return

            devices = controller.devices
            dpad = devices[DPAD]
            direction = dpad.get_direction()
            move = dpad.check()

            child_selectable = False
            if ao.child:
                child_selectable = any([member.selectable for member in ao.child.member_list])
            origin = self.pointer == self.pointer_origin

            child_dir = ao.child and ao.child_direction == direction and child_selectable
            parent_dir = parent and self.parent_direction == direction and origin
            ignore = (direction in ao.ui_directions) or ao.control_freeze

            to_child = (
                "change_active_block",
                ("block", ao.child),
                ("to_child", True))
            to_parent = (
                "change_active_block",
                ("block", self.parent),
                ("to_parent", True))

            if move and not ignore:
                if child_dir:
                    self.handle_event(to_child)

                elif parent_dir:
                    self.handle_event(to_parent)

                else:
                    last = ao
                    self.cycle_pointer(direction)
                    current = self.active_option

                    if last != current:
                        deselect = (
                            "deselect",
                            ("option", last))
                        select = (
                            "select",
                            ("option", current))
                        change_option = (
                            "change_option",
                            ("option", current))

                        last.handle_event(deselect)
                        current.handle_event(select)
                        self.handle_event(change_option)
        else:
            super(OptionBlock, self).handle_controller(controller)

    def cycle_pointer(self, direction):
        x, y = direction
        i, j = self.pointer
        start = [i, j]

        cycling = True
        while cycling:
            if x != 0:
                j += x
                cells = len(self.options[i]) - 1

                if j > cells:
                    j = 0
                elif j < 0:
                    j = cells

            if y != 0:
                i += y
                rows = len(self.options) - 1

                if i > rows:
                    i = 0
                elif i < 0:
                    i = rows

            self.pointer = [i, j]
            try:
                cycling = not self.active_option.selectable
            except IndexError:
                cycling = True

            if self.pointer == start:
                cycling = False

    def on_change_option(self):
        pass


class DialogBlock(OptionBlock):
    def __init__(self, message, options=None, **kwargs):
        if options:
            options = [TextOption(option) for option in options]
            members = [[TextSprite(message)], options]

        else:
            members = [[TextSprite(message)]]

        kwargs.update({"table_style": "grid"})
        super(DialogBlock, self).__init__("dialog block", members, **kwargs)

        if options:
            for option in options:
                return_event = ("return",
                                ("do_response", True),
                                ("text", option.text))
                option.set_event_listener(
                    "activate", return_event, self)

        else:
            self.return_command_names = ADVANCE + BACK

        self.style = {"align_h": "c"}

    @property
    def options(self):
        if len(self.members) > 1:
            return self.members[1:]

        else:
            return [[None]]

    @property
    def text(self):
        return self.members[0][0].text

    def change_text(self, text):
        self.members[0][0].change_text(text)
