from types import FunctionType, MethodType

from zs_constants.gui import A, START
from zs_src.entities import Layer

GFX, SFX = ".gif", ".txt"


class ContextManager:
    def __init__(self, environment):
        self.environment = environment
        self.model = environment.model
        self.set_value = environment.set_value
        self.get_value = environment.get_value

        self.set_up_model()

    def set_up_model(self):
        self.set_value(
            "frame_advance", False)
        self.set_value(
            "frame_advance_pause", False)
        self.set_value(
            "spawn", self.spawn_sprite)
        self.set_value(
            "sprite_dict", self.set_up_sprite_dict())
        self.set_value(
            "dt", 0)
        self.set_value(
            "layer_dict", self.set_up_layer_dict())
        self.set_value(
            "command_dict", self.set_up_command_dict())
        self.set_value(
            "set_sprite_controller", self.set_sprite_controller
        )

        self.model.link_object(
            self.environment, "game_paused",
            lambda env: env.paused)

    @property
    def layer_dict(self):
        return self.get_value("layer_dict")

    def get_layer(self, name):
        return self.layer_dict[name]["layer"]

    @property
    def sprite_dict(self):
        return self.get_value("sprite_dict")

    def link_interface(self, *items):
        for item in items:
            model = self.environment.model
            if "_" + item.name not in model.values:
                self.environment.set_value(
                    "_" + item.name, item.interface
                )

            for value_name in item.interface:
                value = item.interface[value_name]

                if type(value) not in (FunctionType, MethodType):
                    set_method = getattr(item, "set_" + value_name)

                    model.link_sub_value("_" + item.name, value_name,
                                         set_method)

    def set_up_layer_dict(self):
        pass

    def set_up_collisions(self, *args):
        layer = args[0]
        collision_systems = args[1:]
        for system in collision_systems:
            layer.collision_systems.append(system)

    def set_up_huds(self, *args):
        layer = args[0]
        huds = args[1:]

    def set_up_camera(self, *args):
        layer = args[0]
        rules = args[1:]

    def set_up_regions(self, *args):
        layer = args[0]
        groups = args[1:]
        layer.groups = groups

    def set_up_bg_layers(self, *args):
        layer = args[0]
        bg_layers = args[1:]
        for bg_layer in bg_layers:
            layer.add_bg_layer(bg_layer)

    def load_layer(self, name):
        env = self.environment
        ld = self.layer_dict[name]
        layer = ld["layer"]

        if name == "Pause Menu":
            self.set_value("pause_menu", layer)
        else:
            if ld.get("parent_layer"):
                parent = self.get_layer(
                    ld.get("parent_layer")
                )
                parent.add_sub_layer(layer)
            else:
                env.add_sub_layer(
                    layer)

        if ld.get("groups"):
            layer.groups = list(ld.get("groups"))

        if ld.get("pause"):
            self.model.link_value(
                "game_paused",
                lambda b: layer.set_active(not b)
            )

        if ld.get("frame_advance"):
            self.model.link_value(
                "frame_advance_pause",
                lambda b: layer.set_active(not b)
            )

        if hasattr(layer, "interface"):
            self.link_interface(layer)

        if ld.get("controllers"):
            layer.copy_controllers(
                env.controllers
            )

        setup = {
            "collisions": self.set_up_collisions,
            "huds": self.set_up_huds,
            "camera": self.set_up_camera,
            "bg_layers": self.set_up_bg_layers,
            "regions": self.set_up_regions,
        }

        for key in setup:
            args = ld.get(key)
            if args:
                setup[key](layer)

    def set_up_sprite_dict(self):
        pass

    def spawn_sprite(self, name, **kwargs):
        sd = self.sprite_dict[name]
        load = sd["load"]
        group = sd["group"]

        sprite = load(**kwargs)
        sprite.add(group)

        if hasattr(sprite, "interface"):
            self.link_interface(sprite)

        if sd.get("graphics"):
            self.set_graphics(sprite)

        if sd.get("controller"):
            self.set_sprite_controller(sprite)

        return sprite

    def set_graphics(self, sprite):
        sprite_dict = self.environment.get_value("sprite_dict")
        name = sprite.name
        sd = sprite_dict[name]

        animation_machine = sd["animation_machine"]
        stream_file = sd["graphics"]
        if "sprite_sheet" in sd:
            sprite_sheet = sd["sprite_sheet"]
        else:
            sprite_sheet = stream_file

        sprite.set_up_animations(
            sprite_sheet + GFX,
            stream_file + SFX,
            animation_machine)

    def set_sprite_controller(self, sprite):
        name = sprite.name
        sd = self.sprite_dict[name]

        if "controller" in sd:
            n = sd["controller"]
            layer = self.get_layer(sd["layer"])
            controller = layer.controllers[n]

            sprite.set_controller(controller)

    def set_up_command_dict(self):
        pass


class ContextLayer(Layer):
    def __init__(self, name, context, **kwargs):
        self.main_group = self.make_group()
        super(ContextLayer, self).__init__(name, **kwargs)
        self.context = context(self)

    def reset_controllers(self):
        for sprite in self.main_group:
            self.get_value("set_sprite_controller")(
                sprite)

    def handle_controller(self):
        if self.controller.check_command("double tap up"):
            if not self.paused:
                self.set_value("frame_advance", False)

        devices = self.controller.devices
        start = devices[START]
        a = devices[A]

        frame_advance = self.get_value("frame_advance")
        pause_menu = self.get_value("pause_menu")
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

        super(ContextLayer, self).handle_controller()

    def on_spawn(self):
        for c in self.controllers:
            commands = self.get_value("command_dict")
            c.commands = commands

        super(ContextLayer, self).on_spawn()

        for name in self.context.layer_dict:
            self.context.load_layer(name)

        self.reset_controllers()

    def on_pause(self):
        layer = self.get_value("pause_menu")
        layer.copy_controllers(
            self.controllers
        )
        super(ContextLayer, self).on_pause()


class RegionLayer(Layer):
    @staticmethod
    def get_walls(group):
        walls = []

        for region in group:
            walls += region.walls

        return walls

    def get_collision_system(self, items, group, check_collision, handle_collision):
        def collision_system():
            for item in items:
                for wall in self.get_walls(group):
                    if check_collision(item, wall):
                        handle_collision(item, wall)

        return collision_system

    def get_collision_system_list(self, items, check_collision, handle_collision):
        systems = []

        for group in self.groups:
            systems.append(self.get_collision_system(
                items, group, check_collision, handle_collision
            ))

        return systems
