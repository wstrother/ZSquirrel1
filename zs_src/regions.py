from math import atan2, pi, cos, sin

import pygame
from pygame import draw


class GroupsInterface:
    def __init__(self):
        self.groups = []

    def add(self, *groups):
        for group in groups:
            group.add(self)

    def remove(self, *groups):
        for group in groups:
            group.remove(self)

    def kill(self):
        for g in self.groups:
            self.remove(g)


class Vector(GroupsInterface):
    DRAW_WIDTH = 5

    def __init__(self, name, i_hat, j_hat):
        super(Vector, self).__init__()
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
        if abs(self.i_hat) < .00001:
            self.i_hat = 0
        if abs(self.j_hat) < .00001:
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

        return self

    def multiply(self, vector):
        c = self.complex * vector.complex
        self.i_hat = c.real
        self.j_hat = c.imag

        return self

    def get_friction_vector(self, cof):
        friction = self.get_copy(scale=-1 * cof)
        friction.name = "friction"

        return friction

    def scale(self, scalar):
        self.i_hat *= scalar
        self.j_hat *= scalar

        return self

    def scale_to(self, vector):
        m = vector.magnitude
        r = m / self.magnitude

        self.scale(r)

    def scale_in_direction(self, angle, scalar):
        i, j = self.get_basis_vectors(-angle)
        m1 = Matrix.get_from_vectors(i, j)

        m2 = Matrix([
            [scalar, 0],
            [0, 1]
        ])
        m = Matrix(m2.multiply_matrix(m1))

        i, j = m.multiply_vector(self)
        self.i_hat = i
        self.j_hat = j
        self.rotate(angle)

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
        self.round()

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

    def get_copy(self, rotate=0.0, scale=1):
        v = Vector(self.name, self.i_hat, self.j_hat)

        if rotate:
            v.rotate(rotate)

        v.scale(scale)

        return v

    def set_value(self, value):
        self.i_hat = value[0]
        self.j_hat = value[1]

    def get_value(self):
        return self.i_hat, self.j_hat

    def get_transformation_vector(self, basis_i, basis_j):
        i = basis_i.get_copy(scale=self.i_hat)
        j = basis_j.get_copy(scale=self.j_hat)

        v = i.add(j)
        v.name = "transformation vector"
        v.round()

        return v

    @staticmethod
    def get_basis_vectors(angle):
        i = Vector("basis_i", 1, 0).rotate(angle)
        j = Vector("basis_j", 0, 1).rotate(angle)

        return i, j

    def get_value_in_direction(self, angle):
        i, j = self.get_basis_vectors(angle)

        return self.get_transformation_vector(
            i, j).get_value()

    # def scale_in_direction(self, angle, scalar):
    #     i, j = self.get_basis_vectors(angle)
    #     a, c = i.get_value()
    #     b, d = j.get_value()
    #
    #     a, c = .25, 25
    #     b, d = .25, .25
    #
    #     self.i_hat = (a * x) + (b * y)
    #     self.j_hat = (c * x) + (d * y)

    def matrix_multiplication(self, basis_i, basis_j):
        x, y = self.get_value()
        a, c = basis_i.get_value()
        b, d = basis_j.get_value()

        self.i_hat = (a * x) + (b * y)
        self.j_hat = (c * x) + (d * y)

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
        self.sprite_collide_skeleton = False

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

            if not w_bound or not v_bound:
                return False

            else:
                return collision

    def get_sprite_collision_points(self, sprite, offset=(0, 0)):
        angle = self.normal.get_copy(
            rotate=.5).get_angle()

        nx, ny = sprite.get_collision_edge_point(
            angle)
        nx += offset[0]
        ny += offset[1]

        fx, fy = sprite.collision_point
        fx += offset[0]
        fy += offset[1]

        return (nx, ny), (fx, fy)

    @staticmethod
    def sprite_collision(sprite, wall, offset=(0, 0)):
        v_post = sprite.get_last_velocity()
        v_t = sprite.velocity.get_copy()
        v_t.j_hat += 1

        if not v_t.check_orientation(
                wall.normal.get_copy(rotate=.5)):
            return False

        else:
            near, far = wall.get_sprite_collision_points(
                sprite, offset)
            dx = near[0] - far[0]
            dy = near[1] - far[1]
            skeleton = Vector("skeleton", dx, dy)

            near_collision = wall.vector_collision(
                near, v_post)
            far_collision = wall.vector_collision(
                far, skeleton)

            if near_collision:
                # wall.sprite_collide_skeleton = False
                return near_collision

            else:
                # wall.sprite_collide_skeleton = True
                return far_collision

    def get_sprite_position_adjustment(self, sprite, offset=(0, 0)):
        near, far = self.get_sprite_collision_points(sprite, offset)
        x, y = near
        ix, iy = self.axis_collision(
            (x, y), self.normal)
        dx = ix - x
        dy = iy - y
        adjust = Vector("position adjustment", dx, dy)

        return adjust

    @staticmethod
    def handle_collision_smooth(sprite, wall, offset=(0, 0)):
        adjust = wall.get_sprite_position_adjustment(
            sprite, offset)

        sprite.move(adjust.get_value())

        sprite.velocity.scale_in_direction(
            wall.normal.get_angle(), 0
        )

        if wall.ground:
            sprite.set_on_ground(wall)

    @staticmethod
    def handle_collision_mirror(sprite, wall):
        adjust = wall.get_sprite_position_adjustment(
            sprite).scale(2)

        sprite.move(adjust.get_value())
        sprite.apply_force(adjust)

        if wall.ground:
            sprite.set_on_ground(wall)

    def draw(self, screen, color, offset=(0, 0)):
        x, y = self.origin
        x += offset[0]
        y += offset[1]

        super(Wall, self).draw(
            screen, color, offset=(x, y))

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

            start_n = xn + offset[0], yn + offset[1]
            normal = self.normal.get_copy(scale=self.NORMAL_DRAW_SCALE)
            normal.draw(screen, color, offset=start_n)


