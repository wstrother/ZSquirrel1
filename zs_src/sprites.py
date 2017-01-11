from zs_constants.gui import UP, DOWN, LEFT, RIGHT
from zs_constants.sprite_demo import MASS, ELAST
from zs_src.animations import AnimationGraphics, LeftRightGraphics
from zs_src.entities import ZsSprite
from zs_src.physics import PhysicsInterface


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
        self.set_rect_size_to_image()

    def update(self, dt):
        super(AnimationSprite, self).update(dt)

        if self.animation_machine:
            self.animation_machine.update()

    def get_image_state(self):
        try:
            return self.animation_machine.get_state().name
        except AttributeError:
            return "Error"


class CharacterSprite(PhysicsInterface, AnimationSprite):
    UP, DOWN, LEFT, RIGHT = UP, DOWN, LEFT, RIGHT

    def __init__(self, name, mass=MASS, elasticity=ELAST, **kwargs):
        kwargs.update({"graphics_class": LeftRightGraphics})
        AnimationSprite.__init__(self, name, **kwargs)
        PhysicsInterface.__init__(self, mass, elasticity)

        self.controller = None
        self.direction = RIGHT
        self._position = 0.0, 0.0

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, value):
        self.adjust_position(value)

    def adjust_position(self, value):
        self._position = value
        x, y = value
        self.rect.topleft = round(x), round(y)

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
