from zs_tests.zs_unit_test import ZsUnitTest
from zs_src.style import Style, StyleInterface
from random import randint, seed
from os.path import join

IMAGE_PATH = join("resources", "images")
SOUND_PATH = join("resources", "sounds")


class StyleUnitTest(ZsUnitTest):
    @staticmethod
    def get_char():
        abc = "abcdefghijklmnopqrstuvwxyz"

        return abc[randint(0, len(abc) - 1)]

    def do_tests(self, r=5):
        l = self.log
        l("!s", Style)
        seed(r)

        s = Style()
        assert s.image_path == IMAGE_PATH
        l("image_path ok")

        assert s.sound_path == SOUND_PATH
        l("sound_path ok")

        error_caught = False
        try:
            s.change_dict({Style.K_BG_STYLE: "error"})
        except ValueError:
            error_caught = True
        assert error_caught
        l("change_dict value error caught ok")
        s.change_dict({Style.K_BG_STYLE: "tile"})

        alpha = Style.COLORS[4]
        d = {
            Style.K_BORDER_SIDES: Style.BORDER_SIDES + "xy",
            Style.K_COLORS: {
                "test": r,
                alpha: r
            }
        }
        s.change_dict(d)
        for char in s.border_style[0]:
            assert char in Style.BORDER_SIDES
        assert s.colors["test"] == r
        assert s.colors[alpha] == r
        l("change_dict ok")

        l("")
        self.test_properties(r)
        l("! ")

    def test_properties(self, r):
        l = self.log
        l("!m", self.test_properties)

        ri = randint
        keys = Style.KEYS
        bg_style, align_h, align_v, border_sides, border_corners, \
            colors, images, sounds, fonts, buffers = keys

        for x in range(r):
            l("!r")
            d = {
                bg_style: Style.BG_STYLE[ri(0, 2)],
                align_h: Style.ALIGN_H[ri(0, 2)],
                align_v: Style.ALIGN_V[ri(0, 2)],
                border_sides: Style.BORDER_SIDES[0:ri(1, 3)],
                border_corners: Style.BORDER_CORNERS[0:ri(1, 3)]}

            get_sub_keys = lambda kl: (kl + ("test",))[:ri(1, len(kl) + 1)]
            color_keys = get_sub_keys(Style.COLORS)
            image_keys = get_sub_keys(Style.IMAGES)
            sound_keys = get_sub_keys(Style.SOUNDS)
            font_keys = get_sub_keys(Style.FONTS)
            buffer_keys = get_sub_keys(Style.BUFFERS)

            pairs = (
                (colors, color_keys),
                (images, image_keys),
                (sounds, sound_keys),
                (fonts, font_keys),
                (buffers, buffer_keys)
            )
            for key, sub_keys in pairs:
                d[key] = {k: self.get_char() for k in sub_keys}

            s = Style(d)
            s.print_dict()
            l("")

            assert s.bg_style == d[bg_style]
            l("bg_style ok")

            assert s.align_h == d[align_h]
            l("align_h ok")

            assert s.align_v == d[align_v]
            l("align_v ok")

            assert s.border_style == (d[border_sides], d[border_corners])
            l("border_style ok")

            for key in color_keys:
                assert key in s.colors
                if key in d[colors]:
                    assert s.colors[key] == d[colors][key]
            assert ("test" in color_keys) == ("test" in s.colors)
            l("colors ok")

            for key in image_keys:
                assert key in s.images
                if key in d[images]:
                    assert s.images[key] == d[images][key]
            assert ("test" in image_keys) == ("test" in s.images)
            l("images ok")

            for key in sound_keys:
                assert key in s.sounds
                if key in d[sounds]:
                    assert s.sounds[key] == d[sounds][key]
            assert ("test" in sound_keys) == ("test" in s.sounds)
            l("sounds ok")

            for key in font_keys:
                assert key in s.fonts
                if key in d[fonts]:
                    assert s.fonts[key] == d[fonts][key]
            assert ("test" in font_keys) == ("test" in s.fonts)
            l("fonts ok")

            for key in buffer_keys:
                assert key in s.buffers
                if key in d[buffers]:
                    assert s.buffers[key] == d[buffers][key]
            assert ("test" in buffer_keys) == ("test" in s.buffers)
            l("buffers ok")


class StyleInterfaceUnitTest(ZsUnitTest):
    def do_tests(self):
        l = self.log
        l("!s", StyleInterface)

        colors = Style.K_COLORS
        d = {colors: {"test": None}}
        si = StyleInterface(d)

        assert "test" in si.style.colors
        l("style_dict ok")
        l("style ok")

        d = {colors: {"test": True}}
        si.style = d
        assert si.style.colors["test"]
        l("style.setter ok")
        l("! ")

TESTS = StyleUnitTest, StyleInterfaceUnitTest


def do_tests():
    for t in TESTS:
        t().do_tests()
