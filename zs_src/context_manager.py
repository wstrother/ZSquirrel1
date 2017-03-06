from collections import OrderedDict
from copy import deepcopy
from os.path import join
from types import FunctionType, MethodType

from zs_constants.paths import CONFIG
from zs_constants.sprite_demo import GRAVITY, COF
from zs_src.controller import Command, Step
from zs_src.events import Event
from zs_src.layers.camera import CameraLayer, ParallaxBgLayer
from zs_src.layers.physics import PhysicsLayer
from zs_src.layers.regions import RegionLayer
from zs_src.regions.platforms import TreePlat
from zs_src.sprites.sprites import DemoSprite
from zs_src.state_machines import SpriteDemoMachine
from zs_utils.debug_utils import DebugLayer, PauseMenu

GFX, SFX = ".gif", ".txt"


class ContextManager:
    def __init__(self, env):
        self.environment = env
        self.layers_dict = None
        self.bg_layers_dict = None
        self.command_dict = None
        self.items_dict = None
        self.collision_systems = None
        self.huds_dict = None
        self.camera_windows = None
        self.camera_dict = None
        self.populate_dict = None
        self.groups_dict = {}

        file = open(join(CONFIG, env.file_name), "r")
        lines = [line for line in file if line != "\n"]
        file.close()

        self.set_up_context(lines)

    def print_dicts(self):
        print("\nCONTEXT FOR {}".format(self.environment))
        dicts = {
            "Layers": self.layers_dict,
            "Sprites": self.sprite_dict,
            "Commands": self.command_dict,
            "Regions": self.items_dict,
            "Collisions": self.collision_systems,
            "Huds": self.huds_dict,
            "Groups": self.groups_dict
        }

        def print_dict(d, t=0):

            tab = "\t" * t

            for key in d:
                value = d[key]
                if type(value) is dict:
                    print(tab + key)
                    print_dict(value, t=t + 1)

                else:
                    print(tab + key + ":\t" + str(value))

        for name in dicts:
            print(name)
            if dicts[name]:
                print_dict(dicts[name], t=1)

            print("")

    def set_up_context(self, lines):
        name = ""
        section = []
        d = {}

        for line in lines:
            if line[-1] == "\n":
                line = line[:-1]

            if line[0] == "#":      # heading_name
                if name:
                    d[name] = section

                name = line[2:]
                section = []

            else:
                section.append(line)
        d[name] = section

        if d.get("layers"):
            self.layers_dict = self.set_up_dict(
                d["layers"])

        if d.get("bg_layers"):
            self.bg_layers_dict = self.set_up_dict(
                d["bg_layers"])

        if d.get("commands"):
            self.command_dict = self.set_up_command_dict(
                d["commands"])

        if d.get("items"):
            self.items_dict = self.set_up_dict(
                d["items"])

        if d.get("collision_systems"):
            self.collision_systems = self.set_up_dict(
                d["collision_systems"])

        if d.get("huds"):
            self.huds_dict = self.set_up_dict(
                d["huds"])

        if d.get("groups"):
            for group in d.get("groups"):
                self.groups_dict[group] = self.environment.Group()

        if d.get("camera_windows"):
            self.camera_windows = self.set_up_dict(
                d.get("camera_windows"))

        if d.get("camera"):
            self.camera_dict = self.set_up_dict(
                d.get("camera"))

        if d.get("populate"):
            self.populate_dict = self.set_up_populate(
                d.get("populate"))

    @staticmethod
    def set_up_dict(section):
        d = OrderedDict()
        name = ""
        args = []

        for line in section:
            if not line[0] == "\t":
                if name:
                    d[name] = args
                name = line
                args = []

            else:
                args.append(line[1:])
        d[name] = args

        stn = Event.string_to_number

        for name in d:
            ld = {}
            lines = d[name]

            for line in lines:
                if len(line.split()) == 1:
                    key = line
                    value = True

                else:
                    lhs, rhs = line.split(": ")
                    key = lhs

                    if ", " in rhs:
                        value = tuple(
                            [stn(v) for v in rhs.split(", ") if v]
                        )

                    else:
                        value = stn(rhs)

                ld[key] = value
            d[name] = ld

        return d

    @staticmethod
    def set_up_populate(section):
        d = OrderedDict()
        names = []
        current = ""

        sub_section = []
        for line in section:
            if not line[0] == "\t":
                if names:
                    d[current].append(
                        ContextManager.set_up_dict(
                            sub_section)['']
                    )
                    sub_section = []

                if line not in names:
                    current = line
                    names.append(line)
                    d[line] = []

            else:
                sub_section.append(line)

        return d

    @staticmethod
    def set_up_command_dict(section):
        d = ContextManager.set_up_dict(section)
        cd = {}

        def get_step(step_name):
            conditions = STEP_DICT[step_name]

            return Step(step_name, conditions)

        for name in d:
            command = d[name]
            steps = [get_step(n) for n in command["steps"]]
            devices = command["devices"]
            window = command["window"]

            cd[name] = Command(
                name, steps, devices,
                frame_window=window
            )

        return cd

    def handle_collisions(self):
        d = self.collision_systems
        get_group = self.environment.get_group

        for name in d:
            system = d[name]
            args = tuple([
                get_group(n) for n in system["args"]
            ])

            COLLISIONS_DICT[name](*args)

    def set_up_camera(self):
        env = self.environment

        for name in self.camera_windows:
            wd = self.camera_windows[name]
            layer = env.get_layer(wd.get(
                "layer", "Camera Layer"))

            args = (
                wd.get("window_size"),
                wd.get("shift"),
                wd.get("offset", (0, 0))
            )
            layer.add_window(name, args)

            for arg_name in wd:
                if arg_name in ("track_sprite", "track_sprite_heading"):
                    args = list(wd[arg_name])
                    i = 0
                    for arg in args:
                        if type(arg) is str:
                            args[i] = env.get_value(arg)
                        i += 1

                    print("ARGS", args)
                    CAMERA_DICT[arg_name](layer, name, *args)

        for name in self.camera_dict:
            cd = self.camera_dict[name]
            args = [
                cd[n] for n in cd.keys() if n not in ("func", "layer")
            ]
            layer = env.get_layer(cd.get(
                "layer", "Camera Layer"))

            if "func" in cd:
                func, fargs = cd["func"][0], list(cd["func"][1:])
                func = CAMERA_DICT[func]

                i = 0
                for arg in fargs:
                    if type(arg) is str:
                        fargs[i] = env.get_value(arg)
                    i += 1

                CAMERA_DICT[name](layer, lambda: func(*fargs), *args)

            else:
                CAMERA_DICT[name](layer, *args)

    def set_up_huds(self):
        for name in self.layers_dict:
            ld = self.layers_dict[name]
            if "huds" in ld:
                layer = ld["layer"]

                for value_name in ld["huds"]:
                    hd = self.huds_dict[value_name]

                    if "object" in hd:
                        obj = self.environment.get_value(hd["object"])
                    else:
                        obj = self.environment

                    field_names = [n for n in hd if n != "object"]
                    fields = [
                        (n, ) + FIELDS_DICT[n] for n in field_names
                    ]

                    layer.add_hud_box(value_name, obj, fields)

    def set_up_commands(self):
        for c in self.environment.controllers:
            commands = self.command_dict
            c.commands = deepcopy(commands)

    def link_interface(self, *items):
        env = self.environment

        for item in items:
            model = env.model
            if "_" + item.name not in model.values:
                env.set_value(
                    "_" + item.name, item.interface
                )

            for value_name in item.interface:
                value = item.interface[value_name]

                if type(value) not in (FunctionType, MethodType):
                    set_method = getattr(item, "set_" + value_name)

                    model.link_sub_value("_" + item.name, value_name,
                                         set_method)

    def reset_controllers(self):
        gd = self.groups_dict

        for name in gd:
            group = gd[name]
            for sprite in group:
                if hasattr(sprite, "controller"):
                    self.set_item_controller(sprite)

    def load_layer(self, name):
        env = self.environment
        ld = self.layers_dict[name]

        if ld.get("environment"):
            layer = CONTEXT_DICT[name](env)
        else:
            layer = CONTEXT_DICT[name]()

        ld["layer"] = layer

        if ld.get("pause_menu"):
            env.set_value("pause_menu", layer)

        else:
            if ld.get("parent_layer"):
                parent = env.get_layer(
                    ld.get("parent_layer")
                )
                parent.add_sub_layer(layer)
            else:
                env.add_sub_layer(
                    layer)

        if ld.get("camera"):
            env.set_value(
                "Camera", layer.camera)

        if ld.get("groups"):
            groups = [env.get_group(g) for g in ld.get("groups")]
            layer.groups = groups

        if ld.get("pause"):
            env.model.link_value(
                "game_paused",
                lambda b: layer.set_active(not b))

        if ld.get("frame_advance"):
            env.model.link_value(
                "frame_advance_pause",
                lambda b: layer.set_active(not b))

        if hasattr(layer, "interface"):
            self.link_interface(layer)

        if ld.get("controllers"):
            layer.copy_controllers(
                env.controllers)

        # ADD TO LAYER DICT
        if ld.get("bg_layers"):
            for name in ld.get("bg_layers"):
                bg = self.bg_layers_dict[name]
                cls = bg.get("class")
                if not cls:
                    cls = "Parallax Bg Layer"
                image = bg["image"]
                scale = bg["scale"]
                args = (image, scale)
                kwargs = {
                    "position": bg["position"],
                    "wrap": bg["wrap"],
                    "buffer": bg["buffer"]
                }

                bg_layer = CONTEXT_DICT[cls](
                    *args, **kwargs)
                layer.bg_layers.append(bg_layer)

    def load_item(self, name, *args, **kwargs):
        d = self.items_dict[name]
        item = CONTEXT_DICT[name](*args, **kwargs)
        group = self.environment.get_group(d["group"])
        item.add(group)

        if hasattr(item, "interface"):
            self.link_interface(item)

        if d.get("animation"):
            self.set_up_animations(item)

        if d.get("controller"):
            self.set_item_controller(item)

        return item

    def set_up_animations(self, item):
        item_dict = self.items_dict
        name = item.name
        d = item_dict[name]

        animation_machine = d.get("machine")
        if not animation_machine:
            animation_machine = ANIMATION_DICT[self.environment.name]

        stream_file = d["animation"]
        if "sprite_sheet" in d:
            sprite_sheet = d["sprite_sheet"]
        else:
            sprite_sheet = stream_file

        item.set_up_animations(
            sprite_sheet + GFX,
            stream_file + SFX,
            animation_machine)

    def set_item_controller(self, item):
        name = item.name
        d = self.items_dict[name]

        args = d["controller"]
        n = args[1]
        layer = self.environment.get_layer(args[0])
        controller = layer.controllers[n]

        item.set_controller(controller)

    def populate(self):
        env = self.environment

        for key in self.populate_dict:
            items = self.populate_dict[key]

            for item_d in items:
                args = item_d.get("args", [])
                if args:
                    item_d.pop("args")

                name = key.split(" = ")[-1]
                item = self.load_item(name, *args, **item_d)

                if " = " in key:
                    rhs, lhs = key.split(" = ")
                    env.set_value(rhs, item)

