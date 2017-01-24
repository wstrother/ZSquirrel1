from types import FunctionType, MethodType

from zs_constants.zs import SCREEN_SIZE, FRAME_RATE
from zs_src.classes import CacheList
from zs_src.events import Event
from zs_src.gui import ContainerSprite, TextSprite
from zs_src.menus import Menu, HeadsUpDisplay
from zs_src.menus_gui import TextFieldOption, SwitchOption, TextOption


class DebugUtils(Menu):
    def __init__(self, **kwargs):
        super(DebugUtils, self).__init__("debug menu", **kwargs)
        self.add_event_methods("load_model_editor")

    def populate(self):
        tools = self.tools

        mb = tools.make_main_block()
        mb.add_member_sprite(
            tools.make_text_option(
                "Load model editor",
                "load_model_editor", self)
        )

    def on_load_model_editor(self):
        d = {
            "0": 0,
            "1": 1,
            "2": 2,
            "3": 3
        }
        env = ListEditor("Model editor", model=d)

        change = ("pause",
                  ("layer", env))
        self.handle_event(change)


class EditorInterface:
    def __init__(self, model, value_name, index=None):
        self.model = model
        self.value_name = value_name
        self.index = index

    @staticmethod
    def get_text(value):
        return str(value)

    def get_value(self):
        pass

    def set_value(self):
        value = self.get_value()
        self.model.set_value(self.value_name, value)


class StringEditor(EditorInterface, TextFieldOption):
    def __init__(self, model, value_name, index=None, **kwargs):
        value = model.values[value_name]
        TextFieldOption.__init__(self, str(value), 50, **kwargs)
        EditorInterface.__init__(self, model, value_name, index)
        self.index = index

    def get_value(self):
        return self.text

    def change_text(self, text):
        super(StringEditor, self).change_text(text)

        self.set_value()


class NumberEditor(StringEditor):
    def __init__(self, model, value_name, index=None):
        self.string_to_number = Event.string_to_number
        super(NumberEditor, self).__init__(model, value_name, index)

    def get_value(self):
        return self.string_to_number(self.text)

    def change_text(self, text):
        num = self.string_to_number(text)

        if type(num) in (int, float) and " " not in text:
            super(NumberEditor, self).change_text(text)

        if text == "-":
            self.text = "-"

        if text == "":
            self.text = ""


class BoolEditor(EditorInterface, SwitchOption):
    def __init__(self, model, value_name, index=None, **kwargs):
        SwitchOption.__init__(self, ["True", "False"], **kwargs)
        EditorInterface.__init__(self, model, value_name, index)

        value = model.values[value_name]
        self.switch.set_state(str(value))

    def get_value(self):
        return self.text == "True"

    def on_change_switch(self):
        self.set_value()


class ObjectEditor(EditorInterface, TextOption):
    def __init__(self, model, value_name, index=None, **kwargs):
        value = model.values[value_name]
        text = self.get_text(value)
        TextOption.__init__(self, text, **kwargs)
        EditorInterface.__init__(self, model, value_name, index)

    @staticmethod
    def get_text(value):
        text = str(value)
        if len(text) > 25:
            text = text[:22] + "..."

        return text


