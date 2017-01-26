from collections import OrderedDict

import pygame

from zs_constants.paths import TILESETS
from zs_constants.sprite_demo import GRAVITY, COF
from zs_src.camera import CameraLayer, ParallaxBgLayer
from zs_src.context import ContextManager, ContextLayer, RegionLayer
from zs_src.controller import Step, Command
from zs_src.graphics import Graphics
from zs_src.physics import PhysicsLayer
from zs_src.regions import Wall, Region
from zs_src.resource_library import get_resources
from zs_src.sprites import CharacterSprite
from zs_src.state_machines import AnimationMachine
from zs_utils.debug_utils import PauseMenu, DebugLayer


class SpriteDemoContext(ContextManager):
    def set_up_bg_layers(self, layer):
        trees = "smalltree", "midtree", "bigtree"
        get = ParallaxBgLayer.get_bg_image

        def get_scale(name):
            full_w = get("bigtree.gif").get_size()[0]
            w = get(name).get_size()[0]

            return w / full_w

        bg_layers = []
        for tree in trees:
            scale = get_scale(tree + ".gif")
            offset = 150
            depth = 60
            position = 0, (((depth * scale) + offset) * scale) + offset

            bg_layers.append(ParallaxBgLayer(
                get(tree + ".gif"), scale,
                buffer=(50, 0), wrap=(True, False),
                position=position)
            )

        super(SpriteDemoContext, self).set_up_bg_layers(
            layer, *bg_layers)

    def set_up_layer_dict(self):
        group = self.environment.main_group

        ld = OrderedDict()
        ld["Camera Layer"] = {
                "layer": CameraLayer("Camera Layer"),
                "pause": True,
                "frame_advance": True,
                "bg_layers": (True,),
                "camera": (True,)
            }
        ld["Walls Layer"] = {
                "layer": RegionLayer("Walls Layer"),
                "regions": (True,),
                "parent_layer": "Camera Layer"
            }
        ld["Sprite Layer"] = {
                "layer": PhysicsLayer("Sprite Layer", GRAVITY, COF),
                "controllers": True,
                "parent_layer": "Camera Layer",
                "collisions": (True,),
                "groups": (group,)
            }
        ld["Debug Layer"] = {
                "layer": DebugLayer(self.environment),
                "huds": (True,)
            }
        ld["Pause Menu"] = {
                "layer": PauseMenu(self.environment)
            }

        return ld

    def set_up_sprite_dict(self):
        group = self.environment.main_group

        d = {
            "player": {
                "load": lambda **kwargs: DemoSprite("player", **kwargs),
                "controller": 0,
                "graphics": "squirrel",
                "animation_machine": SpriteDemoMachine,
                "layer": "Sprite Layer",
                "group": group},
            "yoshi": {
                "load": lambda **kwargs: DemoSprite("yoshi", **kwargs),
                "graphics": "yoshi",
                "animation_machine": SpriteDemoMachine,
                "layer": "Sprite Layer",
                "group": group},
            "squirrel2": {
                "load": lambda **kwargs: DemoSprite("squirrel2", **kwargs),
                "controller": 2,
                "graphics": "squirrel",
                "sprite_sheet": "squirrel2",
                "animation_machine": SpriteDemoMachine,
                "layer": "Sprite Layer",
                "group": group}
        }

        return d

    def set_up_regions(self, layer, *args):
        group = RegionLayer.make_group()

        plats = [
            (5, .01, (0, 580), True),
            (2, .08125, (1200, 480), True),
            (1, .9, (1850, 120), True),
            (3, .105, (2180, 150), True),
            (8, .8175, (3000, -150), True),

        ]

        for args in plats:
            length, angle, origin, ground = args[0:4]
            if len(args) == 5:
                friction = args[4]
            else:
                friction = False
            plat = TreePlat(length, angle, origin,
                            ground=ground,
                            friction=friction)
            plat.add(group)

        super(SpriteDemoContext, self).set_up_regions(layer, group)

    def set_up_collisions(self, layer, *args):
        group = self.environment.main_group
        walls_layer = self.get_layer("Walls Layer")

        # SPRITE COLLISION SYSTEM
        collision_systems = walls_layer.get_collision_system_list(
            group, Wall.sprite_collision, Wall.handle_collision_smooth)
        collision_systems.append(
            lambda: PhysicsLayer.group_perm_collision_check(
                group, PhysicsLayer.sprite_collision,
                PhysicsLayer.handle_collision)
        )

        super(SpriteDemoContext, self).set_up_collisions(
            layer, *collision_systems)

    def set_up_command_dict(self):
        press_left = Step("press_left",
                          [lambda f: f[0][0] == -1])
        press_right = Step("press_right",
                           [lambda f: f[0][0] == 1])
        neutral = Step("neutral dpad",
                       [lambda f: f[0] == (0, 0)])
        press_up = Step("press_up",
                        [lambda f: f[0][1] == -1])

        window = 20
        commands = {
            "double tap right": Command(
                "double tap right",
                [neutral, press_right, neutral, press_right],
                ["dpad"], window),
            "double tap up": Command(
                "double tap up",
                [neutral, press_up, neutral, press_up],
                ["dpad"], window),
            "double tap left": Command(
                "double tap left",
                [neutral, press_left, neutral, press_left],
                ["dpad"], window)
        }

        return commands

    def set_up_huds(self, layer, *args):
        player = self.get_value("player")

        player_huds = [
            ("Acceleration",
             lambda: player.acceleration.get_value(),
             "average", 2),
            ("Velocity",
             lambda: player.velocity.get_value(),
             "average", 2),
            ("Position",
             lambda: player.position),
            ("Grounded",
             lambda: player.is_grounded())
        ]
        d = {
            "Player": player_huds
        }

        super(SpriteDemoContext, self).set_up_huds(layer, d)

    def set_up_camera(self, layer, *args):
        # super(SpriteDemoContext, self).set_up_camera(*args)
        camera_layer = self.get_layer("Camera Layer")

        player = self.get_value("player")

        w1 = ("slow_push", [(300, 350), (300, 150), (0, 0)])
        w2 = ("fast_push", [(400, 500), (550, 0), (0, -100)])

        # BUILD CAMERA WINDOWS
        camera_layer.set_up_windows(w1, w2)

        # TRACK CAMERA FUNCTION
        camera_layer.set_sprite_window_track(
            player, "slow_push", .08)
        camera_layer.set_sprite_window_track(
            player, "fast_push", .5)
        camera_layer.track_window_to_sprite_heading(
            player, "slow_push", 1.5)
        camera_layer.track_window_to_sprite_heading(
            player, "fast_push", .5)

        # TRACK ANCHOR FUNCTION
        camera_layer.set_anchor_track_function(
            lambda: player.get_ground_anchor(),
            lambda: player.is_grounded(), .05
        )

        camera_layer.set_anchor(450)
        a_min = 450
        a_max = 550

        def get_position():
            span = a_max - a_min
            x, y = camera_layer.camera.position
            r = y / 600
            value = r * span

            return value + 450

        camera_layer.set_anchor_position_function(
            get_position, (a_min, a_max)
        )

        camera_layer.set_camera_bounds_edge(900)

        def get_scale():
            camera = camera_layer.camera
            y = camera.focus_point[1]
            scale = round(
                1 + ((y + 500) / 900), 3)

            return scale

        camera_layer.set_scale_tracking_function(
            get_scale, (1, 2)
        )


