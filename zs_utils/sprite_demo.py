from zs_constants.zs import SCREEN_SIZE
from zs_src.classes import CacheList
from zs_src.controller import Command, Step
from zs_src.entities import Layer
from zs_src.menus import HeadsUpDisplay
from zs_src.physics import PhysicsLayer
from zs_src.sprites import CharacterSprite
from zs_src.state_machines import AnimationMachine
from zs_utils.debug_menu import DebugMenu

MASS, ELAST = 1, .1


class SpriteDemo(Layer):
    def __init__(self, **kwargs):
        super(SpriteDemo, self).__init__("sprite demo", **kwargs)
        self.context = ContextManager(self)

        gravity = 1
        self.set_value("gravity", gravity)
        cof = (.1, .03)
        self.set_value("friction", cof)
        sprite_layer = PhysicsLayer(
            gravity, "sprite demo physics layer")
        sprite_layer.friction = cof
        self.model.link_value("gravity",
                              sprite_layer.set_gravity)
        self.model.link_value("friction",
                              sprite_layer.set_friction)

        g = self.make_group()
        self.main_group = g

        sprite_layer.groups.append(g)
        sprite_layer.add_hitbox_layer(g)
        sprite_layer.add_vector_layer(g)
        sprite_layer.collision_systems.append(
            [sprite_layer.group_perm_collision_check,
             (self.main_group,
              sprite_layer.sprite_collision,
              sprite_layer.handle_collision)]
        )

        self.add_sub_layer(sprite_layer)
        self.sprite_layer = sprite_layer

        self.debug_layer = DebugLayer()
        self.debug_layer.model = self.model
        self.add_sub_layer(self.debug_layer)

        pause_menu = PauseMenu()
        pause_menu.model = self.model
        self.pause_menu = pause_menu

    def handle_controller(self):
        super(SpriteDemo, self).handle_controller()

        devices = self.controller.devices
        start = devices["start"]

        if start.check() and not self.pause_menu.active:
            self.handle_event(("pause",
                               ("layer",
                                self.pause_menu)))

        # if start.held:
        #     if start.check():
        #         self.sprite_layer.active = True
        #     else:
        #         self.sprite_layer.active = False
        # else:
        #     self.sprite_layer.active = True

    def populate(self):
        self.set_value("controller", self.controllers[0])
        g = self.main_group
        self.groups = [self.make_group()]

        player = self.context.make_sprite(
            "player", position=(400, 300),
            mass=1.5
        )
        player.add(g)

        yoshi = self.context.make_sprite(
            "yoshi", position=(500, 300),
            mass=1.5
        )
        yoshi.add(g)

        self.set_value("player", player)
        # self.sprite_layer.toggle_hitbox_layer()
        # self.sprite_layer.toggle_vector_layer()

    def on_pause(self):
        super(SpriteDemo, self).on_pause()
        self.sprite_layer.active = False

    def on_unpause(self):
        super(SpriteDemo, self).on_unpause()
        self.sprite_layer.active = True

    def on_birth(self):
        super(SpriteDemo, self).on_birth()

        self.context.set_up_graphics(self.main_group)
        self.context.set_up_controllers(self.main_group)
        self.pause_menu.controllers = self.controllers