class DictEditor(Menu):
    def __init__(self, name, **kwargs):
        self.menu_color = kwargs.pop("color", None)
        super(DictEditor, self).__init__(name, **kwargs)

        self.add_event_methods("load_sub_editor", "update_model")

    def populate(self):
        tools = self.tools
        mb = tools.make_main_block()

        tools.link_value_to_member_column(
            mb, "_value_names",
            self.get_value_option,
            update=self.get_main_block_update
        )

        tools.set_auto_sub_block_trigger(
            "change_linked_value", mb,
            self.get_value_sub_block,

        )

        mb.handle_event("change_linked_value")

    def get_value_option(self, value_name):
        value = self.get_value(value_name)
        tools = self.tools

        o = tools.TextOption(value_name)

        if type(value) in (MethodType, FunctionType):
            tools.set_function_call_on_activation(
                o, value)

        if type(value) in (dict, list, tuple):
            o = self.get_load_editor_option(value_name)

        return o

    def get_main_block_update(self):
        return []

    def get_value_sub_block(self, option):
        tools = self.tools
        value_name = option.text
        if value_name[:5] == "Edit ":
            value_name = value_name[5:]
        print("SUB BLOCK ", value_name)
        value = self.get_value(value_name)

        if not value:
            return None

        if type(value) in (MethodType, FunctionType):
            return None

        x, y = option.position
        x += self.main_block.size[0]
        sb = tools.OptionBlock(
            value_name + " sub block",
            position=(x, y))

        o = self.get_value_editor(value_name)
        sb.add_member_sprite(o)
        if type(value) not in (int, float, str):
            o.selectable = False

        return sb

    def get_load_editor_option(self, value_name):
        value = self.get_value(value_name)
        tools = self.tools
        text = "Edit {}".format(value_name)

        o = None
        if type(value) is dict:
            o = tools.make_text_option(
                text,
                ("load_sub_editor",
                 ("value_name", value_name),
                 ("cls", type(value)),
                 ("model", value)),
                self)

        if type(value) in (tuple, list):
            l = dict(zip(
                [str(x) for x in range(len(value))],
                value)
            )
            o = tools.make_text_option(
                text,
                ("load_sub_editor",
                 ("value_name", value_name),
                 ("cls", type(value)),
                 ("model", l)),
                self)

        return o

    def get_value_editor(self, value_name):
        model = self.model
        value = model.values[value_name]
        i = model.value_names.index(value_name)

        if type(value) is str:
            o = StringEditor(model, value_name, i)

        elif type(value) in (int, float):
            o = NumberEditor(model, value_name, i)

        elif type(value) is bool:
            o = BoolEditor(model, value_name, i)

        else:
            o = ObjectEditor(model, value_name, i)

        return o

    def on_load_sub_editor(self):
        name = self.event.value_name
        value = self.get_value(name)
        t = type(value)

        cls = {
            dict: DictEditor,
            list: ListEditor,
            tuple: ListEditor
        }[t]

        if t is dict:
            model = value
        else:
            model = dict(zip([str(x) for x in range(len(value))], value))

        x, y = self.main_block.position
        x += self.main_block.size[0]
        y += 20

        layer = cls(name, model=model,
                    position=(x, y))
        self.queue_events(("pause",
                           ("layer", layer)))

        update_event = ("update_model",
                        ("value_name", name))
        self.set_event_listener(
            "unpause", update_event,
            self, temp=True
        )

    def on_die(self):
        super(DictEditor, self).on_die()
        d = self.format_model()
        self.set_value("_return", d)

    def format_model(self):
        d = {}
        for name in self.model.value_names:
            d[name] = self.get_value(name)

        return d

    def on_update_model(self):
        name = self.event.value_name
        t = type(self.get_value(name))

        if t in (dict, list):
            d = self.get_return_value()
        elif t is tuple:
            d = tuple(self.get_return_value())
        else:
            raise ValueError

        self.set_value(name, d)
        self.main_block.handle_event("change_linked_value")

    # def on_update_dict(self):
    #     d = self.get_return_value()
    #     value_name = self.event.value_name
    #     self.set_value(value_name, d)
    #     self.main_block.handle_event("change_linked_value")
    #
    # def on_update_list(self):
    #     l = self.get_return_value()
    #     value_name = self.event.value_name
    #     self.set_value(value_name, l)
    #     self.main_block.handle_event("change_linked_value")
    #
    # def on_update_tuple(self):
    #     t = tuple(self.get_return_value())
    #     value_name = self.event.value_name
    #     self.set_value(value_name, t)
    #     self.main_block.handle_event("change_linked_value")


