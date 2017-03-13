from random import randint, seed

from pygame.sprite import Group

from zs_constants.zs import TRANSITION_TIME
from zs_src.entities import Entity, Sprite, Layer
from zs_tests.zs_unit_test import ZsUnitTest


class ZsEntityUnitTest(ZsUnitTest):
    def do_tests(self, r=5):
        l = self.log
        l("!s", Entity)
        seed(r)

        self.test_init()
        l("")

        self.test_rect(r)
        l("")

        self.test_graphics()
        l("")

        self.test_event_methods()
        l("! ")

    def test_init(self):
        l = self.log
        l("!m", self.test_init)

        entity = Entity("test entity")

        assert entity.name == "test entity"
        l("name ok")

        assert entity.id_num == Entity.ID_NUM - 1
        l("id_num ok")

        assert entity.parent is None
        l("parent ok")

        assert entity.child is None
        l("child ok")

        assert entity.spawn_time == TRANSITION_TIME
        l("spawn_time ok")

        assert entity.death_time == TRANSITION_TIME
        l("death_time ok")

        assert entity.states == Entity.STATES
        l("states ok")
        l("")

    class MockEntity(Entity):
        def __init__(self, *args, **kwargs):
            super(ZsEntityUnitTest.MockEntity, self).__init__(*args, **kwargs)
            self.adjust_size_called = False
            self.adjust_position_called = False
            self.on_change_state_called = False

        def adjust_size(self, value):
            super(ZsEntityUnitTest.MockEntity, self).adjust_size(value)
            self.adjust_size_called = True

        def adjust_position(self, value):
            super(ZsEntityUnitTest.MockEntity, self).adjust_position(value)
            self.adjust_position_called = True

        def on_change_state(self):
            super(ZsEntityUnitTest.MockEntity, self).on_change_state()
            self.on_change_state_called = True

    def test_rect(self, r):
        l = self.log
        l("!m", self.test_rect)

        for x in range(r):
            l("!r")
            size = randint(1, r * 2), randint(1, r * 2)
            position = randint(1, r * 2), randint(1, r * 2)
            l("testing size={}, position={}".format(size, position))

            make = ZsEntityUnitTest.MockEntity
            entity = make("test entity", size=size, position=position)

            assert entity.size == size
            l("size ok")

            assert entity.position == position
            l("position ok")

            assert entity.width == size[0]
            l("width ok")

            assert entity.height == size[1]
            l("height ok")

            entity.size = (1, 1)
            assert entity.adjust_size_called
            l("adjust_size ok")

            entity.position = (0, 0)
            assert entity.adjust_position_called
            l("adjust_position ok")

    def test_graphics(self):
        l = self.log
        l("!m", self.test_graphics)

        class MockGraphics:
            def __init__(self):
                self.get_image_called = False
                self.get_size_called = False

            def get_image(self):
                self.get_image_called = True
                return self

            def get_size(self):
                self.get_size_called = True
                return self

        entity = ZsEntityUnitTest.MockEntity("test entity")
        gfx = MockGraphics()

        entity.graphics = gfx
        assert entity.graphics is gfx
        l("graphics ok")

        gfx.get_image_called = False
        assert entity.image is gfx
        assert gfx.get_image_called
        l("image ok")

    def test_event_methods(self):
        l = self.log
        l("!m", self.test_event_methods)

        entity = ZsEntityUnitTest.MockEntity("test entity")
        states, event_names = Entity.STATES, Entity.EVENT_NAMES
        spawning, alive, dying, dead = states

        assert sorted(list(entity.event_handler.event_methods.keys())) == sorted(event_names)
        l("add_event_methods ok")

        assert entity.get_update_methods() == [entity.event_handler.update]
        l("get_update_methods ok")

        entity.reset_spawn()
        entity.update(1)
        assert entity.get_state() == spawning
        l("get_state ok")

        for x in range(TRANSITION_TIME):
            entity.update(1)
        assert entity.get_state() == alive
        l("set_state ok")

        l("reset_spawn ok")

        entity.reset_death()
        entity.update(1)
        assert entity.get_state() == dying

        for x in range(TRANSITION_TIME):
            entity.update(1)
        assert entity.get_state() == dead
        l("reset_death ok")

        l("update ok")

        assert entity.on_change_state_called
        l("event_methods called ok")


