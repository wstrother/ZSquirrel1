from zs_src.entities import Layer, ZsSprite
from zs_constants.zs import SCREEN_SIZE
from math import pi, cos, sin, atan2
from pygame import draw


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


class Velocity(Vector):
    def integrate_acceleration(self, *vectors):
        acceleration = sum(vector.complex for vector in vectors)

        vector = self.get_from_complex(acceleration)
        self.add(vector)
        return vector


class PhysicsLayer(Layer):
    def __init__(self, g, *args, **kwargs):
        super(PhysicsLayer, self).__init__(*args, **kwargs)

        self.gravity = Vector("gravity", 0, g)
        self.friction = (.08, .03)

    def get_draw_order(self):
        order = []
        for layer in self.sub_layers:
            if layer.name == "draw hitbox layer":
                order.append(layer)

        for group in self.groups:
            order.append(group)

        for layer in self.sub_layers:
            if layer.name != "draw hitbox layer":
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

        return um + [self.apply_acceleration,
                     self.apply_friction,
                     self.apply_velocity,
                     self.apply_collisions,
                     self.apply_gravity]

    def apply_gravity(self, dt):
        for group in self.groups:
            for sprite in group:
                if not sprite.grounded:
                    gravity = self.gravity.get_copy(scale=sprite.mass)
                    sprite.add_force(gravity)

                else:
                    sprite.velocity.j_hat = 0

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
                sprite.apply_friction(self.friction)

    def apply_collisions(self, dt):
        pass


class DrawVectorLayer(Layer):
    def __init__(self, group, **kwargs):
        super(DrawVectorLayer, self).__init__("draw vector layer", **kwargs)
        self.group = group

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

    def draw(self, screen):
        for sprite in self.group:
            r = sprite.collision_region

            if hasattr(r, "radius"):
                draw.circle(screen, (255, 0, 0), r.center, r.radius, 1)

            else:
                draw.rect(screen, (255, 0, 0), r, 1)


class PhysicsSprite(ZsSprite):
    def __init__(self, *args, mass=1, **kwargs):
        super(PhysicsSprite, self).__init__(*args, **kwargs)

        self.forces = []
        self.acceleration = Vector("acceleration", 0, 0)
        self.velocity = Velocity(self.name + " velocity", 0, 0)
        self.max_i = 20
        self.max_j = 20

        self.mass = mass
        self.elasticity = .1

    @property
    def collision_region(self):
        return self.rect

    @property
    def grounded(self):
        r = self.collision_region
        y = r.top + r.height
        grounded = y >= SCREEN_SIZE[1]

        return grounded

    def add_force(self, vector):
        self.forces.append(vector)

    def apply_acceleration(self):
        self.acceleration = self.velocity.integrate_acceleration(*self.forces)
        self.forces = []

    def apply_velocity(self):
        if self.max_i and self.max_j:
            self.velocity.cap_values(self.max_i, self.max_j)

        scalar = 1 / self.mass
        movement = self.velocity.get_copy(scale=scalar)
        self.position = movement.apply_to_point(self.position)

    def apply_friction(self, coefficients):
        ground_cf, air_cf = coefficients
        i, j = self.velocity.get_values()

        j_cf = air_cf
        if not self.grounded:
            i_cf = air_cf
        else:
            i_cf = ground_cf

        i_value = (i_cf * i) * -1
        j_value = (j_cf * j) * -1
        friction = Vector("friction", i_value, j_value)

        self.velocity.add(friction)

    @staticmethod
    def handle_collision(self, sprite):
        r1 = self.collision_region
        x1, y1 = r1.center

        r2 = sprite.collision_region
        x2, y2 = r2.center

        dx = 0
        dy = 0

        # r2 above r1
        above = r2.bottom > r1.top and y2 < y1
        if above:
            # print("above")
            dy = r2.bottom - r1.top

        # r2 below r1
        below = r2.top < r1.bottom and y2 > y1
        if below:
            # print("below")
            dy = -1 * (r1.bottom - r2.top)

        # r2 left of r1
        left = r2.right > r1.left and x2 < x1
        if left:
            # print("left")
            dx = r2.right - r1.left

        # r2 right of r1
        right = r2.left < r1.right and x2 > x1
        if right:
            # print("right")
            dx = -1 * (r1.right - r2.left)

        elasticity = (self.elasticity + sprite.elasticity) / 2
        push_out = Vector("collision", dx, dy).scale(.5).scale(1 - elasticity)
        # theta = push_out.get_angle()

        # self.position = push_out.apply_to_point(self.position)
        # opposite = push_out.get_copy(rotate=.5)
        # sprite.position = opposite.apply_to_point(sprite.position)

        opposite = push_out.get_copy(rotate=.5)

        self.add_force(push_out)
        sprite.add_force(opposite)


