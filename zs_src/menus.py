from zs_constants.zs import DIALOG_POSITION
from zs_src import menus_gui
from zs_src.entities import Layer
from zs_src.events import Event


class Menu(Layer):
    EVENT_NAMES = (
        "change_active_block", "show_sub_block", "hide_sub_block",
        "return", "show_dialog", "prompt_exit")

    def __init__(self, name, **kwargs):
        super(Menu, self).__init__(name, **kwargs)
        self.add_event_methods(*Menu.EVENT_NAMES)

        self.main_block = None
        self.active_block = None
        self.return_block = None

        self.model.values["dialog"] = ""
        self.tools = MenuTools(self)

    def get_update_methods(self):
        um = super(Menu, self).get_update_methods()

        um += [self.model.event_handler.update]

        return um

    def reset_spawn(self, trigger=None):
        super(Menu, self).reset_spawn(trigger)

        self.return_block = None
        self.set_menu_group()

        mb = self.main_block
        if mb:
            ao = mb.active_option
            select = (
                "select",
                ("option", ao),
                ("no_sound", True))
            if ao:
                ao.queue_events(select)

        self.queue_events(("show_sub_block",
                           ("block", mb)))

    def set_menu_group(self):
        self.groups = [self.make_group(True)]

    @property
    def menu_group(self):
        return self.groups[0]

    def add_block(self, block):
        for name in Menu.EVENT_NAMES:
            block.remove_event_listener(name)
            block.set_event_passer(name, self)

    def add_main_block(self, block):
        self.main_block = block
        self.add_block(block)
        self.active_block = self.main_block

    def add_sub_block(self, block, sub_block, option):
        self.add_block(sub_block)
        listeners = (("select", "show_sub_block"), ("deselect", "hide_sub_block"))
        for event, response in listeners:
            option.set_event_listener(event, (response, ("block", sub_block)), self)

        option.child = sub_block
        sub_block.parent = block

    def handle_controller(self):
        if self.active_block and self.active_block.get_state() == "alive":
            if self.controllers:
                self.active_block.handle_controller(self.controller)

    def on_change_active_block(self):
        block = self.event.get("block")
        current = self.active_block

        to_parent = self.event.get("to_parent", False)
        to_child = self.event.get("to_child", False)
        to_dialog = self.event.get("to_dialog", False)

        if to_dialog:
            self.return_block = current

        if to_child:
            deselect = ("deselect", ("no_hide", True))
            self.return_block = current
        else:
            deselect = "deselect"

        if not to_dialog:
            if hasattr(current, "active_option") and current.active_option:
                current.active_option.handle_event(deselect)

        if to_parent:
            if hasattr(current, "pointer"):
                current.pointer = current.pointer_origin
            select = ("select", ("no_show", True))
            self.return_block = block.parent
        else:
            select = "select"

        if self.event.get("trigger.name") == "return":
            select = ("select",
                      ("no_show", True),
                      ("no_sound", True))

        self.active_block = block
        if hasattr(block, "active_option"):
            if block.active_option:
                block.active_option.handle_event(select)
                set_option = ("change_option",
                              ("option", block.active_option))
                block.handle_event(set_option)

    def on_show_sub_block(self):
        show = not self.event.get("trigger.no_show", False)

        if show:
            block = self.event.block
            spawn = ("spawn",
                     ("group", self.menu_group))
            block.handle_event(spawn)

    def on_hide_sub_block(self):
        hide = not self.event.get("trigger.no_hide", False)

        if hide:
            block = self.event.block
            block.handle_event("die")

    def on_return(self):
        block = self.return_block

        if block:
            change_active_block = ("change_active_block",
                                   ("block", block),
                                   ("to_parent", True))
            self.handle_event(change_active_block)

        else:
            self.tools.show_dialog(
                "Leaving?", ("Yes", "No"),
                "prompt_exit")

    def on_show_dialog(self):
        block = self.event.block
        response = self.event.get("response")
        target = self.event.get("response_target", self)
        conditionals = self.event.get("conditionals")

        block.set_event_passer("return", self, temp=True)
        block.set_event_listener("return", "die", block, temp=True)

        conditional = "do_response"

        get_text = lambda e: e.get("trigger.text")
        change_dialog = ("change_value",
                         ("value_name", "dialog"),
                         ("get_value", get_text))
        block.set_event_conditional(
            "return", [conditional], change_dialog,
            self.model, temp=True)

        if response:
            if not conditionals:
                conditionals = ["trigger.do_response"]

            block.set_event_conditional(
                "die", conditionals, response=response,
                target=target, temp=True)

        show_sub_block = ("show_sub_block",
                          ("block", block))
        self.handle_event(show_sub_block)

        change_active_block = ("change_active_block",
                               ("block", block),
                               ("to_dialog", True))
        self.handle_event(change_active_block)

    def on_prompt_exit(self):
        if self.get_value("dialog") == "Yes":
            self.handle_event("die")


