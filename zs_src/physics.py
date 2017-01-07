from math import pi, cos, sin, atan2

from pygame import draw

from zs_constants.zs import FRAME_RATE
from zs_src.entities import Layer


class Vector:
    def __init__(self, name, i_hat, j_hat):
        self.name = name
        self.i_hat = i_hat
        self.j_hat = j_hat

    def __repr__(self):
        i = round(self.i_hat, 4)
        j = round(self.j_hat, 4)
        s = "{}: {}, {}".format(self.name, i, j)

        return s

    def round(self):
        pass
        # if abs(self.i_hat) < .001:
        #     self.i_hat = 0
        # if abs(self.j_hat) < .001:
        #     self.j_hat = 0

    def cap_values(self, max_i, max_j):
        i, j = self.get_values()

        positive = i > 0
        if abs(i) > max_i:
            i = max_i
            if not positive:
                i *= -1

        positive = j > 0
        if abs(j) > max_j:
            j = max_j
            if not positive:
                j *= -1

        self.i_hat = i
        self.j_hat = j

    def add(self, vector):
        c = self.complex + vector.complex
        self.i_hat = c.real
        self.j_hat = c.imag

    def multiply(self, vector):
        c = self.complex * vector.complex
        self.i_hat = c.real
        self.j_hat = c.imag

    def scale(self, scalar):
        self.i_hat *= scalar
        self.j_hat *= scalar

        return self

    def get_angle(self):
        i, j = self.get_values()
        angle = atan2(-j, i) / (2 * pi)

        if angle >= 0:
            theta = angle

        else:
            theta = 1 + angle

        return theta

    def rotate(self, theta):
        theta *= (2 * pi)
        i, j = cos(theta), sin(theta)

        self.multiply(Vector("rotation", i, -j))

        return self

    def apply_to_point(self, point):
        x, y = point
        x += round(self.i_hat)
        y += round(self.j_hat)

        return x, y

    def flip(self):
        self.rotate(.5)

    def get_copy(self, rotate=0, scale=0):
        v = Vector(self.name, self.i_hat, self.j_hat)

        if rotate:
            v.rotate(rotate)

        if scale:
            v.scale(scale)

        return v

    def get_values(self):
        return self.i_hat, self.j_hat

    @staticmethod
    def get_from_complex(c):
        i, j = c.real, c.imag

        return Vector("", i, j)

    @property
    def complex(self):
        return complex(self.i_hat, self.j_hat)

    @property
    def magnitude(self):
        return abs(self.complex)

    @staticmethod
    def sum_forces(*vectors):
        acceleration = sum(vector.complex for vector in vectors)

        vector = Vector.get_from_complex(acceleration)

        return vector


