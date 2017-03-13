from sys import exit
from types import MethodType

from zs_constants.zs import SCREEN_SIZE, TRANSITION_TIME
from zs_src.classes import CollisionSystem
from zs_src.events import EventInterface
from zs_src.geometry import Wall, Rect


class Model(EventInterface):
    def __init__(self, name, v_dict):
        self.name = name
        super(Model, self).__init__(name)
        self.values = {}
        self.change_functions = {}
        self.object_listeners = []

        if v_dict:
            self.set_values(v_dict)
        self.set_value("_value_names", [])
        self.link_object(
            self, "_value_names",
            lambda model: model.value_names
        )

        self.add_event_methods("change_value",
                               "toggle_value",
                               "set_value_to",
                               "append_value",
                               "set_value_at_index")

    @property
    def value_names(self):
        names = []
        for name in self.values:
            if name[0] != "_":
                names.append(name)
        names.sort()

        return names

    def set_values(self, v_dict):
        for name in v_dict:
            self.values[name] = v_dict[name]

    def link_value(self, value_name, function):
        functions = self.change_functions.get(value_name, [])
        functions.append(function)
        self.change_functions[value_name] = functions

    def clear_value_link(self, value_name):
        self.change_functions[value_name] = []

    def link_sub_value(self, value_name, key, function):
        functions = self.change_functions.get(value_name, [])

        def sub_function(value):
            function(value[key])

        functions.append(sub_function)
        self.change_functions[value_name] = functions

    def link_object(self, obj, value_name, function):
        l = (obj, value_name, function)
        self.object_listeners.append(l)
        self.check_object_listeners()

    def handle_change(self, value_name):

        if value_name in self.change_functions:
            value = self.values.get(value_name)
            for func in self.change_functions[value_name]:
                func(value)

    def set_value(self, value_name, value):
        self.values[value_name] = value
        self.handle_change(value_name)

    def on_change_value(self):
        name = self.event.value_name
        value = self.event.get_value(self.event)

        self.values[name] = value
        self.handle_change(name)

    def on_append_value(self):
        name = self.event.value_name
        item = self.event.item
        value = self.values[name]
        value.append(item)

        self.values[name] = value
        self.handle_change(name)

    def on_set_value_at_index(self):
        name = self.event.value_name
        i = self.event.index
        item = self.event.item

        value = self.values[name]
        try:
            value[i] = item
        except IndexError:
            value.append(item)

        self.values[name] = value
        self.handle_change(name)

    def on_toggle_value(self):
        name = self.event.value_name
        value = self.values[name]

        if not value:
            self.values[name] = True
        else:
            self.values[name] = False
        self.handle_change(name)

    def on_set_value_to(self):
        name = self.event.value_name
        value = self.event.value
        self.values[name] = value

        if not self.event.get("ignore", False):
            self.handle_change(name)

    def update(self):
        self.event_handler.update()

        self.check_object_listeners()

    def clear_object_link(self, obj):
        remove = []

        for l in self.object_listeners:
            o, value_name, func = l
            if o is obj:
                remove.append(l)

        self.object_listeners = [
            l for l in self.object_listeners if l not in remove
        ]

    def check_object_listeners(self):
        for l in self.object_listeners:
            obj, value_name, func = l
            current = self.values.get(value_name)
            value = func(obj)

            if not current == value:
                self.set_value(value_name, value)


