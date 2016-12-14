from zs_src.classes import Timer, Clock


class Event:
    """
    An Event object is a request for a future, abstract method call of
    a certain 'name'. The 'trigger' attribute is a place holder for a
    reference to another Event when heard by an EventListener object.
    It also has a list of handlers for each EventHandler that it is
    passed to in a call to EventHandler.handle_event()

    Any arbitrary dictionary of keywords can be passed to an Event on
    initialization unless they use an attribute name that is already
    taken. The Event.interpret() method can be used to turn a variety
    of simplified argument formats into an Event object
    """
    ID_NUM = 0
    RESERVED = "timer", "handlers", "name", "id_num"

    def __init__(self, name, **kwargs):
        self.name = name
        self.id_num = Event.get_id()

        if "trigger" not in kwargs:
            self.trigger = None
        self.timer = None
        self.handlers = []

        for key in kwargs:
            if key not in self.__dict__:
                self.__dict__[key] = kwargs[key]

    def __repr__(self):
        s = "{}_{}"

        return s.format(self.name, str(self.id_num))

    @staticmethod
    def get_id():
        n = Event.ID_NUM
        Event.ID_NUM += 1

        return n

    # this method returns default if the attribute name is not in the
    # dictionary. The attributes of the "trigger" event can be
    # referenced by including "trigger." at the beginning of the
    # key string.
    def get(self, key, default=None):
        if key.split(".")[0] == "trigger":
            new_key = ".".join(key.split(".")[1:])
            if self.trigger:
                return self.trigger.get(new_key, default)
            else:
                return False        # returns False if event has no trigger

        else:
            return self.__dict__.get(key, default)

    def set(self, key, value):
        if key not in Event.RESERVED:
            self.__dict__[key] = value
        else:
            raise ValueError

    @staticmethod
    def string_to_number(s):
        try:
            num = float(s)
            if num.is_integer():
                num = int(num)
            return num
        except ValueError:
            return s

    @staticmethod
    def str_parse(s):
        if len(s.split()) == 1:
            name, kwargs = s, {}

        else:
            name, query = s.split()[0], " ".join(s.split()[1:])

            keys = []
            values = []
            queries = query.split("=")

            for section in queries:
                first = queries.index(section) == 0
                last = queries.index(section) == len(queries) - 1

                key = section.split()[-1]
                keys.append(key)

                if not first:
                    if not last:
                        value = " ".join(section.split()[:-1])

                    else:
                        value = section
                    values.append(Event.string_to_number(value))
            keys.pop()

            kwargs = dict(zip(keys, values))

        return name, kwargs

    # this static method is used to return an Event object from
    # a number of simplified initializing argument formats.
    # the name and all keys should be strings as they represent
    # attribute names. If an Event object is passed it will be
    # returned
    @staticmethod
    def interpret(args):
        name, kwargs = "", {}

        if type(args) == Event:
            return args

        # string 'name key=value key=value ...'
        elif type(args) == str:              # if 'arg' is a string
            name, kwargs = Event.str_parse(args)

        # dict {"name": name, key: value,...}
        elif type(args) == dict:                   # 'arg' can be a dict of attributes but
            name, kwargs = args.pop("name"), args  # must have a 'name' key

        # tuple (name, (key, value), (key, value),...)
        elif type(args) == tuple or type(args) == list:  # 'arg' can be a tuple, where the first
            name, kwargs = args[0], dict(args[1:])       # item is the 'name' value and each
                                                         # subsequent item is a '(key, value)' tuple

        for key in kwargs:
            if key in Event.RESERVED:
                raise ValueError("reserved key in kwargs '{}'".format(key))

        return Event(name, **kwargs)


class Action(Timer):
    """
    An Action object is a type of Timer that pairs an Event object
    with a target object that will handle that event as the Action
    timer ticks. A method call is made on each tick and when the
    timer is switched off, an optional 'link' action will start.

    Optionally, a 'duration' or 'unit' argument can be passed through
    the Event object itself, their default values are 1 and 'f' (frame)
    """
    def __init__(self, event):
        name = event.name
        duration = event.get("duration", 1)
        unit = event.get("unit", "f")

        super(Action, self).__init__(name, duration, unit=unit, temp=True)
        self.id_num = Event.get_id()

        self.target = event.target
        self.event = event
        event.timer = self
        self.link = None

    def __repr__(self):
        return "{} on {}".format(self.name, self.target.name)

    def start(self):
        self.reset()
        if self.target is None:
            print("")
        self.target.event_handler.handle_action(self)

    # pass in actions to chain, in order, to self.chain_actions
    def chain_actions(self, *actions):
        al = [self] + list(actions)
        for i in range(len(al) - 1):
            a = al[i]
            a.link = al[i + 1]

    def on_tick(self):
        self.target.handle_event(self.event)

    def on_switch_off(self):
        if self.link:
            self.link.event.trigger = self.event
            self.link.start()


class EventListener:
    def __init__(self, trigger_name, target, response_event=None, temp=False):
        self.trigger = trigger_name
        self.target = target

        if response_event:
            response_event = Event.interpret(response_event)
            response_event.set("target", target)
            self.response = Action(response_event)
            self.response_name = self.response.name
            self.on_match = self.do_response
        else:
            self.response = None
            self.response_name = trigger_name
            self.on_match = self.pass_event

        self.temp = temp

    def __repr__(self):
        return "{} event listener, response ({})".format(self.trigger, self.response)

    def test_match(self, event):
        return event.name == self.trigger

    def hear(self, event):
        match = self.test_match(event)

        if match:
            self.on_match(event)

        return match

    def do_response(self, event):
        self.response.event.trigger = event
        self.response.start()

    def pass_event(self, event):
        self.target.handle_event(event)


