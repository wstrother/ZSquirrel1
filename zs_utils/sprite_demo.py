from zs_constants.zs import SCREEN_SIZE
from zs_src.entities import Layer
from zs_src.menus import HeadsUpDisplay
from zs_src.physics import PhysicsLayer
from zs_src.sprites import CharacterSprite
from zs_src.state_machines import AnimationMachine
from zs_utils.debug_menu import DictEditor

MASS, ELAST = 1, .1


class SpriteDemo(Layer):
    def __init__(self, **kwargs):
        super(SpriteDemo, self).__init__("sprite demo", **kwargs)
        self.context = ContextManager(self)

        gravity = 1
        physics_layer = PhysicsLayer(
            gravity, "sprite demo physics layer")
        g = self.make_group()
        physics_layer.groups.append(g)
        physics_layer.add_hitbox_layer(g)
        physics_layer.add_vector_layer(g)

        self.add_sub_layer(physics_layer)
        self.physics_layer = physics_layer
        self.main_group = g

        self.debug_layer = DebugLayer()
        self.debug_layer.model = self.model
        self.add_sub_layer(self.debug_layer)

        self.set_value("test_list", [1, 2, 3, 4])
        pause_menu = PauseMenu()
        pause_menu.model = self.model
        self.pause_menu = pause_menu

    def handle_controller(self):
        super(SpriteDemo, self).handle_controller()

        devices = self.controller.devices

        if devices["start"].check() and not self.pause_menu.active:
            self.handle_event(("pause",
                               ("layer",
                                self.pause_menu)))

        # if self.pause_menu.active:
        #     self.pause_menu.handle_controller()

    def main(self, dt, screen):
        for c in self.controllers:
            c.update()

        self.handle_controller()
        self.update(dt)
        self.draw(screen)

    def populate(self):
        self.pause_menu.controllers = self.controllers

        g = self.main_group
        self.groups = [self.make_group()]

        player = self.context.make_sprite(
            "player", position=(400, 300))
        player.add(g)

        self.set_value("player", player)

    def on_pause(self):
        self.add_sub_layer(self.pause_menu)
        super(SpriteDemo, self).on_pause()
        self.physics_layer.active = False

    def on_unpause(self):
        super(SpriteDemo, self).on_unpause()
        self.physics_layer.active = True

    def on_birth(self):
        super(SpriteDemo, self).on_birth()

        self.context.set_up_graphics(self.main_group)
        self.context.set_up_controllers(self.main_group)


class ContextManager:
    def __init__(self, environment):
        self.sprite_dict = self.set_up_sprite_dict()
        self.environment = environment

    @staticmethod
    def set_up_sprite_dict():
        d = {
            "player": [lambda **kwargs: DemoSprite("player", **kwargs),
                       0, "yoshi.gif", "demo.txt", SpriteDemoMachine]
        }

        return d

    def set_up_graphics(self, group):
        for sprite in group:
            name = sprite.name
            args = self.sprite_dict[name][2:]
            sprite_sheet, stream_file, animation_machine = args

            sprite.set_up_animations(
                sprite_sheet,
                stream_file,
                animation_machine())

    def set_up_controllers(self, group):
        for sprite in group:
            name = sprite.name
            controller = self.sprite_dict[name][1]

            if type(controller) is int:
                controller = self.environment.controllers[0]

            sprite.set_controller(controller)

    def make_sprite(self, key, **kwargs):
        sprite = self.sprite_dict[key][0](**kwargs)

        return sprite


class SpriteDemoMachine(AnimationMachine):
    def __init__(self):
        super(SpriteDemoMachine, self).__init__("demo_animation.txt")

        self.add_event_methods(
            "press_direction", "press_jump", "press_down",
            "neutral_dpad", "v_acceleration_0", "ground_collision",
            "auto"
        )

    @property
    def dpad(self):
        if self.sprite.controller:
            return self.sprite.controller.devices["dpad"]

        else:
            return False

    def on_press_direction(self):
        if self.sprite.controller:
            x, y = self.dpad.get_direction()
            return x != 0

        else:
            return False

    def on_press_jump(self):
        if self.sprite.controller:
            jump = bool(self.sprite.controller.devices["b"].held == 1)

            return jump
        else:
            return False

    def on_press_down(self):
        if self.sprite.controller:
            down = self.dpad.get_direction()[1] == 1
            return down

        else:
            return False

    def on_release_down(self):
        if self.sprite.controller:
            dpad = self.sprite.controller.devices["dpad"]
            down = dpad.get_direction()[1] > 0

            return not down

        else:
            return False

    def on_neutral_dpad(self):
        if self.sprite.controller:
            neutral = self.dpad.get_direction() == (0, 0)
            return neutral

        else:
            return False

    def on_v_acceleration_0(self):
        if self.sprite.velocity:
            apex = self.sprite.velocity.j_hat >= 0

            return apex
        else:
            return False

    def on_ground_collision(self):
        return self.sprite.is_grounded()

    def on_auto(self):
        if self.sprite.graphics:
            return self.sprite.graphics.animation_completed()

        else:
            return False


class DemoSprite(CharacterSprite):
    def update(self, dt):
        super(CharacterSprite, self).update(dt)

        if self.animation_machine:
            state = self.animation_machine.get_state().name

            if state == "jump_up" and self.is_grounded():
                self.set_off_ground()

                jump = self.Vector("jump", 0, -25)
                self.add_force(jump)

            dpad = self.controller.devices["dpad"]
            x = dpad.get_direction()[0]

            if state in ("walk", "jump_squat", "crouch_down", "crouch_idle", "crouch_up"):
                if x > 0:
                    self.direction = self.RIGHT
                if x < 0:
                    self.direction = self.LEFT

            if state in ("walk", "jump_squat", "jump_up", "jump_apex", "jump_fall", "jump_land"):
                dx = 1.5 * x
                if not self.is_grounded():
                    dx /= 5

                move = self.Vector("move", dx, 0)
                self.add_force(move)

            x, y = self.position
            bottom = self.hitbox.bottom
            dx = bottom - y

            if bottom > SCREEN_SIZE[1]:
                y = SCREEN_SIZE[1] - dx
                self.set_on_ground()
                self.position = x, y


class DebugLayer(HeadsUpDisplay):
    def __init__(self, **kwargs):
        super(DebugLayer, self).__init__("debug layer", **kwargs)

    def populate(self):
        tools = self.tools

        def report_player(p):
            if p.animation_machine:
                state = p.animation_machine.get_state().name
                direction = p.get_direction_string()
                grounded = str(p.is_grounded())

                text = [
                    "{:>20}: {:^30}".format("STATE", state),
                    "{:>20}: {:^30}".format("DIRECTION", direction),
                    "{:>20}: {:^30}".format("GROUNDED", grounded)
                ]

                return text

            else:
                return "Not set up"

        player = self.get_value("player")
        reporter = tools.make_reporter_sprite(
            player, report_player)

        table = tools.ContainerSprite(
            "hud container", [[reporter]],
            position=(25, 0),
            table_style="grid")

        table.style = {"align_h": "l", "align_v": "c"}
        table.add(self.hud_group)


class PauseMenu(DictEditor):
    def __init__(self, **kwargs):
        super(PauseMenu, self).__init__("sprite demo pause menu", **kwargs)

        self.active = False

