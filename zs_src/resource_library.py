import json
from os.path import join

import pygame

from zs_constants.paths import IMAGES, SOUNDS, RESOURCE_DICTS

pygame.init()
load_image = pygame.image.load
load_sound = pygame.mixer.Sound


def load_json(file_name):
    path = join(RESOURCE_DICTS, file_name + ".json")

    file = open(path, "r")
    d = json.load(file)
    file.close()

    return d


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


def get_resources(name):
    rd = load_json(name)

    rl = ResourceLibrary()
    if "images" in rd:
        for name in rd["images"]:
            rl.add_image(name)

    if "sounds" in rd:
        for name in rd["sounds"]:
            rl.add_sound(name)

    if "fonts" in rd:
        for name in rd["fonts"]:
            entry = rd["fonts"][name]
            font_name, size = entry[0], entry[1]
            args = entry[2:]
            rl.add_font(name, font_name, size, *args)

    return rl

