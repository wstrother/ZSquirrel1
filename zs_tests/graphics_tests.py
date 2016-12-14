from zs_tests.zs_unit_test import ZsUnitTest
from zs_src.graphics import ImageSet, Graphics


class ImageSetUnitTest(ZsUnitTest):
    def do_tests(self):
        l = self.log
        l("!s", ImageSet)

        chars = "abcdefg"
        img_set = ImageSet("test image set", chars)

        assert img_set.current_frame == 0
        l("current_frame ok")

        assert img_set.max_frame == len(chars) - 1
        l("max_frame ok")

        for x in range(2 * len(chars)):
            l(img_set.get_image())
            assert img_set.get_image() == chars[x % len(chars)]
            img_set.next()
        l("next ok")

        for x in range(2 * len(chars)):
            l(img_set.get_image())
            assert img_set.get_image() == chars[-(x % len(chars))]
            img_set.prev()
        l("prev ok")
        l("get_image ok")
        l("! ")


class GraphicsUnitTest(ZsUnitTest):
    class MockEntity:
        def __init__(self, name):
            self.name = name
            self.id_num = 0

        def get_image_state(self):
            return self.name

    class MockImageSet:
        def __init__(self, name):
            self.name = name
            self.frame = 0

        def get_image(self):
            return self.name

        def next(self):
            self.frame += 1

    def do_tests(self):
        l = self.log
        l("!s", Graphics)

        entity = self.MockEntity("test")
        img_set = self.MockImageSet("test")
        gfx = Graphics(entity, img_set)

        assert gfx.entity is entity
        assert gfx.name == entity.name
        assert gfx.id_num == entity.id_num
        l("entity ok")

        assert gfx.image_sets["test"] is img_set
        l("add_image_sets ok")

        assert gfx.get_image_set() is img_set
        l("get_image_set ok")

        assert gfx.get_image() == "test"
        l("get_image ok")

        gfx.update()
        assert img_set.frame > 0
        l("update ok")
        l("! ")

TESTS = ImageSetUnitTest, GraphicsUnitTest


def do_tests():
    for test in TESTS:
        test().do_tests()
