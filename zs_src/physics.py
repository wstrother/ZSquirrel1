from math import pi, cos, sin, atan2

from pygame import draw

from zs_constants.zs import FRAME_RATE
from zs_src.entities import Layer


class Vector:
    DRAW_WIDTH = 5

    def __init__(self, name, i_hat, j_hat):
        self.name = name
        self.i_hat = i_hat
        self.j_hat = j_hat

    def __repr__(self):
        i = round(self.i_hat, 4)
        j = round(self.j_hat, 4)
        a = round(self.get_angle(), 3)
        s = "{}: {}, {} angle: {}".format(self.name, i, j, a)

        return s

    def round(self):
        if abs(self.i_hat) < .001:
            self.i_hat = 0
        if abs(self.j_hat) < .001:
            self.j_hat = 0

    def cap_values(self, max_i, max_j):
        i, j = self.get_value()

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

    def scale_to(self, vector):
        m = vector.magnitude
        r = m / self.magnitude

        self.scale(r)

    def get_angle(self):
        i, j = self.get_value()
        angle = atan2(-j, i) / (2 * pi)

        if angle >= 0:
            theta = angle

        else:
            theta = 1 + angle

        return theta

    def set_angle(self, angle):
        theta = self.get_angle()
        delta = angle - theta
        self.rotate(delta)

    def rotate(self, theta):
        theta *= (2 * pi)
        i, j = cos(theta), sin(theta)

        self.multiply(Vector("rotation", i, -j))
        # self.round()

        return self

    def rotate_to(self, vector, offset=0.0):
        theta = vector.get_angle() + offset
        self.set_angle(theta)

        return self

    def flip(self):
        self.rotate(.5)

    def check_orientation(self, vector):
        t1, t2 = self.get_angle(), vector.get_angle()

        def compare_angles(a1, a2):
            top = a1 + .25
            bottom = a1 - .25

            return bottom < a2 < top

        if .25 <= t1 < .75:
            return compare_angles(t1, t2)

        elif t1 < .25:
            return compare_angles(
                t1 + .25, (t2 + .25) % 1)

        elif .75 <= t1:
            return compare_angles(
                t1 - .25, (t2 - .25) % 1)

    def apply_to_point(self, point):
        x, y = point
        x += self.i_hat
        y += self.j_hat

        return x, y

    def get_copy(self, rotate=0.0, scale=0):
        v = Vector(self.name, self.i_hat, self.j_hat)

        if rotate:
            v.rotate(rotate)

        if scale:
            v.scale(scale)

        return v

    def set_value(self, value):
        self.i_hat = value[0]
        self.j_hat = value[1]

    def get_value(self):
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

    def get_y_intercept(self, offset):
        if self.i_hat == 0:
            return False

        if self.j_hat == 0:
            return offset[1]

        slope = self.j_hat / self.i_hat
        x1, y1 = offset
        c = y1 - (slope * x1)
        y0 = 0 - c

        return -1 * y0

    def draw(self, screen, color, offset=(0, 0)):
        x, y = offset
        dx, dy = self.get_value()
        dx += x
        dy += y
        draw.line(screen, color,
                  (x, y), (dx, dy),
                  self.DRAW_WIDTH)

        draw.circle(screen, color,
                    (int(dx), int(dy)), self.DRAW_WIDTH)


