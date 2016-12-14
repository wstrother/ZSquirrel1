from zs_src.classes import StateMeter
from zs_src.events import ZsEventInterface
from zs_src.graphics import Graphics
from zs_constants.zs import SCREEN_SIZE, TRANSITION_TIME

from pygame.rect import Rect
from pygame.sprite import Group, OrderedUpdates, Sprite

from sys import exit
from types import MethodType

from pygame import transform, Surface, SRCALPHA


class Model(ZsEventInterface):
    def __init__(self, name, v_dict):
        self.name = name
        super(Model, self).__init__(name)
        self.values = {}
        self.change_methods = {}

        if v_dict:
            self.set_values(v_dict)

        self.add_event_methods("change_value",
                               "toggle_value",
                               "set_value_to",
                               "append_value",
                               "set_value_at_index")

    def set_values(self, v_dict):
        for name in v_dict:
            self.values[name] = v_dict[name]

    def link_value(self, value_name, method):
        self.add_change_method(value_name, method)

    def handle_change(self, value_name):
        if value_name in self.change_methods:
            value = self.values[value_name]
            for method in self.change_methods[value_name]:
                method(value)

    def add_change_method(self, value_name, method):
        methods = self.change_methods.get(value_name, [])
        methods.append(method)
        self.change_methods[value_name] = methods

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

        self.spawn_time = TRANSITION_TIME
        self.death_time = TRANSITION_TIME
        self._state = StateMeter(name, ZsEntity.STATES)

    def reset_transition_events(self):
        events = "spawning", "birth", "dying", "death"
        self.cancel_events(*events)

    def reset_spawn(self, trigger=None):
        self.reset_transition_events()
        spawning = ("spawning",
                    ("duration", self.spawn_time),
                    ("trigger", trigger))
        self.queue_events(spawning, "birth")

    def reset_death(self, trigger=None):
        self.reset_transition_events()
        dying = ("dying",
                 ("duration", self.spawn_time),
                 ("trigger", trigger))
        self.queue_events(dying, "death")

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
        try:
            return self.graphics.get_image()
        except AttributeError:
            return Graphics.CLEAR_IMG

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

    def get_state(self):
        return self._state.state

    def set_state(self, state):
        if state is not self.get_state():
            self._state.set_state(state)
            name = "change_state"
            change_state = "{} state={}".format(name, state)
            self.handle_event(change_state)

    def get_image_state(self):
        pass

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
        self.reset_spawn(trigger=self.event)

    def on_spawning(self):
        self.set_state(ZsEntity.STATES[0])

    def on_birth(self):
        self.set_state(ZsEntity.STATES[1])

    def on_die(self):
        self.reset_death(trigger=self.event)

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
    def __init__(self, name, size=SCREEN_SIZE, position=(0, 0), model=None):
        super(Layer, self).__init__(name, size, position)

        self.transition_to = None
        self.return_to = None

        self.controllers = []
        self.groups = []
        self.sub_layers = []

        self.model = Model(self.name + " model", model)

        self.add_event_methods("change_environment")

    # the populate method is meant to be overwritten by subclasses.
    # the PopulateMetaclass ensures that the populate() method is
    # called immediately after __init__ completes.
    def populate(self):
        pass

    def reset_spawn(self, trigger=None):
        self.populate()
        super(Layer, self).reset_spawn(trigger)
        for layer in self.sub_layers:
            layer.reset_spawn()

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
    def make_group(ordered=False):
        group = {True: OrderedUpdates, False: Group}[ordered]()

        return group

    def get_value(self, name):
        return self.model.values[name]

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
        pass

    def get_update_methods(self):
        um = super(Layer, self).get_update_methods()

        return um + [self.update_groups, self.update_sub_layers]

    def update_groups(self, dt):
        for group in self.groups:
            group.update(dt)

    def update_sub_layers(self, dt):
        for layer in self.sub_layers:
            layer.update(dt)

    def get_sprite(self, name):
        for group in self.groups:
            for sprite in group:
                if sprite.name == name:
                    return sprite

    # the Layer object's rect attribute determines the region where the
    # layer will be drawn to the screen. Then all sub_layers are drawn
    # to this region recursively.
    def draw(self, screen):
        sub_rect = self.rect.clip(screen.get_rect())
        try:
            sub_screen = screen.subsurface(sub_rect)
        except ValueError:      # if the layer's area is entirely outside of the screen's
            return              # area, it doesn't get drawn

        # bg = self.get_background()
        # if bg:
        #     sub_screen.blit(bg, (0, 0))

        self.blit_to_screen(sub_screen)

    def blit_to_screen(self, screen):
        for item in self.get_draw_order():
            item.draw(screen)

    def get_draw_order(self):
        order = []
        if self.graphics:
            order.append(self.graphics)

        for group in self.groups:
            order.append(group)

        for layer in self.sub_layers:
            order.append(layer)

        return order

    # the main() method is called by the Game object's main() method
    # each iteration of the loop (i.e. once per frame) if it is assigned
    # to the game's "environment" attribute.
    def main(self, dt, screen):
        self.handle_controller()
        self.update(dt)
        self.draw(screen)

    def on_change_environment(self):
        env = self.event.environment
        env.return_to = self

        self.handle_event("die")
        self.return_to = env

    def on_death(self):
        if self.return_to:
            self.transition_to = self.return_to
            self.return_to = None
        else:
                exit()

    def on_die(self):
        super(Layer, self).on_die()

        for group in self.groups:
            for sprite in group:
                sprite.handle_event("die")


class Layer2x(Layer):
    def blit_to_screen(self, screen):
        w, h = screen.get_size()
        w /= 2
        h /= 2

        sub_screen = Surface((w, h), SRCALPHA, 32)

        for item in self.get_draw_order():
            item.draw(sub_screen)
        sub_screen = transform.scale2x(sub_screen)
        screen.blit(sub_screen, (0, 0))


class SpawnMetaclass(type):
    """
    This Metaclass ensures that all ZsSprite objects will call the
    reset_spawn() method immediately after __init__() is called
    """
    def __call__(cls, *args, **kwargs):
        n = type.__call__(cls, *args, **kwargs)
        if hasattr(n, "reset_spawn") and type(n.reset_spawn) is MethodType:
            n.reset_spawn()
        else:
            raise AttributeError("class does not have 'reset_spawn' method")

        return n


class ZsSprite(ZsEntity, Sprite, metaclass=SpawnMetaclass):
    def __init__(self, name, size=(1, 1), position=(0, 0)):
        Sprite.__init__(self)
        ZsEntity.__init__(self, name, size, position)

        self.sub_sprites = []

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

    def reset_spawn(self, trigger=None):
        super(ZsSprite, self).reset_spawn(trigger)

        # for sprite in self.sub_sprites:
        #     sprite.reset_spawn()

    def reset_death(self, trigger=None):
        super(ZsSprite, self).reset_death(trigger)

        # for sprite in self.sub_sprites:
        #     sprite.reset_death()

    def on_spawn(self):
        super(ZsSprite, self).on_spawn()
        group = self.event.group
        self.add(group)

    def on_death(self):
        super(ZsSprite, self).on_death()
        self.kill()

    # the following methods are inherited from the pygame.Sprite class
    # for interfacing with the pygame.Group object, they ensure that
    # all sub_sprites are added and removed from the groups passed to
    # the add, remove and kill methods.
    def add(self, *groups):
        super(ZsSprite, self).add(*groups)

        for sprite in self.sub_sprites:
            sprite.add(*groups)

    def remove(self, *groups):
        super(ZsSprite, self).remove(*groups)

        for sprite in self.sub_sprites:
            sprite.remove(*groups)