class MenuTools:
    DIALOG_POSITION = DIALOG_POSITION
    TextSprite = menus_gui.TextSprite
    TextOption = menus_gui.TextOption
    TextFieldOption = menus_gui.TextFieldOption
    SwitchOption = menus_gui.SwitchOption
    CheckBox = menus_gui.CheckBox
    SubBox = menus_gui.SubBox
    OptionBlock = menus_gui.OptionBlock
    DialogBlock = menus_gui.DialogBlock
    InputBlock = menus_gui.InputBlock
    FunctionBlock = menus_gui.FunctionBlock

    def __init__(self, menu):
        self.menu = menu
        self.model = menu.model

    def make_main_block(self, **kwargs):
        main_block = self.OptionBlock("main block", **kwargs)
        self.menu.add_main_block(main_block)

        return main_block

    def make_sub_block(self, name, block, option, **kwargs):
        sub_block = self.OptionBlock(name, **kwargs)
        self.menu.add_sub_block(block, sub_block, option)

        return sub_block

    def add_sub_box(self, block, members=None, **kwargs):
        name = block.name + " sub box"
        sub_box = self.SubBox(self.menu, name, members, **kwargs)

        block.add_sub_sprite(sub_box, self.menu)

        return sub_box

    def make_input_prompt(self, prompt, length, **kwargs):
        if "position" not in kwargs:
            kwargs["position"] = DIALOG_POSITION

        input_block = self.InputBlock(
            prompt, length, **kwargs)

        return input_block

    @staticmethod
    def make_dialog_box(text, options=None, **kwargs):
        if "position" not in kwargs:
            kwargs["position"] = DIALOG_POSITION

        message_box = MenuTools.DialogBlock(
            text, options,
            **kwargs)

        return message_box

    def make_text_option(self, text, activation_event=None,
                         target=None, **kwargs):
        option = self.TextOption(text, **kwargs)
        if activation_event:
            self.set_activation_event(
                option, activation_event, target)

        return option

    @staticmethod
    def set_activation_event(option, event, target):
        option.set_event_listener("activate", event, target)

    def show_dialog_on_activate(self, option, block, response=None,
                                target=None, conditionals=None):
        menu = self.menu
        show_block = ("show_dialog",
                      ("block", block),
                      ("response", response),
                      ("response_target", target),
                      ("conditionals", conditionals))
        option.set_event_listener(
            "activate", show_block, menu)
        # block.set_event_listener("return", "die")

    def show_input_dialog_on_activate(self, option, prompt, length, response,
                                      target, conditionals=None, **kwargs):
        block = self.make_input_prompt(
            prompt, length, **kwargs)

        self.show_dialog_on_activate(
            option, block, response,
            target, conditionals)

    def prompt_for_value_on_activate(self, option, prompt, length,
                                     value_name, **kwargs):
        block = self.make_input_prompt(prompt, length, **kwargs)

        def function(event):
            return block.text

        response = ("change_value",
                    ("value_name", value_name),
                    ("get_value", function))
        self.show_dialog_on_activate(option, block, response, self.model)

    def change_block_on_activate(self, option, block):
        menu = self.menu
        show_block = ("show_sub_block",
                      ("block", block))
        change_block = ("change_active_block",
                        ("block", block),
                        ("to_child", True))
        self.set_activation_event(
            option, show_block, menu)
        self.set_activation_event(
            option, change_block, menu)

        menu.add_block(block)

    def show_dialog(self, message, options=None, response=None,
                    conditionals=None, **kwargs):
        dialog = self.make_dialog_box(
            message, options, **kwargs)

        show_dialog = ("show_dialog",
                       ("block", dialog),
                       ("response", response),
                       ("conditionals", conditionals))
        self.menu.queue_events(show_dialog)

    @staticmethod
    def set_activation_events_for_block(block, function, target):
        for item in block.member_list:
            if item.selectable:
                event = function(item)
                MenuTools.set_activation_event(item, event, target)

    def link_option_block_to_value(self, block, value_name):
        model = self.model

        def get_function(event):
            return block.active_option.text

        change_value = ("change_value",
                        ("value_name", value_name),
                        ("get_value", get_function))

        if len(block.members) > 1:
            block.set_event_listener("change_option", change_value, model)
            model.set_value(value_name, block.active_option.text)
        model.handle_change(value_name)

    def link_value_to_sprite_members(self, sprite, value_name, function=None):
        model = self.model

        def change_method(value):
            sprite.clear_members()

            members = []
            for row in value:
                new_row = []
                for item in row:
                    if function:
                        item = function(item)
                    new_row.append(item)
                members.append(new_row)

            sprite.set_table(members)
            self.handle_change_linked_value(
                sprite, value_name, value)

        model.link_value(value_name, change_method)
        model.handle_change(value_name)

    def link_value_to_member_column(self, sprite, value_name, function=None):
        model = self.model

        def change_method(value):
            sprite.clear_members()
            members = []
            for item in value:
                if function:
                    item = function(item)
                    members.append(item)

                else:
                    members.append(item)

            sprite.set_table(members)
            self.handle_change_linked_value(
                sprite, value_name, value)

        model.link_value(value_name, change_method)
        model.handle_change(value_name)

    def link_value_to_sprite_text(self, sprite, value_name, function=None):
        model = self.model

        def change_method(value):
            if function:
                value = function(value)
            sprite.change_text(value)
            self.handle_change_linked_value(
                sprite, value_name, value)

        model.link_value(value_name, change_method)
        model.handle_change(value_name)

    def link_value_to_value(self, value_name, value_name2, method=None):
        model = self.model

        def change_func(value):
            if method:
                value = method(value)
            self.menu.set_value(value_name2, value)
            self.handle_change_linked_value(
                self.menu, value_name, value)

        model.link_value(value_name, change_func)

    @staticmethod
    def handle_change_linked_value(entity, value_name, value):
        change = ("change_linked_value",
                  ("value_name", value_name),
                  ("value", value))
        entity.handle_event(change)