class ContextManager:
    def __init__(self, environment):
        self.sprite_dict = self.set_up_sprite_dict()
        self.environment = environment

    @staticmethod
    def set_up_sprite_dict():
        d = {
            "player": [lambda **kwargs: DemoSprite("player", **kwargs),
                       0, "squirrel", SpriteDemoMachine],
            "yoshi": [lambda **kwargs: DemoSprite("yoshi", **kwargs),
                      None, "yoshi", SpriteDemoMachine]
        }

        return d

    def set_up_graphics(self, group):
        for sprite in group:
            name = sprite.name
            args = self.sprite_dict[name][2:]
            stream_file, animation_machine = args

            sprite.set_up_animations(
                stream_file + ".gif",
                stream_file + ".txt",
                animation_machine())

    def set_up_controllers(self, group):
        press_left = Step("press_left",
                          [lambda f: f[0][0] == -1])
        press_right = Step("press_right",
                           [lambda f: f[0][0] == 1])
        neutral = Step("neutral dpad",
                       [lambda f: f[0][0] == 0])
        double_right = Command("double tap right",
                               [press_right, neutral, press_right],
                               ["dpad", "start"], 20)
        double_left = Command("double tap left",
                              [press_left, neutral, press_left],
                              ["dpad", "start"], 20)
        self.environment.controllers[0].commands.append(
            double_left)
        self.environment.controllers[0].commands.append(
            double_right)

        for sprite in group:
            name = sprite.name
            controller = self.sprite_dict[name][1]

            if type(controller) is int:
                controller = self.environment.controllers[0]

            sprite.set_controller(controller)

    def make_sprite(self, key, **kwargs):
        sprite = self.sprite_dict[key][0](**kwargs)

        return sprite


class SpriteDemoMachine(AnimationMachine):
    def __init__(self):
        super(SpriteDemoMachine, self).__init__("demo_sprite.txt")

        self.add_event_methods(
            "press_direction", "press_jump", "press_down",
            "neutral_dpad", "v_acceleration_0", "ground_collision",
            "auto", "tap_direction"
        )

    @property
    def dpad(self):
        if self.sprite.controller:
            return self.sprite.controller.devices["dpad"]

        else:
            return False

    def on_tap_direction(self):
        if self.sprite.controller:
            double_right, double_left = self.sprite.controller.commands
            command = double_right.active or double_left.active

            return command

        else:
            return False

    def on_press_direction(self):
        if self.sprite.controller:
            x, y = self.dpad.get_direction()
            return x != 0

        else:
            return False

    def on_press_jump(self):
        if self.sprite.controller:
            jump = bool(self.sprite.controller.devices["b"].held == 1)

            return jump
        else:
            return False

    def on_press_down(self):
        if self.sprite.controller:
            down = self.dpad.get_direction()[1] == 1
            return down

        else:
            return False

    def on_release_down(self):
        if self.sprite.controller:
            dpad = self.sprite.controller.devices["dpad"]
            down = dpad.get_direction()[1] > 0

            return not down

        else:
            return False

    def on_neutral_dpad(self):
        if self.sprite.controller:
            neutral = self.dpad.get_direction() == (0, 0)
            return neutral

        else:
            return False

    def on_v_acceleration_0(self):
        if self.sprite.velocity:
            apex = self.sprite.velocity.j_hat >= 0

            return apex
        else:
            return False

    def on_ground_collision(self):
        return self.sprite.is_grounded()

    def on_auto(self):
        if self.sprite.graphics:
            return self.sprite.graphics.animation_completed()

        else:
            return False


