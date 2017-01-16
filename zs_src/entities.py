from sys import exit
from types import MethodType

from pygame.rect import Rect

from zs_constants.zs import SCREEN_SIZE, TRANSITION_TIME
from zs_src.classes import StateMeter
from zs_src.events import ZsEventInterface


class Model(ZsEventInterface):
    def __init__(self, name, v_dict):
        self.name = name
        super(Model, self).__init__(name)
        self.values = {}
        self.change_functions = {}
        self.object_listeners = []

        if v_dict:
            self.set_values(v_dict)
        self.link_object(
            self, "_value_names",
            lambda model: model.value_names
        )
        self.set_value("_value_names", [])

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

    def link_sub_value(self, value_name, key, function):
        functions = self.change_functions.get(value_name, [])

        def sub_function(value):
            function(value[key])

        functions.append(sub_function)
        self.change_functions[value_name] = functions

    def link_object(self, obj, value_name, function):
        l = (obj, value_name, function)
        self.object_listeners.append(l)

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

    def update(self, dt):
        self.event_handler.update(dt)

        self.check_object_listeners()

    def check_object_listeners(self):
        for l in self.object_listeners:
            obj, value_name, func = l
            current = self.values.get(value_name)
            value = func(obj)

            if not current == value:
                self.set_value(value_name, value)


class ZsEntity(ZsEventInterface):
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

        super(ZsEntity, self).__init__(name)
        self.add_event_methods(*ZsEntity.EVENT_NAMES)

        self.rect = Rect(position, size)
        self._graphics = None
        self.parent = None
        self.child = None
        self.visible = True

        self.spawn_time = TRANSITION_TIME
        self.death_time = TRANSITION_TIME
        self._state = StateMeter(name, ZsEntity.STATES)

    def reset_transition_events(self):
        events = "spawning", "birth", "dying", "death"
        self.cancel_events(*events)

    def __repr__(self):
        if self.name == "":
            name = self.__class__.__name__
        else:
            name = self.name
        n, i = name, self.id_num

        return "{} ({})".format(n, i)

    @staticmethod
    def get_id():
        n = ZsEntity.ID_NUM
        ZsEntity.ID_NUM += 1

        return n

    @property
    def graphics(self):
        return self._graphics

    @graphics.setter
    def graphics(self, value):
        self._graphics = value

    @property
    def image(self):
        return self.graphics.get_image()

    @property
    def size(self):
        return self.rect.size

    @size.setter
    def size(self, value):
        self.adjust_size(value)

    @property
    def position(self):
        return self.rect.topleft

    @position.setter
    def position(self, value):
        self.adjust_position(value)

    @property
    def width(self):
        return self.rect.width

    @property
    def height(self):
        return self.rect.height

    @property
    def states(self):
        return self._state.states

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
        pass

    def adjust_position(self, value):
        self.rect.topleft = value

    def move(self, value):
        dx, dy = value
        x, y = self.position
        x += dx
        y += dy
        self.position = x, y

    def get_state(self):
        return self._state.state

    def set_state(self, state):
        if state is not self.get_state():
            self._state.set_state(state)
            name = "change_state"
            change_state = "{} state={}".format(name, state)
            self.handle_event(change_state)

    def update(self, dt):
        if self.graphics:
            self.graphics.update()

        for method in self.get_update_methods():
            method(dt)

    # ALL subclasses that overwrite this method
    # should ALWAYS call the super() version and
    # combine results before returning.
    def get_update_methods(self):
        return [self.event_handler.update]

    def on_spawn(self):
        self.reset_transition_events()

        spawning = ("spawning",
                    ("duration", self.spawn_time),
                    ("trigger", self.event))
        self.queue_events(spawning, "birth")

    def on_spawning(self):
        self.set_state(ZsEntity.STATES[0])

    def on_birth(self):
        self.set_state(ZsEntity.STATES[1])

    def on_die(self):
        self.reset_transition_events()
        dying = ("dying",
                 ("duration", self.spawn_time),
                 ("trigger", self.event))
        self.queue_events(dying, "death")

    def on_dying(self):
        self.set_state(ZsEntity.STATES[2])

    def on_death(self):
        self.set_state(ZsEntity.STATES[3])

    def on_change_state(self):
        pass

    def on_change_linked_value(self):
        pass