class Region(GroupsInterface):
    WALL_COLOR = 255, 0, 255

    def __init__(self, name, *points, position=(0, 0), **kwargs):
        super(Region, self).__init__()
        self.name = name

        self.walls = []
        self.position = position
        if points:
            self.set_walls(points, **kwargs)

    def set_walls(self, points, **kwargs):
        self.walls = self.get_walls(points, **kwargs)

    @staticmethod
    def get_walls(points, ground_angle=0.0, orientation=True,
                  offset=(0, 0), friction=None, closed=True):
        if not orientation:
            points = list(points)
            points.reverse()
            points = tuple(points)

        def get_wall(p1, p2):
            x1, y1 = p1
            x2, y2 = p2
            x1 += offset[0]
            x2 += offset[0]
            y2 += offset[1]
            y2 += offset[1]

            return Wall((x1, y1), (x2, y2),
                        friction=friction)

        last = None
        walls = []
        for point in points:
            if last:
                walls.append(get_wall(last, point))

            last = point
        if closed:
            walls.append(get_wall(last, points[0]))

        for w in walls:
            angle = w.get_angle()
            w.ground = angle <= ground_angle or angle >= 1 - ground_angle

        return walls

    def draw(self, screen, offset=(0, 0)):
        for wall in self.walls:
            wall.draw(screen, self.WALL_COLOR, offset=offset)

    def update(self, dt):
        pass

    def get_collision_system(self, items, check_collision, handle_collision):
        def collision_system():
            for item in items:
                for wall in self.walls:
                    if check_collision(item, wall):
                        handle_collision(item, wall)

        return collision_system

    def get_sprite_collision_system(self, group, handle_collision):
        return self.get_collision_system(
            group, Wall.sprite_collision,
            handle_collision)

    def get_vector_collision_system(self, vectors, handle_collision):
        return self.get_collision_system(
            vectors, Wall.vector_collision, handle_collision
        )

    def get_smooth_sprite_collision_system(self, group):
        return self.get_sprite_collision_system(
            group, Wall.handle_collision_smooth
        )

    def get_mirror_sprite_collision_system(self, group):
        return self.get_sprite_collision_system(
            group, Wall.handle_collision_mirror
        )


