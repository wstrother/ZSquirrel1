from os.path import join

import pygame

from zs_constants.paths import ANIMATIONS, ANIMATION_STREAMS
from zs_src.graphics import Graphics, ImageSet


class AnimationGraphics(Graphics):
    def __init__(self, sprite_sheet, entity, get_image_state):
        super(AnimationGraphics, self).__init__(entity, get_image_state)

        path = join(ANIMATIONS, sprite_sheet)
        sprite_sheet = pygame.image.load(path)
        sprite_sheet.set_colorkey(sprite_sheet.get_at((0, 0)))
        self.sprite_sheet = sprite_sheet

    def get_hitbox(self):
        animation = self.get_image_set()
        w, h, x, y = animation.hitbox

        return pygame.Rect((x, y), (w, h))

    def get_frame_number(self):
        return self.get_image_set().current_frame

    def animation_completed(self):
        return self.get_image_set().loops > 0

    def reset_animations(self):
        for name in self.image_sets:
            self.image_sets[name].reset()

    def set_animation(self, name, stream):
        animation = Animation(name, self.sprite_sheet, stream)
        self.image_sets[name] = animation

    def set_mirror_animation(self, name, stream):
        animation = Animation(name, self.sprite_sheet, stream)

        mirror_images = {}
        for image in animation.images:
            i = animation.images.index(image)

            h = hash(image)
            if h not in mirror_images:
                mirror_image = pygame.transform.flip(image, True, False)
                mirror_images[h] = mirror_image
            else:
                mirror_image = mirror_images[h]

            animation.images[i] = mirror_image

        i = 0
        for hitbox in animation.hitboxes:
            w, h, ox, oy = hitbox
            cw, ch = animation.cell_size

            ox = cw - (w + ox)
            animation.hitboxes[i] = w, h, ox, oy
            i += 1

        self.image_sets[name] = animation

    def set_up_animations(self, stream_file):
        path = join(ANIMATION_STREAMS, stream_file)

        file = open(path, "r")
        sections = file.read()
        file.close()

        sections = sections.split("#")
        for section in sections:
            if section:
                lines = section.split("\n")
                name = lines.pop(0)

                if not lines[-1]:
                    lines.pop(-1)

                stream = self.get_stream(lines)

                self.set_animation(name, stream)

    @staticmethod
    def get_stream(lines):
        stream = []
        i = 0
        last_hitbox = None
        for line in lines:
            line = line.split()

            def get(x):
                return int(line[x])

            if i == 0:
                cell_w = get(0)
                cell_h = get(1)
                frame_l = get(2)
                last_hitbox = 0, 0, cell_w, cell_w

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
                    w = get(2)
                    h = get(3)
                    ox = get(4)
                    oy = get(5)
                    last_hitbox = w, h, ox, oy

                else:
                    w, h, ox, oy = last_hitbox

                new_line = (i, j), (w, h, ox, oy)
                stream.append(new_line)
            i += 1

        return stream


class LeftRightGraphics(AnimationGraphics):
    def set_animation(self, name, stream):
        super(LeftRightGraphics, self).set_animation("right_" + name, stream)
        self.set_mirror_animation("left_" + name, stream)


class Animation(ImageSet):
    def __init__(self, name, sprite_sheet, stream):
        super(Animation, self).__init__(name, [])
        self.frames = []
        self.hitboxes = []
        self.hitbox_type = "a"
        self.stream = stream
        self.animation_complete = False

        self.header = None
        self.apply_stream(sprite_sheet, stream)

    @property
    def hitbox(self):
        return self.hitboxes[self.hitbox_index]

    @property
    def hitbox_index(self):
        return self.current_frame // self.frame_length

    @property
    def frame_length(self):
        return self.header[1]

    @property
    def cell_size(self):
        return self.header[0]

    @property
    def start_position(self):
        return self.header[2]

    def apply_stream(self, sprite_sheet, stream):
        header = stream[0]  # ((cw, ch), fl, (sx, sy))
        self.header = header
        cell_size = header[0]
        frame_length = header[1]
        start = header[2]

        frames = []
        hitboxes = []
        for line in stream[1:]:             # ((i, j), (w, h, ox, oy))
            frames.append(line[0])
            hitboxes.append(line[1])

        self.frames = frames
        self.hitboxes = hitboxes
        self.make_images(sprite_sheet, cell_size, frame_length, start)

    def make_images(self, sprite_sheet, cell_size, frame_length=1, start=(0, 0)):
        images = []
        w, h = cell_size
        sx, sy = start
        for frame in self.frames:
            # print(frame)
            x, y = frame
            x *= w
            y *= h

            position = x + (sx * w), y + (sy * h)
            r = pygame.Rect(position, cell_size)

            cell = sprite_sheet.subsurface(r)
            images += ([cell] * frame_length)

        self.set_images(images)