class PhysicsLayer(Layer):
    def __init__(self, g, *args, **kwargs):
        super(PhysicsLayer, self).__init__(*args, **kwargs)

        self.gravity = Vector("gravity", 0, g)
        self.friction = (.08, .03)
        self.collision_systems = []

    def set_gravity(self, g):
        self.gravity.j_hat = g

    def set_friction(self, coefficients):
        self.friction = coefficients

    def add_hitbox_layer(self, group):
        self.add_sub_layer(
            DrawHitboxLayer(group))

    def toggle_hitbox_layer(self):
        for layer in self.sub_layers:
            if "draw hitbox layer" in layer.name:
                layer.visible = not layer.visible

    def add_vector_layer(self, group):
        self.add_sub_layer(
            DrawVectorLayer(group))

    def toggle_vector_layer(self):
        for layer in self.sub_layers:
            if "draw vector layer" in layer.name:
                layer.visible = not layer.visible

    def get_draw_order(self):
        order = []
        for layer in self.sub_layers:
            if "draw hitbox layer" in layer.name:
                if layer.visible:
                    order.append(layer)

        for group in self.groups:
            order.append(group)

        for layer in self.sub_layers:
            if "draw vector layer" in layer.name:
                if layer.visible:
                    order.append(layer)

        return order

    @staticmethod
    def sprite_collision(sprite1, sprite2):
        return sprite1.collision_region.colliderect(sprite2.collision_region)

    @staticmethod
    def wall_collision(sprite1, wall):
        return wall.colliderect(sprite1)

    @staticmethod
    def group_perm_collision_check(
            group, collision_test, handle_collision):
        tested = []

        tests = 0
        for sprite in group:
            tested.append(sprite)
            check_against = [sprite if sprite not in tested else None for sprite in group]

            for other in check_against:
                if other:
                    tests += 1
                    if collision_test(sprite, other):
                        handle_collision(sprite, other)

    @staticmethod
    def sprite_group_collision_check(
            sprite, group, collision_test, handle_collision):
        for other in group:
            if sprite is not other:
                if collision_test(sprite, other):
                    handle_collision(sprite, other)

    @staticmethod
    def sprite_regions_collision_check(
            sprite, regions, collision_test, handle_collision):
        for region in regions:
            if collision_test(sprite, region):
                handle_collision(sprite, region)

    @staticmethod
    def group_regions_collision_check(
            group, regions, collision_test, handle_collision):
        for sprite in group:
            PhysicsLayer.sprite_regions_collision_check(
                sprite, regions, collision_test, handle_collision)

    def get_update_methods(self):
        um = super(PhysicsLayer, self).get_update_methods()

        return um + [
            self.apply_friction,
            self.apply_acceleration,
            self.apply_collisions,
            self.apply_velocity,
            self.apply_gravity
        ]

    def apply_gravity(self, dt):
        for group in self.groups:
            for sprite in group:
                if not sprite.is_grounded():
                    gravity = self.gravity.get_copy(scale=sprite.mass)
                    sprite.apply_force(gravity)

                else:
                    if sprite.velocity.j_hat < 0:
                        sprite.set_off_ground()

    def apply_velocity(self, dt):
        for group in self.groups:
            for sprite in group:
                sprite.apply_velocity()

    def apply_acceleration(self, dt):
        for group in self.groups:
            for sprite in group:
                sprite.apply_acceleration()

    def apply_friction(self, dt):
        for group in self.groups:
            for sprite in group:
                cof = self.friction
                if sprite.is_grounded():
                    sprite.apply_friction(cof[0])
                else:
                    sprite.apply_friction(cof[1])

    def apply_collisions(self, dt):
        for system in self.collision_systems:
            method, args = system
            method(*args)

    @staticmethod
    def handle_collision(sprite_a, sprite_b):
        r1 = sprite_a.collision_region
        x1, y1 = r1.center

        r2 = sprite_b.collision_region
        x2, y2 = r2.center

        dx = x1 - x2
        dy = y1 - y2

        elasticity = (sprite_a.elasticity + sprite_b.elasticity) / 2
        magnitude = (sprite_a.velocity.magnitude + sprite_b.velocity.magnitude) / 2

        push_out = Vector("collision", dx, dy).scale(.5).scale(1 - elasticity)
        push_out = push_out.scale(1 / FRAME_RATE).scale(magnitude)
        opposite = push_out.get_copy(rotate=.5)

        sprite_a.apply_force(push_out)
        sprite_b.apply_force(opposite)


class DrawVectorLayer(Layer):
    def __init__(self, group, **kwargs):
        super(DrawVectorLayer, self).__init__("draw vector layer", **kwargs)
        self.group = group
        self.visible = False

    def draw(self, screen):
        for sprite in self.group:
            x, y = sprite.collision_region.center
            dx, dy = sprite.velocity.get_values()
            dx *= 5
            dy *= 5
            dx += x
            dy += y
            draw.line(screen, (0, 255, 0), (x, y), (dx, dy), 5)

            dx, dy = sprite.acceleration.get_values()
            dx *= 50
            dy *= 50
            dx += x
            dy += y
            draw.line(screen, (0, 0, 255), (x, y), (dx, dy), 5)


class DrawHitboxLayer(Layer):
    def __init__(self, group, **kwargs):
        super(DrawHitboxLayer, self).__init__("draw hitbox layer", **kwargs)
        self.group = group
        self.visible = False

    def draw(self, screen):
        for sprite in self.group:
            r = sprite.collision_region

            if hasattr(r, "radius"):
                draw.circle(screen, (255, 0, 0), r.center, r.radius, 1)

            else:
                draw.rect(screen, (255, 0, 0), r, 1)

