from zs_src.graphics import Graphics, ImageSet
from pygame import Rect


class AnimationGraphics(Graphics):
    def __init__(self, sprite_sheet, *args, **kwargs):
        super(AnimationGraphics, self).__init__(*args, **kwargs)

        sprite_sheet.set_colorkey(sprite_sheet.get_at((0, 0)))
        self.sprite_sheet = sprite_sheet

    def set_animation(self, name, stream):
        animation = Animation(name, self.sprite_sheet, stream)
        self.image_sets[name] = animation

    @staticmethod
    def get_stream(lines):
        stream = []
        i = 0
        last_hitbox = None
        for line in lines:
            line = line.split()
            get = lambda x: int(line[x])

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


class Animation(ImageSet):
    def __init__(self, name, sprite_sheet, stream):
        super(Animation, self).__init__(name, [])
        self.frames = []
        self.hitboxes = []
        self.hitbox_type = "a"
        self.stream = stream

        self.apply_stream(sprite_sheet, stream)

    @property
    def hitbox(self):
        return self.hitboxes[self.current_frame]

    def apply_stream(self, sprite_sheet, stream):
        header = stream.pop(0)  # ((cw, ch), fl, (sx, sy))
        cell_size = header[0]
        frame_length = header[1]
        start = header[2]

        frames = []
        hitboxes = []
        for line in stream:             # ((i, j), (w, h, ox, oy))
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
            x, y = frame
            x *= w
            y *= h

            position = x + sx, y + sy
            r = Rect(position, cell_size)

            cell = sprite_sheet.subsurface(r)
            images += ([cell] * frame_length)

        self.set_images(images)
