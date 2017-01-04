from os import listdir
from os.path import join

from update_constants import update_constants
from zs_constants.paths import CONFIG, CONTROLLER_TEMPLATES, CONTROLLER_PROFILES
from zs_src.controller import InputMapper, ZsController
from zs_src.menus import Menu
from zs_src.profiles import Profile

CPF, CTP = ".cpf", ".ctp"


def print_dic(d, t=0):
    lead = "\t" * t
    for key in d:
        if not type(d[key]) is dict:
            print(lead + key + ": " + str(d[key]))
        else:
            print_dic(d[key], t + 1)


class ControllerMenu(Menu):
    def __init__(self, **kwargs):
        super(ControllerMenu, self).__init__("controller menu", **kwargs)
        get_ext = lambda x: x[-4:]
        get_file_name = lambda x: x[:-4]

        file_names = listdir(CONTROLLER_TEMPLATES)
        templates = []
        for n in file_names:
            if get_ext(n) == CTP:
                templates.append(get_file_name(n))
        self.set_value("templates", templates)

        file_names = listdir(CONTROLLER_PROFILES)
        profiles = []
        for n in file_names:
            if get_ext(n) == CPF:
                profiles.append(get_file_name(n))
        self.set_value("profiles", profiles)

        path = join(CONFIG, "zs.cfg")
        file = open(path, "r")
        lines = [line for line in file]
        file.close()
        for line in lines:
            line = line.split()
            if line:
                if line[0] == "CONTROLLERS":
                    value = " ".join(line[2:])
                    value = "".join([c for c in value if c not in "\"\'(),"])
                    value = value.split()
                    self.set_value("controllers", value)

        self.add_event_methods("load_edit_template_menu",
                               "load_make_profile_menu",
                               "update_template_box",
                               "update_config_block",
                               "save_config")

    def populate(self):
        tools = self.tools
        mb = tools.make_main_block(table_style="column")

        template_option = mb.add_option(
            "Edit controller template")
        profile_option = mb.add_option(
            "Make controller profile")
        config_option = mb.add_option(
            "Edit controller config")
        save_option = mb.add_option(
            "Save controller config")
        tools.set_activation_event(
            save_option, "save_config", self)

        x, y = (300, 0)

        # edit templates
        template_block = tools.make_sub_block(
            "template block", mb, template_option,
            position=(x, y), table_style="column")

        #       Make new template
        nt = template_block.add_option("Make new template")
        tools.prompt_for_value_on_activate(
            nt, "Template name:", 40, "new_template")

        def add_template(value):
            templates = self.get_value("templates")
            templates.append(value)

            return templates

        tools.link_value_to_value("new_template", "templates", add_template)

        #       Edit template
        et = template_block.add_option("Edit template")
        edit_template_block = tools.make_sub_block(
            "edit_template block", template_block, et,
            position=(x + 220, 0))

        def option_func(text):
            event = ("load_edit_template_menu",
                     ("template", text))

            option = tools.make_text_option(
                text, event, self)

            return option

        tools.link_value_to_member_column(
            edit_template_block, "templates",
            function=option_func)

        template_box = tools.make_sub_box(
            edit_template_block, position=(0, 200))
        response = ("update_template_box",
                    ("block", template_box))
        edit_template_block.set_event_listener(
            "change_option", response,
            self)

        # make profile
        profile_block = tools.make_sub_block(
            "profile block", mb, profile_option,
            position=(x, y))
        profile_block.add_sub_sprite(template_box, self)

        def profile_option(value):
            option = tools.TextOption(value)
            load_menu = ("load_make_profile_menu",
                         ("template", value))
            tools.show_input_dialog_on_activate(
                option, "Profile name:", 40,
                load_menu, self)

            return option

        tools.link_value_to_member_column(
            profile_block, "templates",
            function=profile_option)
        profile_block.set_event_listener(
            "change_option", response,
            self)

        # edit config
        config_block = tools.make_sub_block(
            "config block", mb, config_option,
            position=(x, y))

        controllers_box = tools.make_sub_box(
            config_block, position=(500, 0))

        response = (("update_config_block",
                     ("block", config_block),
                     ("sub_box", controllers_box)))
        controllers_box.set_event_listener(
            "change_linked_value", response,
            self)

        tools.link_value_to_member_column(
            controllers_box, "controllers",
            function=tools.TextSprite)

    def on_load_edit_template_menu(self):
        menu = EditTemplateMenu(self.event.template)
        change_env = ("change_environment",
                      ("environment", menu))
        self.handle_event(change_env)

    def on_load_make_profile_menu(self):
        profile = self.get_value("dialog")
        template = self.event.template

        env = MakeProfileMenu(profile, template)
        change_env = ("change_environment",
                      ("environment", env))
        self.handle_event(change_env)

    def on_update_template_box(self):
        template = self.event.trigger.option.text
        block = self.event.block

        try:
            path = join(CONTROLLER_TEMPLATES, template + CTP)
            file = open(path, "r")
            text = [line[:-1] for line in file]
            file.close()
        except IOError:
            text = ""

        ts = self.tools.TextSprite
        block.clear_members()
        block.add_member_sprite(
            ts(template, style_dict={
                "fonts": {"main": "dev_title"}}))
        block.add_member_sprite(ts(text))

    def on_update_config_block(self):
        block = self.event.block
        block.clear_members()
        tools = self.tools
        to = tools.TextOption

        clear = to("clear profiles")
        block.add_member_sprite(clear)
        clear_controllers = (
            "set_value_to",
            ("value_name", "controllers"),
            ("value", []))
        tools.set_activation_event(
            clear, clear_controllers,
            self.model)

        profiles = self.get_value("profiles")
        controllers = self.get_value("controllers")
        choices = [c for c in profiles if c not in controllers]
        for choice in choices:
            option = to(choice)
            block.add_member_sprite(option)
            add_profile = (
                "append_value",
                ("value_name", "controllers"),
                ("item", choice))
            tools.set_activation_event(
                option, add_profile,
                self.model)

        if block is self.active_block:
            block.pointer = [0, 0]
            block.active_option.handle_event("select")

    def on_save_config(self):
        controllers = self.get_value("controllers")
        if not controllers:
            return

        output = []
        for c in controllers:
            output.append("\"{}\"".format(c))
        if len(output) == 1:
            output = output[0] + ","
        else:
            output = ", ".join(output)

        path = join(CONFIG, "zs.cfg")
        file = open(path, "r")
        lines = []
        for line in file:
            if line.split() and line.split()[0] == "CONTROLLERS":
                new_line = "CONTROLLERS{:10}= {}\n".format(" ", output)
                lines.append(new_line)
                print(new_line)
            else:
                lines.append(line)
        file.close()

        file = open(path, "w")
        for line in lines:
            file.write(line)
        file.close()
        update_constants()


