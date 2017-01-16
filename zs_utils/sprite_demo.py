from types import FunctionType, MethodType

from zs_constants.sprite_demo import GRAVITY, COF
from zs_constants.zs import SCREEN_SIZE
from zs_src.camera import CameraLayer
from zs_src.camera import ParallaxBgLayer
from zs_src.classes import CacheList
from zs_src.controller import Command, Step
from zs_src.entities import Layer
from zs_src.menus import HeadsUpDisplay, Menu
from zs_src.physics import PhysicsLayer, Wall
from zs_src.resource_library import get_resources
from zs_src.sprites import CharacterSprite
from zs_src.state_machines import AnimationMachine
from zs_utils.debug_menu import DictEditor


class SpriteDemo(Layer):
    def __init__(self, **kwargs):
        super(SpriteDemo, self).__init__("sprite demo", **kwargs)
        self.main_group = self.make_group()
        self.context = ContextManager(self)

        self.camera_layer = CameraLayer("camera layer")
        self.add_sub_layer(self.camera_layer)

        self.sprite_layer = PhysicsLayer(
            GRAVITY, COF, "sprite demo physics layer")
        self.camera_layer.add_sub_layer(
            self.sprite_layer)

        self.debug_layer = DebugLayer(self)
        self.debug_layer.model = self.model
        self.add_sub_layer(self.debug_layer)
        # self.camera_layer.add_sub_layer(
        #     self.debug_layer)

        self.pause_menu = PauseMenu(self)
        self.frame_advance = False
        self.paused = False

    def handle_controller(self):
        super(SpriteDemo, self).handle_controller()

        if self.controller.check_command("double tap up"):
            if not self.pause_menu.active:
                self.frame_advance = not self.frame_advance

        devices = self.controller.devices
        start = devices["start"]
        pause_ok = not self.pause_menu.active

        if not self.frame_advance:
            if start.check() and pause_ok:
                self.queue_events(("pause",
                                   ("layer",
                                    self.pause_menu)))
        else:
            if start.held:
                if devices["a"].check():
                    self.camera_layer.active = True
                else:
                    self.camera_layer.active = False
            else:
                self.camera_layer.active = True

        if not self.paused:
            for c in self.sprite_layer.controllers:
                if c:
                    c.update()

    def populate(self):
        # # REPLACE WITH DATA FROM CONFIG VALUE FILE LOOKUP
        spawn = self.context.spawn_sprite

        spawn("yoshi", position=(500, 300))
        spawn("yoshi", position=(200, 300))

        player = spawn("player", position=(450, 100))
        self.set_value("player", player)

    def reset_controllers(self):
        for sprite in self.main_group:
            self.context.set_sprite_controller(sprite)

    def on_spawn(self):
        context = self.context
        context.set_up_controllers()

        self.set_value(
            "_spawn", context.spawn_sprite)
        self.set_value(
            "_sprite_dict", context.set_up_sprite_dict())

        super(SpriteDemo, self).on_spawn()

        camera_layer = self.camera_layer
        sprite_layer = self.sprite_layer
        debug_layer = self.debug_layer

        context.set_up_bg_layers(camera_layer)
        context.set_up_collisions(sprite_layer)
        context.set_up_layers(
            sprite_layer, debug_layer, camera_layer)

        player = self.get_value("player")
        window = self.camera_layer.camera.window
        self.camera_layer.track_sprite_to_window(
            player, window, 1 / 8)
        self.camera_layer.track_sprite_heading_to_window(
            player, window, 4 / 3)

    def on_pause(self):
        self.paused = True
        super(SpriteDemo, self).on_pause()
        self.camera_layer.active = False

    def on_unpause(self):
        self.paused = False
        super(SpriteDemo, self).on_unpause()
        self.camera_layer.active = True


