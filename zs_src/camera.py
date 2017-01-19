from os.path import join

import pygame

from zs_constants.paths import BG_LAYERS
from zs_src.classes import Meter
from zs_src.entities import Layer
from zs_src.graphics import IconGraphics
from zs_src.physics import PhysicsInterface
from zs_src.regions import RectRegion, Region


class Camera(PhysicsInterface):
    WINDOW_COLOR = (0, 255, 255)

    class Window(RectRegion):
        def __init__(self, screen_size, window_size, shift, offset):
            rect = pygame.Rect((0, 0), window_size)
            x, y = screen_size[0] / 2, screen_size[1] / 2
            x += offset[0]
            y += offset[1]
            rect.center = x, y
            super(Camera.Window, self).__init__(
                "camera window", rect)

            self.offsets = self.get_offset_meters(
                (x, y), shift
            )

        @staticmethod
        def get_offset_meters(values, shift):
            x, y = values
            dx, dy = shift

            x_min = x - (dx / 2)
            x_max = x + (dx / 2)
            y_min = y - (dy / 2)
            y_max = y + (dy / 2)

            x_offset = Meter(
                "x_offset", x, x_max, x_min)
            y_offset = Meter(
                "y_offset", y, y_max, y_min)

            return x_offset, y_offset

        def shift(self, shift):
            dx, dy = shift
            xo, yo = self.offsets
            xo.value += dx
            yo.value += dy

        def get_rect(self):
            x, y = self.offsets
            r = super(Camera.Window, self).get_rect()
            r.center = x.value, y.value

            return r

    def __init__(self, size):
        super(Camera, self).__init__(1, 0)
        self.rect = pygame.Rect((0, 0), size)
        self.position = 0, 0
        self.size = size
        self.scale = 1

        self.visible = True

        self.windows = []
        self.anchor = (0, 0)

    def make_window(self, window_size,
                    shift=(0, 0), offset=(0, 0)):

        w = self.Window(
            self.size, window_size, shift, offset
        )
        self.windows.append(w)
        return w

    @property
    def collision_region(self):
        return self.rect

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

    def draw(self, screen):
        for w in self.windows:
            pygame.draw.rect(
                screen, self.WINDOW_COLOR,
                w.get_rect(), 1)

        x, y = self.get_screen_position(
            self.focus_point)

        pygame.draw.circle(
            screen, self.WINDOW_COLOR,
            (x, y), 5, 1)
        self.velocity.draw(
            screen, self.WINDOW_COLOR, (x, y))

        xa, ya = self.anchor
        if ya:
            start = x - 100, ya
            end = x + 100, ya
            pygame.draw.line(
                screen, self.WINDOW_COLOR,
                start, end, 5
            )
        if xa:
            start = xa, y - 100
            end = xa, y + 100
            pygame.draw.line(
                screen, self.WINDOW_COLOR,
                start, end, 5
            )

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

        self.apply_force(
            self.Vector("tracking", dx, dy))

    def window_track(self, window, point, rate):
        outside = self.outside_window(window, point)

        if outside:
            dx, dy = outside
            dx *= rate
            dy *= rate
            self.apply_force(
                self.Vector("tracking", dx, dy))

    def anchor_track(self, point, rate):
        xa, ya = self.anchor
        sx, sy = self.get_screen_position(point)
        fx, fy = self.focus_point

        dx, dy = 0, 0
        if xa and xa != sx:
            dx = xa - sx

        if ya and ya != sy:
            dy = ya - sy

        fx -= dx
        fy -= dy
        self.track((fx, fy), rate)

    # def apply_velocity(self):
    #     super(Camera, self).apply_velocity()
    #     self.velocity.scale(0)