class Wall(Vector):
    NORMAL_DRAW_SCALE = Vector.DRAW_WIDTH * 2

    def __init__(self, start, finish, ground=False, friction=0.0):
        i_hat, j_hat = finish
        i_hat -= start[0]
        j_hat -= start[1]
        super(Wall, self).__init__("wall", i_hat, j_hat)

        self.origin = start
        self._normal = Vector("normal", 1, 0)

        self.friction = friction
        self.ground = ground
        self.sprite_collide_offset = False

    def __repr__(self):
        return "Wall with angle {:.3f} at {}".format(
            self.get_angle(), self.origin)

    @property
    def normal(self):
        self._normal.rotate_to(self, .25)

        return self._normal

    @property
    def end_point(self):
        return self.apply_to_point(self.origin)

    def axis_collision(self, offset, vector):
        dx = offset[0] - self.origin[0]
        dy = offset[1] - self.origin[1]

        delta = .75 - self.get_angle()
        translated_vector = vector.get_copy(
            rotate=delta)

        new_offset = Vector(
            "new offset", dx, dy).rotate(
            delta).get_value()

        y_intercept = translated_vector.get_y_intercept(
            new_offset)

        if y_intercept is False:
            return False

        else:
            point = Vector(
                "axis intersection", 0,
                y_intercept).rotate(
                -1 * delta)

            return point.apply_to_point(self.origin)

    def vector_collision(self, offset, vector):
        collision = self.axis_collision(offset, vector)

        if not collision:
            return False

        else:
            def point_in_bounds(point, start, finish):
                x, y = point
                sx, sy = start
                fx, fy = finish

                if fx > sx:
                    x_bound = sx - 1 <= x <= fx + 1
                else:
                    x_bound = sx + 1 >= x >= fx - 1
                if fy > sy:
                    y_bound = sy - 1 <= y <= fy + 1
                else:
                    y_bound = sy + 1 >= y >= fy - 1

                return x_bound and y_bound

            w_bound = point_in_bounds(
                collision, self.origin, self.end_point
            )
            v_bound = point_in_bounds(
                collision, offset, vector.apply_to_point(offset)
            )
            # args = [(round(x[0]), round(x[1])) for x in (collision, offset, vector.apply_to_point(offset))]
            # print(args)

            if not w_bound or not v_bound:
                # print(w_bound, v_bound)
                return False

            else:
                return collision

    def get_sprite_collision_points(self, sprite):
        angle = self.normal.get_copy(
            rotate=.5).get_angle()

        near = sprite.get_collision_edge_point(
            angle)

        far = sprite.collision_point

        return near, far

    def sprite_collision(self, sprite):
        v = sprite.velocity

        if not v.check_orientation(
                self.normal.get_copy(rotate=.5)):
            return False

        else:
            # print("testing " + str(self))
            near, far = self.get_sprite_collision_points(
                sprite)
            dx = near[0] - far[0]
            dy = near[1] - far[1]
            skeleton = Vector("skeleton", dx, dy)

            near_collision = self.vector_collision(
                near, v)
            far_collision = self.vector_collision(
                far, skeleton)

            if near_collision:
                self.sprite_collide_offset = False
                return near_collision

            else:
                self.sprite_collide_offset = True
                return far_collision

    @staticmethod
    def handle_collision_smooth(sprite, wall):
        # print("{} handling collision".format(wall))

        near, far = wall.get_sprite_collision_points(sprite)
        x, y = sprite.velocity.apply_to_point(
            near)
        ix, iy = wall.axis_collision(
            (x, y), wall.normal)
        dx = ix - x
        dy = iy - y
        adjust = Vector("velocity adjustment", dx, dy)
        sprite.move(adjust.get_value())
        # print("applying {} to {}".format(adjust, sprite))

        if wall.sprite_collide_offset:
            dx = near[0] - far[0]
            dy = near[1] - far[1]
            adjust.i_hat += dx
            adjust.j_hat += dy
            print(dx, dy, adjust)
        sprite.apply_force(adjust)

        if wall.ground:
            sprite.set_on_ground(wall)

    def draw(self, screen, color, offset=(0, 0)):
        super(Wall, self).draw(
            screen, color, offset=self.origin)

        start = self.origin

        i = 4
        for x in range(i):
            segment = (self.i_hat / i), (self.j_hat / i)
            x_offset = segment[0] * x
            y_offset = segment[1] * x

            xn = x_offset + (segment[0] / 2)
            yn = y_offset + (segment[1] / 2)
            xn += start[0]
            yn += start[1]

            start_n = xn, yn
            normal = self.normal.get_copy(scale=self.NORMAL_DRAW_SCALE)
            normal.draw(screen, color, offset=start_n)


