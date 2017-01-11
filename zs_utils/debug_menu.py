from types import FunctionType, MethodType

from zs_src.events import Event
from zs_src.menus import Menu
from zs_src.menus_gui import TextFieldOption, SwitchOption, TextOption


class DebugMenu(Menu):
    def __init__(self, **kwargs):
        super(DebugMenu, self).__init__("debug menu", **kwargs)
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
        env = DictEditor("Model editor")
        env.model = self.model

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
        super(DictEditor, self).__init__(name + " editor", **kwargs)

        self.add_event_methods("load_sub_editor", "update_dict",
                               "update_tuple", "update_list")

    def populate(self):
        tools = self.tools
        mb = tools.make_main_block()

        tools.link_value_to_member_column(
            mb, "_value_names",
            lambda n: tools.TextOption(n)
        )

        x, y = mb.position
        x += 200

        tools.set_auto_sub_block_trigger(
            "change_linked_value", mb,
            lambda o: self.get_value_sub_block(
                o, position=(x, y)
            )
        )
        mb.handle_event("change_linked_value")

    def get_value_sub_block(self, option, **kwargs):
        tools = self.tools
        value_name = option.text
        value = self.get_value(value_name)

        sb = tools.OptionBlock(
            value_name + " sub block",
            **kwargs)

        editor = self.get_load_editor_option(value_name)
        if editor:
            sb.add_member_sprite(editor)

        o = self.get_value_editor(value_name)
        sb.add_member_sprite(o)
        if type(value) not in (int, float, str):
            o.selectable = False

        return sb

    def get_load_editor_option(self, value_name):
        value = self.get_value(value_name)
        tools = self.tools

        o = None
        if type(value) is dict:
            o = tools.make_text_option(
                "Edit dict",
                ("load_sub_editor",
                 ("value_name", value_name),
                 ("cls", type(value)),
                 ("model", value)),
                self)

        if type(value) in (FunctionType, MethodType):
            o = tools.TextOption("Call function")
            tools.set_function_call_on_activation(
                o, value)

        if type(value) in (tuple, list):
            l = dict(zip(
                [str(x) for x in range(len(value))],
                value)
            )
            o = tools.make_text_option(
                "Edit " + type(value).__name__,
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
        cls = {
            dict: DictEditor,
            list: ListEditor,
            tuple: ListEditor
        }[self.event.cls]
        model = self.event.model

        x, y = self.position
        x += 120
        y += 100
        layer = cls(name, model=model,
                    position=(x, y))
        self.queue_events(("pause",
                           ("layer", layer)))

        update_event = "update_{}".format(
            self.event.cls.__name__)
        self.set_event_listener(
            "unpause", (update_event,
                        ("value_name", name)),
            self, temp=True
        )

    def on_load_dict_editor(self):
        name = self.event.value_name
        d = self.get_value(name)
        x, y = self.position
        x += 120
        y += 100

        env = DictEditor(name, model=d,
                         position=(x, y))
        self.set_event_listener(
            "unpause",
            ("update_dict",
             ("value_name", name)),
            self, temp=True
        )

        change = ("pause",
                  ("layer", env))
        self.handle_event(change)

    def on_load_list_editor(self):
        name = self.event.value_name
        l = self.get_value(name)
        keys = ["index_{}".format(x) for x in range(len(l))]
        d = dict(zip(keys, l))
        x, y = self.position
        x += 120
        y += 100

        env = ListEditor(name, model=d,
                         position=(x, y))
        self.set_event_listener(
            "unpause",
            ("update_list",
             ("value_name", name)),
            self, temp=True
        )

        change = ("pause",
                  ("layer", env))
        self.handle_event(change)

    def on_return(self):
        super(DictEditor, self).on_return()
        d = self.format_model()
        self.set_value("_return", d)

    def format_model(self):
        d = {}
        for name in self.model.value_names:
            d[name] = self.get_value(name)

        return d

    def on_update_dict(self):
        d = self.get_return_value()
        value_name = self.event.value_name
        self.set_value(value_name, d)
        self.main_block.handle_event("change_linked_value")

    def on_update_list(self):
        l = self.get_return_value()
        value_name = self.event.value_name
        self.set_value(value_name, l)
        self.main_block.handle_event("change_linked_value")

    def on_update_tuple(self):
        t = tuple(self.get_return_value())
        value_name = self.event.value_name
        self.set_value(value_name, t)
        self.main_block.handle_event("change_linked_value")


class ListEditor(DictEditor):
    def __init__(self, name, **kwargs):
        super(ListEditor, self).__init__(name + " list", **kwargs)

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
        x += 200

        tools.set_auto_sub_block_trigger(
            "change_linked_value", mb,
            lambda o: self.get_value_sub_block(
                o, position=(x, y + 150)
            )
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

    def get_value_sub_block(self, option, **kwargs):
        tools = self.tools
        value_name = option.index

        sb = tools.OptionBlock(
            str(value_name) + " sub block",
            **kwargs)

        o = self.get_load_editor_option(value_name)
        if o:
            sb.add_member_sprite(o)

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