class ContextManager:
    def __init__(self, environment):
        self.environment = environment
        self.model = environment.model
        self.set_value = environment.set_value
        self.get_value = environment.get_value

    def set_up_layers(self, *layers):
        for layer in layers:
            if hasattr(layer, "interface"):
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
    def set_up_bg_layers(layer):
        trees = "smalltree", "midtree", "bigtree"
        get = ParallaxBgLayer.get_bg_image

        def get_scale(name):
            full_w = get("bigtree").get_size()[0]
            w = get(name).get_size()[0]

            return w / full_w

        for tree in trees:
            scale = get_scale(tree)
            offset = 250
            depth = 30
            position = 0, (depth * scale) + offset

            layer.add_bg_layer(
                tree, scale, buffer=(50, 0),
                wrap=(True, False), position=position)

    def set_up_collisions(self, layer):
        group = self.environment.main_group
        a = 300, 300
        b = 750, 450
        walls = [Wall(a, b, ground=True),
                 Wall((160, 390), (160, 750)),
                 Wall((800, 550), (1050, 360), True),
                 Wall((1050, 360), (800, 550)),
                 Wall((1200, 470), (1430, 280), True),
                 Wall((1620, 280), (2250, 150), True),
                 Wall((2490, 90), (2790, -180), True),
                 Wall((2200, -120), (2500, -220), True),
                 Wall((2500, -220), (2200, -120)),
                 Wall((0, 720), (1999, 720), True)]
        layer.add_wall_layer(walls)
        layer.groups.append(group)
        layer.add_hitbox_layer(group)
        layer.add_vector_layer(group)

        # SPRITE COLLISION SYSTEM
        layer.collision_systems.append(
            [layer.group_perm_collision_check,
             (group, layer.sprite_collision,
              layer.handle_collision)]
        )

        #
        layer.collision_systems.append(
            [layer.group_regions_collision_check,
             (group, walls, layer.wall_collision,
              Wall.handle_collision_smooth)]
        )

    @staticmethod
    def set_up_commands(controller):
        press_left = Step("press_left",
                          [lambda f: f[0][0] == -1])
        press_right = Step("press_right",
                           [lambda f: f[0][0] == 1])
        neutral = Step("neutral dpad",
                       [lambda f: f[0] == (0, 0)])
        press_up = Step("press_up",
                        [lambda f: f[0][1] == -1])

        window = 20
        double_right = Command("double tap right",
                               [neutral, press_right, neutral, press_right],
                               ["dpad"], window)
        double_left = Command("double tap left",
                              [neutral, press_left, neutral, press_left],
                              ["dpad"], window)
        double_up = Command("double tap up",
                            [neutral, press_up, neutral, press_up],
                            ["dpad"], window)

        for command in (double_right, double_left, double_up):
            controller.commands.append(
                command)

    def set_up_controllers(self):
        for controller in self.environment.controllers:
            self.set_up_commands(controller)
            self.environment.sprite_layer.controllers.append(
                controller.get_copy())

    def set_up_sprite_dict(self):
        group = self.environment.main_group

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
                "group": group},
            "squirrel2": {
                "load": lambda **kwargs: DemoSprite("squirrel2", **kwargs),
                "controller": 1,
                "graphics": "squirrel2",
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
            animation_machine)

    def set_sprite_controller(self, sprite):
        sprite_dict = self.environment.get_value("_sprite_dict")
        name = sprite.name
        n = sprite_dict[name]["controller"]

        if type(n) is int:
            controller = self.environment.sprite_layer.controllers[n]
        else:
            controller = None

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
        self.set_sprite_controller(sprite)

        return sprite


class SpriteDemoMachine(AnimationMachine):
    def __init__(self, sprite):
        super(SpriteDemoMachine, self).__init__("demo_sprite.txt", sprite)

        self.add_event_methods(
            "press_direction", "press_jump", "press_down",
            "neutral_dpad", "v_acceleration_0", "ground_collision",
            "auto", "tap_direction", "press_opposite_direction",
            "run_momentum", "falling"
        )

    @property
    def dpad(self):
        if self.controller:
            return self.controller.devices["dpad"]

    def on_tap_direction(self):
        if self.controller:
            check = self.controller.check_command
            tap = check("double tap left") or check("double tap right")

            a, b = self.controller.devices["a"], self.controller.devices["b"]
            if a.held > 20 and b.held > 20:
                tap = True

            return tap

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

    def on_falling(self):
        return not self.sprite.is_grounded()

    def on_auto(self):
        if self.sprite.graphics:
            return self.sprite.animation_completed()