class PhysicsLayer(Layer):
    def __init__(self, g, cof, *args, **kwargs):
        super(PhysicsLayer, self).__init__(*args, **kwargs)

        self.gravity = Vector("gravity", 0, g)
        self.friction = cof
        self.collision_systems = []

        self.interface = {
            "gravity": g,
            "friction": cof,
            "toggle hitbox layer": self.toggle_hitbox_layer,
            "toggle vector layer": self.toggle_vector_layer
        }

    def set_gravity(self, g):
        self.gravity.j_hat = g

    def set_friction(self, coefficients):
        self.friction = coefficients

    def add_wall_layer(self, walls):
        self.add_sub_layer(
            DrawWallsLayer(walls))

    def toggle_wall_layer(self):
        for layer in self.sub_layers:
            if "draw walls layer" in layer.name:
                layer.visible = not layer.visible

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
            if "draw walls layer" in layer.name:
                if layer.visible:
                    order.append(layer)

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
    def sprite_collision(sprite_a, sprite_b):
        r1 = sprite_a.collision_region.copy()
        r1.topleft = sprite_a.position
        r2 = sprite_b.collision_region.copy()
        r2.topleft = sprite_b.position

        return r1.colliderect(r2)

    @staticmethod
    def wall_collision(sprite, wall):
        return wall.sprite_collision(sprite)

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
        # if sprite.velocity.j_hat < 0:
        sprite.set_off_ground()

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
                # if not sprite.is_grounded():
                gravity = self.gravity.get_copy(scale=sprite.mass)
                sprite.apply_force(gravity)

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
                    friction = cof[0] + sprite.ground.friction
                    sprite.apply_friction(friction)
                else:
                    sprite.apply_friction(cof[1])

    def apply_collisions(self, dt):
        for system in self.collision_systems:
            method, args = system
            method(*args)

    @staticmethod
    def handle_collision(sprite_a, sprite_b):
        r1 = sprite_a.collision_region
        x1, y1 = sprite_a.collision_point

        r2 = sprite_b.collision_region
        x2, y2 = sprite_b.collision_point

        left = x1 < x2
        right = x1 > x2
        above = y1 < y2
        below = y1 > y2

        dx = x1 - x2
        dy = y1 - y2
        if left or right:
            x_span = (r2.width + r1.width) / 2
            x_ratio = abs(dx) / x_span
            dx *= 1 / x_ratio
        if above or below:
            y_span = (r2.height + r1.height) / 2
            y_ratio = abs(dy) / y_span
            dy *= 1 / y_ratio

        elasticity = (sprite_a.elasticity + sprite_b.elasticity) / 2
        magnitude = (sprite_a.velocity.magnitude + sprite_b.velocity.magnitude) / 2

        push_out = Vector("collision", dx, dy).scale(.5).scale(1 - elasticity)
        push_out = push_out.scale(1 / FRAME_RATE).scale(magnitude)
        opposite = push_out.get_copy(rotate=.5)

        dampener = elasticity * 2.5
        if left:
            if sprite_a.velocity.i_hat > 0:
                sprite_a.velocity.i_hat *= dampener
            if sprite_b.velocity.i_hat < 0:
                sprite_b.velocity.i_hat *= dampener
        if right:
            if sprite_a.velocity.i_hat < 0:
                sprite_a.velocity.i_hat *= dampener
            if sprite_b.velocity.i_hat > 0:
                sprite_b.velocity.i_hat *= dampener
        if above:
            if sprite_a.velocity.j_hat > 0:
                sprite_a.velocity.j_hat *= dampener
            if sprite_b.velocity.j_hat < 0:
                sprite_b.velocity.j_hat *= dampener
        if below:
            if sprite_a.velocity.j_hat < 0:
                sprite_a.velocity.j_hat *= dampener
            if sprite_b.velocity.j_hat > 0:
                sprite_b.velocity.j_hat *= dampener

        sprite_a.apply_force(push_out)
        sprite_b.apply_force(opposite)


class DrawWallsLayer(Layer):
    WALL_COLOR = (255, 255, 0)

    def __init__(self, walls, **kwargs):
        super(DrawWallsLayer, self).__init__("draw walls layer", **kwargs)
        self.walls = walls
        self.visible = False

    def draw(self, screen):
        for wall in self.walls:
            wall.draw(screen, self.WALL_COLOR)


class DrawVectorLayer(Layer):
    VELOCITY_COLOR = (0, 255, 0)
    VELOCITY_SCALE = 6
    ACCELERATION_COLOR = (0, 0, 255)
    ACCELERATION_SCALE = 60

    def __init__(self, group, **kwargs):
        super(DrawVectorLayer, self).__init__("draw vector layer", **kwargs)
        self.group = group
        self.visible = False

    def draw(self, screen):
        for sprite in self.group:
            x, y = sprite.collision_point
            # dx, dy = sprite.get_collision_edge_point(.75)
            # dx -= x
            # dy -= y
            # skeleton = Vector("skeleton", dx, dy)
            # skeleton.draw(screen, self.VELOCITY_COLOR,
            #               offset=(x, y))
            sprite.velocity.get_copy(
                scale=self.VELOCITY_SCALE).draw(
                    screen, self.VELOCITY_COLOR,
                    offset=(x, y))

            sprite.acceleration.get_copy(
                scale=self.ACCELERATION_SCALE).draw(
                    screen, self.ACCELERATION_COLOR,
                    offset=(x, y))