class ListEditor(DictEditor):
    def __init__(self, name, **kwargs):
        super(ListEditor, self).__init__(name, **kwargs)

        self.add_event_methods("swap_item", "update_sub_blocks")

    def format_model(self):
        names = self.model.value_names

        return [self.get_value(n) for n in names]

    def populate(self):
        tools = self.tools
        mb = tools.make_main_block()

        def get_list_option(value_name):
            o = self.get_value_editor(value_name)
            o.set_event_conditional(
                "activate", "not active",
                "update_sub_blocks", self
            )

            return o

        tools.link_value_to_member_column(
            mb, "_value_names",
            get_list_option
        )

        x, y = mb.position
        x += mb.size[0]

        tools.set_auto_sub_block_trigger(
            "change_linked_value", mb,
            self.get_value_sub_block
        )

        def get_b_item(s):
            ao = s.main_block.active_option
            if ao.child:
                if ao.child is self.active_block:
                    o = ao.child.active_option
                    swap = "swap {} with ".format(ao.text)
                    cutoff = len(swap)
                    text = o.text[cutoff:]

                    return text
                else:
                    return ""
            else:
                return ""

        a_item = tools.make_reporter_sprite(
            self, lambda s: s.main_block.active_option.text
        )
        a_item.style = {
            "fonts": {"main": "dev_title"},
            "colors": {
                "text": a_item.style.colors["selected"]}
        }

        b_item = tools.make_reporter_sprite(
            self, get_b_item
        )
        tools.make_sub_box(
            mb, [a_item, b_item], position=(x, y)
        )

        mb.handle_event("change_linked_value")

    def get_value_sub_block(self, option):
        tools = self.tools
        value_name = option.index

        x, y = option.position
        x += self.main_block.size[0] + 20
        y += 20
        sb = tools.OptionBlock(
            str(value_name) + " sub block",
            position=(x, y))

        def get_swap(index):
            return ("swap_item",
                    ("a_index", option.index),
                    ("b_index", index))

        for j in range(len(self.model.value_names)):
            if not j == option.index:
                j_text = str(self.get_value_at_index(j))
                if len(j_text) > 25:
                    j_text = j_text[:22] + "..."

                swap = tools.make_text_option(
                    "Swap {} with {}".format(
                        option.text, j_text),
                    get_swap(j), self)

                sb.add_member_sprite(swap)
                swap.set_event_listener(
                    "activate", "die", sb, temp=True)
        return sb

    def on_swap_item(self):
        i, j = self.event.a_index, \
               self.event.b_index

        a = self.get_value(str(i))
        b = self.get_value(str(j))
        self.set_value(str(i), b)
        self.set_value(str(j), a)

        self.model.handle_change("_value_names")
        self.handle_event(
            ("change_active_block",
             ("block", self.main_block))
        )

    def on_update_sub_blocks(self):
        self.main_block.handle_event("change_linked_value")
        self.main_block.active_option.handle_event(
            ("select",
             ("no_sound", True))
        )