class Entity(EventInterface):
    """
    The ZsEntity Class is an abstract superclass that provides the interface
    for all objects that will directly be loaded, updated, and drawn by the
    Game object. The main subclass families are Layers which define an area
    that will contain ZsSprites and be drawn to the Game's screen.

    All ZsEntities have a Rect object as an attribute, created from arguments
    passed to the __init__ function. Also, all ZsEntities
    have attributes for 'parent' and 'child' assigned to None on initialization.
    """
    ID_NUM = 0
    EVENT_NAMES = ("spawn", "spawning", "birth",
                   "die", "dying", "death",
                   "change_state", "change_linked_value")
    STATES = "spawning", "alive", "dying", "dead"

    def __init__(self, name, size=(1, 1), position=(0, 0)):
        self.name = name
        self.id_num = self.get_id()

        super(Entity, self).__init__(name)
        self.add_event_methods(*Entity.EVENT_NAMES)

        self.rect = Rect(size, position)

        self._graphics = None
        self.parent = None
        self.child = None

        self.active = True
        self.visible = True

        self.spawn_time = TRANSITION_TIME
        self.death_time = TRANSITION_TIME
        self.spawn_state = None

        self._log = []

    def __repr__(self):
        n, i = self.name, self.id_num
        cls = self.__class__.__name__

        return "{}: {} ({})".format(cls, n, i)

    def log(self, message):
        self._log.append(message)

    def print(self):
        for message in self._log:
            print(message)

        self._log.clear()

    @staticmethod
    def get_id():
        n = Entity.ID_NUM
        Entity.ID_NUM += 1

        return n

    @property
    def graphics(self):
        return self._graphics

    @graphics.setter
    def graphics(self, value):
        self._graphics = value

    @property
    def image(self):
        if self.graphics:
            return self.graphics.get_image()

    @property
    def size(self):
        return self.rect.size

    @size.setter
    def size(self, value):
        self.adjust_size(value)

    @property
    def position(self):
        return self.rect.position

    @position.setter
    def position(self, value):
        self.adjust_position(value)

    @property
    def width(self):
        return self.rect.width

    @property
    def height(self):
        return self.rect.height

    '''
    The adjust_size and adjust_position methods
    are called whenever the object's 'size' or
    'position' attributes (properties) are assigned
    to. They are meant to be overwritten by subclasses
    '''
    #   WARNING: BY DEFAULT YOU CANNOT ASSIGN A SIZE VALUE
    #   TO A ZsSprite OBJECT. Override this method to change
    #   that behavior
    def adjust_size(self, value):
        self.rect.size = value

    def adjust_position(self, value):
        self.rect.position = value

    def move(self, value):
        dx, dy = value
        x, y = self.position
        x += dx
        y += dy
        self.position = x, y

    def update(self):
        if self.graphics:
            self.graphics.update()

        for method in self.get_update_methods():
            method()

    # ALL subclasses that overwrite this method
    # should ALWAYS call the super() version and
    # combine results before returning.
    def get_update_methods(self):
        return [self.event_handler.update]

    def get_state(self):
        return self.spawn_state

    def set_state(self, state):
        if state is not self.get_state():
            self.spawn_state = state
            name = "change_state"
            change_state = "{} state={}".format(name, state)
            self.handle_event(change_state)

    def set_active(self, value):
        self.active = value

    def set_visible(self, value):
        self.visible = value

    def set_controller(self, controller):
        self.controller = controller

    def reset_transition_events(self):
        events = "spawning", "birth", "dying", "death"
        self.cancel_events(*events)

    def on_spawn(self):
        self.reset_transition_events()

        spawning = ("spawning",
                    ("duration", self.spawn_time),
                    ("trigger", self.event))
        self.queue_events(spawning, "birth")

    def on_spawning(self):
        self.set_state(Entity.STATES[0])

    def on_birth(self):
        self.set_state(Entity.STATES[1])

    def on_die(self):
        self.reset_transition_events()
        dying = ("dying",
                 ("duration", self.spawn_time),
                 ("trigger", self.event))
        self.queue_events(dying, "death")

    def on_dying(self):
        self.set_state(Entity.STATES[2])

    def on_death(self):
        self.set_state(Entity.STATES[3])

    def on_change_state(self):
        pass

    def on_change_linked_value(self):
        pass