class Layer(ZsEntity):
    """
    The Layer object contains Groups (from pygame.sprite) of ZsSprites
    that are updated, and then drawn, all from a main method. Layers can
    also contain sub_layers with their own groups of sprites. The main
    method also calls the get_input() method which can reference any
    of the Controller objects in the 'controllers' list.
    """
    class Group:
        def __init__(self):
            self._sprites = []

        def __iter__(self):
            return iter(self._sprites)

        def update(self, *args):
            for sprite in self._sprites:
                sprite.update(*args)

        def draw(self, screen, offset=(0, 0)):
            for sprite in self._sprites:
                if sprite.image:
                    x, y = sprite.position
                    dx, dy = offset
                    x += dx
                    y += dy
                    position = round(x), round(y)
                    screen.blit(sprite.image, position)

        def add(self, sprite):
            self._sprites.append(sprite)
            sprite.groups.append(self)

        def remove(self, sprite):
            sprite.groups = [g for g in sprite.groups if g is not self]
            self._sprites = [s for s in self._sprites if s is not sprite]

    def __init__(self, name, size=SCREEN_SIZE, position=(0, 0), model=None, controllers=None):
        super(Layer, self).__init__(name, size, position)

        self.game_environment = False
        self.transition_to = None
        self.return_to = None

        self.active = True

        if controllers:
            self.controllers = controllers
        else:
            self.controllers = []
        self.groups = []
        self.sub_layers = []

        self.model = Model(self.name + " model", model)

        self.add_event_methods("change_environment", "pause", "unpause")

    def adjust_size(self, value):
        self.rect.size = value

    # the populate method is meant to be overwritten by subclasses.
    # the PopulateMetaclass ensures that the populate() method is
    # called immediately after __init__ completes.
    def populate(self):
        pass

    def on_spawn(self):
        self.populate()
        self.active = True

        super(Layer, self).on_spawn()
        for layer in self.sub_layers:
            layer.handle_event("spawn")

    @property
    def controller(self):
        try:
            return self.controllers[0]
        except IndexError:
            return None

    def add_controllers(self, *controllers):
        for controller in controllers:
            self.controllers.append(controller)

    @staticmethod
    def make_group():
        return Layer.Group()

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
        for layer in self.sub_layers:
            if layer.active:
                layer.handle_controller()

    def get_update_methods(self):
        um = super(Layer, self).get_update_methods()

        return um + [self.update_groups,
                     self.update_sub_layers,
                     self.model.update]

    def update_groups(self, dt):
        for group in self.groups:
            group.update(dt)

    def update_sub_layers(self, dt):
        for layer in self.sub_layers:
            if layer.active:
                layer.update(dt)

    def get_sprite(self, name):
        for group in self.groups:
            for sprite in group:
                if sprite.name == name:
                    return sprite

    # the Layer object's rect attribute determines the region where the
    # layer will be drawn to the screen. Then all sub_layers are drawn
    # to this region recursively.
    def draw(self, screen, offset=(0, 0)):
        sub_rect = self.rect.clip(screen.get_rect())

        try:
            sub_screen = screen.subsurface(sub_rect)
        except ValueError:      # if the layer's area is entirely outside of the screen's
            return              # area, it doesn't get drawn

        if self.graphics:
            self.graphics.draw(screen, offset=offset)

        if self.groups:
            self.draw_sprites(sub_screen, offset=offset)

        if self.sub_layers:
            for layer in self.sub_layers:
                if layer.visible:
                    layer.draw(sub_screen, offset=offset)

    def draw_sprites(self, screen, offset=(0, 0)):
        for g in self.groups:
            for sprite in g:
                if sprite.image and sprite.visible:
                    x, y = sprite.position
                    x += offset[0]
                    y += offset[1]
                    screen.blit(sprite.image, (x, y))

    # the main() method is called by the Game object's main() method
    # each iteration of the loop (i.e. once per frame) if it is assigned
    # to the game's "environment" attribute.
    def main(self, dt, screen):
        for c in self.controllers:
            c.update()

        self.handle_controller()
        self.update(dt)
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

        unpause = ("unpause",
                   ("layer", layer))
        layer.set_event_listener(
            "death", unpause, self
        )

        layer.active = True
        layer.visible = True
        if layer not in self.sub_layers:
            self.add_sub_layer(layer)

    def on_unpause(self):
        layer = self.event.layer
        sub_layers = [l for l in self.sub_layers if l is not layer]
        self.sub_layers = sub_layers

        r = layer.get_value("_return")
        print("returning {}".format(r))
        if r:
            self.set_value("_return", r)

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


class ZsSprite(ZsEntity, metaclass=SpawnMetaclass):
    def __init__(self, name, size=(1, 1), position=(0, 0)):
        # Sprite.__init__(self)
        ZsEntity.__init__(self, name, size, position)

        self.sub_sprites = []
        self.groups = []

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
        super(ZsSprite, self).on_die()

        for sprite in self.sub_sprites:
            sprite.handle_event("die")

    def on_spawn(self):
        super(ZsSprite, self).on_spawn()
        group = self.event.get("group")
        if group:
            self.add(group)

    def on_death(self):
        super(ZsSprite, self).on_death()
        self.remove(*self.groups)

    # the following methods are inherited from the pygame.Sprite class
    # for interfacing with the pygame.Group object, they ensure that
    # all sub_sprites are added and removed from the groups passed to
    # the add, remove and kill methods.
    def add(self, *groups):
        # super(ZsSprite, self).add(*groups)
        for group in groups:
            group.add(self)

        for sprite in self.sub_sprites:
            sprite.add(*groups)

    def remove(self, *groups):
        # super(ZsSprite, self).remove(*groups)
        for group in groups:
            group.remove(self)

        for sprite in self.sub_sprites:
            sprite.remove(*groups)

    def kill(self):
        for g in self.groups:
            self.remove(g)
