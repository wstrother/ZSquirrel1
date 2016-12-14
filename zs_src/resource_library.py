from os.path import join
from zs_constants.paths import IMAGES, SOUNDS
import pygame

load_image = pygame.image.load
load_sound = pygame.mixer.Sound


class ResourceLibrary(dict):
    def add_image(self, file_name):
        path = join(IMAGES, file_name)
        self[file_name] = load_image(path)

    def add_sound(self, file_name):
        path = join(SOUNDS, file_name)
        self[file_name] = load_sound(path)

    def add_font(self, key, name, size, *args):
        bold = "bold" in args
        italic = "italic" in args
        path = pygame.font.match_font(name, bold, italic)

        self[key] = pygame.font.Font(path, size)


def get_resources(rd):
    rl = ResourceLibrary()
    for name in rd["images"]:
        rl.add_image(name)

    for name in rd["sounds"]:
        rl.add_sound(name)

    for name in rd["fonts"]:
        entry = rd["fonts"][name]
        font_name, size = entry[0], entry[1]
        args = entry[2:]
        rl.add_font(name, font_name, size, *args)

    return rl