class CameraLayer(Layer):
    def __init__(self, name, **kwargs):
        super(CameraLayer, self).__init__(name, **kwargs)
        self.camera = Camera(self.size)
        self.bg_layers = []

        self.track_functions = []
        self.collision_systems = []

        self.camera_windows = {}
        self.regions = []

        def toggle_visible():
            self.camera.visible = not self.camera.visible

        self.interface = {
            "Toggle window visibility": toggle_visible,
        }
        # self._positions = CacheList(2)
        # self._positions.append((0, 0))

    def set_up_windows(self, *windows):
        for w in windows:
            name, args = w
            self.camera_windows[name] = self.camera.make_window(
                *args
            )

    def set_anchor(self, value, vertical=True):
        if not vertical:
            self.camera.anchor = value, 0

        else:
            self.camera.anchor = 0, value

    def set_edge_bounds(self, span, vertical=False):
        if not vertical:
            self.h_span = span

        else:
            self.v_span = span

    def update(self, dt):
        super(CameraLayer, self).update(dt)

        self.camera.apply_acceleration()
        self.camera.apply_velocity()

        for func in self.track_functions:
            func()

        for system in self.collision_systems:
            system()

        self.camera.velocity.scale(0)

    @staticmethod
    def get_collision_vars(camera, wall):
        angle = wall.get_angle()
        angles = [(x / 4) + .125 for x in range(4)]

        r = camera.rect.copy()
        r.topleft = camera.position

        p1, p2 = wall.origin, wall.end_point

        return angle, r, p1, p2

    @staticmethod
    def check_collision(camera, wall):
        angle, r, p1, p2 = CameraLayer.get_collision_vars(
            camera, wall
        )
        v = camera.get_last_velocity()
        collision = False
        mid_x = (p1[0] + p2[0]) / 2
        mid_y = (p1[1] + p2[1]) / 2

        # BOTTOM EDGE >
        if angle == 0:
            if r.bottom > mid_y and not r.centery > mid_y:
                if not (r.right < p1[0] or r.left > p2[0]):
                    collision = True

        # RIGHT EDGE ^
        if angle == .25:
            if r.right > mid_x and not r.centerx > mid_x:
                if not (r.bottom < p2[1] or r.top > p1[1]):
                    collision = True

        # TOP EDGE <
        if angle == .5:
            if r.top < mid_y and not r.centery < mid_y:
                if not (r.right < p2[0] or r.left > p1[0]):
                    collision = True

        # LEFT EDGE v
        if angle == .75:
            if r.left < mid_x and not r.centerx < mid_x:
                print("left")
                if not (r.bottom < p1[1] or r.top > p2[1]):
                    print("collision")
                    collision = True

        if collision:
            return wall.axis_collision(
                camera.collision_point, v)

    @staticmethod
    def handle_collision(camera, wall):
        angle, r, p1, p2 = CameraLayer.get_collision_vars(
            camera, wall
        )

        if angle == 0:
            print("BOTTOM")
            r.bottom = p1[1]

        if angle == .25:
            print("RIGHT")
            r.right = p1[0]

        if angle == .5:
            print("TOP")
            r.top = p1[1]

        if angle == .75:
            print("LEFT")
            r.left = p1[0]

        camera.focus_point = r.center

    def set_camera_bounds_region(self, size, position=(0, 0),
                                 orientation=False, **kwargs):
        region = RectRegion(
            "camera bounds", pygame.Rect(position, size),
            orientation=orientation, **kwargs)

        self.collision_systems.append(
            region.get_collision_system(
                [self.camera], self.check_collision,
                self.handle_collision)
        )

        self.regions.append(region)

    def set_camera_bounds_shape(self, *points, **kwargs):
        region = Region("camera bounds region", *points, **kwargs)

        self.collision_systems.append(
            region.get_collision_system(
                [self.camera], self.check_collision,
                self.handle_collision)
        )

        self.regions.append(region)

    def set_tracking_point_function(self, get_point, rate):
        def set_camera():
            p = get_point()
            self.camera.track(p, rate)

        self.track_functions.append(set_camera)

    def set_sprite_window_track(self, sprite, name, rate):
        window = self.camera_windows[name]

        def set_camera():
            point = sprite.collision_point
            self.camera.window_track(
                window, point, rate
            )

            return point

        self.track_functions.append(set_camera)

    def set_anchor_track_function(self, get_point, check_func, rate):
        def track_anchor():
            if check_func():
                self.camera.anchor_track(
                    get_point(), rate
                )

        self.track_functions.append(track_anchor)

    def set_anchor_position_function(self, get_position, span, vertical=True):
        meter = Meter("span", span[0], span[1], span[0])

        def set_anchor():
            meter.value = get_position()
            self.set_anchor(meter.value, vertical)

        self.track_functions.append(set_anchor)

    def track_window_to_sprite_heading(self, sprite, name, rate):
        window = self.camera_windows[name]

        def set_heading():
            velocity = sprite.velocity.get_value()
            direction = sprite.direction
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

        self.track_functions.append(set_heading)

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
            self.camera.draw(screen)

            for region in self.regions:
                region.draw(
                    screen, offset=self.camera.get_offset())

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
