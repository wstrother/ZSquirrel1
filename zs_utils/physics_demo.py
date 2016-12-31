import pygame

from zs_constants.zs import SCREEN_SIZE
from zs_src.animations import AnimationGraphics
from zs_src.entities import Layer
from zs_src.gui import TextSprite
from zs_src.physics import PhysicsSprite, PhysicsLayer, Vector, DrawVectorLayer, DrawHitboxLayer


class YoshiAnimation(AnimationGraphics):
    def __init__(self, *args):
        yoshi_sheet = pygame.image.load("resources/animations/yoshi.gif")
        super(YoshiAnimation, self).__init__(yoshi_sheet, *args)

        lines = "100 100 5\n0 0 50 60 20 20\n1 0\n2 0\n1 0\n0 0\n0 0\n1 0\n2 0\n3 0\n2 0"
        lines = lines.split("\n")
        self.set_animation("default", self.get_stream(lines))


class TestSprite(PhysicsSprite):
    def __init__(self, name, **kwargs):
        super(TestSprite, self).__init__(name, **kwargs)
        self.graphics = YoshiAnimation(self)
        self.set_rect_size_to_image()
        self.hit_box = pygame.Rect((0, 0), (50, 60))
        self.hit_box_offsets = 20, 20

    @property
    def collision_region(self):
        dx, dy = self.hit_box_offsets
        x, y = self.rect.topleft
        x += dx
        y += dy
        self.hit_box.topleft = x, y

        return self.hit_box


class Reporter(TextSprite):
    def __init__(self, sprite, **kwargs):
        super(Reporter, self).__init__("", **kwargs)
        self.report = sprite

    def update(self, dt):
        super(Reporter, self).update(dt)
        r = self.report

        vx, vy = r.velocity.get_values()
        vx = round(vx, 2)
        vy = round(vy, 2)
        va = round(r.velocity.get_angle(), 2)
        velocity = "V: {:8}, {:8}\t angle: {:8}".format(
            vx, vy, va)

        ax, ay = r.acceleration.get_values()
        ax = round(ax, 2)
        ay = round(ay, 2)
        aa = round(r.acceleration.get_angle(), 2)
        acceleration = "A: {:8}, {:8}\t angle: {:8}".format(
            ax, ay, aa)

        px, py = r.position
        position = "P: {:8}, {:8}".format(px, py)

        self.change_text([velocity, acceleration, position])


class PhysicsDemo(PhysicsLayer):
    def __init__(self, *args, **kwargs):
        g = 1

        super(PhysicsDemo, self).__init__(g, "test layer", *args, **kwargs)
        self.hud = Layer("hud layer")
        self.add_sub_layer(self.hud)
        self.hud.groups.append(self.make_group())
        self.hud_group = self.hud.groups[0]

        self.main_sprite = None

    def populate(self):
        g = self.make_group()
        self.groups.append(g)

        for x in range(18):
            px = x * 175
            py = 300
            mass = 1 + (x / 4)
            sprite = TestSprite("rabbit1", mass=mass, position=(px, py))
            sprite.add(g)

        sprite = TestSprite("rabbit2", position=(400, 400))
        sprite.add(g)

        reporter = Reporter(sprite)
        reporter.add(self.hud_group)
        self.main_sprite = sprite

        self.add_sub_layer(DrawHitboxLayer(g))
        self.add_sub_layer(DrawVectorLayer(g))

    def handle_controller(self):
        cont = self.controller

        if 0 < cont.devices["a"].held < 8:
            for group in self.groups:
                for sprite in group:
                    if sprite is self.main_sprite:
                        sprite.add_force(Vector("jump", 0, -2.5))

        if 0 < cont.devices["b"].held < 8:
            for group in self.groups:
                for sprite in group:
                    if sprite is self.main_sprite:
                        sprite.velocity.scale(0)
                        sprite.acceleration.rotate(.5)
                    else:
                        sprite.add_force(Vector("jump", 0, -4))

        dpad = cont.devices["dpad"]
        x, y = dpad.get_direction_string()
        scale = 1.2

        vector = Vector("movement", x * scale, y * scale)
        self.main_sprite.add_force(vector)

    def apply_floor(self):
        for group in self.groups:
            for sprite in group:
                x, y = sprite.collision_region.topleft
                w, h = sprite.collision_region.size
                sx, sy = sprite.position
                dx = x - sx
                dy = y - sy

                if x > SCREEN_SIZE[0]:
                    x = 0

                if x < 0:
                    x = SCREEN_SIZE[0]

                if y > SCREEN_SIZE[1] - h:
                    y = SCREEN_SIZE[1] - h

                sx = x - dx
                sy = y - dy
                sprite.position = sx, sy

    def apply_collisions(self, dt):
        self.apply_floor()

        self.group_perm_collision_check(
            self.groups[0], self.sprite_collision,
            self.main_sprite.handle_collision)

        self.apply_floor()