class DemoSprite(CharacterSprite):
    def __init__(self, *args, **kwargs):
        super(DemoSprite, self).__init__(*args, **kwargs)

        sounds = get_resources("demo_sounds")

        def play(key):
            s = sounds[key + ".ogg"]
            s.set_volume(.1)
            s.play()
            # pass

        def stop(key):
            s = sounds[key + ".ogg"]
            s.stop()
            # pass

        self.play_sound = play
        self.stop_sound = stop

        def check_b():
            if self.controller:
                return self.controller.devices["b"].held

        self.add_meter(
            "jump", 10, True, check_b
        )

    @property
    def dpad(self):
        if self.controller:
            return self.controller.devices["dpad"]

    def update(self, dt):
        super(DemoSprite, self).update(dt)

        base_jump = 5
        base_speed = 5
        right, left = self.RIGHT, self.LEFT

        if self.animation_machine and self.controller:
            state = self.get_animation_name()
            frame_number = self.get_state_frame()
            last = self.dpad.last_direction
            x = self.dpad.get_direction()[0]

            # PLAY SOUNDS
            if state in ("jump_squat", "walk", "run", "dash", "run_stop"):
                if self.get_animation_frame() == 0:
                    self.play_sound(state)
            for name in ("walk", "run", "dash", "run_stop"):
                if state != name:
                    self.stop_sound(name)

            # JUMP
            if state == "jump_up" and frame_number < 5:
                if frame_number == 0:
                    dy = base_jump
                else:
                    jump_height = self.meters["jump"].get_ratio()
                    jump_height += 3 / self.meters["jump"].maximum

                    dy = base_jump * jump_height
                jump = self.get_jump_vector(dy).rotate(
                    (1 / 32) * -x)

                self.apply_force(jump)

            # FACE DIRECTION
            if state in (
                    "walk", "jump_squat", "crouch_down",
                    "crouch_idle", "crouch_up", "dash", "pivot"):
                if last in (right, left):
                    if state == "dash" and frame_number == 0:
                        self.direction = last
                    elif state == "jump_squat":
                        if abs(self.velocity.i_hat) < 1:
                            self.direction = last
                    elif state == "pivot":
                        if frame_number == self.graphics.get_frame_count() - 1:
                            dx, dy = self.direction
                            dx *= -1
                            self.direction = dx, dy
                    else:
                        self.direction = last

            # MOVEMENT SPEED
            movement = {
                "walk": 1,
                "jump_squat": 0,
                "jump_up": .5,
                "jump_apex": .5,
                "jump_fall": .5,
                "jump_land": 0,
                "dash": 2.5,
                "run": 2,
                "run_slow": 2.5,
                "run_stop": .5,
                "pivot": .5
            }

            if state in ("jump_up", "jump_apex", "jump_fall"):
                dx = movement[state] * x
            elif state in ("jump_squat", "jump_land"):
                dx = self.get_ground_speed() * self.friction
            elif state == "idle" or "crouch" in state:
                dx = 0
                if self.ground.get_angle() != 0:
                    m = self.velocity.magnitude
                    r = m / base_speed
                    if r > 1:
                        r = 1
                    dx = self.get_slide_force() * (-1)
                    dx -= (dx * (1 - r)) / (base_speed ** 2)
            else:
                if state == "dash" and frame_number == 0:
                    self.velocity.i_hat = 0
                    self.velocity.j_hat = 0
                dx = movement[state] * self.direction[0] * self.friction * base_speed

            move = self.get_ground_vector(dx)
            self.apply_force(move)


class DebugLayer(HeadsUpDisplay):
    def __init__(self, environment, **kwargs):
        super(DebugLayer, self).__init__(environment.name + " debug layer", **kwargs)
        self.environment = environment

        def toggle_visible():
            self.visible = not self.visible

        self.interface = {
            "Toggle debug layer": toggle_visible,
        }

    def set_hi(self, value):
        print(value)

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
        w, h = SCREEN_SIZE
        w -= 50
        print(w)
        if w > 750:
            cutoff = 4
        else:
            cutoff = 3

        player = self.get_value("player")
        reporters = [
            tools.make_reporter_sprite(
                player, self.animation_machine_reporter()),
            tools.make_reporter_sprite(
                player, self.physics_reporter()
            ),
            tools.make_reporter_sprite(
                self.environment,
                lambda e: "FRAME_ADVANCE: {}".format(e.frame_advance)),
            tools.make_reporter_sprite(
                self.environment.camera_layer,
                lambda l: "CAMERA_FOCUS: {}".format(l.camera.focus_point)
            )
        ]
        block = tools.ContainerSprite(
            "physics reporter box", reporters,
            size=(w, 0), table_style="cutoff {}".format(cutoff),
            position=(25, 0)
        )
        block.style = {"align_h": "c"}
        block.add(self.hud_group)


class PauseMenu(Menu):
    def __init__(self, environment, **kwargs):
        super(PauseMenu, self).__init__("pause menu", **kwargs)
        self.add_event_methods(
            "load_sprite_editor", "load_physics_editor",
            "update_sprite_dict", "update_physics",
            "load_debug_editor", "update_debug")

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

    def handle_controller(self):
        super(PauseMenu, self).handle_controller()

        if self.get_state() == "alive":
            if self.controller.devices["start"].held == 1:
                self.handle_event("die")

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

        debug_option = tools.make_text_option(
            "Debug Layer Options", "load_debug_editor",
            self
        )
        mb.add_member_sprite(debug_option)

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

    def on_load_debug_editor(self):
        d = self.get_value("_sprite demo debug layer")
        layer = DictEditor(
            "debug editor", model=d)
        load = ("pause",
                ("layer", layer))
        self.queue_events(load)
        self.set_event_listener(
            "unpause", "update_debug",
            self, temp=True)

    def on_update_physics(self):
        d = self.get_return_value()
        self.set_value("_sprite demo physics layer", d)

    def on_update_debug(self):
        d = self.get_return_value()
        self.set_value("_sprite demo debug layer", d)

    def on_update_sprite_dict(self):
        d = self.get_return_value()
        name = self.event.get("sprite_name")
        self.set_value("_" + name, d)