# def sprite_demo_camera(layer, environment):
#     player = environment.get_value("Player")
#
#     w1 = ("slow_push", [(300, 350), (300, 150), (0, 0)])
#     w2 = ("fast_push", [(400, 500), (550, 0), (0, -100)])
#
#     # BUILD CAMERA WINDOWS
#     layer.set_up_windows(w1, w2)
#
#     # TRACK CAMERA FUNCTION
#     layer.set_sprite_window_track(
#         player, "slow_push", .08)
#     layer.set_sprite_window_track(
#         player, "fast_push", .5)
#     layer.track_window_to_sprite_heading(
#         player, "slow_push", 1.5)
#     layer.track_window_to_sprite_heading(
#         player, "fast_push", .5)
#
#     # TRACK ANCHOR FUNCTION
#     layer.set_anchor_track_function(
#         lambda: player.get_ground_anchor(),
#         lambda: player.is_grounded(), .05
#     )
#
#     layer.set_anchor(450)
#     a_min = 450
#     a_max = 550
#
#     def get_position():
#         span = a_max - a_min
#         x, y = layer.camera.position
#         r = y / 600
#         value = r * span
#
#         return value + 450
#
#     layer.set_anchor_position_function(
#         get_position, (a_min, a_max)
#     )
#
#     layer.set_camera_bounds_edge(900)
#
#     def get_scale():
#         camera = layer.camera
#         y = camera.focus_point[1]
#         scale = round(
#             1 + ((y + 500) / 900), 3)
#
#         return scale
#
#     layer.set_scale_track_function(
#         get_scale, (1, 2)
#     )
#