class ConditionalListener(EventListener):
    def __init__(self, conditions, *args, **kwargs):
        super(ConditionalListener, self).__init__(*args, **kwargs)

        if conditions[0] in ("all", "any"):
            self.condition_type = conditions.pop(0)
        else:
            self.condition_type = "all"
        self.conditions = conditions

    def test_match(self, event):
        if not super(ConditionalListener, self).test_match(event):
            return False

        tests = []
        for c in self.conditions:
            if type(c) == str:
                test = event.get(c) == True
            else:
                test = c(event)
            tests.append(test)

        ct = self.condition_type
        if ct == "any":
            return any(tests)

        if ct == "all":
            return all(tests)


class EventHandler:
    """
    The EventHandler class creates an object that is composed
    into ZsEntity objects through the ZsEventInterface. It
    has a list of EventListener (and subclass) objects and
    a dictionary that maps event_name keys to event_methods.
    """
    def __init__(self, name):
        self.name = name
        self.event_methods = {}
        self.listeners = []
        self.clock = Clock(name)

    def __repr__(self):
        n, em, l = self.name, len(self.event_methods), len(self.listeners)

        return "EventHandler '{}' with {} methods, {} listeners".format(n, em, l)

    # This method maps event_names specifically to bound methods
    # of a target object. The methods must be named according to the
    # convention "on_event_name" or it will raise a value error.
    def add_event_methods(self, target, *event_names):
        ok_names = []
        for name in event_names:
            em = getattr(target, "on_" + name, False)
            if not em:
                raise ValueError("no method with 'on_{}' pattern in {}".format(name, target))

            ok_names.append((name, em))

        for name, em in ok_names:
            self.set_event_method(name, em)

    # NOTE: you can technically use this method to map an event
    # to an unbound method or a method bound to another object
    # although I haven't thought of a use for this
    def set_event_method(self, event_name, method):
        self.event_methods[event_name] = method

    def remove_event_methods(self, *event_names):
        for event_name in event_names:
            self.event_methods.pop(event_name)

    def add_listeners(self, *listeners):
        for l in listeners:
            self.listeners.append(l)

    # the remove_listener method takes an event_name and also
    # an optional response_name argument.
    def remove_listener(self, event_name, response_name=None):
        if response_name:
            match = lambda l: (l.trigger == event_name and l.response_name == response_name)
            nl = [l for l in self.listeners if not match(l)]
        else:
            match = lambda l: l.trigger == event_name
            nl = [l for l in self.listeners if not match(l)]
        self.listeners = nl

    # the handle_event method takes a single event argument
    # that can be passed in any valid format for the
    # Event.interpret() method
    def handle_event(self, event):
        event = Event.interpret(event)
        event.handlers.append(self)
        name = event.name

        if name in self.event_methods:
            method = self.event_methods[name]       # before the matching event_method is
            if hasattr(method, "__self__"):         # called, the bound object (if it is a
                method.__self__.event = event       # bound method) will have it's 'event'
            self.event_methods[name]()              # attribute set to reference the event

        for l in self.listeners:
            h = l.hear(event)       # NOTE: listener.hear() method is called
            if h and l.temp:        # after the event_method is called
                self.remove_listener(name, l.response_name)

    def handle_action(self, action):
        self.clock.add_timers(action)

    def update(self, dt):
        self.clock.tick(dt)


class ZsEventInterface:
    """
    The ZsEventInterface is a mixin class used to provide an API frontend
    for using the zs_src.events module without directly importing the classes.

    The ZsEntity object is given an EventHandler object and 'event' attribute.
    Any object using this interface can reference the event attribute in event_methods
    for access to the event that was handled.
    """
    def __init__(self, name):
        self.event_handler = EventHandler(name)
        self.event = None

    """
    The following methods provide convenient and direct ways to interface with
    the EventHandler object. All of the 'event' arguments can be passed in any
    valid format that Event.interpret() can take.
    """
    def handle_event(self, event):
        self.event_handler.handle_event(event)

    def add_event_methods(self, *event_names):
        self.event_handler.add_event_methods(self, *event_names)

    def remove_event_methods(self, *event_names):
        self.event_handler.remove_event_methods(*event_names)

    def queue_events(self, *events):
        a = []
        for event in events:
            e = Event.interpret(event)
            if not e.get("target"):
                e.set("target", self)
            a.append(Action(e))

        first = a[0]
        if len(a) > 1:
            rest = a[1:]
            first.chain_actions(*rest)
        first.start()

    def cancel_events(self, *event_names):
        for event_name in event_names:
            self.event_handler.clock.remove_timer(event_name)

    def set_event_listener(self, event_name, response, target=None, temp=False):
        if not target:
            response = Event.interpret(response)
            target = response.get("target", self)

        listener = EventListener(event_name, target, response, temp=temp)
        self.event_handler.add_listeners(listener)

    def set_event_passer(self, event_name, target, temp=False):
        passer = EventListener(event_name, target, temp=temp)
        self.event_handler.add_listeners(passer)

    def set_event_conditional(self, event_name, conditions,
                              response=None, target=None, temp=False):
        if not target:
            response = Event.interpret(response)
            target = response.get("target", self)

        listener = ConditionalListener(conditions, event_name, target, response, temp=temp)
        self.event_handler.add_listeners(listener)

    def remove_event_listener(self, event_name, response_name=None):
        self.event_handler.remove_listener(event_name, response_name=response_name)

