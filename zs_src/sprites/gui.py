from zs_constants import gui as constants
from zs_constants.style import L, C, R, T, B
from zs_src.classes import MemberTable
from zs_src.entities import Sprite
from zs_src.graphics import ContainerGraphics, TextGraphics
from zs_src.style import StyleInterface


class GuiSprite(StyleInterface, Sprite):
    EVENT_NAMES = ("change_position", "change_size")

    def __init__(self, name, **kwargs):
        StyleInterface.__init__(self)

        size = kwargs.get("size", (1, 1))
        position = kwargs.get("position", (0, 0))
        Sprite.__init__(self, name, size=size, position=position)

        style_dict = kwargs.get("style_dict")
        if style_dict:
            self.style.change_dict(style_dict)
        self.add_event_methods(*GuiSprite.EVENT_NAMES)

        self.selectable = False
        self.control_freeze = False

        self.parent_direction = constants.LEFT
        self.child_direction = constants.RIGHT
        self.ui_directions = []
        self.return_command_names = constants.B

    def adjust_position(self, value):
        super(GuiSprite, self).adjust_position(value)
        self.handle_event("change_position")

    def adjust_style(self, value):
        super(GuiSprite, self).adjust_style(value)
        if self.graphics:
            self.graphics.reset_image()

    def set_rect_size_to_image(self):
        super(GuiSprite, self).set_rect_size_to_image()
        self.handle_event("change_size")

    def play_sound(self, key):
        gs = self.style.get_sound
        sound = gs(key)

        sound.stop()
        sound.set_volume(.1)
        sound.play()

    def change_color(self, key, value):
        if self.style.colors[key] != value:
            self.style = {"colors": {key: value}}

        self.graphics.reset_image()

    def on_change_position(self):
        pass

    def on_change_size(self):
        pass


class TextSprite(GuiSprite):
    def __init__(self, text, name=None, position=(0, 0),
                 style_dict=None, cutoff=None, nl=True,
                 font=None, **kwargs):
        if not name:
            name = text
        if font:
            self.font_name = font
        else:
            self.font_name = "main"
        super(TextSprite, self).__init__(name, position=position, style_dict=style_dict, **kwargs)

        self.text = text
        self.cutoff = cutoff
        self.nl = nl
        if text is None:
            print("")
        self.graphics = TextGraphics(self)

        self.add_event_methods("change_text")

    @property
    def size(self):
        return self.image.get_size()

    @size.setter
    def size(self, value):
        pass

    def change_text(self, text):
        if self.text != text:
            self.text = text
            self.graphics.change_text()
            self.set_rect_size_to_image()

            self.handle_event(("change_text",
                               ("text", text)))

    def on_change_text(self):
        pass