class EditTemplateMenu(Menu):
    def __init__(self, template, **kwargs):
        super(EditTemplateMenu, self).__init__("edit template menu", **kwargs)
        self.template = template

        path = join(CONTROLLER_TEMPLATES, template + CTP)
        devices = []

        try:
            file = open(path, "r")
            for line in file:
                if line[0] == "*":
                    optional = True
                    line = line[1:]
                else:
                    optional = False

                cls, name = line.split()

                device = optional, cls, name
                devices.append(device)
            file.close()
        except FileNotFoundError:
            pass
        self.set_value("devices", devices)

        self.add_event_methods("save_device",
                               "delete_device",
                               "update_main_block",
                               "save_template")

    def populate(self):
        tools = self.tools
        mb = tools.make_main_block()

        def dev_option(device):
            o, cls, name = device
            text = "{} {}".format(cls, name)
            if o:
                text = "* " + text

            option = tools.make_text_option(text)
            device_block = self.get_device_block(device)
            tools.show_dialog_on_activate(
                option, device_block)

            return option

        mb.set_event_listener(
            "change_linked_value", "update_main_block", self)
        tools.link_value_to_member_column(
            mb, "devices", function=dev_option)

    def get_device_block(self, device):
        optional, cls, name = device
        names = [d[2] for d in self.get_value("devices")]
        try:
            i = names.index(name)
        except ValueError:
            i = len(names)

        tools = self.tools
        block = tools.OptionBlock(
            name + " device block", table_style="grid",
            position=(300, 0))
        rows = []

        name_option = tools.TextFieldOption(
            name, 40)
        rows.append([name_option])

        cls_names = ["Button", "Dpad", "ThumbStick", "Trigger"]
        cls_switch = tools.SwitchOption(cls_names)
        cls_switch.set_switch(cls)
        rows.append([cls_switch])

        o_check_box = tools.CheckBox("optional")
        if optional:
            o_check_box.handle_event("activate")
        rows.append([o_check_box,
                     tools.TextSprite("Optional")])

        save = tools.TextOption("Save device")
        rows.append([save])
        save_device = ("save_device",
                       ("block", block),
                       ("index", i))
        tools.set_activation_event(
            save, save_device, self)
        tools.set_activation_event(
            save, "return", block)

        delete = tools.TextOption("Delete device")
        rows.append([delete])
        delete_device = ("delete_device",
                         ("index", i))
        tools.set_activation_event(
            delete, delete_device, self)
        tools.set_activation_event(
            delete, "return", block)

        for row in rows:
            block.add_member_row(row)

        return block

    def on_update_main_block(self):
        mb = self.main_block
        tools = self.tools
        add = mb.add_option("Add device")
        device = (False, "Button", "name")
        tools.show_dialog_on_activate(
            add, self.get_device_block(device))

        save = mb.add_option("Save template")
        tools.set_activation_event(
            save, "save_template", self)

    def on_save_device(self):
        block = self.event.block
        i = self.event.index

        optional = block.members[2][0].active
        name = block.members[0][0].text
        cls = block.members[1][0].text

        device = optional, cls, name
        self.model.handle_event(
            ("set_value_at_index",
             ("value_name", "devices"),
             ("index", i),
             ("item", device)))

    def on_delete_device(self):
        i = self.event.index

        devices = self.get_value("devices")
        try:
            devices.pop(i)
        except IndexError:
            pass
        self.set_value("devices", devices)

    def on_save_template(self):
        file_name = self.template + CTP
        path = join(CONTROLLER_TEMPLATES, file_name)

        lines = []
        for device in self.get_value("devices"):
            o, cls, name = device
            line = ""
            if o:
                line += "*"
            line += "{} {}\n".format(cls, name)
            lines.append(line)
            print(line)

        file = open(path, "w")
        for line in lines:
            file.write(line)
        file.close()

        self.tools.show_dialog(
            "Template {} saved to\n{}".format(
                self.template, path))