class PauseMenu(Menu):
    def __init__(self, environment, **kwargs):
        super(PauseMenu, self).__init__("Pause Menu", **kwargs)
        self.environment = environment
        self.model = environment.model

        self.active = False

        self.add_event_methods(
            "load_sub_editor", "update_model")

    def handle_controller(self):
        super(PauseMenu, self).handle_controller()

        if self.get_state() == "alive":
            start = self.controller.devices["start"].held == 1

            if start:
                pause_layer = self.pause_layer

                def live_key(l):
                    if l.main_block.active_option.child:
                        o = l.main_block.active_option.child.active_option

                        return isinstance(o, self.tools.TextFieldOption)

                if self.paused:
                    target = pause_layer
                else:
                    target = self
                if not live_key(target):
                    target.handle_event("die")

                # if self.paused:
                #     if not pause_layer.control_freeze:
                #         pause_layer.handle_event("die")
                # else:
                #     if not self.control_freeze:
                #         self.handle_event("die")

    def populate(self):
        tools = self.tools

        mb = tools.make_main_block(position=(200, 200),
                                   size=(300, 0))

        def in_model(name):
            return name in self.model.values

        self.add_controller_option(mb)

        if in_model("frame_advance"):
            self.add_frame_advance_option(mb)

        if in_model("sprite_dict"):
            self.add_sprite_options(mb)

        if in_model("layer_dict"):
            ld = self.get_value("layer_dict")
            layers = [l["layer"] for l in ld.values()]
            interface_layers = [
                l for l in layers if hasattr(l, "interface")
            ]

            self.add_layer_options(mb, interface_layers)

        self.add_exit_option(mb)

    def add_frame_advance_option(self, mb):
        tools = self.tools

        frame_option = tools.TextOption(
            "Frame Advance mode"
        )

        def frame_advance():
            self.set_value("frame_advance", True)
            tools.show_dialog(
                "Frame Advance active \n Double Tap Up to toggle",
                response="die")

        tools.set_function_call_on_activation(
            frame_option, frame_advance)
        mb.add_member_sprite(frame_option)

    def add_sprite_options(self, mb):
        tools = self.tools
        spawn_option = tools.TextOption(
            "Spawn Sprite"
        )
        mb.add_member_sprite(spawn_option)

        self.add_sub_block(
            mb, self.get_spawn_sub_block(),
            spawn_option)

        sprite_option = tools.TextOption(
            "Sprite Options")
        mb.add_member_sprite(sprite_option)

        self.add_sub_block(
            mb, self.get_sprite_dict_block(),
            sprite_option)

    def add_controller_option(self, mb):
        tools = self.tools

        controller_option = tools.TextOption(
            "Change Controller")
        mb.add_member_sprite(controller_option)
        self.add_sub_block(
            mb, self.get_controller_sub_block(),
            controller_option)

    def add_layer_options(self, mb, layers):
        tools = self.tools

        for layer in layers:
            text = "Edit {}".format(
                layer.name)

            layer_option = tools.make_text_option(
                text, ("load_sub_editor",
                       ("value_name", "_" + layer.name)),
                self)
            mb.add_member_sprite(layer_option)

    def add_exit_option(self, mb):
        tools = self.tools

        text = "Exit {}".format(
            self.environment.name)

        leave = tools.make_text_option(
            text, "die", self.environment
        )
        mb.add_member_sprite(leave)

    def get_controller_sub_block(self):
        tools = self.tools
        x, y = self.main_block.position
        x += self.main_block.size[0]

        block = tools.OptionBlock(
            "controller sub block",
            position=(x, y))

        controller_option = tools.SwitchOption(
            [c.name for c in self.controllers]
        )
        block.add_member_sprite(controller_option)

        def change_function():
            sets = (self.environment.controllers,
                    self.environment.sprite_layer.controllers)
            for controllers in sets:
                name = controller_option.text
                i = [c.name for c in controllers].index
                s = i(name)

                a, b = controllers[0], controllers[s]
                controllers[0] = b
                controllers[s] = a
            self.environment.reset_controllers()

        change_option = tools.TextOption("select")
        tools.set_function_call_on_activation(
            change_option, change_function
        )
        block.add_member_sprite(change_option)

        return block

    def get_spawn_sub_block(self):
        sprite_dict = self.get_value("sprite_dict")
        tools = self.tools
        x, y = self.main_block.position
        x += self.main_block.size[0]
        to, fo = tools.TextOption, tools.TextFieldOption

        sprite_option = tools.SwitchOption(
            list(sprite_dict.keys()))

        x_option = fo("0", 4)
        y_option = fo("0", 4)

        def spawn():
            name = sprite_option.text
            load = self.get_value("spawn")
            sx, sy = int(x_option.text), int(y_option.text)

            load(name, position=(sx, sy))

        spawn_option = to(
            "Spawn Sprite")
        tools.set_function_call_on_activation(
            spawn_option, spawn)

        members = [
            [sprite_option],
            [x_option],
            [y_option],
            [spawn_option]
        ]
        block = tools.OptionBlock(
            "spawn sprite block", members,
            position=(x, y), table_style="grid")

        return block

    def get_sprite_dict_block(self):
        sprite_dict = self.get_value("sprite_dict")
        tools = self.tools
        x, y = self.main_block.position
        x += self.main_block.size[0]

        block = tools.OptionBlock(
            "sprite dict block", position=(x, y))
        for name in sprite_dict:
            value_name = "_" + name
            if self.get_value(value_name):
                o = tools.make_text_option(
                    name, ("load_sub_editor",
                           ("value_name", value_name)),
                    self)
                block.add_member_sprite(o)

        return block

    def on_load_sub_editor(self):
        name = self.event.value_name
        d = self.get_value(name)

        x, y = self.main_block.position
        x += self.main_block.size[0]
        y += 20

        layer = DictEditor(
            name.replace("_", ""),
            model=d, position=(x, y)
        )
        load = ("pause", ("layer", layer))
        self.queue_events(load)

        update_event = ("update_model",
                        ("value_name", name))
        self.set_event_listener(
            "unpause", update_event,
            self, temp=True)

    def on_update_model(self):
        value_name = self.event.value_name
        d = self.get_return_value()
        self.set_value(value_name, d)


