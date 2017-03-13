from zs_constants.gui import DPAD, A, B
from zs_constants.zs import SCREEN_SIZE
from zs_src.classes import CollisionSystem
from zs_src.entities import Layer, Region
from zs_src.geometry import Wall, Vector
from zs_src.graphics import BgGraphics
from zs_src.style import Style


class RegionLayer(Layer):
    def __init__(self, *args, **kwargs):
        super(RegionLayer, self).__init__(*args, **kwargs)

        self.vectors_visible = False

    @staticmethod
    def get_vectors(group):
        walls = []

        for region in group:
            walls += region.walls

        return walls

    @staticmethod
    def smooth_sprite_collision_system(items, group):
        walls = RegionLayer.get_vectors(group)
        check = Wall.sprite_collision
        handle = Wall.handle_collision_smooth

        return CollisionSystem.group_collision_system(check, handle, items, walls)

    def draw(self, screen, offset=(0, 0)):
        super(RegionLayer, self).draw(screen, offset=offset)
        for g in self.groups:

            if self.vectors_visible:
                for item in g:
                    item.draw_vectors(screen, offset=offset)


class VectorFieldLayer(RegionLayer):
    def __init__(self, name, **kwargs):
        super(VectorFieldLayer, self).__init__(name, **kwargs)

        # self.style = Style({"images": {"bg": "test_bg.png"}})
        # self.graphics = BgGraphics(self)
        self.vectors_visible = True


class VectorGrid(Region):
    def __init__(self, name, origin=(0, 0), **kwargs):
        if "size" not in kwargs:
            w, h = SCREEN_SIZE
            w *= 1.5
            h *= 1.5
            kwargs["size"] = w, h
        super(VectorGrid, self).__init__(name, **kwargs)

        self.rect.center = origin
        self.grid_vectors = []
        self.add_grid_vectors()

        self.style = Style({"images": {"bg": "test_bg.png"}})
        self.graphics = BgGraphics(self)

    @property
    def non_grid_vectors(self):
        gv = self.grid_vectors

        return [
            v for v in self.vectors if v not in gv
        ]

    def add_vector(self, vector, grid=False):
        if not grid:
            ox,  oy = vector.origin
            px, py = self.rect.center
            ox += px
            oy += py
            vector.origin = ox, oy

        super(VectorGrid, self).add_vector(vector)

    def add_grid_vectors(self):
        origin = self.rect.center
        w, h = self.size
        w /= 2
        h /= 2

        args_list = [
            ("positive x axis", w, 0),
            ("negative x axis", -w, 0),
            ("positive y axis", 0, h),
            ("negative y axis", 0, -h)
        ]

        for args in args_list:
            v = Vector(*args, origin=origin)
            self.add_vector(v, grid=True)
            self.grid_vectors.append(v)

    def move(self, value):
        super(VectorGrid, self).move(value)

        for v in self.grid_vectors:
            v.move(value)

    def rotate_grid(self, angle):
        for v in self.grid_vectors:
            v.rotate_around(
                self.rect.center, angle)

    def rotate_non_grid(self, angle):
        for v in self.non_grid_vectors:
            v.rotate_around(
                self.rect.center, angle)

    def adjust_coordinates(self, point):
        px, py = point
        ox, oy = self.rect.center
        px -= ox
        py -= oy

        return px, py

    def update(self):
        super(VectorGrid, self).update()

        devices = self.controller.devices
        a, b = devices[A], devices[B]
        dpad = devices[DPAD]

        x, y = dpad.get_direction()
        angle = 1/32 * -x
        g_angle = 1/32 * -y

        move = 5
        x *= move
        y *= move

        cursor = self.get_value("Cursor")
        vector = self.get_value("Cursor Vector")
        cursor_layer = self.get_value("Cursor Layer")

        cursor_layer.active = not a.held

        if a.held and not b.held:
            self.move((x, y))

        if b.held and not a.held:
            vector.move((x, y))

        if a.held and b.held and dpad.check():
            self.rotate_non_grid(angle)
            self.rotate_grid(g_angle)

            cx, cy = vector.apply_to_point(vector.origin)
            cursor.rect.center = cx, cy

        if vector:
            cx, cy = cursor.rect.center
            ox, oy = vector.origin
            dx = cx - ox
            dy = cy - oy
            vector.set_value((dx, dy))

    def report_cursor(self):
        vector = self.get_value("Cursor Vector")
        origin = self.adjust_coordinates(vector.origin)
        text = [
            "Vector: {:3.1f}i + {:3.1f}j".format(*vector.get_value()),
            "Origin: {:3.1f}, {:3.1f}".format(*origin)
        ]

        return text

    def report_line(self):
        vector = self.get_value("Cursor Vector")
        y_int = vector.get_y_intercept(self.rect.center)
        dx, dy = vector.get_value()

        slope = 0
        nan = dx == 0

        if not nan:
            slope = dy / dx

        c = round(y_int, 3)
        m = round(slope, 3)

        if nan:
            return "y = NaN"

        elif dy == 0:
            return "y = {}".format(c)

        else:
            return "y = {}x + {}".format(m, c)

    def report_collision(self):
        c_vector = self.get_value("Cursor Vector")
        test_vector = self.get_value("Test Vector")

        ac = c_vector.axis_collision(test_vector)
        vc = c_vector.vector_collision(test_vector)
        f_str = "{:3.1f}, {:3.1f}"

        if not ac:
            ac_text = "False"
        else:
            ac_text = f_str.format(
                *self.adjust_coordinates(ac))

        if not vc:
            vc_text = "False"
        else:
            vc_text = f_str.format(
                *self.adjust_coordinates(vc))

        return "  Axis: {}\nVector: {}".format(
            ac_text, vc_text
        )

