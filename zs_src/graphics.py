from pygame import Surface
from pygame.constants import SRCALPHA
from pygame.transform import scale, flip

from zs_constants.style import BG_STYLES, BORDER_CORNER_CHOICES, BG, ALPHA
from zs_constants.zs import TEXT_ANTI_ALIAS, SCREEN_SIZE
from zs_src.classes import Meter
from zs_src.style import Style


class ImageSet:
    def __init__(self, name, images):
        self.name = name
        self.loops = 0
        self.images = None
        self._meter = None

        if images:
            self.set_images(images)

    def set_images(self, images):
        self.images = images
        self._meter = Meter(self.name, 0, maximum=len(images) - 1)

    @property
    def max_frame(self):
        return len(self.images) - 1

    @property
    def current_frame(self):
        return self._meter.value

    def next_frame(self):
        v = self.current_frame
        self._meter.next()
        dv = self.current_frame - v

        if dv != 1:
            self.loops += 1

    def get_image(self):
        return self.images[self.current_frame]

    def reset(self):
        self._meter.reset()
        self.loops = 0


class Graphics:
    CLEAR_IMG = Surface((1, 1))
    CLEAR_IMG.set_alpha(255)

    def __init__(self, entity, get_image_state=None):
        self.name = entity.name
        self.id_num = entity.id_num
        self.entity = entity
        self.image_sets = {}

        if get_image_state:
            self.get_image_state = get_image_state
        else:
            self.get_image_state = lambda: "default"

        self.reset_image()

    def set_default_image(self, *images):
        default = ImageSet("default", images)
        self.image_sets["default"] = default

    def add_image_set(self, name, images):
        self.image_sets[name] = ImageSet(name, images)

    def draw(self, screen, offset=(0, 0), area=None):
        screen.blit(self.get_image(), offset, area=area)

    def get_image(self):
        s = self.get_image_set()
        if s:
            return s.get_image()
        else:
            return Graphics.CLEAR_IMG

    def get_image_set(self):
        state = self.get_image_state()
        s = self.image_sets

        if s and state in s:
            return s[state]
        else:
            return None

    def update(self):
        s = self.get_image_set()
        if s:
            s.next_frame()

    def reset_image(self):
        pass


class IconGraphics(Graphics):
    def __init__(self, entity, *images):
        self.images = images
        super(IconGraphics, self).__init__(entity)

    def reset_image(self):
        self.set_default_image(*self.images)


class BgGraphics(Graphics):
    PRE_RENDERS = {}

    def __init__(self, entity):
        super(BgGraphics, self).__init__(entity)
        self.set_default_image(self.get_bg_image())

    def reset_image(self):
        self.set_default_image(self.get_bg_image())

    def get_bg_image(self):
        cg, bg = (
            self.make_color_image,
            self.make_bg_image)

        s = self.entity.style
        size = self.entity.size

        if hasattr(self.entity, "bg_color"):
            bg_color = self.entity.bg_color
        else:
            bg_color = s.colors["bg"]

        if s.images["bg"]:
            bg_image = s.get_image(BG)
        else:
            bg_image = None

        bg_style = s.bg_style

        surface = cg(size, bg_color)
        if bg_image and bg_style:
            image = bg(bg_image, surface, bg_style)
        else:
            image = surface

        return image

    @staticmethod
    def make_color_image(size, color):
        s = Surface(size).convert()
        if color:
            s.fill(color)
        else:
            s.set_colorkey(s.get_at((0, 0)))

        return s

    @staticmethod
    def make_bg_image(bg_image, surface, bg_style):
        tile, stretch, center = BG_STYLES

        {                                   # chooses a method to use
            tile: BgGraphics.tile,        # for blitting bg_image to
            stretch: BgGraphics.stretch,  # surface by using bg_style
            center: BgGraphics.center     # as a dict key
        }[bg_style](bg_image, surface)

        return surface

    @staticmethod
    def tile(bg_image, surface):
        bg_hash = hash(bg_image)
        if bg_hash not in BgGraphics.PRE_RENDERS:
            sx, sy = SCREEN_SIZE
            sx *= 2
            sy *= 2
            pr_surface = Surface((sx, sy), SRCALPHA, 32)

            w, h = pr_surface.get_size()
            img_w, img_h = bg_image.get_size()

            for x in range(0, w + img_w, img_w):
                for y in range(0, h + img_h, img_h):
                    pr_surface.blit(bg_image, (x, y))

            BgGraphics.PRE_RENDERS[bg_hash] = pr_surface

        full_bg = BgGraphics.PRE_RENDERS[bg_hash]

        r = surface.get_rect().clip(full_bg.get_rect())
        blit_region = full_bg.subsurface(r)
        surface.blit(blit_region, (0, 0))

    @staticmethod
    def stretch(bg_image, surface):
        w, h = surface.get_size()
        new_img = scale(bg_image, (w, h))
        surface.blit(new_img, (0, 0))

    @staticmethod
    def center(bg_image, surface):
        w, h = surface.get_size()
        img_w, img_h = bg_image.get_size()

        x = round((w / 2)) - round((img_w / 2))
        y = round((h / 2)) - round((img_h / 2))

        surface.blit(bg_image, (x, y))


