# from zs_src.menus_gui import OptionBlockColumn, OptionBlock, TextOption, \
#     MeterOption, TextFieldOption, SubBox, ChangeBlockOption
# from zs_src.menus import Menu
# from zs_src.gui import TextSprite
from zs_src.animations import AnimationGraphics
# from zs_src.graphics import Graphics
# from zs_src.entities import ZsSprite, Layer
# from zs_constants.paths import ANIMATIONS
# from os.path import join
import pygame


class YoshiAnimation(AnimationGraphics):
    def __init__(self, *args):
        yoshi_sheet = pygame.image.load("resources/animations/yoshi.gif")
        super(YoshiAnimation, self).__init__(yoshi_sheet, *args)

        lines = "100 100 5\n0 0 50 60 20 20\n1 0\n2 0\n1 0\n0 0\n0 0\n1 0\n2 0\n3 0\n2 0"
        lines = lines.split("\n")
        self.set_animation("default", self.get_stream(lines))
'''

class TestSprite(ZsSprite):
    def __init__(self, name, sprite_sheet, **kwargs):
        super(TestSprite, self).__init__(name, **kwargs)
        # self.graphics = AnimationGraphics(sprite_sheet, self)
        self.graphics = YoshiAnimation(self)


class SpriteSheetLayer(Layer):
    def __init__(self, sprite_sheet, **kwargs):
        super(SpriteSheetLayer, self).__init__("sprite sheet layer", **kwargs)

        sprite_sheet.set_colorkey(sprite_sheet.get_at((0, 0)))
        self.graphics = Graphics(self)
        self.graphics.set_default_image(sprite_sheet)

        self.sheet_size = self.image.get_size()
        self.cell_size = 1, 1
        self.starting_point = 0, 0
        self.pointer = [0, 0]

    def blit_to_screen(self, screen):
        super(SpriteSheetLayer, self).blit_to_screen(screen)
        px, py = self.starting_point

        pointer_rect = pygame.Rect((0, 0), self.cell_size)
        x, y = self.pointer
        w, h = self.cell_size
        x *= w
        y *= h
        pointer_rect.topleft = x + px, y + py

        pygame.draw.rect(screen, (255, 0, 0), pointer_rect, 1)


class AnimationMenu(Menu):
    def __init__(self, file_name=None):
        super(AnimationMenu, self).__init__("animation menu")

        if not file_name:
            file_name = "yoshi.gif"
        sprite_sheet = pygame.image.load(join(ANIMATIONS, file_name))

        self.sheet_layer = SpriteSheetLayer(sprite_sheet, position=(0, 300))
        self.add_sub_layer(self.sheet_layer)

        self.sprite = TestSprite("test sprite", sprite_sheet)

        self.add_event_methods("set_cell_width", "set_cell_height",
                               "set_start_x", "set_start_y")

    def get_draw_order(self):
        order = []

        for layer in self.sub_layers:
            order.append(layer)

        for group in self.groups:
            order.append(group)

        return order

    def populate(self):
        mb = OptionBlockColumn("main block")

        choose_animation = TextOption("Choose animation")
        mb.add_member_sprite(choose_animation)
        mb.add_sub_block(self.get_choose_animation_block(),
                         (0, 0), self)

        edit_hitboxes = TextOption("Edit Hitboxes")
        mb.add_member_sprite(edit_hitboxes)

        name = self.sprite.get_image_state()
        if not name:
            name = "default"
        block = self.get_header_block(name)
        edit_animation = ChangeBlockOption(block, self, "Edit " + name)
        mb.add_member_sprite(edit_animation)

        self.add_main_block(mb)

        sprite_box = SubBox(self, "sprite box",
                            [[self.sprite]], position=(600, 0))
        mb.add_sub_sprite(sprite_box, self)

    def get_choose_animation_block(self):
        block = OptionBlockColumn("choose animation block", position=(200, 0))
        image_sets = self.sprite.graphics.image_sets

        for name in image_sets:
            option = TextOption(name)
            block.add_member_sprite(option)
            change_animation = "change_sprite_animation state={}".format(name)
            option.set_event_listener("activate", change_animation, self)

        return block

    def get_header_block(self, name):
        members = []

        choose_name = TextFieldOption(name, 40)
        members.append([choose_name])

        width = MeterOption(200, 1)
        members.append([width, TextSprite("width")])
        width.set_event_listener("change_switch", "set_cell_width", self)

        height = MeterOption(200, 1)
        members.append([height, TextSprite("height")])
        height.set_event_listener("change_switch", "set_cell_height", self)

        max_x = self.sheet_layer.sheet_size[0]
        max_y = self.sheet_layer.sheet_size[1]

        start_x = MeterOption(max_x, 0)
        start_y = MeterOption(max_y, 0)

        members.append([start_x, TextSprite("Starting X")])
        members.append([start_y, TextSprite("Starting Y")])

        start_x.set_event_listener("change_switch", "set_start_x", self)
        start_y.set_event_listener("change_switch", "set_start_y", self)

        frames_block = self.get_frames_block()
        add_frames = ChangeBlockOption(frames_block, self, "Add frames")
        members.append([add_frames])

        block = OptionBlock("header block", members, position=(300, 0), size=(250, 0))
        block.style = {"align_h": "c"}

        return block

    def get_frames_block(self):
        members = []
        members.append(TextOption("New frame"))

        block = OptionBlockColumn("frames block", members, position=(300, 0), size=(250, 0))

        return block

    def on_set_cell_width(self):
        value = int(self.event.trigger.text)

        sheet = self.sheet_layer
        w, h = sheet.cell_size
        w = value
        sheet.cell_size = w, h

    def on_set_cell_height(self):
        value = int(self.event.trigger.text)

        sheet = self.sheet_layer
        w, h = sheet.cell_size
        h = value
        sheet.cell_size = w, h

    def on_set_start_y(self):
        value = int(self.event.trigger.text)

        sheet = self.sheet_layer
        x, y = sheet.starting_point
        y = value
        sheet.starting_point = x, y

    def on_set_start_x(self):
        value = int(self.event.trigger.text)

        sheet = self.sheet_layer
        x, y = sheet.starting_point
        x = value
        sheet.starting_point = x, y
        '''