class MakeProfileMenu(Menu):
    def __init__(self, profile_name, template, **kwargs):
        super(MakeProfileMenu, self).__init__("make profile menu", **kwargs)
        self.profile_name = profile_name
        self.template = template

        path = join(CONTROLLER_TEMPLATES, template + CTP)
        devices = []

        file = open(path, "r")
        for line in file:
            if line[0] == "*":
                optional = True
                line = line[1:]
            else:
                optional = False

            cls, name = line.split()

            device = optional, cls, name
            devices.append(device)
        file.close()
        self.set_value("template_devices", devices)

        self.set_value("d_mappings", [None, None, None, None])
        self.set_value("axes", [None, None])

        i = len(devices)
        self.set_value("profile_devices", [None] * i)

        self.mapping_block = self.tools.FunctionBlock(
            "mapping block", InputMapper.get_mapping,
            position=self.tools.DIALOG_POSITION)
        self.axis_block = self.tools.FunctionBlock(
            "axis block", InputMapper.get_axis,
            position=self.tools.DIALOG_POSITION)

        self.add_event_methods("save_profile", "clear_mappings",
                               "add_mapping", "map_button",
                               "map_dpad", "map_thumbstick",
                               "map_trigger", "update_main_block")

    def populate(self):
        tools = self.tools
        mb = tools.make_main_block()
        names = [c[2] for c in self.get_value("template_devices")]

        sb = tools.make_sub_box(mb, position=(300, 0))

        def make_sprite(device):
            if device:
                name = device["name"]
            else:
                name = ""

            return tools.TextSprite(name + " set")
        tools.link_value_to_member_column(
            sb, "profile_devices", make_sprite)

        def dev_option(device):
            o, cls, name = device
            i = names.index(name)

            text = "{} {}".format(cls, name)
            if o:
                text = "* " + text

            option = tools.make_text_option(text)
            add_mapping = ("add_mapping",
                           ("device", device),
                           ("index", i))
            tools.set_activation_event(
                option, add_mapping, self)

            return option

        mb.set_event_listener(
            "change_linked_value", "update_main_block", self)
        tools.link_value_to_member_column(
            mb, "template_devices", function=dev_option)
        mb.set_event_listener(
            "change_linked_value", "update_main_block",
            self)

    def get_mapping_block(self, prompt, axis=False):
        mb, ab = self.mapping_block, self.axis_block
        if not axis:
            mb.change_text(prompt)
            return mb

        else:
            ab.change_text(prompt)
            return ab

    def show_mapper(self, map_event, prompt, axis=False):
        mapper = self.get_mapping_block(prompt, axis)
        show_dialog = ("show_dialog",
                       ("block", mapper),
                       ("response", map_event))
        self.queue_events(show_dialog)

    def on_add_mapping(self):
        device = self.event.device
        optional, cls, name = device
        get_map_event = lambda x: x + " device_name={} index={}".format(
            name, self.event.index)

        if cls == "Button":
            map_button = get_map_event("map_button")
            self.show_mapper(
                map_button, "Press {} button".format(name))

        if cls == "Dpad":
            map_dpad = get_map_event(
                "map_dpad direction=up")
            self.show_mapper(
                map_dpad, "Press Up:")

        if cls == "ThumbStick":
            map_thumbstick = get_map_event(
                "map_thumbstick direction=down")
            self.show_mapper(
                map_thumbstick, "Press Down:", True)

        if cls == "Trigger":
            map_trigger = get_map_event("map_trigger")
            self.show_mapper(
                map_trigger, "Press {} Trigger:".format(name),
                True)

    def add_profile_device(self, index, cls, name, *mappings):
        mappings = [m.get_profile() for m in mappings]

        device_profile = {"name": name,
                          "type": cls}

        if cls == "Button":
            device_profile["mapping"] = mappings[0]

        if cls == "Dpad":
            i = 0
            for d in ("up", "down", "left", "right"):
                button = {"name": "button_map",
                          "type": "Button",
                          "mapping": mappings[i]}
                device_profile[d] = button
                i += 1

        if cls == "ThumbStick":
            device_profile["x_axis"] = mappings[0]
            device_profile["y_axis"] = mappings[1]

        if cls == "Trigger":
            device_profile["axis"] = mappings[0]
            device_profile["button"] = mappings[0]

        self.set_value_at_index(
            "profile_devices", index,
            device_profile)

    def on_map_button(self):
        mapping = self.get_value("dialog")
        name = self.event.device_name
        i = self.event.index

        self.add_profile_device(
            i, "Button", name, mapping)

    def on_map_dpad(self):
        mapping = self.get_value("dialog")
        name = self.event.device_name
        i = self.event.index
        direction = self.event.direction

        map_dpad = lambda d: ("map_dpad",
                              ("direction", d),
                              ("device_name", name),
                              ("index", i))
        if direction == "up":
            self.set_value_at_index(
                "d_mappings", 0, mapping)
            self.show_mapper(
                map_dpad("down"), "Press Down:")

        if direction == "down":
            self.set_value_at_index(
                "d_mappings", 1, mapping)
            self.show_mapper(
                map_dpad("left"), "Press Left:")

        if direction == "left":
            self.set_value_at_index(
                "d_mappings", 2, mapping)
            self.show_mapper(
                map_dpad("right"), "Press Right:")

        if direction == "right":
            self.set_value_at_index(
                "d_mappings", 3, mapping)

            mappings = self.get_value("d_mappings")
            self.add_profile_device(
                i, "Dpad", name, *mappings)

    def on_map_thumbstick(self):
        mapping = self.get_value("dialog")
        name = self.event.device_name
        i = self.event.index
        direction = self.event.direction

        if type(mapping) is IOError:
            self.tools.show_dialog(
                str(mapping))
            return

        if direction == "down":
            map_stick = ("map_thumbstick",
                         ("direction", "right"),
                         ("device_name", name),
                         ("index", i))
            self.set_value_at_index(
                "axes", 0, mapping)
            self.show_mapper(
                map_stick, "Press Right:",
                True)

        if direction == "right":
            self.set_value_at_index(
                "axes", 1, mapping)

            mappings = self.get_value("axes")
            self.add_profile_device(
                i, "ThumbStick", name, *mappings)

    def on_map_trigger(self):
        mapping = self.get_value("dialog")
        name = self.event.device_name
        i = self.event.index

        self.add_profile_device(
            i, "Trigger", name, mapping)

    def on_update_main_block(self):
        mb = self.main_block
        tools = self.tools

        save = mb.add_option("Save profile")
        dialog = tools.make_dialog_box(
            "Save profile?", ("Yes", "No"))
        c = lambda e: e.trigger.text == "Yes"
        tools.show_dialog_on_activate(
            save, dialog, "save_profile",
            self, conditionals=[c])

        clear = mb.add_option("Clear mappings")
        tools.set_activation_event(
            clear, "clear_mappings", self)

    def on_save_profile(self):
        devices = self.get_value("profile_devices")
        d = {
            "name": self.profile_name,
            "devices": [d for d in devices if d]}
        controller = ZsController(d["name"],
                                  Profile.make_profile(d))

        try:
            if not devices:
                raise AssertionError

            for d in devices:
                i = devices.index(d)
                optional = self.get_value(
                    "template_devices")[i][0]

                if not optional:
                    assert d

        except AssertionError:
            self.tools.show_dialog(
                "Not all required devices are mapped.")
            return

        controller.save_profile()

        path = join(CONTROLLER_PROFILES,
                    self.profile_name + ".cpf")
        self.tools.show_dialog(
            "Profile {} saved to \n{}".format(
                self.profile_name, path))

    def on_clear_mappings(self):
        devices = self.get_value("profile_devices")
        for d in devices:
            i = devices.index(d)
            devices[i] = None

        self.set_value("profile_devices", devices)