class ZsSpriteUnitTest(ZsUnitTest):
    def do_tests(self, r=5):
        l = self.log
        l("!s", Sprite)
        seed(r)

        self.test_group_methods()
        l("")

        self.test_event_methods()
        l("! ")

    def test_group_methods(self):
        l = self.log
        l("!m", self.test_group_methods)

        chars = "abcdefg"
        group = Group()
        sprites = [Sprite(char) for char in chars]
        main_sprite = sprites[0]
        main_sprite.sub_sprites = sprites[1:]

        main_sprite.add_to(group)
        for sprite in sprites:
            assert sprite in group
        l("add ok")

        main_sprite.remove_from(group)
        for sprite in sprites:
            assert sprite not in group
        l("remove ok")

    def test_event_methods(self):
        l = self.log
        l("!m", self.test_event_methods)

        chars = "abcdefg"
        group = Group()
        sprites = [Sprite(char) for char in chars]
        main_sprite = sprites[0]
        main_sprite.sub_sprites = sprites[1:]
        spawning, alive, dying, dead = Entity.STATES

        main_sprite.add_to(group)
        group.update(1)

        for sprite in sprites:
            assert sprite.get_state() == spawning

        for x in range(TRANSITION_TIME):
            group.update(1)
        for sprite in sprites:
            assert sprite.get_state() == alive
        l("reset_spawn ok")

        # main_sprite.reset_death()
        # group.update(1)
        #
        # for x in range(TRANSITION_TIME):
        #     group.update(1)
        #
        # for sprite in sprites:
        #     assert sprite not in group
        # l("reset_death ok")
        #
        # l("on_death ok")


class LayerUnitTest(ZsUnitTest):
    def do_tests(self):
        l = self.log
        l("!s", Layer)

        class TestLayer(Layer):
            def __init__(self, *args, **kwargs):
                super(TestLayer, self).__init__(*args, **kwargs)
                self.test_sub_layer = None
                self.test_groups = []
                self.test_sprite = None

            def populate(self):
                g1 = self.make_group()
                g2 = self.make_group()
                self.test_groups = [g1, g2]
                self.groups = [g1, g2]

                class TestSprite(Sprite):
                    def __init__(self, *args, **kwargs):
                        super(TestSprite, self).__init__(*args, **kwargs)
                        self.update_called = False

                    def update(self, dt):
                        self.update_called = True

                self.test_sprite = TestSprite("test sprite")
                self.test_sprite.add_to(g1)

                class TestSubLayer(Layer):
                    def __init__(self, *args, **kwargs):
                        super(TestSubLayer, self).__init__(*args, **kwargs)
                        self.update_called = False

                    def update(self, dt):
                        self.update_called = True

                self.test_sub_layer = Layer("sub layer", size=(1, 1))
                self.add_sub_layer(self.test_sub_layer)

        test_layer = TestLayer("test layer")
        test_layer.reset_spawn()

        assert test_layer.transition_to is None
        l("transition_to ok")

        assert test_layer.return_to is None
        l("return_to ok")

        um = [
            test_layer.event_handler.update,
            test_layer.update_groups,
            test_layer.update_sub_layers]
        assert test_layer.get_update_methods() == um
        l("get_update_methods ok")

        test_layer.add_controllers("test controller")
        assert test_layer.controller == "test controller"
        l("add_controller ok")
        l("controller ok")

        assert test_layer.sub_layers == [test_layer.test_sub_layer]
        l("add_sub_layers ok")

        assert test_layer.groups == test_layer.test_groups
        l("add_group ok")
        l("populate ok")

        spawning, alive, dying, dead = Entity.STATES
        test_layer.update(1)
        assert test_layer.test_sprite.update_called
        l("update_groups ok")

        assert test_layer.get_state() == spawning
        assert test_layer.test_sub_layer.get_state() == spawning

        for x in range(TRANSITION_TIME):
            test_layer.update(1)
        assert test_layer.get_state() == alive
        assert test_layer.test_sub_layer.get_state() == alive
        l("update_sub_layers ok")

        l("reset_spawn ok")
        l("! ")

TESTS = ZsEntityUnitTest, ZsSpriteUnitTest, LayerUnitTest


def do_tests():
    for test in TESTS:
        test().do_tests()
