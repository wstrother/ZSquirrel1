from types import FunctionType, MethodType

from zs_constants.sprite_demo import GRAVITY, COF
from zs_src.classes import CacheList
from zs_src.controller import Command, Step
from zs_src.entities import Layer
from zs_src.menus import HeadsUpDisplay, Menu
from zs_src.physics import PhysicsLayer, Wall
from zs_src.sprites import CharacterSprite
from zs_src.state_machines import AnimationMachine
from zs_utils.debug_menu import DictEditor


class SpriteDemo(Layer):
    def __init__(self, **kwargs):
        super(SpriteDemo, self).__init__("sprite demo", **kwargs)
        self.main_group = self.make_group()
        self.sprite_layer = PhysicsLayer(
            GRAVITY, COF, "sprite demo physics layer")
        self.add_sub_layer(self.sprite_layer)
        self.context = ContextManager(self)

        self.debug_layer = DebugLayer()
        self.debug_layer.model = self.model
        self.add_sub_layer(self.debug_layer)

        self.pause_menu = PauseMenu(self)

    def handle_controller(self):
        super(SpriteDemo, self).handle_controller()

        devices = self.controller.devices
        start = devices["start"]

        # if start.check() and not self.pause_menu.active:
        #     self.queue_events(("pause",
        #                        ("layer",
        #                         self.pause_menu)))

        if start.held:
            if devices["a"].check():
                self.sprite_layer.active = True
            else:
                self.sprite_layer.active = False
        else:
            self.sprite_layer.active = True

    def populate(self):
        self.sprite_layer.toggle_wall_layer()
        # self.sprite_layer.toggle_hitbox_layer()
        # self.sprite_layer.toggle_vector_layer()
        # self.debug_layer.visible = False

        for controller in self.controllers:
            self.context.set_commands(controller)

        spawn = self.context.spawn_sprite

        self.set_value(
            "player",
            spawn("player", position=(450, 100))
        )
        # spawn("yoshi", position=(500, 300))
        # spawn("yoshi", position=(200, 300))

    def reset_controllers(self):
        for sprite in self.main_group:
            self.context.set_controller(sprite)

    def on_pause(self):
        super(SpriteDemo, self).on_pause()
        self.sprite_layer.active = False

    def on_unpause(self):
        super(SpriteDemo, self).on_unpause()
        self.sprite_layer.active = True