class RectRegion(Region):
    def __init__(self, name, size, position, **kwargs):
        self.size = size
        self.position = position

        points = (self.bottomleft, self.topleft,
                  self.topright, self.bottomright)

        super(RectRegion, self).__init__(
            name, *points, position=position,
            **kwargs
        )

    def __repr__(self):
        return "{}: {}, {}".format(self.name, self.size, self.position)

    def draw(self, screen, offset=(0, 0)):
        r = self.pygame_rect
        color = self.WALL_COLOR

        r.x += offset[0]
        r.y += offset[1]

        pygame.draw.rect(
            screen, color,
            r, 1
        )

    def move(self, value):
        dx, dy = value
        x, y = self.position
        x += dx
        y += dy
        self.position = x, y

    @property
    def pygame_rect(self):
        r = pygame.Rect(
            self.position, self.size
        )

        return r

    @property
    def clip(self):
        return self.pygame_rect.clip

    @property
    def copy(self):
        return self.pygame_rect.copy

    @property
    def width(self):
        return self.size[0]

    @width.setter
    def width(self, value):
        self.size = value, self.size[1]

    @property
    def height(self):
        return self.size[1]

    @height.setter
    def height(self, value):
        self.size = self.size[0], value

    @property
    def right(self):
        return self.position[0] + self.width

    @property
    def left(self):
        return self.position[0]

    @property
    def top(self):
        return self.position[1]

    @property
    def bottom(self):
        return self.top + self.height

    @property
    def midleft(self):
        return self.left, self.top + (self.height / 2)

    @property
    def topleft(self):
        return self.left, self.top

    @property
    def midtop(self):
        return self.left + (self.width / 2), self.top

    @property
    def topright(self):
        return self.right, self.top

    @property
    def midright(self):
        return self.right, self.top + (self.height / 2)

    @property
    def bottomleft(self):
        return self.left, self.bottom

    @ property
    def midbottom(self):
        return self.left + (self.width / 2), self.bottom

    @property
    def bottomright(self):
        return self.right, self.bottom

    @property
    def center(self):
        return (self.right + (self.width / 2),
                self.top + (self.height / 2))

    @center.setter
    def center(self, value):
        x, y = value
        x -= self.width / 2
        y -= self.height / 2

        self.position = x, y


class Matrix:
    # [[a, c],
    #  [b, d]]
    # i_hat = ax + by       ae + bg     af + bh
    # j_hat = cx + dy       ce + dg     cf + dh
    def __init__(self, values):
        self.values = values

        self.a, self.b = values[0]
        self.c, self.d = values[1]

    @staticmethod
    def get_from_vectors(i, j):
        m = [
            [i.i_hat, j.i_hat],
            [i.j_hat, j.j_hat]
        ]
        return Matrix(m)

    def get_vectors(self):
        return (
            Vector("i_hat", self.a, self.c),
            Vector("j_hat", self.b, self.d)
        )

    def multiply_vector(self, vector):
        x, y = vector.get_value()
        ax = self.a * x
        by = self.b * y
        cx = self.c * x
        dy = self.d * y
        i = ax + by
        j = cx + dy

        return i, j

    def multiply_matrix(self, matrix):
        i, j = matrix.get_vectors()

        new_i = self.multiply_vector(i)
        new_j = self.multiply_vector(j)

        values = [
            [new_i[0], new_j[0]],
            [new_i[1], new_j[1]]
        ]

        return values