class DemoSprite(CharacterSprite):
    def update(self, dt):
        super(CharacterSprite, self).update(dt)

        if self.animation_machine:
            state = self.animation_machine.get_state().name

            if state == "jump_up" and self.is_grounded():
                jump = self.Vector("jump", 0, -25)
                self.apply_force(jump)

            if self.controller:
                dpad = self.controller.devices["dpad"]
                last = dpad.last_direction
                x = dpad.get_direction()[0]

                if state in ("walk", "idle", "crouch_down", "crouch_idle", "crouch_up", "dash"):
                    if state == "dash":
                        if self.graphics.get_frame_number() == 0:
                            if last in (self.RIGHT, self.LEFT):
                                self.direction = last
                                print("DASHING {}".format(last))
                    else:
                        if last in (self.RIGHT, self.LEFT):
                            self.direction = last

                # if state in ("jump_squat", "jump_land"):
                #     if self.velocity.i_hat > 0:
                #         self.direction = self.RIGHT
                #     if self.velocity.i_hat < 0:
                #         self.direction = self.LEFT

                movement = {
                    "walk": 1,
                    "jump_squat": .5,
                    "jump_up": .5,
                    "jump_apex": .5,
                    "jump_fall": .5,
                    "jump_land": .5,
                    "dash": 2.5,
                    "run": 2
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

            bottom = self.collision_region.bottom

            x, y = self.position
            if bottom >= SCREEN_SIZE[1]:
                y -= bottom - SCREEN_SIZE[1]
                self.position = x, y
                self.set_on_ground()
                self.velocity.j_hat = 0

            else:
                self.set_off_ground()

            if self.collision_region.right < 0:
                x = SCREEN_SIZE[0] - self.collision_region.width
                self.position = x, y

            if self.collision_region.left > SCREEN_SIZE[0]:
                x = 0
                self.position = x, y


class DebugLayer(HeadsUpDisplay):
    def __init__(self, **kwargs):
        super(DebugLayer, self).__init__("debug layer", **kwargs)

    def populate(self):
        tools = self.tools

        states = CacheList(7)

        def report_player(p):
            if p.animation_machine:
                state = p.animation_machine.get_state().name
                if not states or states[-1] != state:
                    states.append(state)

                last = None
                lines = []
                for s in states:
                    if last != s:
                        last = s
                        lines.append(s)

                return lines

            else:
                return "Not set up"

        player = self.get_value("player")
        reporter = tools.make_reporter_sprite(
            player, report_player)

        controller = self.get_value("controller")
        frame_cache = CacheList(5)
        text_cache = CacheList(1)

        def report_frames(c):
            if c.commands:
                frames = c.commands[0].frames

                text = {
                    (0, 0): "neutral",
                    (-1, 0): "left",
                    (1, 0): "right",
                    (1, 1): "down right",
                    (1, -1): "up right",
                    (0, 1): "down",
                    (0, -1): "up",
                    (-1, -1): "up left",
                    (-1, 1): "down left"
                }

                for f in frames:
                    if frame_cache:
                        if f[0] != frame_cache[-1]:
                            frame_cache.append(f[0])
                    else:
                        frame_cache.append(f[0])

                def get_line_changes(l):
                    last = None
                    out = []
                    for line in l:
                        if line != last:
                            last = line
                            out.append(line)

                    return out

                lines = [text[f[0]] for f in c.commands[0].frames]
                return get_line_changes(lines)
            else:
                return ""

        frame_reporter = tools.make_reporter_sprite(
            controller, report_frames
        )

        check_cache = CacheList(60)

        def report_commands(c):
            lines = []
            for command in c.commands:
                check_cache.append(command.active)
                line = "{}: {}".format(command.name, True in check_cache)
                lines.append(line)

            return lines

        command_reporter = tools.make_reporter_sprite(
            controller, report_commands
        )

        # def report_physics(p):
        #     vx, vy = p.velocity.get_values()
        #     ax, ay = p.acceleration.get_values()
        #     x, y = p.position
        #
        #     f_string = "{:>15}: {:> 04.3f}, {:> 04.3f}"
        #     text = [
        #         f_string.format("ACCELERATION", ax, ay),
        #         f_string.format("VELOCITY", vx, vy),
        #         "{:>15}: {}, {}".format("POSITION", x, y),
        #     ]
        #
        #     return text
        #
        # physics_reporter = tools.make_reporter_sprite(
        #     player, report_physics
        # )

        members = [[reporter, frame_reporter, command_reporter]]
        table = tools.ContainerSprite(
            "hud container", members,
            position=(25, 0), size=(750, 175),
            table_style="grid")

        table.style = {"align_h": "c", "align_v": "t"}
        table.add(self.hud_group)


class PauseMenu(DebugMenu):
    def __init__(self, **kwargs):
        super(PauseMenu, self).__init__(**kwargs)

        self.active = False