class ContextManager:
    def __init__(self, environment):
        self.environment = environment

        set_value = environment.set_value
        group = environment.main_group
        sprite_layer = environment.sprite_layer

        set_value("_spawn", self.spawn_sprite)
        set_value("_sprite_dict", self.set_up_sprite_dict(group))

        self.set_up_physics(sprite_layer, group)
        self.set_up_layers()

    def set_up_layers(self):
        for layer in self.environment.sub_layers:
            self.link_interface(layer)

            self.environment.set_value(
                "_" + layer.name, layer.interface
            )

    def link_interface(self, obj):
        model = self.environment.model

        for value_name in obj.interface:
            value = obj.interface[value_name]

            if type(value) not in (FunctionType, MethodType):
                set_method = getattr(obj, "set_" + value_name)

                model.link_sub_value("_" + obj.name, value_name,
                                     set_method)

    @staticmethod
    def set_up_physics(layer, group):
        a = 350, 350
        b = 780, 480
        walls = [Wall(a, b, True),
                 Wall((0, 600), (999, 600), True),
                 Wall((50, 0), (50, 600)),
                 Wall((750, 600), (750, 0))]
        layer.add_wall_layer(walls)
        layer.groups.append(group)
        layer.add_hitbox_layer(group)
        layer.add_vector_layer(group)

        layer.collision_systems.append(
            [layer.group_perm_collision_check,
             (group, layer.sprite_collision,
              layer.handle_collision)]
        )

        layer.collision_systems.append(
            [layer.group_regions_collision_check,
             (group, walls, layer.wall_collision,
              Wall.handle_collision_smooth)]
        )

    @staticmethod
    def set_up_sprite_dict(group):
        d = {
            "player": {
                "load": lambda **kwargs: DemoSprite("player", **kwargs),
                "controller": 0,
                "graphics": "squirrel",
                "animation_machine": SpriteDemoMachine,
                "group": group},
            "yoshi": {
                "load": lambda **kwargs: DemoSprite("yoshi", **kwargs),
                "controller": None,
                "graphics": "yoshi",
                "animation_machine": SpriteDemoMachine,
                "group": group}
        }

        return d

    def set_graphics(self, sprite):
        sprite_dict = self.environment.get_value("_sprite_dict")
        name = sprite.name
        d = sprite_dict[name]
        stream_file = d["graphics"]
        animation_machine = d["animation_machine"]

        sprite.set_up_animations(
            stream_file + ".gif",
            stream_file + ".txt",
            animation_machine())

    @staticmethod
    def set_commands(controller):
        press_left = Step("press_left",
                          [lambda f: f[0][0] == -1])
        press_right = Step("press_right",
                           [lambda f: f[0][0] == 1])
        neutral = Step("neutral dpad",
                       [lambda f: f[0][0] == 0])
        window = 20
        double_right = Command("double tap right",
                               [neutral, press_right, neutral, press_right],
                               ["dpad", "start"], window)
        double_left = Command("double tap left",
                              [neutral, press_left, neutral, press_left],
                              ["dpad", "start"], window)
        controller.commands.append(
            double_left)
        controller.commands.append(
            double_right)

    def set_controller(self, sprite):
        sprite_dict = self.environment.get_value("_sprite_dict")
        name = sprite.name
        controller = sprite_dict[name]["controller"]

        if type(controller) is int:
            controller = self.environment.controllers[0]

        sprite.set_controller(controller)

    def spawn_sprite(self, key, **kwargs):
        model = self.environment.model
        sprite_dict = model.values["_sprite_dict"][key]
        load = sprite_dict["load"]
        group = sprite_dict["group"]

        sprite = load(**kwargs)
        sprite.add(group)

        if "_" + sprite.name not in model.values:
            self.environment.set_value(
                "_" + sprite.name, sprite.interface)

        self.link_interface(sprite)
        self.set_graphics(sprite)
        self.set_controller(sprite)

        return sprite


class SpriteDemoMachine(AnimationMachine):
    def __init__(self):
        super(SpriteDemoMachine, self).__init__("demo_sprite.txt")

        self.add_event_methods(
            "press_direction", "press_jump", "press_down",
            "neutral_dpad", "v_acceleration_0", "ground_collision",
            "auto", "tap_direction", "press_opposite_direction",
            "run_momentum"
        )

    @property
    def dpad(self):
        if self.controller:
            return self.controller.devices["dpad"]

    def on_tap_direction(self):
        if self.controller:
            double_right, double_left = self.controller.commands
            command = double_right.active or double_left.active

            return command

    def on_press_direction(self):
        if self.controller:
            x, y = self.dpad.get_direction()
            return x != 0

    def on_press_jump(self):
        if self.controller:
            jump = bool(self.controller.devices["b"].held == 1)

            return jump

    def on_press_down(self):
        if self.controller:
            down = self.dpad.get_direction()[1] == 1
            return down

    def on_release_down(self):
        if self.controller:
            dpad = self.dpad
            down = dpad.get_direction()[1] > 0

            return not down

    def on_neutral_dpad(self):
        if self.controller:
            neutral = self.dpad.get_direction() == (0, 0)
            return neutral

    def on_v_acceleration_0(self):
        if self.sprite.velocity:
            apex = self.sprite.velocity.j_hat >= 0

            return apex

    def on_ground_collision(self):
        return self.sprite.is_grounded()

    def on_run_momentum(self):
        v = self.sprite.velocity
        if abs(v.i_hat) > 14 and self.controller:
            dpad = self.sprite.controller.devices["dpad"]
            x = dpad.get_direction()[0]
            dx = self.sprite.direction[0]
            vx = v.i_hat
            right = vx > 0 and x > 0 and dx > 0
            left = vx < 0 and x < 0 and dx < 0

            return left or right

    def on_press_opposite_direction(self):
        if self.controller:
            dpad = self.dpad
            direction = self.sprite.direction

            opposite = direction[0] * dpad.get_value()[0] == -1
            return opposite

    def on_auto(self):
        if self.sprite.graphics:
            return self.sprite.graphics.animation_completed()


