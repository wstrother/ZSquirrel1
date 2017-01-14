from os import listdir

from launch_environment import get_environment
from zs_constants.paths import ZS_UTILS
from zs_src.menus import Menu


class MainMenu(Menu):
    def __init__(self):
        super(MainMenu, self).__init__("main menu")
        self.add_event_methods("load_menu")

    def populate(self):
        tools = self.tools
        mb = tools.make_main_block()

        names = listdir(ZS_UTILS)
        for name in names:
            if name[-3:] == ".py" and name != "main_menu.py":
                o_name = name[:-3]
                try:
                    cls = get_environment(o_name)

                    option = tools.TextOption(o_name)
                    mb.add_member_sprite(option)

                    load_menu = ("load_menu",
                                 ("cls", cls))
                    option.set_event_listener("activate", load_menu, self)
                except AttributeError:
                    pass

        self.add_main_block(mb)

    def on_load_menu(self):
        cls = self.event.cls

        env = cls()
        self.handle_event(("change_environment",
                           ("environment", env)))
