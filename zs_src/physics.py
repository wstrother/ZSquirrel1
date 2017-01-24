from pygame import draw

from zs_constants.zs import FRAME_RATE, SCREEN_SIZE
from zs_src.entities import Layer
from zs_src.regions import RectRegion, Vector


class PhysicsLayer(Layer):
    def __init__(self, name, g, cof, **kwargs):
        super(PhysicsLayer, self).__init__(name, **kwargs)

        self.gravity = Vector("gravity", 0, g)
        self.friction = cof
        self.collision_systems = []

        self.interface = {
            "gravity": g,
            "friction": cof,
            "toggle hitbox layer": self.toggle_hitbox_layer,
            "toggle vector layer": self.toggle_vector_layer,
            "toggle walls layer": self.toggle_wall_layer
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

    @staticmethod
    def sprite_collision(sprite_a, sprite_b):
        r1 = sprite_a.collision_region
        r2 = sprite_b.collision_region

        return r1.colliderect(r2)

    def get_update_methods(self):
        um = super(PhysicsLayer, self).get_update_methods()

        print("\n--------------")
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
                gravity = self.gravity.get_copy(
                    scale=sprite.mass)
                if sprite.is_grounded():
                    angle = sprite.ground.normal.get_angle()
                    gravity.scale_in_direction(angle, 0)
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
        for group in self.groups:
            for sprite in group:
                sprite.set_off_ground()

        for system in self.collision_systems:
            system()


class DrawWallsLayer(Layer):
    GROUND_COLOR = (125, 125, 0)
    WALL_COLOR = (100, 200, 0)

    def __init__(self, walls, **kwargs):
        super(DrawWallsLayer, self).__init__("draw walls layer", **kwargs)
        self.walls = walls
        self.visible = True

    def draw(self, screen, offset=(0, 0)):
        for wall in self.walls:
            if wall.ground:
                color = self.GROUND_COLOR
            else:
                color = self.WALL_COLOR
            wall.draw(screen, color, offset=offset)


class DrawVectorLayer(Layer):
    VELOCITY_COLOR = (0, 255, 0)
    VELOCITY_SCALE = 1
    ACCELERATION_COLOR = (0, 0, 255)
    ACCELERATION_SCALE = 10

    def __init__(self, group, **kwargs):
        super(DrawVectorLayer, self).__init__("draw vector layer", **kwargs)
        self.group = group
        self.visible = False

    def draw(self, screen, offset=(0, 0)):
        for sprite in self.group:
            x, y = sprite.collision_lead_point
            x += offset[0]
            y += offset[1]

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

    def draw(self, screen, offset=(0, 0)):
        for sprite in self.group:
            sprite.draw_collision_region(
                screen, offset=offset)


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
        self.last_ground = None
        self.last_position = None

        self._collision_region = RectRegion(
            "collision region", (0, 0), (0, 0)
        )

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
        r = self._collision_region

        if self.graphics:
            w, h, x, y = self.graphics.get_hitbox()
            px, py = self.position
            x += px
            y += py

            r.size = (w, h)
            r.position = (x, y)

        else:
            r = self.rect

        return r

    @property
    def collision_point(self):
        return self.collision_region.center

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
        right = angle < angles[0] or angle >= angles[7]

        r = self.collision_region

        if top_right:
            return r.topright

        if top:
            return r.midtop

        if top_left:
            return r.topleft

        if left:
            return r.midleft

        if bottom_left:
            return r.bottomleft

        if bottom:
            return r.midbottom

        if bottom_right:
            return r.bottomright

        if right:
            return r.midright

    def draw_collision_region(self, screen, offset=(0, 0)):
        r = self.collision_region
        x, y = self.position
        r.x += x + offset[0]
        r.y += y + offset[1]

        draw.rect(screen, (255, 0, 0), r, 1)

    def is_grounded(self):
        return bool(self.ground)

    def set_on_ground(self, ground):
        self.ground = ground

    def set_off_ground(self):
        if self.ground:
            self.last_ground = self.ground
        self.ground = None

    def get_ground_vector(self, dx):
        move = self.Vector("move", dx, 0)
        if self.ground:
            move.rotate(self.ground.get_angle())

        return move

    def get_jump_vector(self, dy):
        if self.ground:
            angle = self.ground.normal.get_angle()
        else:
            angle = self.last_ground.normal.get_angle()
        jump = self.Vector(
            "jump", 1 * dy, 0).rotate((angle + .25) / 2)

        return jump

    @property
    def gravity(self):
        g = None
        for f in self.forces:
            if f.name == "gravity":
                g = f

        if not g:
            g = Vector("gravity", 0, 1)

        return g

    def get_slide_force(self):
        g = self.gravity

        return g.get_value_in_direction(self.ground.get_angle())[0] * -1

    def get_ground_speed(self):
        if self.ground:
            i, j = self.velocity.get_value_in_direction(
                self.ground.get_angle())

            return i

        else:
            return 0

    def get_ground_anchor(self):
        g = self.ground
        if not g:
                return None

        y1, y2 = g.origin[1], g.end_point[1]
        x, y = self.collision_point
        mid_y = (y1 + y2) / 2
        if abs(y1 - y2) > SCREEN_SIZE[1] / 2:
            anchor = x, y

        else:
            anchor = x, mid_y

        return anchor

    def get_last_velocity(self):
        if not self.last_position:
            return Vector("post velocity", 0, 0)

        x, y = self.last_position
        dx, dy = self.position
        dx -= x
        dy -= y

        return Vector("post velocity", dx, dy)

    def get_friction_velocity(self):
        v = self.velocity.get_copy()
        friction = v.get_friction_vector(self.friction)
        v.add(friction)

        return v

    def get_projected_position(self, point):
        return self.get_friction_velocity().apply_to_point(
            point)

    def apply_force(self, vector):
        # print("\t", vector)
        # print(self.collision_point)
        self.forces.append(vector)

    def apply_acceleration(self):
        self.acceleration = Vector.sum_forces(*self.forces)
        self.velocity.add(self.acceleration)
        self.velocity.round()
        self.forces = []

    def apply_velocity(self):
        self.last_position = self.position

        scalar = 1 / self.mass
        movement = self.velocity.get_copy(scale=scalar)
        movement.name = "movement"
        self.move(movement.get_value())

    def apply_friction(self, cof):
        friction = self.velocity.get_friction_vector(cof)
        self.apply_force(friction)
        self.friction = cof