class DemoSprite(CharacterSprite):
    def update(self, dt):
        super(CharacterSprite, self).update(dt)

        if self.animation_machine:
            state = self.animation_machine.get_state().name

            if state == "jump_up" and self.is_grounded():
                jump = self.Vector("jump", 0, -25)
                self.apply_force(jump)
                self.set_off_ground()

            if self.controller:
                dpad = self.controller.devices["dpad"]
                last = dpad.last_direction
                x = dpad.get_direction()[0]

                if state in ("walk", "crouch_down", "crouch_idle", "crouch_up", "dash"):
                    if state == "dash":
                        if self.graphics.get_frame_number() == 0:
                            if last in (self.RIGHT, self.LEFT):
                                self.direction = last
                    else:
                        if last in (self.RIGHT, self.LEFT):
                            self.direction = last

                movement = {
                    "walk": 1,
                    "jump_squat": .5,
                    "jump_up": .5,
                    "jump_apex": .5,
                    "jump_fall": .5,
                    "jump_land": .5,
                    "dash": 2.5,
                    "run": 2,
                    "run_stop": .5
                }
                if state in movement:
                    speed = movement[state]
                    if state in ("jump_up", "jump_apex", "jump_fall"):
                        dx = speed * x
                    elif state in ("jump_squat", "jump_land"):
                        dx = self.friction.i_hat * -1
                    else:
                        dx = movement[state] * self.direction[0]

                    move = self.Vector("move", dx, 0)
                    self.apply_force(move)


class DebugLayer(HeadsUpDisplay):
    def __init__(self, **kwargs):
        super(DebugLayer, self).__init__("debug layer", **kwargs)

    @staticmethod
    def animation_machine_reporter():
        states = CacheList(4)

        def report_animation(p):
            if p.animation_machine:
                state = p.animation_machine.get_state()
                if not states or states[-1] is not state:
                    states.append(state)

                return [s.name for s in states]
            else:
                return "Not set up"

        return report_animation

    @staticmethod
    def physics_reporter():
        velocities = CacheList(5)
        accelerations = CacheList(5)

        def report_physics(p):
            velocities.append(
                p.velocity.get_value())
            accelerations.append(
                p.acceleration.get_value())

            vx = [v[0] for v in velocities]
            vy = [v[1] for v in velocities]
            vx = sum(vx) / len(vx)
            vy = sum(vy) / len(vy)

            ax = [a[0] for a in accelerations]
            ay = [a[1] for a in accelerations]
            ax = sum(ax) / len(ax)
            ay = sum(ay) / len(ay)

            x, y = p.collision_point

            f_string = "{:>15}: {:> 04.3f}, {:> 04.3f}"
            text = [
                f_string.format("ACCELERATION", ax, ay),
                f_string.format("VELOCITY", vx, vy),
                f_string.format("POSITION", x, y),
                "GROUNDED: " + str(p.is_grounded())
            ]

            return text

        return report_physics

    def populate(self):
        tools = self.tools

        player = self.get_value("player")
        reporters = [
            tools.make_reporter_sprite(
                player, self.animation_machine_reporter()),
            tools.make_reporter_sprite(
                player, self.physics_reporter()
            )
        ]
        block = tools.ContainerSprite(
            "physics reporter box", reporters,
            size=(750, 100), table_style="cutoff 4",
            position=(25, 0)
        )
        block.style = {"align_h": "c"}
        block.add(self.hud_group)
        # self.physics_reporter(player)

        # controller = self.get_value("_controller")
        # frame_cache = CacheList(5)
        # text_cache = CacheList(1)
        #
        # def report_frames(c):
        #     if c.commands:
        #         frames = c.commands[0].frames
        #
        #         text = {
        #             (0, 0): "neutral",
        #             (-1, 0): "left",
        #             (1, 0): "right",
        #             (1, 1): "down right",
        #             (1, -1): "up right",
        #             (0, 1): "down",
        #             (0, -1): "up",
        #             (-1, -1): "up left",
        #             (-1, 1): "down left"
        #         }
        #
        #         for f in frames:
        #             if frame_cache:
        #                 if f[0] != frame_cache[-1]:
        #                     frame_cache.append(f[0])
        #             else:
        #                 frame_cache.append(f[0])
        #
        #         def get_line_changes(l):
        #             last = None
        #             out = []
        #             for line in l:
        #                 if line != last:
        #                     last = line
        #                     out.append(line)
        #
        #             return out
        #
        #         lines = [text[f[0]] for f in c.commands[0].frames]
        #         return get_line_changes(lines)
        #     else:
        #         return ""
        #
        # frame_reporter = tools.make_reporter_sprite(
        #     controller, report_frames
        # )
        #
        # check_cache = CacheList(60)
        #
        # def report_commands(c):
        #     lines = []
        #     for command in c.commands:
        #         check_cache.append(command.active)
        #         line = "{}: {}".format(command.name, True in check_cache)
        #         lines.append(line)
        #
        #     return lines
        #
        # command_reporter = tools.make_reporter_sprite(
        #     controller, report_commands
        # )
        #