CONTEXT_DICT = {
    "Sprite Layer": lambda: PhysicsLayer(
        "Sprite Layer", GRAVITY, COF),

    "Walls Layer": lambda: RegionLayer(
        "Walls Layer"),

    "Debug Layer": lambda env: DebugLayer(env),

    "Pause Menu": lambda env: PauseMenu(env),

    "Player": lambda **kwargs: DemoSprite(
        "Player", **kwargs),

    "Squirrel2": lambda **kwargs: DemoSprite(
        "Squirrel2", **kwargs),

    "Tree Plat": lambda *args, **kwargs: TreePlat(
        *args, **kwargs),

    "Camera Layer": lambda: CameraLayer(
        "Camera Layer"),

    "Parallax Bg Layer": lambda *args, **kwargs: ParallaxBgLayer(
        *args, **kwargs),
}


CAMERA_DICT = {
    "track_sprite": CameraLayer.set_sprite_window_track,

    "track_sprite_heading": CameraLayer.track_window_to_sprite_heading,

    "ground_track": CameraLayer.ground_track,

    "vertical_position_track": CameraLayer.vertical_position_track,

    "anchor_track_function": CameraLayer.set_anchor_track_function,

    "anchor_position_function": CameraLayer.set_anchor_position_function,

    "bounds_edge": CameraLayer.set_camera_bounds_edge,

    "bounds_region": CameraLayer.set_camera_bounds_region,

    "scale_track_function": CameraLayer.set_scale_track_function
}


COLLISIONS_DICT = {
    "wall_collisions": RegionLayer.smooth_wall_collision_system,

    "sprite_collisions": PhysicsLayer.collision_system,
}


STEP_DICT = {
    "neutral": [lambda f: f[0] == (0, 0)],
    "up": [lambda f: f[0][1] == -1],
    "left": [lambda f: f[0][0] == -1],
    "right": [lambda f: f[0][0] == 1]
}


FIELDS_DICT = {
    "acceleration": (
        lambda obj: obj.acceleration.get_value(),
        "average", 2),

    "velocity": (
         lambda obj: obj.velocity.get_value(),
         "average", 2),

    "position": (
         lambda obj: obj.position,),

    "size": (
        lambda obj: obj.size,),

    "grounded": (
         lambda obj: obj.is_grounded(),),

    "focus_point": (
        lambda obj: obj.focus_point,),

    "collision_point": (
        lambda obj: obj.collision_point,),

    "dt": (
        lambda obj: obj.get_value("dt"),)
}


ANIMATION_DICT = {
    "Sprite Demo": SpriteDemoMachine,
}