class Layer(Entity):
    """
    The Layer object contains Groups (from pygame.sprite) of ZsSprites
    that are updated, and then drawn, all from a main method. Layers can
    also contain sub_layers with their own groups of sprites. The main
    method also calls the get_input() method which can reference any
    of the Controller objects in the 'controllers' list.
    """
    class Group:
        def __init__(self):
            self._items = []

        def __iter__(self):
            return iter(self._items)

        def update(self, *args):
            for item in self._items:
                item.update(*args)

        def draw(self, screen, offset=(0, 0)):
            for item in self:
                x, y = item.position
                x += offset[0]
                y += offset[1]

                image = item.image
                if image and item.visible:
                    screen.blit(image, (x, y))

        def add_item(self, *items):
            for item in items:
                self._items.append(item)
                item.groups.append(self)

        def remove_item(self, item):
            item.groups = [g for g in item.groups if g is not self]
            self._items = [s for s in self._items if s is not item]

    def __init__(self, name, size=SCREEN_SIZE,
                 position=(0, 0), model=None):
        super(Layer, self).__init__(name, size, position)

        self.transition_to = None
        self.return_to = None
        self.pause_layer = None

        self.game_environment = False

        self.controllers = []
        self.groups = []
        self.sub_layers = []

        self.model = Model(self.name + " model", model)
        self.add_event_methods("change_environment", "pause", "unpause")

    @property
    def paused(self):
        return bool(self.pause_layer)

    @property
    def controller(self):
        try:
            return self.controllers[0]
        except IndexError:
            return None

    def copy_controllers(self, controllers):
        new_controllers = []
        for c in controllers:
            new_controllers.append(
                c.get_copy())

        self.controllers = new_controllers

    def get_value(self, name):
        return self.model.values.get(name, None)

    def set_value(self, name, value):
        self.model.set_value(name, value)

    def set_value_at_index(self, name, index, item):
        value = self.model.values[name]
        value[index] = item
        self.model.set_value(name, value)

    def append_value(self, name, item):
        value = self.model.values[name]
        value.append(item)
        self.model.set_event_conditional(name, value)

    def add_sub_layer(self, layer):
        self.sub_layers.append(layer)

    def handle_controller(self):
        for c in self.controllers:
            c.update()

        for layer in self.sub_layers:
            if layer.active:
                layer.handle_controller()

    def get_update_methods(self):
        um = super(Layer, self).get_update_methods()

        return um + [self.update_groups,
                     self.update_sub_layers,
                     self.model.update]

    def update_groups(self):
        for group in self.groups:
            group.update()

    def update_sub_layers(self):
        for layer in self.sub_layers:
            if layer.active:
                layer.update()

    # the Layer object's rect attribute determines the region where the
    # layer will be drawn to the screen. Then all sub_layers are drawn
    # to this region recursively.
    def draw(self, screen, offset=(0, 0)):
        sub_rect = self.rect.clip(
            screen.get_rect())

        try:
            sub_screen = screen.subsurface(sub_rect)
        except ValueError:      # if the layer's area is entirely outside of the screen's
            return              # area, it doesn't get drawn

        if self.graphics:
            self.graphics.draw(
                screen, offset=offset)

        if self.groups:
            for g in self.groups:
                g.draw(sub_screen, offset=offset)

        if self.sub_layers:
            for layer in self.sub_layers:
                if layer.visible:
                    layer.draw(
                        sub_screen, offset=offset)

        return sub_screen

    # the main() method is called by the Game object's main() method
    # each iteration of the loop (i.e. once per frame) if it is assigned
    # to the game's "environment" attribute.
    def main(self, screen):
        self.handle_controller()
        self.update()
        self.draw(screen)

    def on_change_environment(self):
        env = self.event.environment
        env.return_to = self

        transition = ("die",
                      ("goto", env))
        self.handle_event(transition)

    def on_pause(self):
        layer = self.event.layer
        layer.handle_event("spawn")

        layer.set_event_listener(
            "death", "unpause", self,
            temp=True
        )

        layer.active = True
        layer.visible = True
        self.add_sub_layer(layer)
        self.pause_layer = layer

    def on_unpause(self):
        layer = self.pause_layer

        sub_layers = [l for l in self.sub_layers if l is not layer]
        self.sub_layers = sub_layers
        self.pause_layer = None

        r = layer.get_value("_return")
        # print("returning {}".format(r))

        if r:
            self.set_value("_return", r)

    def on_spawn(self):
        self.active = True

        super(Layer, self).on_spawn()
        for layer in self.sub_layers:
            layer.handle_event("spawn")

    def on_die(self):
        super(Layer, self).on_die()

        for group in self.groups:
            for sprite in group:
                sprite.handle_event("die")

    def on_death(self):
        self.active = False

        env = self.event.get(
            "trigger.trigger.goto")
        if not env:
            env = self.return_to

        if env:
            self.transition_to = env
        elif self.game_environment:
                exit()


class SpawnMetaclass(type):
    """
    This Metaclass ensures that all ZsSprite objects will call the
    reset_spawn() method immediately after __init__() is called
    """
    def __call__(cls, *args, **kwargs):
        n = type.__call__(cls, *args, **kwargs)
        if hasattr(n, "on_spawn") and type(n.on_spawn) is MethodType:
            n.handle_event("spawn")
        else:
            raise AttributeError("class does not have 'on_spawn' method")

        return n