class PauseMenu(Menu):
    def __init__(self, environment, **kwargs):
        super(PauseMenu, self).__init__("pause menu", **kwargs)
        self.add_event_methods(
            "load_sprite_editor", "load_physics_editor",
            "update_sprite_dict", "update_physics")

        self.active = False
        self.environment = environment

        # EDIT MODEL VALUES
        # EDIT SPRITE DICT
        #    SPRITE VALUES
        #    MAKE SPRITE
        # TOGGLE DEBUG LAYERS
        #    HITBOXES
        #    VECTORS
        # CHOOSE CONTROLLER
        # CHOOSE REPORTERS

    def populate(self):
        self.model = self.environment.model
        self.controllers = self.environment.controllers

        tools = self.tools
        mb = tools.make_main_block(position=(200, 200),
                                   size=(300, 0))

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

        physics_option = tools.make_text_option(
            "Physics Layer Options", "load_physics_editor",
            self)
        mb.add_member_sprite(physics_option)

        controller_option = tools.TextOption(
            "Change Controller")
        mb.add_member_sprite(controller_option)
        self.add_sub_block(
            mb, self.get_controller_sub_block(),
            controller_option)

        leave = tools.make_text_option(
            "Leave demo", "die", self.environment)
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
            controllers = self.environment.controllers
            name = controller_option.text
            i = [c.name for c in controllers].index
            s = i(name)

            a, b = controllers[0], controllers[s]
            self.environment.controllers[0] = b
            self.environment.controllers[s] = a
            self.environment.reset_controllers()

        change_option = tools.TextOption("select")
        tools.set_function_call_on_activation(
            change_option, change_function
        )
        block.add_member_sprite(change_option)

        return block

    def get_spawn_sub_block(self):
        sprite_dict = self.get_value("_sprite_dict")
        tools = self.tools
        x, y = self.main_block.position
        x += self.main_block.size[0]
        to, fo = tools.TextOption, tools.TextFieldOption

        sprite_option = tools.SwitchOption(
            list(sprite_dict.keys()))

        x_option = fo("0", 3)
        y_option = fo("0", 3)

        def spawn():
            name = sprite_option.text
            print(name)
            load = self.get_value("_spawn")
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
        sprite_dict = self.get_value("_sprite_dict")
        tools = self.tools
        x, y = self.main_block.position
        x += self.main_block.size[0]

        block = tools.OptionBlock(
            "sprite dict block", position=(x, y))
        for name in sprite_dict:
            d = self.get_value("_" + name)
            o = tools.make_text_option(
                name, ("load_sprite_editor",
                       ("sprite_name", name),
                       ("dict", d)),
                self)
            block.add_member_sprite(o)

        return block

    def on_load_sprite_editor(self):
        name = self.event.get("sprite_name")
        d = self.get_value("_" + name)
        layer = DictEditor(
            name + " editor", model=d)
        load = ("pause",
                ("layer", layer))
        self.queue_events(load)
        self.set_event_listener(
            "unpause", ("update_sprite_dict",
                        ("sprite_name", name)),
            self, temp=True)

    def on_load_physics_editor(self):
        d = self.get_value("_sprite demo physics layer")
        layer = DictEditor(
            "physics editor", model=d)
        load = ("pause",
                ("layer", layer))
        self.queue_events(load)
        self.set_event_listener(
            "unpause", "update_physics",
            self, temp=True)

    def on_update_physics(self):
        d = self.get_return_value()
        self.set_value("_sprite demo physics layer", d)

    def on_update_sprite_dict(self):
        d = self.get_return_value()
        name = self.event.get("sprite_name")
        self.set_value("_" + name, d)

