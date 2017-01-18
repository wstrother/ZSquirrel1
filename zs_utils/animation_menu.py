from os import listdir

from zs_constants.paths import ANIMATION_STREAMS
from zs_src.animations import StreamManager
from zs_src.menus import Menu
from zs_utils.debug_utils import DictEditor


class AnimationMenu(Menu):
    def __init__(self, **kwargs):
        super(AnimationMenu, self).__init__("animation menu", **kwargs)
        self.add_event_methods("load_sprite_menu")

    def populate(self):
        tools = self.tools
        to = tools.TextOption

        mb = tools.make_main_block()
        for name in listdir(ANIMATION_STREAMS):
            mb.add_member_sprite(to(name[:-4]))

        def get_activation_event(o):
            return ("load_sprite_menu",
                    ("stream_file", o.text))

        tools.set_activation_events_for_block(
            mb, get_activation_event, self
        )

    def on_load_sprite_menu(self):
        file_name = self.event.stream_file

        layer = SpriteSheetMenu(
            file_name + " menu", file_name,
            position=(25, 25))

        pause = ("pause", ("layer", layer))
        self.queue_events(pause)


class SpriteSheetMenu(Menu):
    def __init__(self, name, file_name, **kwargs):
        super(SpriteSheetMenu, self).__init__(name, **kwargs)
        self.file_name = file_name
        self._stream = StreamManager(file_name + ".txt")

        for name in self.stream_dict:
            stream = self.stream_dict[name]
            self.set_value(name, stream)

        self.add_event_methods("load_animation_editor")

    @property
    def stream_dict(self):
        return self._stream.stream_dict

    def populate(self):
        tools = self.tools

        mb = tools.make_main_block()
        tools.link_value_to_member_column(
            mb, "_value_names", tools.TextOption
        )

        def get_activation_event(o):
            section = self.get_value(o.text)
            return ("load_animation_editor",
                    ("section", section))

        tools.set_auto_activation_events_trigger(
            "change_linked_value", mb, get_activation_event,
            self
        )

    def on_load_animation_editor(self):
        section = self.event.section
        d = {
            "name": section.name,
            "stream": section.stream,
            "hitboxes": section.hitboxes
        }

        layer = AnimationEditor(
            section.name + " animation editor",
            model=d)
        pause = ("pause", ("layer", layer))
        self.queue_events(pause)


class AnimationEditor(DictEditor):
    pass