class ItemInterface:
    def __init__(self):
        self.controller = None
        self.control_freeze = False
        self.groups = []
        self.model = None

    def get_value(self, key):
        if self.model:
            return self.model.values.get(key)

    def add_to(self, *groups):
        for group in groups:
            group.add_item(self)

    def remove_from(self, *groups):
        for group in groups:
            group.remove_item(self)

    def kill(self):
        for g in self.groups:
            self.remove_from(g)


class Sprite(ItemInterface, Entity, metaclass=SpawnMetaclass):
    def __init__(self, name, size=(1, 1), position=(0, 0)):
        ItemInterface.__init__(self)
        Entity.__init__(self, name, size, position)

        self.sub_sprites = []
        # self.groups = []
        # self.controller = None

    @property
    def graphics(self):
        return self._graphics

    @graphics.setter
    def graphics(self, value):
        self._graphics = value
        self.set_rect_size_to_image()

    def set_rect_size_to_image(self):
        self.rect.size = self.graphics.get_image().get_size()

    def reset_image(self):
        self.graphics.reset_image()
        self.set_rect_size_to_image()

    def on_die(self):
        super(Sprite, self).on_die()

        for sprite in self.sub_sprites:
            sprite.handle_event("die")

    def on_spawn(self):
        super(Sprite, self).on_spawn()
        group = self.event.get("group")
        if group:
            self.add_to(group)

    def on_death(self):
        super(Sprite, self).on_death()
        self.remove_from(*self.groups)

    def add_to(self, *groups):
        super(Sprite, self).add_to(*groups)

        for sprite in self.sub_sprites:
            sprite.add_to(*groups)

    def remove_from(self, *groups):
        super(Sprite, self).remove_from(*groups)

        for sprite in self.sub_sprites:
            sprite.remove_from(*groups)


class Region(ItemInterface, Entity):
    WALL_COLOR = 255, 0, 255

    def __init__(self, name, *points, size=(1, 1),
                 position=(0, 0), **kwargs):

        ItemInterface.__init__(self)
        Entity.__init__(self, name, size=size,
                        position=position)
        self.name = name
        self.position = position

        self.vectors = []
        self.visible = True

        if points:
            self.set_vectors(points, **kwargs)

    def add_vector(self, vector):
        self.vectors.append(vector)

    def set_vectors(self, points, **kwargs):
        self.vectors = self.get_vectors(points, **kwargs)

    @staticmethod
    def get_vectors(points, ground_angle=0.0, orientation=True,
                    offset=(0, 0), friction=None, closed=True):
        if not orientation:
            points = list(points)
            points.reverse()
            points = tuple(points)

        def get_vector(p1, p2):
            x1, y1 = p1
            x2, y2 = p2
            x1 += offset[0]
            x2 += offset[0]
            y2 += offset[1]
            y2 += offset[1]

            return Wall((x1, y1), (x2, y2),
                        friction=friction)

        last = None
        vectors = []
        for point in points:
            if last:
                vectors.append(get_vector(last, point))

            last = point
        if closed:
            vectors.append(get_vector(last, points[0]))

        for v in vectors:
            angle = v.get_angle()
            v.ground = angle <= ground_angle or angle >= 1 - ground_angle

        return vectors

    def draw_vectors(self, screen, offset=(0, 0)):
        for v in self.vectors:
            v.draw(
                screen, offset=offset)

    def get_collision_system(self, items, check, handle):
        cs = CollisionSystem(
            check, handle,
            "group", self.vectors, items
        )

        return cs

    def get_sprite_collision_system(self, group, handle):
        return self.get_collision_system(
            group, Wall.sprite_collision,
            handle)

    def get_vector_collision_system(self, vectors, handle):
        return self.get_collision_system(
            vectors, Wall.vector_collision, handle
        )

    def get_smooth_sprite_collision_system(self, group):
        return self.get_sprite_collision_system(
            group, Wall.handle_collision_smooth
        )

    def get_mirror_sprite_collision_system(self, group):
        return self.get_sprite_collision_system(
            group, Wall.handle_collision_mirror
        )


class RectRegion(Region):
    def __init__(self, name, size, position, **kwargs):
        rect = Rect(size, position)

        points = (rect.bottomleft, rect.topleft,
                  rect.topright, rect.bottomright)

        super(RectRegion, self).__init__(
            name, *points, position=position,
            **kwargs)
