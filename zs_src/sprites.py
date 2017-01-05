from zs_constants.gui import UP, DOWN, LEFT, RIGHT
from zs_src.animations import AnimationGraphics, LeftRightGraphics
from zs_src.entities import ZsSprite
from zs_src.physics import Vector, Velocity


class AnimationSprite(ZsSprite):
    def __init__(self, name, **kwargs):
        gc = kwargs.pop("graphics_class", AnimationGraphics)
        super(AnimationSprite, self).__init__(name, **kwargs)

        self.graphics_class = gc
        self.animation_machine = None

    def set_up_animations(self, sprite_sheet, stream_file, animation_machine):
        self.animation_machine = animation_machine
        self.animation_machine.sprite = self

        self.graphics = self.graphics_class(sprite_sheet, self, self.get_image_state)
        self.graphics.set_up_animations(stream_file)

    def update(self, dt):
        super(AnimationSprite, self).update(dt)

        if self.animation_machine:
            self.animation_machine.update()

    def get_image_state(self):
        try:
            return self.animation_machine.get_state().name
        except AttributeError:
            return "Error"


class PhysicsSprite(AnimationSprite):
    Vector = Vector

    def __init__(self, name, mass=1, elasticity=.1, **kwargs):
        super(PhysicsSprite, self).__init__(name, **kwargs)

        self.mass = mass
        self.elasticity = elasticity

        self.acceleration = Vector("acceleration", 0, 0)
        self.velocity = Velocity("velocity", 0, 0)
        self.forces = []

        self._grounded = False

    @property
    def hitbox(self):
        if self.graphics:
            return self.graphics.get_hitbox()

        else:
            return self.rect

    def is_grounded(self):
        return self._grounded

    def set_on_ground(self):
        self._grounded = True

    def set_off_ground(self):
        self._grounded = False

    def add_force(self, vector):
        self.forces.append(vector)

    def apply_acceleration(self):
        self.acceleration = self.velocity.integrate_acceleration(*self.forces)
        self.forces = []

    def apply_velocity(self):
        scalar = 1 / self.mass
        movement = self.velocity.get_copy(scale=scalar)
        self.position = movement.apply_to_point(self.position)

    def apply_friction(self, coefficients):
        ground_cf, air_cf = coefficients
        i, j = self.velocity.get_values()

        j_cf = air_cf
        if not self.is_grounded():
            i_cf = air_cf
        else:
            i_cf = ground_cf

        i_value = (i_cf * i) * -1
        j_value = (j_cf * j) * -1
        friction = Vector("friction", i_value, j_value)

        self.velocity.add(friction)


class CharacterSprite(PhysicsSprite):
    UP, DOWN, LEFT, RIGHT = UP, DOWN, LEFT, RIGHT

    def __init__(self, name, **kwargs):
        kwargs.update({"graphics_class": LeftRightGraphics})
        super(CharacterSprite, self).__init__(name, **kwargs)

        self.controller = None
        self.direction = RIGHT

    def set_controller(self, controller):
        self.controller = controller

    def get_direction_string(self):
        return {
            UP: "up",
            DOWN: "down",
            LEFT: "left",
            RIGHT: "right"
        }[self.direction]

    def get_image_state(self):
        if self.graphics:
            name = self.animation_machine.get_state().name
            direction = self.get_direction_string()

            return "{}_{}".format(direction, name)
        else:
            return "error"