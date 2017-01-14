from os.path import join

import pygame

from zs_constants.paths import ANIMATIONS, ANIMATION_STREAMS
from zs_src.graphics import Graphics, ImageSet


class AnimationGraphics(Graphics):
    def __init__(self, sprite_sheet, stream_file, entity, get_image_state):
        super(AnimationGraphics, self).__init__(entity, get_image_state)

        self.sprite_sheet = self.get_sprite_sheet(sprite_sheet)
        self.set_up_animations(stream_file)

    @staticmethod
    def get_sprite_sheet(name):
        path = join(ANIMATIONS, name)
        sprite_sheet = pygame.image.load(path)
        sprite_sheet.set_colorkey(sprite_sheet.get_at((0, 0)))

        return sprite_sheet

    def get_hitbox(self):
        animation = self.get_image_set()
        if animation:
            w, h, x, y = animation.hitbox

            return pygame.Rect((x, y), (w, h))
        else:
            return self.entity.rect

    def get_frame_number(self):
        if self.get_image_set():
            return self.get_image_set().current_frame
        else:
            return 0

    def animation_completed(self):
        if self.get_image_set():
            return self.get_image_set().loops > 0
        else:
            return True

    def reset_animations(self):
        for name in self.image_sets:
            self.image_sets[name].reset()

    def set_animation(self, name, stream):
        animation = stream.get_animation(
            name, self.sprite_sheet)
        self.image_sets[name] = animation

    def set_up_animations(self, stream_file):
        stream = StreamManager(stream_file)

        for name in stream.stream_dict:
            self.set_animation(name, stream)


class LeftRightGraphics(AnimationGraphics):
    def __init__(self, sprite_sheet, stream_file, entity, get_image_state):
        self.mirror_sprite_sheet = pygame.transform.flip(
            self.get_sprite_sheet(sprite_sheet), True, False)

        super(LeftRightGraphics, self).__init__(sprite_sheet, stream_file, entity, get_image_state)

    def set_animation(self, name, stream):
        animation = stream.get_animation(
            name, self.sprite_sheet)
        self.image_sets["right_" + name] = animation

        animation = stream.get_animation(
            name, self.mirror_sprite_sheet,
            mirror=True)
        self.image_sets["left_" + name] = animation


class Animation(ImageSet):
    def __init__(self, name, sprite_sheet, stream, hitboxes, mirror=False):
        super(Animation, self).__init__(name, [])
        self._hitboxes = hitboxes
        self._stream = stream
        self.animation_complete = False

        self._header = None
        self.apply_stream(sprite_sheet, mirror=mirror)

        if mirror:
            self.reverse_hitboxes()

    def reverse_hitboxes(self):
        cw, ch = self.cell_size
        hitboxes = []

        for hitbox in self._hitboxes:
            if len(hitbox) == 4:
                w, h, ox, oy = hitbox

                ox = cw - (ox + w)
                hitbox = w, h, ox, oy

            hitboxes.append(hitbox)

        self._hitboxes = hitboxes

    @property
    def hitbox(self):
        return self.hitboxes[0]

    @property
    def hitboxes(self):
        h_indexes = self._stream[self.stream_index][1]

        return [self._hitboxes[i] for i in h_indexes]

    @property
    def stream_index(self):
        return self.current_frame // self.frame_length + 1

    @property
    def frame_length(self):
        return self._header[1]

    @property
    def cell_size(self):
        return self._header[0]

    @property
    def start_position(self):
        return self._header[2]

    def apply_stream(self, sprite_sheet, mirror=False):
        stream = self._stream
        header = stream[0]  # ((cw, ch), fl, (sx, sy))
        self._header = header

        cell_size = header[0]
        frame_length = header[1]
        start = header[2]
        self.make_images(sprite_sheet, cell_size,
                         frame_length, start, mirror)

    def make_images(self, sprite_sheet, cell_size, frame_length=1,
                    start=(0, 0), mirror=False):
        images = []
        w, h = cell_size
        sx, sy = start
        cw, ch = sprite_sheet.get_size()

        for frame in self._stream[1:]:
            x, y = frame[0]
            x *= w
            y *= h

            px, py = x + (sx * w), y + (sy * h)
            if mirror:
                px = (cw - w) - px
                # py = (ch - h) - py
            position = px, py

            r = pygame.Rect(position, cell_size)
            cell = sprite_sheet.subsurface(r)
            images += ([cell] * frame_length)

        self.set_images(images)


class StreamManager:
    class Section:
        def __init__(self, name, stream, hitboxes):
            self.name = name
            self.stream = stream
            self.hitboxes = hitboxes

    def __init__(self, stream_file):
        self.stream_dict = self.get_stream_dict(stream_file)

    def get_animation(self, name, sprite_sheet, **kwargs):
        section = self.stream_dict[name]
        stream = section.stream
        hitboxes = section.hitboxes

        animation = Animation(
            name, sprite_sheet, stream,
            hitboxes, **kwargs
        )
        return animation

    def get_stream_dict(self, stream_file):
        path = join(ANIMATION_STREAMS, stream_file)

        file = open(path, "r")
        stream_sections = file.read()
        file.close()

        stream_sections = stream_sections.split("#")

        stream_dict = {}
        hitboxes = []
        for section in stream_sections:
            if section:
                lines = section.split("\n")
                name = lines.pop(0)

                if not lines[-1]:
                    lines.pop(-1)

                if name == "hitboxes":
                    hitboxes = []
                    for line in lines:
                        hitboxes.append(tuple([int(n) for n in line.split()]))
                else:
                    stream = self.get_stream(lines)
                    stream_dict[name] = self.Section(name, stream, hitboxes)

        return stream_dict

    @staticmethod
    def get_stream(lines):
        stream = []
        i = 0
        for line in lines:
            line = line.split()

            def get(x):
                return int(line[x])

            if i == 0:
                cell_w = get(0)
                cell_h = get(1)
                frame_l = get(2)

                if len(line) == 3:
                    start = 0, 0
                else:
                    start = get(3), get(4)

                new_line = (cell_w, cell_h), frame_l, start
                stream.append(new_line)

            else:
                i = get(0)
                j = get(1)

                if len(line) > 2:
                    hitboxes = tuple(
                        [get(i) for i in range(2, len(line))])

                else:
                    hitboxes = (0,)

                new_line = (i, j), hitboxes
                stream.append(new_line)
            i += 1

        return stream