class ContainerSprite(GuiSprite):
    EVENT_NAMES = ("change_member_size",)

    def __init__(self, name, members=None, title=None, **kwargs):
        super(ContainerSprite, self).__init__(name, **kwargs)
        self.initial_size = kwargs.get("size", (1, 1))
        self.add_event_methods(*ContainerSprite.EVENT_NAMES)

        self.title = title
        if title:
            self.title = TextSprite(title, font="title")
        self.table_style = kwargs.get("table_style", None)
        self.member_table = None
        self.set_table(members)

        self.bg_color = self.style.colors["bg"]
        self.graphics = ContainerGraphics(self)

    def add_to_container(self, *sprites):
        for sprite in sprites:
            sprite.remove_event_listener(
                "change_size", "change_member_size")
            sprite.set_event_listener(
                "change_size", "change_member_size", self)
            sprite.parent = self

            for group in self.groups:
                sprite.add(group)
        self.handle_event("change_member_size")

    def set_table(self, members=None):
        self.member_table = self.get_table(members)
        self.add_to_container(*self.member_list)

        if self.title:
            self.member_table.members = [[self.title]] + self.members
            self.add_to_container(self.title)

    def get_table(self, members):
        table_style = self.table_style
        name = self.name + " table"

        if table_style == "column" or table_style is None:
            return GuimtColumn(name, members)

        if table_style == "grid":
            return GuiMemberTable(name, members)

        if "cutoff" in table_style:
            cutoff = int(table_style.split()[1])
            return GuimtCutoff(name, cutoff, members)

    def on_spawn(self):
        super(ContainerSprite, self).on_spawn()

        for sprite in self.member_list:
            sprite.handle_event("spawn")

    @property
    def members(self):
        return self.member_table.members

    @property
    def member_list(self):
        ml = []
        for row in self.members:
            for item in row:
                ml.append(item)

        return ml

    def add_member_sprite(self, sprite, *args):
        self.member_table.add_member(sprite, *args)
        self.add_to_container(sprite)

    def add_member_row(self, row):
        self.member_table.add_row(row)
        self.add_to_container(*row)

    def remove_member_sprite(self, index):
        sprite = self.member_table.remove_member(index)
        sprite.kill()
        self.handle_event("change_member_size")

    def remove_member_row(self, index):
        row = self.member_table.remove_row(index)
        for sprite in row:
            sprite.kill()
        self.handle_event("change_member_size")

    def clear_members(self):
        for sprite in self.member_list:
            sprite.kill()

        self.set_table()

    def adjust_style(self, value):
        super(ContainerSprite, self).adjust_style(value)
        for item in self.member_list:
            item.adjust_style(value)

        self.handle_event("change_member_size")
        # self.set_member_positions()
        # self.set_size_to_table()

    def adjust_size(self, value):
        self.rect.size = value
        self.handle_event("change_size")

    def adjust_position(self, value):
        super(ContainerSprite, self).adjust_position(value)
        self.set_member_positions()

    def set_member_positions(self):
        s = self.style
        self.member_table.set_member_positions(
            self.position, self.size, s.border_size,
            s.buffers["cell"], s.aligns)

        for sprite in self.member_list:
            if isinstance(sprite, ContainerSprite):
                sprite.set_member_positions()

    def set_size_to_table(self):
        s = self.style
        self.size = self.initial_size
        self.size = self.member_table.adjust_size(
            self.size, s.border_size, s.buffers["cell"])

    def on_change_member_size(self):
        old = self.size
        self.set_size_to_table()
        self.set_member_positions()

        if self.size != old and self.graphics:
            self.graphics.change_size()

    def add(self, *groups):
        super(ContainerSprite, self).add(*groups)

        for sprite in self.member_list:
            sprite.add(*groups)

    def remove(self, *groups):
        super(ContainerSprite, self).remove(*groups)

        for sprite in self.member_list:
            sprite.remove(*groups)

    def kill(self):
        super(ContainerSprite, self).kill()

        for sprite in self.member_list:
            sprite.kill()

    def on_dying(self):
        ratio = 1 - self.event.timer.get_ratio()

        bg_color = self.style.colors["bg"]
        if bg_color:
            new_color = tuple([value * ratio for value in bg_color])
            self.bg_color = new_color
            self.reset_image()

    def on_spawning(self):
        ratio = self.event.timer.get_ratio()

        bg_color = self.style.colors["bg"]
        if bg_color:
            new_color = tuple([round(value * ratio) for value in bg_color])
            self.bg_color = new_color
            self.reset_image()

# GUI Member Table classes


