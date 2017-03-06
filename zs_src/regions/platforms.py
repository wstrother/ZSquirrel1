import pygame

from zs_constants.paths import TILESETS
from zs_src.entities import Region
from zs_src.geometry import Wall
from zs_src.graphics import Graphics


class PlatformGraphics(Graphics):
    def __init__(self, entity):
        super(PlatformGraphics, self).__init__(entity)

    def reset_image(self):
        self.set_default_image(
            self.get_platform_image())

    @staticmethod
    def get_px_width(length):
        start, mid, end = PlatformGraphics.get_tree_tiles()
        sw, sh = start.get_size()
        mw, mh = mid.get_size()
        ew, eh = end.get_size()

        return sw + (mw * (length - 1)) + ew

    @staticmethod
    def get_tree_tiles():
        start, mid, end = (
            PlatformGraphics.load_image(
                TILESETS, "treestart.gif"),
            PlatformGraphics.load_image(
                TILESETS, "treemid.gif"),
            PlatformGraphics.load_image(
                TILESETS, "treeend.gif")
        )

        return start, mid, end

    def get_platform_image(self):
        start, mid, end = self.get_tree_tiles()

        angle = self.entity.get_angle()

        sw, sh = start.get_size()
        mw, mh = mid.get_size()
        ew, eh = end.get_size()

        length = self.entity.plat_length
        width = self.get_px_width(length)
        height = sh

        surface = pygame.Surface((width, height))
        surface.fill((255, 255, 255))
        surface.blit(start, (0, 0))
        for i in range(length - 1):
            surface.blit(mid, (sw + (i * mw), 0))
        surface.blit(end, (width - ew, 0))

        surface = pygame.transform.rotate(surface, angle * 360)
        surface.set_colorkey(
            surface.get_at((0, 0))
        )

        return surface


class TreePlat(Region):
    def __init__(self, length=1, angle=0.0, origin=(0, 0), **kwargs):
        width = PlatformGraphics.get_px_width(length)
        ox, oy = origin
        wall = Wall(origin, (ox + width, oy), **kwargs)
        wall.rotate(angle)

        self.plat_length = length
        self.get_angle = wall.get_angle
        self.normal = wall.normal

        super(TreePlat, self).__init__(
            "platform")
        self.graphics = PlatformGraphics(self)

        self.walls = [wall]

    @property
    def position(self):
        image = self.graphics.get_image()
        r = pygame.Rect((0, 0), image.get_size())

        wall = self.walls[0]
        sx, sy = wall.origin
        ex, ey = wall.end_point

        mx = (sx + ex) / 2
        my = (sy + ey) / 2
        r.center = mx, my

        return r.topleft

    @position.setter
    def position(self, value):
        pass

    def update(self):
        super(TreePlat, self).update()
