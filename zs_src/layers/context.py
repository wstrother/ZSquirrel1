from zs_constants.gui import START, A
from zs_src.context_manager import ContextManager
from zs_src.entities import Layer


class ContextLayer(Layer):
    def __init__(self, name, file_name, **kwargs):
        super(ContextLayer, self).__init__(name, **kwargs)
        self.context = None
        self.file_name = file_name

    def get_group(self, key):
        return self.context.groups_dict[key]

    def get_layer(self, key):
        return self.context.layers_dict[key]["layer"]

    def update(self):
        super(ContextLayer, self).update()

        self.context.handle_collisions()

    def set_up_model(self):
        self.set_value(
            "frame_advance", False)
        self.set_value(
            "frame_advance_pause", False)
        self.set_value(
            "dt", 0)
        self.set_value(
            "items_dict", self.context.items_dict)
        self.set_value(
            "layers_dict", self.context.layers_dict)

        self.model.link_object(
            self, "game_paused",
            lambda e: e.paused)

        if "Camera Layer" in self.context.layers_dict:
            self.set_value(
                "Camera", self.get_layer(
                    "Camera Layer").camera)

    def on_spawn(self):
        self.context = ContextManager(self)

        self.context.set_up_commands()
        for name in self.context.layers_dict:
            self.context.load_layer(name)

        self.set_up_model()

        self.context.populate()
        self.context.set_up_camera()
        self.context.set_up_huds()
        self.context.reset_controllers()
        super(ContextLayer, self).on_spawn()

    def on_pause(self):
        layer = self.get_layer("Pause Menu")
        layer.copy_controllers(
            self.controllers
        )
        super(ContextLayer, self).on_pause()


class PauseMenuLayer(ContextLayer):
    def handle_controller(self):
        if self.controller.check_command("double tap up"):
            if not self.paused:
                self.set_value("frame_advance", False)

        devices = self.controller.devices
        start = devices[START]
        a = devices[A]

        frame_advance = self.get_value("frame_advance")
        pause_menu = self.get_layer("Pause Menu")
        pause_ok = not self.paused and not frame_advance and pause_menu

        if start.check() and pause_ok:
            self.queue_events(
                ("pause", ("layer", pause_menu))
            )

        if frame_advance:
            if start.held:
                if a.check():
                    frame_pause = False
                else:
                    frame_pause = True
            else:
                frame_pause = False
            self.set_value("frame_advance_pause",
                           frame_pause)

        super(PauseMenuLayer, self).handle_controller()