class DrawHitboxLayer(Layer):
    def __init__(self, group, **kwargs):
        super(DrawHitboxLayer, self).__init__("draw hitbox layer", **kwargs)
        self.group = group
        self.visible = False

    def draw(self, screen):
        for sprite in self.group:
            sprite.draw_collision_region(screen)


class PhysicsInterface:
    Vector = Vector

    def __init__(self, mass, elasticity):
        self.mass = mass
        self.elasticity = elasticity
        self.friction = 0.0

        self.acceleration = Vector("acceleration", 0, 0)
        self.velocity = Vector("velocity", 0, 0)
        self.forces = []

        self.ground = None
        self._last_collision_heading = "right"

        self.interface = {
            "mass": self.mass,
            "elasticity": self.elasticity
        }

    def set_mass(self, mass):
        self.mass = mass

    def set_elasticity(self, elasticity):
        self.elasticity = elasticity

    @property
    def collision_region(self):
        if self.graphics:
            return self.graphics.get_hitbox()

        else:
            r = self.rect.copy()
            r.topleft = 0, 0

        return r

    @property
    def collision_point(self):
        x, y = self.position
        r = self.collision_region
        x += (r.width / 2) + r.x
        y += (r.width / 2) + r.y

        return x, y

    @property
    def collision_lead_point(self):
        return self.get_collision_edge_point(
            self.velocity.get_angle())

    @property
    def collision_far_point(self):
        angle = self.velocity.get_copy(
            rotate=.5).get_angle()

        return self.get_collision_edge_point(
            angle)

    def get_collision_edge_point(self, angle):
        angles = [(x / 8) + .0625 for x in range(8)]

        top_right = angles[0] <= angle < angles[1]
        top = angles[1] <= angle < angles[2]
        top_left = angles[2] <= angle < angles[3]
        left = angles[3] <= angle < angles[4]
        bottom_left = angles[4] <= angle < angles[5]
        bottom = angles[5] <= angle < angles[6]
        bottom_right = angles[6] <= angle < angles[7]
        right = angle < angles[0] or angle > angles[7]

        x, y = self.position
        r = self.collision_region
        x += r.x
        y += r.y

        if top_right:
            x += r.width

        if top:
            x += r.width / 2

        if left:
            y += r.height / 2

        if bottom_left:
            y += r.height

        if bottom:
            x += r.width / 2
            y += r.height

        if bottom_right:
            x += r.width
            y += r.height

        if right:
            x += r.width
            y += r.height / 2

        if not any([right, top_right, top,
                    top_left, left, bottom_left,
                    bottom, bottom_right]):
            x += r.width / 2
            y += r.height / 2

        return x, y

    def draw_collision_region(self, screen):
        r = self.collision_region
        x, y = self.position
        r.x += x
        r.y += y

        draw.rect(screen, (255, 0, 0), r, 1)

    def is_grounded(self):
        return bool(self.ground)

    def set_on_ground(self, ground):
        self.ground = ground

    def set_off_ground(self):
        self.ground = None

    def apply_force(self, vector):
        # print(vector)
        # print(self.collision_point)
        self.forces.append(vector)

    def apply_acceleration(self):
        self.acceleration = Vector.sum_forces(*self.forces)
        self.velocity.add(self.acceleration)
        self.forces = []

    def apply_velocity(self):
        scalar = 1 / self.mass
        movement = self.velocity.get_copy(scale=scalar)
        movement.name = "movement"
        self.move(movement.get_value())

    def apply_friction(self, cof):
        friction = self.velocity.get_copy(scale=-1 * cof)
        friction.name = "friction"
        self.apply_force(friction)
        self.friction = cof

    def move(self, value):
        dx, dy = value
        x, y = self.position
        x += dx
        y += dy
        self.position = x, y
