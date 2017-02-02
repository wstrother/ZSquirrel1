from os.path import join

import pygame

from zs_constants.paths import BG_LAYERS
from zs_src.classes import Meter
from zs_src.entities import Layer
from zs_src.entities import RectRegion
from zs_src.geometry import Vector, Wall, Rect
from zs_src.graphics import IconGraphics
from zs_src.layers.physics import PhysicsInterface


class Camera(PhysicsInterface):
    WINDOW_COLOR = (0, 255, 255)

    class Window(Rect):
        def __init__(self, camera, window_size, shift, offset):
            x, y = camera.screen_size
            x /= 2
            y /= 2
            x += offset[0]
            y += offset[1]

            self.camera = camera
            w, h = window_size
            w /= camera.scale
            h /= camera.scale

            self._size = w, h
            self._position = 0, 0
            self.offsets = self.get_offset_meters(
                (x, y), shift
            )

            super(Camera.Window, self).__init__(
                window_size, (0, 0))

        @property
        def size(self):
            x, y = self._size
            x /= self.camera.scale
            y /= self.camera.scale

            return x, y

        @size.setter
        def size(self, value):
            pass

        @property
        def position(self):
            x, y = self.camera.position
            ox, oy = self.offsets
            x += ox.value / self.camera.scale
            y += oy.value / self.camera.scale
            self.center = x, y

            return self._position

        @position.setter
        def position(self, value):
            self._position = value

        @staticmethod
        def get_offset_meters(values, shift):
            x, y = values
            dx, dy = shift

            x_min = x - (dx / 2)
            x_max = x + (dx / 2)
            y_min = y - (dy / 2)
            y_max = y + (dy / 2)

            x_offset = Meter(
                "x_offset", x_min, x, x_max)
            y_offset = Meter(
                "y_offset", y_min, y, y_max)

            return x_offset, y_offset

        def shift(self, shift):
            dx, dy = shift
            xo, yo = self.offsets
            xo.value += dx
            yo.value += dy

        def draw(self, screen, offset=(0, 0)):
            color = Camera.WINDOW_COLOR
            r = self.pygame_rect
            r.x += offset[0]
            r.y += offset[1]

            pygame.draw.rect(
                screen, color,
                r, 1
            )

            pygame.draw.circle(
                screen, color,
                r.center, 5, 1)

    def __init__(self, size, scale=1):
        super(Camera, self).__init__(1, 0)
        self._focus_point = size[0] / 2, size[1] / 2
        self._scale = scale
        self.screen_size = size

        self.visible = False
        self.anchor = (0, 0)
        self.x_anchor = Vector("x anchor", 0, size[1] / 4)
        self.y_anchor = Vector("y anchor", size[0] / 4, 0)

        self.regions = [Camera.Window(
                self, size,
                (0, 0), (0, 0)
        )]

    @property
    def collision_region(self):
        return self.regions[0]

    @property
    def scale(self):
        return self._scale

    @scale.setter
    def scale(self, value):
        self._scale = value
        for r in self.regions:
            r.scale = value

    @property
    def focus_point(self):
        return self._focus_point

    @focus_point.setter
    def focus_point(self, value):
        self._focus_point = value
        for r in self.regions:
            r.position = value

    def make_window(self, window_size,
                    shift=(0, 0), offset=(0, 0)):

        w = self.Window(
            self, window_size, shift, offset
        )
        self.regions.append(w)
        return w

    @property
    def size(self):
        return self.collision_region.size

    @property
    def position(self):
        return self.get_world_px((0, 0))

    @property
    def reticle(self):
        w, h = self.screen_size
        sx, sy = w / 2, h / 2

        return sx, sy

    def get_world_px(self, screen_px):
        sx, sy = screen_px
        fx, fy = self.focus_point

        # delta = (reticle) - (screen px value)
        rx, ry = self.reticle
        dx = rx - sx
        dy = ry - sy

        # convert screen px delta to world px delta
        dx /= self.scale
        dy /= self.scale

        # world px = (focus point) + delta
        wx = fx - dx
        wy = fy - dy

        return wx, wy

    def get_screen_px(self, world_px):
        x, y = self.position
        wx, wy = world_px

        # delta = (world pixels of top left) - (world pixel value)
        dx = x - wx
        dy = y - wy

        # screen px = delta / scale
        sx = dx / self.scale
        sy = dy / self.scale

        return int(sx), int(sy)

    def get_offset(self):
        ox, oy = self.position

        return -ox, -oy

    def draw(self, sub_screen, layers):
        for layer in layers:
            layer.draw(sub_screen, self.get_offset())

        if self.visible:
            for r in self.regions:
                r.draw(sub_screen, self.get_offset())

            xa, ya = self.anchor
            rx, ry = self.reticle
            if xa:
                self.x_anchor.draw(
                    sub_screen, (xa, ry),
                    self.WINDOW_COLOR)

            if ya:
                self.y_anchor.draw(
                    sub_screen, (rx, ya),
                    self.WINDOW_COLOR)

    def outside_window(self, window, world_px):
        r = window.pygame_rect
        rx, ry = r.topleft
        x, y = self.position
        x += rx
        y += ry

        if r.collidepoint(world_px):
                return False

        else:
            wx, wy = world_px
            dx = 0
            if wx > r.right:
                dx = wx - r.right
            if wx < r.left:
                dx = wx - r.left

            dy = 0
            if wy > r.bottom:
                dy = wy - r.bottom
            if wy < r.top:
                dy = wy - r.top

            return dx, dy

    def move(self, world_px_distance):
        # scale screen pixel delta
        dx, dy = world_px_distance
        # dx *= self.scale
        # dy *= self.scale

        # focus point = focus point + delta
        x, y = self.focus_point
        x += dx
        y += dy

        self.focus_point = x, y

    def track(self, world_px, rate, screen_px=None):
        wx, wy = world_px

        if not screen_px:
            fx, fy = self.focus_point
        else:
            fx, fy = self.get_world_px(screen_px)

        # delta = world pixel value - focus_point
        dx = wx - fx
        dy = wy - fy

        # delta interpolated by rate
        dx *= rate
        dy *= rate

        tracking = self.Vector("tracking", dx, dy)
        self.apply_force(tracking)

    def window_track(self, window, world_px, rate):
        outside = self.outside_window(window, world_px)

        if outside:
            fx, fy = self.focus_point
            dx, dy = outside
            self.track((fx + dx, fy + dy), rate)

    def anchor_track(self, world_px, rate):
        wx, wy = world_px
        xa, ya = self.anchor
        rx, ry = self.reticle
        fx, fy = self.focus_point

        sx, sy = xa, ya

        # X ANCHOR
        if xa:
            sy = ry
            wy = fy

        if ya:
            sx = rx
            wx = fx

        self.track((wx, wy), rate,
                   screen_px=(sx, sy))


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
            "Toggle visibility": lambda: self.set_visible(not self.visible)
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

    def update(self):
        super(CameraLayer, self).update()

        self.camera.apply_acceleration()
        for func in self.track_functions:
            func()

        for system in self.collision_systems:
            system()

        self.camera.velocity.round()
        self.camera.apply_velocity()
        self.camera.velocity.scale(0)

    @staticmethod
    def get_collision_vars(camera, wall):
        angle = wall.get_angle()
        r = camera.collision_region
        p1, p2 = wall.origin, wall.end_point

        return angle, r, p1, p2

    @staticmethod
    def check_collision(camera, wall):
        angle, r, p1, p2 = CameraLayer.get_collision_vars(
            camera, wall
        )
        r = r.pygame_rect
        v = camera.velocity
        vx, vy = v.get_value()
        r.x += vx
        r.y += vy

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
                if not (r.bottom < p1[1] or r.top > p2[1]):
                    collision = True

        if collision:
            return wall.axis_collision(
                camera.collision_point, v)

    @staticmethod
    def check_edge_collision(camera, wall):
        angle, r, p1, p2 = CameraLayer.get_collision_vars(
            camera, wall
        )
        v = camera.velocity
        vx, vy = v.get_value()

        r = r.pygame_rect
        r.x += vx
        r.y += vy

        collision = False
        mid_x = (p1[0] + p2[0]) / 2
        mid_y = (p1[1] + p2[1]) / 2

        # BOTTOM EDGE >
        if angle == 0:
            if r.bottom > mid_y:
                    collision = True

        # RIGHT EDGE ^
        if angle == .25:
            if r.right > mid_x:
                    collision = True

        # TOP EDGE <
        if angle == .5:
            if r.top < mid_y:
                    collision = True

        # LEFT EDGE v
        if angle == .75:
            if r.left < mid_x:
                    collision = True

        if collision:
            return wall.axis_collision(
                camera.collision_point, v)

    @staticmethod
    def handle_collision(camera, wall):
        angle, r, p1, p2 = CameraLayer.get_collision_vars(
            camera, wall
        )
        r = r.pygame_rect

        if angle == 0:
            r.bottom = p1[1]

        if angle == .25:
            r.right = p1[0]

        if angle == .5:
            r.top = p1[1]

        if angle == .75:
            r.left = p1[0]

        camera.focus_point = r.center

        if angle == 0 or angle == .5:
            camera.velocity.j_hat = 0

        if angle == .25 or angle == .75:
            camera.velocity.i_hat = 0

    def set_camera_bounds_region(self, size, position=(0, 0),
                                 orientation=False, **kwargs):
        region = RectRegion(
            "camera bounds", size, position,
            orientation=orientation, **kwargs)

        self.collision_systems.append(
            region.get_collision_system(
                [self.camera], self.check_collision,
                self.handle_collision)
        )

        self.regions.append(region)

    def set_camera_bounds_edge(self, value, angle=0):
        w, h = self.camera.screen_size
        if angle == 0:
            start, end = (0, value), (w, value)
        elif angle == .25:
            start, end = (value, h), (value, 0)
        elif angle == .5:
            start, end = (w, value), (0, value)
        elif angle == .75:
            start, end = (value, 0), (value, h)
        else:
            raise ValueError("{} not orthogonal angle".format(angle))

        wall = Wall(start, end)

        def collision_system():
            if self.check_edge_collision(self.camera, wall):
                self.handle_collision(self.camera, wall)

        self.collision_systems.append(
            collision_system)

        self.regions.append(wall)

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
            # direction = sprite.direction
            vx, vy = velocity
            # dx, dy = direction

            left = vx < 1
            right = vx > 1
            up = vx < -1
            down = vx > 1

            x, y = 0, 0
            if left or right:
                x = vx * -rate
            if up or down:
                y = vy * -rate

            window.shift((x, y))

        self.track_functions.append(set_heading)

    def set_scale_tracking_function(self, get_scale, span):
        meter = Meter("span", span[0], span[0], span[1])

        def set_scale():
            meter.value = get_scale()
            self.camera.scale = round(meter.value, 3)

        self.track_functions.append(set_scale)

    def add_bg_layer(self, layer):
        self.bg_layers.append(layer)

    def draw(self, screen, offset=(0, 0)):
        sub_rect = self.rect.clip(screen.get_rect())

        try:
            canvas = screen.subsurface(sub_rect)
        except ValueError:      # if the layer's area is entirely outside of the screen's
            return              # area, it doesn't get drawn

        canvas.fill((0, 0, 0))

        if self.camera.scale > 1:
            w, h = self.size
            w /= self.camera.scale
            h /= self.camera.scale
            sub_screen = pygame.Surface((w, h))

            self.draw_bg_layers(sub_screen)
            self.camera.draw(
                sub_screen, self.sub_layers)

            sx, sy = self.size
            pygame.transform.scale(
                sub_screen, (int(sx), int(sy)),
                canvas)

        else:
            self.draw_bg_layers(canvas)
            self.camera.draw(
                canvas, self.sub_layers)

    def draw_bg_layers(self, screen):
        for layer in self.bg_layers:
            layer.draw(
                screen, self.camera.get_offset())


class ParallaxBgLayer(Layer):
    def __init__(self, image, scale, buffer=(0, 0), wrap=(False, False), **kwargs):
        super(ParallaxBgLayer, self).__init__("bg layer", **kwargs)

        self.set_up_graphics(image, buffer)

        self.scale = scale
        self.wrap = wrap

    def set_up_graphics(self, image, buffer):
        self.graphics = IconGraphics(self, image)

        w, h = image.get_size()
        w += buffer[0]
        h += buffer[1]
        self.size = w, h

    @staticmethod
    def get_bg_image(image_name):
        path = join(BG_LAYERS, image_name)
        image = pygame.image.load(path)
        image.set_colorkey(image.get_at((0, 0)))

        return image

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
                    self.graphics.draw_walls(
                        screen, offset=(ox, oy))

        elif x_wrap:
            for i in range((sw // w) + 2):
                ox = x + ((i - 1) * w)

                self.graphics.draw(
                    screen, offset=(ox, y))

        elif y_wrap:
            for j in range((sh // h) + 2):
                oy = y + ((j - 1) * h)
                self.graphics.draw_walls(
                    screen, offset=(x, oy))

        else:
            self.graphics.draw_walls(
                screen, offset=(x, y))
