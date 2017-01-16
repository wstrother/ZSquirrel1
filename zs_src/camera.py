from os.path import join

import pygame

from zs_constants.paths import BG_LAYERS
from zs_src.classes import Meter
from zs_src.entities import Layer
from zs_src.graphics import IconGraphics
from zs_src.regions import RectRegion


class Camera:
    WINDOW_COLOR = (0, 255, 255)

    class Window(RectRegion):
        def __init__(self, screen_size, window_size, shift_range, offset=(0, 0)):
            rect = pygame.Rect((0, 0), window_size)
            x, y = screen_size[0] / 2, screen_size[1] / 2
            x += offset[0]
            y += offset[1]
            rect.center = x, y
            super(Camera.Window, self).__init__(
                "camera window", rect)

            dx, dy = shift_range
            x_min = x - (dx / 2)
            x_max = x + (dx / 2)
            y_min = y - (dy / 2)
            y_max = y + (dy / 2)

            self.x_offset = Meter(
                "x_offset", x, x_max, x_min)
            self.y_offset = Meter(
                "y_offset", y, y_max, y_min)

        def get_rect(self):
            r = super(Camera.Window, self).get_rect()
            x, y = self.x_offset.value, self.y_offset.value
            r.center = x, y

            return r

        def shift(self, value):
            dx, dy = value
            self.x_offset.value += dx
            self.y_offset.value += dy

    def __init__(self, size):
        self.position = 0, 0
        self.size = size
        self.scale = 1
        self.window = Camera.Window(size, (260, 400), (300, 100), offset=(0, 50))
        self.visible = False

        def toggle_visible():
            self.visible = not self.visible

        self.interface = {
            "Toggle window visibility": toggle_visible,
        }

    @property
    def focus_point(self):
        x, y = self.position
        x += (self.size[0] / 2) / self.scale
        y += (self.size[1] / 2) / self.scale

        return int(x), int(y)

    @focus_point.setter
    def focus_point(self, value):
        x, y = value
        x -= (self.size[0] / 2) / self.scale
        y -= (self.size[1] / 2) / self.scale

        self.position = int(x), int(y)

    def get_screen_position(self, position):
        x, y = position
        dx, dy = self.get_offset()
        x += dx
        y += dy
        x *= self.scale
        y *= self.scale

        return int(x), int(y)

    def get_offset(self):
        x, y = self.position
        x *= self.scale
        y *= self.scale

        return -x, -y

    def draw_window(self, screen):
        pygame.draw.rect(
            screen, self.WINDOW_COLOR,
            self.window.get_rect(), 1)

        x, y = self.get_screen_position(
            self.focus_point)

        pygame.draw.circle(
            screen, self.WINDOW_COLOR,
            (x, y), 5, 1)

    def outside_window(self, window, point):
        point = self.get_screen_position(point)
        r = window.get_rect()

        if r.collidepoint(point):
            return False

        else:
            x, y = point
            dx = 0
            if x > r.right:
                dx = x - r.right
            if x < r.left:
                dx = x - r.left

            dy = 0
            if y > r.bottom:
                dy = y - r.bottom
            if y < r.top:
                dy = y - r.top

            return dx, dy

    def move(self, value):
        dx, dy = value
        dx /= self.scale
        dy /= self.scale
        x, y = self.position
        x += dx
        y += dy

        self.position = round(x), round(y)

    def track(self, point, rate):
        x, y = point
        fx, fy = self.focus_point
        dx = x - fx
        dy = y - fy
        dx *= rate
        dy *= rate

        self.move((dx, dy))

    def window_track(self, window, point, rate):
        outside = self.outside_window(window, point)

        if outside:
            dx, dy = outside
            dx *= rate
            dy *= rate
            self.move((dx, dy))


