import json
from copy import deepcopy
from os.path import join

from zs_constants import paths
from zs_constants.zs import GLOBAL_STYLE_DICT, GLOBAL_RESOURCE_DICT
from zs_src.resource_library import get_resources

BG_STYLE = "bg_style"
ALIGN_H = "align_h"
ALIGN_V = "align_v"
BORDER_SIDES = "border_sides"
BORDER_CORNERS = "border_corners"
BUFFERS = "buffers"
COLORS = "colors"
IMAGES = "images"
SOUNDS = "sounds"
FONTS = "fonts"

TILE = "tile"
STRETCH = "stretch"
CENTER = "center"

L = "l"
C = "c"
R = "r"
T = "t"
B = "b"
A = "a"
D = "d"

TEXT = "text"
CELL = "cell"
BG = "bg"
SELECTED = "selected"
UNSELECTED = "unselected"
ACTIVE = "active"
ALPHA = "alpha"

BORDER_CORNER = "border_corner"
BORDER_H_SIDE = "border_h_side"
BORDER_V_SIDE = "border_v_side"

SELECT = "select"
ACTIVATE = "activate"

BG_STYLES = (TILE, STRETCH, CENTER, "")
ALIGNS_H = (L, C, R)
ALIGNS_V = (T, C, B)
BORDER_SIDE_CHOICES = (T, L, R, B)
BORDER_CORNER_CHOICES = (A, B, C, D)
BUFFER_KEYS = (TEXT, CELL)
COLOR_KEYS = (BG, TEXT, SELECTED, UNSELECTED, ACTIVE, ALPHA)
IMAGE_KEYS = (BG, BORDER_CORNER, BORDER_H_SIDE, BORDER_V_SIDE)
SOUND_KEYS = (SELECT, ACTIVATE)
FONT_KEYS = ("main", "title")


def load_json(path, filename):
    path = join(join(path, filename + ".json"))
    file = open(path, "r")
    j_dict = json.load(file)
    file.close()

    return j_dict


class Style:
    DEFAULT_DICT = load_json(paths.STYLE_DICTS, GLOBAL_STYLE_DICT)     # default style_dict
    RESOURCES = get_resources(GLOBAL_RESOURCE_DICT)
    KEYS = (BG_STYLE,
            ALIGN_H,
            ALIGN_V,
            BORDER_SIDES,
            BORDER_CORNERS,
            BUFFERS,
            COLORS,
            IMAGES,
            SOUNDS,
            FONTS)

    def __init__(self, style_dict=None):
        self._style_dict = deepcopy(Style.DEFAULT_DICT)
        self.resources = Style.RESOURCES

        if style_dict:
            self.change_dict(style_dict)

    def change_dict(self, change_dict):
        for key in change_dict:
            item = change_dict[key]

            if type(item) == dict:
                self._style_dict[key].update(item)
            else:
                self._style_dict[key] = item

        self.fix_style_dict()

    def print_dict(self):
        sd = self._style_dict
        keys = Style.KEYS

        for key in keys:
            entry = sd[key]
            if type(entry) == dict:
                print("{:>16} :".format(key))
                for name in entry:
                    print("{:>16}{:>16} : {}".format(" ", name, entry[name]))
                print("")
            else:
                print("{:>16} : {}".format(key, sd[key]))

    def fix_style_dict(self):
        keys = Style.KEYS
        style_dict = self._style_dict
        entries = [style_dict[key] for key in Style.KEYS]

        self.set_bg_style(entries[0], keys[0])
        self.set_align_h(entries[1], keys[1])
        self.set_align_v(entries[2], keys[2])
        self.set_border_sides(entries[3], keys[3])
        self.set_border_corners(entries[4], keys[4])
        self.set_buffers(entries[5], keys[5])
        self.set_colors(entries[6], keys[6])
        self.set_images(entries[7], keys[7])
        self.set_sounds(entries[8], keys[8])
        self.set_fonts(entries[9], keys[9])

    @staticmethod
    def check_value(value, key, choices):
        if value not in choices:
            msg = "bad value '{}' passed for style_dict key {}".format(value, key)
            raise ValueError(msg)

    def set_bg_style(self, entry, key):
        self.check_value(entry, key, BG_STYLES)

    def set_align_h(self, entry, key):
        self.check_value(entry, key, ALIGNS_H)

    def set_align_v(self, entry, key):
        self.check_value(entry, key, ALIGNS_V)

    def check_perm(self, entry, key, choices):
        perm = ""

        for element in entry:
            if element in choices:
                perm += element

        self._style_dict[key] = perm

    def set_border_sides(self, entry, key):
        self.check_perm(entry, key, BORDER_SIDE_CHOICES)

    def set_border_corners(self, entry, key):
        self.check_perm(entry, key, BORDER_CORNER_CHOICES)

    def check_dict(self, sub_dict, key, sub_keys):
        for sub_key in sub_keys:
            if sub_key not in sub_dict:
                sub_dict[sub_key] = Style.DEFAULT_DICT[key][sub_key]

        self._style_dict[key] = sub_dict

    def set_colors(self, entry, key):
        self.check_dict(entry, key, COLOR_KEYS)

    def set_images(self, entry, key):
        self.check_dict(entry, key, IMAGE_KEYS)

    def set_sounds(self, entry, key):
        self.check_dict(entry, key, SOUND_KEYS)

    def set_fonts(self, entry, key):
        self.check_dict(entry, key, FONT_KEYS)

    def set_buffers(self, entry, key):
        self.check_dict(entry, key, BUFFER_KEYS)

    @property
    def bg_style(self):
        return self._style_dict[BG_STYLE]

    @property
    def bg_image(self):
        return self.get_image(BG)

    @property
    def aligns(self):
        return self.align_h, self.align_v

    @property
    def align_h(self):
        return self._style_dict[ALIGN_H]

    @property
    def align_v(self):
        return self._style_dict[ALIGN_V]

    @property
    def border_style(self):
        sd = self._style_dict
        sides, corners = BORDER_SIDES, BORDER_CORNERS
        return sd[sides], sd[corners]

    @property
    def border_size(self):
        corner = self.get_image(BORDER_CORNER)
        return corner.get_size()

    @property
    def border_images(self):
        keys = (BORDER_H_SIDE,
                BORDER_V_SIDE,
                BORDER_CORNER)
        h_side, v_side, corner = [self.get_image(key) for key in keys]

        return h_side, v_side, corner

    @property
    def colors(self):
        return self._style_dict[COLORS]

    @property
    def images(self):
        return self._style_dict[IMAGES]

    def get_image(self, key):
        file_name = self.images[key]

        return self.resources[file_name]

    @property
    def sounds(self):
        return self._style_dict[SOUNDS]

    def get_sound(self, key):
        file_name = self.sounds[key]

        return self.resources[file_name]

    @property
    def fonts(self):
        return self._style_dict[FONTS]

    def get_font(self, key):
        name = self.fonts[key]

        return self.resources[name]

    @property
    def buffers(self):
        return self._style_dict[BUFFERS]


class StyleInterface:
    def __init__(self, style_dict=None):
        self._style = Style(style_dict)

    @property
    def style(self):
        return self._style

    @style.setter
    def style(self, value):
        self.adjust_style(value)

    def adjust_style(self, value):
        self._style.change_dict(value)