class SpriteDemo(ContextLayer):
    def __init__(self, **kwargs):
        super(SpriteDemo, self).__init__(
            "Sprite Demo", SpriteDemoContext, **kwargs)

    def populate(self):
        # pass
        # # REPLACE WITH DATA FROM CONFIG VALUE FILE LOOKUP
        spawn = self.get_value("spawn")

        # spawn("yoshi", position=(500, 300))
        # spawn("yoshi", position=(200, 300))

        player = spawn("player", position=(450, 100))
        self.set_value("player", player)
        # self.sprite_layer.toggle_vector_layer()
        # self.sprite_layer.toggle_hitbox_layer()
        # self.debug_layer.visible = True
        # self.set_value("frame_advance", True)


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
        vy = self.sprite.velocity.j_hat
        ay = self.sprite.acceleration.j_hat

        apex = vy >= 0 and ay >= 0

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

        base_jump = 3.5
        base_speed = 3
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
                    self.set_off_ground()
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
                "pivot": -.1
            }

            if state in ("jump_up", "jump_apex", "jump_fall"):
                dx = movement[state] * x
            elif state in ("jump_squat", "jump_land"):
                dx = self.get_ground_speed() * self.friction
            elif state == "walk":
                dx = (movement["walk"] * x)

                if self.velocity.j_hat < 0 and frame_number == 0:
                    slide = self.get_slide_speed()
                    dx -= slide
            elif state == "idle" or "crouch" in state:
                dx = 0

                if self.ground.get_angle() != 0:
                    if abs(self.get_ground_speed()) < 1:
                        self.velocity.scale_in_direction(
                            self.ground.get_angle(), .1
                        )
            else:
                dx = movement[state] * self.direction[0] * self.friction * base_speed
                if state == "dash":
                    if frame_number < 5:
                        self.velocity.scale_in_direction(
                            self.ground.get_angle(), 0
                        )
                    if frame_number == 5:
                        dx *= 5

            move = self.get_ground_vector(dx)
            self.apply_force(move)