class CameraLayer(Layer):
    def __init__(self, name, **kwargs):
        super(CameraLayer, self).__init__(name, **kwargs)
        self.camera = Camera(self.size)
        self.bg_layers = []

        self.set_value("tracking_point", None)

    def track_sprite_to_window(self, sprite, window, rate):
        self.model.link_object(sprite, "tracking_point",
                               lambda s: s.collision_point)

        def set_camera(point):
            self.camera.window_track(window, point, rate)

        self.model.link_value("tracking_point", set_camera)

    def track_sprite_heading_to_window(self, sprite, window, rate):
        value_name = sprite.name + "_heading"
        self.model.link_object(
            sprite, value_name,
            lambda s: (s.collision_point, s))

        def set_heading(value):
            s = value[1]
            velocity, direction = s.velocity.get_value(), s.direction
            vx, vy = velocity
            dx, dy = direction

            left = vx < 0 and dx < 0
            right = vx > 0 and dx > 0
            up = vx < -1
            down = vx > 1

            x, y = 0, 0
            if left or right:
                x = vx * -rate
            if up or down:
                y = vy * -rate

            window.shift((x, y))

        self.model.link_value(
            value_name, set_heading)

    def add_bg_layer(self, bg_image, scale, **kwargs):
        l = ParallaxBgLayer(
            bg_image, scale, self.camera,
            **kwargs)
        self.bg_layers.append(l)

        return l

    def draw(self, screen, offset=(0, 0)):
        if self.camera.scale > 1:
            w, h = self.size
            w /= 2
            h /= 2
            sub_screen = pygame.Surface((w, h))

            self.draw_bg_layers(sub_screen)
            super(CameraLayer, self).draw(
                sub_screen, self.camera.get_offset())

            pygame.transform.smoothscale(sub_screen, self.size, screen)

        else:
            self.draw_bg_layers(screen)

            super(CameraLayer, self).draw(
                screen, self.camera.get_offset())

        if self.camera.visible:
            self.camera.draw_window(screen)

    def draw_bg_layers(self, screen):
        for layer in self.bg_layers:
            layer.draw(screen, self.camera.get_offset())


class ParallaxBgLayer(Layer):
    def __init__(self, image_name, scale, camera, buffer=(0, 0),
                 wrap=(False, False), **kwargs):
        super(ParallaxBgLayer, self).__init__("bg layer", **kwargs)

        self.set_up_graphics(image_name, buffer)

        self.camera = camera
        self.scale = scale
        self.wrap = wrap

    def set_up_graphics(self, image_name, buffer):
        bg_image = self.get_bg_image(image_name)
        self.graphics = IconGraphics(self, bg_image)

        w, h = bg_image.get_size()
        w += buffer[0]
        h += buffer[1]
        self.size = w, h

    @staticmethod
    def get_bg_image(image_name):
        path = join(BG_LAYERS, image_name + ".gif")
        bg_image = pygame.image.load(path)
        bg_image.set_colorkey(bg_image.get_at((0, 0)))

        return bg_image

    def draw(self, screen, offset=(0, 0)):
        sw, sh = screen.get_size()
        x, y = self.position
        w, h = self.size

        dx, dy = offset
        dx *= self.scale
        dy *= self.scale

        x += dx
        y += dy

        x_wrap, y_wrap = self.wrap
        if x_wrap:
            x %= w
        if y_wrap:
            y %= h

        if x_wrap and y_wrap:
            for i in range((sw // w) + 2):
                ox = x + ((i - 1) * w)

                for j in range((sh // h) + 2):
                    oy = y + ((j - 1) * h)
                    self.graphics.draw(screen, offset=(ox, oy))

        elif x_wrap:
            for i in range((sw // w) + 2):
                ox = x + ((i - 1) * w)

                self.graphics.draw(
                    screen, offset=(ox, y))

        elif y_wrap:
            for j in range((sh // h) + 2):
                oy = y + ((j - 1) * h)
                self.graphics.draw(screen, offset=(x, oy))

        else:
            self.graphics.draw(screen, offset=(x, y))
