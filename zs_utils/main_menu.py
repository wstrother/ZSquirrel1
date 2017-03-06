from os import listdir

from zs_constants.paths import CONFIG
from zs_src.layers.context import PauseMenuLayer
from zs_src.layers.menus import Menu


class MainMenu(Menu):
    def __init__(self):
        super(MainMenu, self).__init__("Main Menu")
        self.add_event_methods("load_menu")

    def on_spawn(self):
        tools = self.tools
        mb = tools.make_main_block()

        files = listdir(CONFIG)
        for file in [f for f in files if f[-4:] == ".cfg"]:
            name = " ".join(w.capitalize() for w in file[:-4].replace("_", " ").split())
            option = tools.TextOption(name)
            mb.add_member_sprite(option)

            load_menu = ("load_menu",
                         ("env_name", name),
                         ("file_name", file))
            option.set_event_listener("activate", load_menu, self)

        self.add_main_block(mb)

        super(MainMenu, self).on_spawn()

    def on_load_menu(self):
        name = self.event.env_name
        file_name = self.event.file_name

        env = PauseMenuLayer(name, file_name)
        self.handle_event(("change_environment",
                           ("environment", env)))