class GuiMemberTable(MemberTable):
    # def set_member_listeners(self, event_name, response_event, target, temp=False):
    #     for member in self.member_list:
    #         member.remove_event_listener(event_name, response_event)
    #         member.set_event_listener(
    #             event_name, response_event, target, temp)

    def adjust_size(self, size, border_size, buffers):
        w, h = size
        border_w, border_h = border_size
        buff_w, buff_h = buffers

        body_w, body_h = self.get_minimum_body_size(buffers)
        full_w, full_h = (
            body_w + ((border_w + buff_w) * 2),
            body_h + ((border_h + buff_h) * 2))

        if w < full_w:
            w = full_w
        if h < full_h:
            h = full_h

        return w, h

    def get_minimum_body_size(self, buffers):
        members = self.members
        r_widths, r_heights = [], []
        buff_w, buff_h = buffers

        for row in members:
            row_w, row_h = self.get_minimum_row_size(row, buff_w)
            r_widths.append(row_w)
            r_heights.append(row_h)

        try:
            width = sorted(r_widths, key=lambda x: x * -1)[0]
        except IndexError:
            width = 0
        height = sum(r_heights) + ((len(r_heights) - 1) * buff_h)

        return width, height

    @staticmethod
    def get_minimum_row_size(row, buff_w):
        row_w, row_h = 0, 0
        item_widths = []

        for item in row:
            w, h = getattr(item, "size", (0, 0))
            item_widths.append(w)

            if h > row_h:
                row_h = h
        row_w = sum(item_widths) + ((len(row) - 1) * buff_w)

        return row_w, row_h

    def set_member_positions(self, position, size, border_size, buffers, aligns):
        if self.member_list:
            parent_x, parent_y = position
            w, h = size
            align_h, align_v = aligns
            border_w, border_h = border_size
            buff_w, buff_h = buffers

            edge_x, edge_y = border_w + buff_w, border_h + buff_h
            body_w, body_h = w - (edge_x * 2), h - (edge_y * 2)
            get_cell_size = lambda items: (body_w / len(items), body_h / len(self.members))

            i, y_disp = 0, 0
            for row in self.members:
                if row:
                    cell_w, cell_h = get_cell_size(row)

                    row_w, row_h = self.get_minimum_row_size(row, buff_w)

                    j, x_disp = 0, 0
                    for item in row:
                        if item:
                            item_w, item_h = item.size
                            x, y = edge_x, edge_y
                            r_offset = body_w - row_w
                            b_edge = body_h - self.get_minimum_body_size(buffers)[1]

                            x += {
                                L: x_disp,
                                C: (j * cell_w) + ((cell_w - item_w) / 2),
                                R: r_offset + x_disp}[align_h]
                            y += {
                                T: y_disp,
                                C: (i * cell_h) + ((cell_h - item_h) / 2),
                                B: b_edge + y_disp}[align_v]

                            item.position = parent_x + x, parent_y + y
                            x_disp += item_w + buff_w
                        j += 1
                    y_disp += row_h + buff_h
                    i += 1

    @staticmethod
    def get_cell_size(size, num_cells):
        w, h = size

        return w / num_cells, h / num_cells


class GuimtCutoff(GuiMemberTable):
    def __init__(self, name, cutoff, member_list=None, **kwargs):
        super(GuimtCutoff, self).__init__(name, **kwargs)
        self.cutoff = cutoff

        if member_list:
            for item in member_list:
                self.add_member(item, cutoff)

    def add_member(self, sprite, *args):
        row_index = len(self.members) - 1
        if row_index < 0:
            row_index = 0

        row = self.members[row_index]
        row_len = len(row)

        if row_len >= self.cutoff:
            row_index = len(self.members)
            cell_index = 0
        else:
            cell_index = len(self.members[row_index])

        index = row_index, cell_index
        self.set_member_at_index(sprite, index)


class GuimtColumn(GuiMemberTable):
    def __init__(self, name, member_list=None, **kwargs):
        super(GuimtColumn, self).__init__(name, **kwargs)

        if member_list:
            for item in member_list:
                self.add_member(item)

    def add_member(self, sprite, *args):
        empty = not self.members[0]
        if len(args) == 1:
            row_index = args[0]
        else:
            row_index = len(self.members)

            if empty:
                row_index = 0
            self.set_member_at_index(sprite, (row_index, 0))
            return

        index = (row_index, 0)
        if not empty and (row_index < len(self.members)):
            rows = self.members[row_index:]
            new_tail = []
            for row in rows:
                new_tail.append([row[0]])

            row_len = len(rows)
            self.set_member_at_index(sprite, index)

            lower_i = row_index + 1
            upper_i = row_index + row_len
            self.members[lower_i:upper_i] = new_tail
        else:
            self.set_member_at_index(sprite, index)