class ContainerGraphics(BgGraphics):
    PRE_RENDERS = {}

    def __init__(self, entity):
        super(ContainerGraphics, self).__init__(entity)
        self.set_default_image(self.get_container_image())

    def reset_image(self):
        self.set_default_image(self.get_container_image())

    def get_container_image(self):
        entity = self.entity
        s = entity.style

        border_images = s.border_images
        sides, corners = s.border_style
        rect_image = self.get_bg_image()
        container_image = self.make_border_image(
            border_images, rect_image, sides, corners)

        if ALPHA in s.colors:
            container_image = self.convert_colorkey(
                container_image, s.colors[ALPHA])

        return container_image

    def change_size(self):
        self.set_default_image(self.get_container_image())

    @staticmethod
    def convert_colorkey(surface, colorkey):
        surface.set_colorkey(colorkey)
        new_surface = Surface(surface.get_size(), SRCALPHA, 32)
        new_surface.blit(surface, (0, 0))

        return new_surface

    @staticmethod
    def make_border_image(border_images, surface, sides, corners):
        contg = ContainerGraphics
        h_side_image, v_side_image, corner_image = border_images

        blit_corners = contg.blit_corners
        full_h_side = contg.get_h_side(h_side_image)
        full_v_side = contg.get_v_side(v_side_image)

        w, h = surface.get_size()

        if "l" in sides:
            surface.blit(full_h_side, (0, 0))

        if "r" in sides:
            h_offset = w - full_h_side.get_size()[0]
            surface.blit(flip(full_h_side, True, False), (h_offset, 0))

        if "t" in sides:
            surface.blit(full_v_side, (0, 0))

        if "b" in sides:
            v_offset = h - full_v_side.get_size()[1]
            surface.blit(flip(full_v_side, False, True), (0, v_offset))

        if corners:
            blit_corners(corner_image, surface, corners)

        return surface

    @staticmethod
    def get_h_side(image):
        return ContainerGraphics.get_full_side_image(image, "h")

    @staticmethod
    def get_v_side(image):
        return ContainerGraphics.get_full_side_image(image, "v")

    @staticmethod
    def get_full_side_image(image, orientation):
        i_hash = hash(image)
        if i_hash not in ContainerGraphics.PRE_RENDERS:
            iw, ih = image.get_size()
            h, v = "hv"
            size = {h: (iw, SCREEN_SIZE[1]),
                    v: (SCREEN_SIZE[0], iw)}[orientation]
            pr_surface = Surface(size, SRCALPHA, 32)

            span = {h: range(0, size[1], ih),
                    v: range(0, size[0], iw)}[orientation]

            for i in span:
                position = {h: (0, i),
                            v: (i, 0)}[orientation]
                pr_surface.blit(image, position)

            ContainerGraphics.PRE_RENDERS[i_hash] = pr_surface

        return ContainerGraphics.PRE_RENDERS[i_hash]

    @staticmethod
    def blit_corners(corner_image, surface, corners):
        w, h = surface.get_size()
        cw, ch = corner_image.get_size()
        a, b, c, d = BORDER_CORNER_CHOICES
        locations = {a: (0, 0),
                     b: (w - cw, 0),
                     c: (0, h - ch),
                     d: (w - cw, h - ch)}

        for corner in corners:
            surface.blit(ContainerGraphics.get_corner(corner_image, corner), locations[corner])

    @staticmethod
    def get_corner(img, string):
        a, b, c, d = BORDER_CORNER_CHOICES
        corner = {a: lambda i: i,
                  b: lambda i: flip(i, True, False),
                  c: lambda i: flip(i, False, True),
                  d: lambda i: flip(i, True, True)}[string](img)

        return corner


