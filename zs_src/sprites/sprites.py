from zs_constants.gui import UP, DOWN, LEFT, RIGHT
from zs_constants.sprite_demo import MASS, ELAST
from zs_src.animations import AnimationGraphics, LeftRightGraphics
from zs_src.classes import Meter, ChargeMeter
from zs_src.entities import Sprite
from zs_src.layers.physics import PhysicsInterface
from zs_src.resource_library import get_resources


class AnimationSprite(Sprite):
    def __init__(self, name, **kwargs):
        gc = kwargs.pop("graphics_class", AnimationGraphics)
        super(AnimationSprite, self).__init__(name, **kwargs)

        self.graphics_class = gc
        self.animation_machine = None
        self.state_frame = 0
        self.last_state = None

    def set_up_animations(self, sprite_sheet, stream_file, animation_machine):
        self.animation_machine = animation_machine(self)
        self.graphics = self.graphics_class(
            sprite_sheet, stream_file, self,
            self.get_image_state)

        self.set_rect_size_to_image()

    def update(self):
        super(AnimationSprite, self).update()

        if self.animation_machine:
            self.animation_machine.update()

            if self.get_animation_name() != self.last_state:
                self.state_frame = 0
            else:
                self.state_frame += 1

            self.last_state = self.get_animation_name()

    def get_animation_name(self):
        if self.animation_machine:
            return self.animation_machine.get_state().name

    def get_animation_frame(self):
        if self.graphics:
            return self.graphics.get_frame_number()

    def get_state_frame(self):
        return self.state_frame

    def animation_completed(self):
        if self.graphics:
            return self.get_state_frame() >= self.graphics.get_frame_count() - 1

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
        self.adjust_position(self.rect.topleft)

        self.meters = {}

    def add_meter(self, name, value, charge=False, *args, **kwargs):
        if not charge:
            meter = Meter(name, value, **kwargs)
        else:
            meter = ChargeMeter(name, value, *args)

        self.meters[name] = meter

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

    def update(self):
        super(CharacterSprite, self).update()

        for name in self.meters:
            m = self.meters[name]
            if hasattr(m, "update"):
                m.update()
                # print(m)


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

    def update(self):
        super(DemoSprite, self).update()

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
                dx = movement[state] * self.direction[0] * self.friction * base_speed

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