class DebugLayer(HeadsUpDisplay):
    ANIMATION_MACHINE_MAX = 5

    def __init__(self, environment, **kwargs):
        super(DebugLayer, self).__init__("Debug Layer", **kwargs)
        self.environment = environment
        self.model = environment.model
        self.visible = False

        def toggle_visible():
            self.visible = not self.visible

        self.interface = {
            "Toggle debug layer": toggle_visible,
        }

        w, h = SCREEN_SIZE
        w -= 50

        if (w / h) > (4 / 3):
            cutoff = 4
        else:
            cutoff = 3

        block = self.tools.ContainerSprite(
            "physics reporter box",
            size=(w, 0), table_style="cutoff {}".format(cutoff),
            position=(25, 0)
        )
        block.add(self.hud_group)
        block.visible = False
        self.hud_table = block

    @staticmethod
    def get_frame_rate_hud(dt):
        rates = AverageCache(int(FRAME_RATE * dt))
        times = AverageCache(int(FRAME_RATE * dt))

        def get_text(d):
            time = d["dt"]
            rate = 1 / time
            times.append(time)
            rates.append(rate)

            rate_text = "   {:2.3f}".format(rates.average())
            dt_text = "dt {:2.3f} s".format(times.average())
            text = rate_text + "\n" + dt_text

            return text

        return get_text

    @staticmethod
    def get_animation_machine_hud(dt, maximum=None):
        if not maximum:
            maximum = DebugLayer.ANIMATION_MACHINE_MAX

        states = ChangeCache(int(FRAME_RATE * dt))

        def get_text(a):
            state = a.get_state().name
            states.append(state)

            return states.changes()[-maximum:]

        return get_text

    @staticmethod
    def get_physics_interface_hud():
        def get_text(p):
            velocity = p.velocity.get_value()
            accel = p.acceleration.get_value()
            position = p.position
            ground = p.is_grounded()

            f_str = "({:3.1f}, {:3.1f})"
            l_str = "{:>15}: {:^17}"

            text = [
                l_str.format("Acceleration: ", f_str.format(*accel)),
                l_str.format("Velocity: ", f_str.format(*velocity)),
                l_str.format("Position: ", f_str.format(*position)),
                "{:^32}".format("Grounded: {}".format(ground))
            ]

            return text

        return get_text

    @staticmethod
    def get_camera_hud():
        def get_text(cl):
            c = cl.camera

            l_str = "{:>13}: {:^17}"
            f_str = "({:3.1f}, {:3.1f})"

            text = [
                l_str.format("Focus point", f_str.format(*c.focus_point)),
                l_str.format("Anchor values", f_str.format(*c.anchor)),
                l_str.format("Position", f_str.format(*c.position)),
                l_str.format("Offset", f_str.format(*c.get_offset()))
            ]

            return text

        return get_text

    def add_hud_box(self, name, huds, interval=5):
        self.hud_table.add_member_sprite(
            HudBox(name, huds, interval)
        )

    def update(self, dt):
        self.model.set_value("dt", dt)
        super(DebugLayer, self).update(dt)


class HudBox(ContainerSprite):
    def __init__(self, name, huds, interval=5, **kwargs):
        kwargs.update({"align_h": "c"})
        super(HudBox, self).__init__(
            name + " HUD", title=name,
            **kwargs)

        self.interval = interval
        self.set_up_huds(huds)

    def set_up_huds(self, huds):
        # hud: (value_name, [average/changes], dt, maximum

        for hud in huds:
            self.add_text_field(hud)

    def add_text_field(self, hud):
        text_field = HudTextSprite(hud)
        self.add_timer(
            "HUD update frequency", self.interval,
            on_switch_off=text_field.set_text,
            temp=False)

        self.add_member_sprite(text_field)


class HudTextSprite(TextSprite):
    L_STR = "{:>20}: {:^20}"
    T_STR = "({:3.1f}, {:3.1f})"
    F_STR = "{:3.1f}"

    def __init__(self, hud, **kwargs):
        super(HudTextSprite, self).__init__("", **kwargs)

        self.cache = None
        self.func = self.get_func(hud)

    def get_func(self, hud):
        value_name = hud[0]
        func = hud[1]
        lhs = value_name

        print(value_name)
        if len(hud) == 2:
            def get_text():
                value = func()

                return self.get_f_text(
                    lhs, value)

        else:
            if hud[2] == "average":
                self.cache = AverageCache(hud[3])

                def get_text():
                    value = func()
                    self.cache.append(value)

                    return self.get_f_text(
                        lhs, self.cache[-1])

            # if hud[2] == "changes":
            else:
                self.cache = ChangeCache(hud[3])

                def get_text():
                    value = func()
                    self.cache.append(value)

                    return self.cache.changes(hud[4])

        return get_text

    def update(self, dt):
        super(HudTextSprite, self).update(dt)

    def set_text(self):
        self.change_text(self.func())

    def get_f_text(self, lhs, value):
        print(lhs)
        if type(value) is tuple:
            rhs = self.T_STR.format(*value)

        elif type(value) is float:
            rhs = self.F_STR.format(value)

        else:
            rhs = str(value)

        return self.L_STR.format(
            lhs, rhs)


class AverageCache(CacheList):
    def average(self):
        if not self:
            return []

        if type(self[0]) in (int, float):
            return sum(self) / len(self)

        else:
            lhs = [i[0] for i in self]
            rhs = [i[1] for i in self]

            return (sum(lhs) / len(lhs)), (sum(rhs) / len(rhs))


class ChangeCache(CacheList):
    def changes(self, maximum):
        changes = []
        last = None
        for item in self:
            if item != last:
                last = item
                changes.append(item)

        if len(self) > maximum:
            return changes[-maximum:]

        else:
            return changes