class PlatformGraphics(Graphics):
    def __init__(self, entity):
        super(PlatformGraphics, self).__init__(entity)

    def reset_image(self):
        self.set_default_image(
            self.get_platform_image())

    @staticmethod
    def get_px_width(length):
        start, mid, end = PlatformGraphics.get_tree_tiles()
        sw, sh = start.get_size()
        mw, mh = mid.get_size()
        ew, eh = end.get_size()

        return sw + (mw * (length - 1)) + ew

    @staticmethod
    def get_tree_tiles():
        start, mid, end = (
            PlatformGraphics.load_image(
                TILESETS, "treestart.gif"),
            PlatformGraphics.load_image(
                TILESETS, "treemid.gif"),
            PlatformGraphics.load_image(
                TILESETS, "treeend.gif")
        )

        return start, mid, end

    def get_platform_image(self):
        start, mid, end = self.get_tree_tiles()

        angle = self.entity.get_angle()

        sw, sh = start.get_size()
        mw, mh = mid.get_size()
        ew, eh = end.get_size()

        length = self.entity.plat_length
        width = self.get_px_width(length)
        height = sh

        surface = pygame.Surface((width, height))
        surface.fill((255, 255, 255))
        surface.blit(start, (0, 0))
        for i in range(length - 1):
            surface.blit(mid, (sw + (i * mw), 0))
        surface.blit(end, (width - ew, 0))

        surface = pygame.transform.rotate(surface, angle * 360)
        surface.set_colorkey(
            surface.get_at((0, 0))
        )

        return surface


class TreePlat(Region):
    def __init__(self, length, angle=0.0, origin=(0, 0), **kwargs):
        width = PlatformGraphics.get_px_width(length)
        ox, oy = origin
        wall = Wall(origin, (ox + width, oy), **kwargs)
        wall.rotate(angle)

        self.plat_length = length
        self.get_angle = wall.get_angle
        self.normal = wall.normal

        super(TreePlat, self).__init__(
            "platform")
        self.graphics = PlatformGraphics(self)

        self.walls = [wall]

    @property
    def position(self):
        image = self.graphics.get_image()
        r = pygame.Rect((0, 0), image.get_size())

        wall = self.walls[0]
        sx, sy = wall.origin
        ex, ey = wall.end_point

        mx = (sx + ex) / 2
        my = (sy + ey) / 2
        r.center = mx, my

        return r.topleft

    @position.setter
    def position(self, value):
        pass

    def update(self, dt):
        super(TreePlat, self).update(dt)