class TextGraphics(Graphics):
    def reset_image(self):
        self.set_default_image(self.get_text_image())

    def get_text_image(self):
        entity = self.entity
        s = entity.style
        buffer = s.buffers["text"]
        key = entity.font_name
        color, font = s.colors["text"], s.get_font(key)
        text, cutoff, nl = entity.text, entity.cutoff, entity.nl
        image = self.make_text_image(text, cutoff, nl, buffer, font, color)

        return image

    def change_text(self):
        self.set_default_image(self.get_text_image())

    @staticmethod
    def get_text(text, cutoff, nl):
        if type(text) == str:
            text = [text]

        for i in range(len(text)):
            line = text[i]
            line = line.replace("\t", "    ")
            line = line.replace("\r", "\n")
            if not nl:
                line = line.replace("\n", "")
            text[i] = line

        new_text = []

        for line in text:
            if cutoff:
                new_text += TextGraphics.format_text(line, cutoff)
            else:
                if nl:
                    new_text += line.split("\n")
                else:
                    new_text += [line]

        if not new_text:
            new_text = [" "]

        return new_text

    @staticmethod
    def make_text_image(text, cutoff, nl, buffer, font, color):
        text = TextGraphics.get_text(text, cutoff, nl)

        line_images = []
        for line in text:
            line_images.append(font.render(line, TEXT_ANTI_ALIAS, color))

        widest = sorted(line_images, key=lambda l: -1 * l.get_size()[0])[0]
        line_height = (line_images[0].get_size()[1] + buffer)
        w, h = widest.get_size()[0], (line_height * len(line_images)) - buffer

        sprite_image = Surface((w, h), SRCALPHA, 32)
        for i in range(len(line_images)):
            image = line_images[i]
            y = line_height * i
            sprite_image.blit(image, (0, y))

        return sprite_image

    @staticmethod
    def get_char_size(style_dict=None, key="main"):
        if not style_dict:
            style_dict = {}
        s = Style(style_dict)
        font = s.get_font(key)

        return font.render(" ", 1, (0, 0, 0)).get_size()

    @staticmethod
    def format_text(text, cutoff):
        f_text = []
        last_cut = 0

        for i in range(len(text)):
            char = text[i]
            done = False

            if char == "\n" and i - last_cut > 0:
                f_text.append(text[last_cut:i])
                last_cut = i + 1
                done = True

            if i == len(text) - 1:
                f_text.append(text[last_cut:])
                done = True

            if i - last_cut >= cutoff and not done:
                if char == " ":
                    f_text.append(text[last_cut:i])
                    last_cut = i + 1
                else:
                    search = True
                    x = i
                    while search:
                        x -= 1
                        if text[x] == " ":
                            next_line = text[last_cut:x]
                            last_cut = x + 1
                            f_text.append(next_line)
                            search = False
                        else:
                            if x <= last_cut:
                                next_line = text[last_cut:i]
                                last_cut = i
                                f_text.append(next_line)
                                search = False

        return f_text
