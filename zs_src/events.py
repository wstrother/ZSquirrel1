from zs_src.classes import Timer, Clock


class Event:
    """
    An Event object is a request for a method call that can be applied
    to any entity that extends the ZsEventInterface class (all the base
    classes in zs_src.entities). The 'name' of the event will typically
    map to a method of the form 'object.on_event_name' and the event object
    itself will typically be assigned to the object's 'event' attribute
    for reference by the method.

    An arbitrary number of keyword arguments can be passed that will assign
    to the Event's __dict__ attribute, and can thus be referenced like a normal
    attribute of that name. However, certain names are reserved and will raise
    an error if they are passed as a keyword argument.
    """
    ID_NUM = 0
    RESERVED = "timer", "handlers", "name", "id_num"

    def __init__(self, name, **kwargs):
        self.name = name
        self.id_num = Event.get_id()

        self.timer = None       # typically these attributes are all assigned
        self.handlers = []      # dynamically by an Action or EventHandler object

        # 'trigger' attribute is normally assigned by an EventListener
        if "trigger" not in kwargs:  # the trigger object can be passed manually
            self.trigger = None      # but should only reference another Event object

        for key in kwargs:
            if key not in self.RESERVED:
                self.__dict__[key] = kwargs[key]
            else:
                raise ValueError("reserved key in kwargs '{}'".format(key))

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
    # referenced by including 'trigger.' at the beginning of the
    # key string, including multiple recursive calls such as
    # 'trigger.trigger.key'
    def get(self, key, default=None):
        if key.split(".")[0] == "trigger":
            new_key = ".".join(key.split(".")[1:])
            if self.trigger:
                return self.trigger.get(new_key, default)
            else:
                return default
        else:
            return self.__dict__.get(key, default)

    def set(self, key, value):
        if key not in Event.RESERVED:
            self.__dict__[key] = value
        else:
            raise ValueError("reserved key '{}'".format(key))

    @staticmethod
    def string_to_number(s):
        try:
            # print(s)
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
    # returned with no in place modifications
    @classmethod
    def interpret(cls, args):
        name, kwargs = "", {}

        if type(args) == cls:
            return args

        # string 'name key=value key=value ...'
        elif type(args) == str:
            name, kwargs = cls.str_parse(args)

        # dict {"name": name, key: value,...}
        elif type(args) == dict:
            name, kwargs = args.pop("name"), args

        # tuple (name, (key, value), (key, value),...)
        elif type(args) == tuple or type(args) == list:
            name, kwargs = args[0], dict(args[1:])

        for key in kwargs:
            if key in cls.RESERVED:
                raise ValueError("reserved key in kwargs '{}'".format(key))

        return cls(name, **kwargs)


class Action(Timer):
    """
    An Action object is a type of Timer that pairs an Event object
    with a target object that will handle that event as the Action
    timer ticks. A call to the event method will be made on each call
    to tick() and the action is stored in the event's 'timer' attribute,
    allowing for interpolated effects within the event method.

    An optional 'link' attribute defines another action whose 'start()'
    method will be called when this action's 'on_switch_off()' method is
    called.

    Optionally, 'duration', 'unit', and 'temp' arguments can be set by
    the event argument, but will default to '1', 'f' (frame), and 'True'
    Events passed with no 'target' attribute will cause an AttributeError
    to be raised
    """
    def __init__(self, event):
        name = event.name
        duration = event.get("duration", 1)
        unit = event.get("unit", "f")
        temp = event.get("temp", True)

        super(Action, self).__init__(name, duration, unit=unit, temp=temp)
        self.id_num = Event.get_id()

        self.target = event.target      # Event target object must be set!
        self.event = event
        event.timer = self
        self.link = None

    def __repr__(self):
        return "{} on {}".format(self.name, self.target.name)

    def start(self):
        self.reset()
        self.target.event_handler.handle_action(self)

    # this method will automatically chain future Actions to be
    # started once this action's on_switch_off() method is called.
    # NOTE: if the initial action's 'temp' flag is set the event_handler's
    # Clock object will reset the action when on_switch_off() is called,
    # NOT when the entire chain is completed. To make a chain that loops
    # itself just pass the initial action as the last argument in the
    # action chain. This will assign it to the 'link' attribute of the
    # final action, restarting the loop when completed.
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
    """
    The EventListener object is assigned to an EventHandler object and
    maps a 'trigger' event_name to a target object. An optional 'response_event'
    can be passed, and it's passage determines a kind of conditional
    polymorphic behavior. I.E.:

    response_event = Event object:
    This creates a true 'event listener' that responds to the trigger event by
    creating an Action object that is handled by the target object.
    NOTE: This means the response_event will NOT occur on the same frame as the
    trigger_event! This is important to remember.

    response_event = None:
    This creates a de facto 'event passer' that responds to the trigger event by
    passing the very same trigger event object to the target's event_handler.
    NOTE: This means the target object's event_method will be called immediately
    after the trigger event is handled (on the same frame)! This is important
    to remember.

    The 'temp' flag is used by the EventHandler object to determine whether the
    listener should be removed after it successfully hears an event.
    NOTE: the 'temp' flag passed to this __init__ method has NO EFFECT on whether
    the response_event's Action object has it's 'temp' flag set. The Action
    object's 'temp' flag can be set through the response_event object.
    """
    def __init__(self, trigger_name, target, response_event=None, temp=False):
        self.trigger = trigger_name
        self.target = target

        # true 'event listener'
        if response_event:
            response_event = Event.interpret(response_event)
            response_event.set("target", target)
            self.response = Action(response_event)
            self.response_name = self.response.name
            self.on_match = self.do_response    # alias 'do_response()' as 'on_match()'

        # 'event passer' object
        else:
            self.response = None
            self.response_name = trigger_name
            self.on_match = self.pass_event     # alias 'pass_event()' as 'on_match()'

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

    # the 'on_match()' method is an alias of this method
    # for true 'event listener' objects
    def do_response(self, event):
        self.response.event.trigger = event
        self.response.start()

    # the 'on_match()' method is an alias of this method
    # for 'event passer' objects
    def pass_event(self, event):
        self.target.handle_event(event)


class ConditionalListener(EventListener):
    """
    A ConditionalListener object is a type of event_listener or event_passer
    such that 'test_match()' only returns True if a set of conditions is met.

    The conditions should be passed as a list where each condition can either be:
        -A string: the string should name a key to pass to event.get() which will
    evaluate the bool() function on the output of event.get
        -A function: the function should take the event as a single argument and
    return a bool

    The first 'condition' in the 'conditions' list can optionally be a string that
    assigns to the 'condition_type' attribute, which will determine the way the
    total output of all conditions is returned. If no such string is included the
    'condition_type' will default to 'all.'

    The 'condition_type' string can be: 'all', 'any', 'not all', or 'not any'
    """
    def __init__(self, conditions, *args, **kwargs):
        super(ConditionalListener, self).__init__(*args, **kwargs)

        header = type(conditions[0]) is str
        if header in ("all", "any", "not all", "not any"):
                self.condition_type = conditions.pop(0)
        else:
            self.condition_type = "all"
        self.conditions = conditions

    def test_match(self, event):
        if not super(ConditionalListener, self).test_match(event):
            return False

        tests = []
        for c in self.conditions:
            if type(c) == str:      # test the bool() value of a given attribute
                inverse = False
                if c[:4] == "not ":
                    c = c[4:]
                    inverse = True
                test = bool(event.get(c)) is True
                if inverse:
                    test = not test
            else:
                test = c(event)     # function takes event as arg and returns bool
            tests.append(test)

        ct = self.condition_type
        if ct == "any":
            return any(tests)

        elif ct == "all":
            return all(tests)

        elif ct == "not any":
            return not any(tests)

        elif ct == "not all":
            return not all(tests)

        else:
            raise ValueError("Bad condition_type set {}".format(self.condition_type))


class EventHandler:
    """
    The EventHandler class creates an object that is composed
    into all ZsEntity objects through the ZsEventInterface. It
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
            em = getattr(target, "on_" + name, None)
            if em:
                ok_names.append((name, em))
            else:
                print("no on_" + name + " method found for " + target.name)

        for name, em in ok_names:
            self.set_event_method(name, em)

    # NOTE: you can technically use this method to map an event
    # to an unbound method or a method bound to another object
    # although this functionality doesn't seem very useful to me
    # at the moment, especially because the handle_event() method
    # will NOT assign the event to anything, meaning the method
    # cannot reference the event
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
            def match(l):
                return l.trigger == event_name and l.response_name == response_name
            nl = [l for l in self.listeners if not match(l)]

        else:
            def match(l):
                return l.trigger == event_name
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
                method.__self__.event = event       # bound method) will have its 'event'
            self.event_methods[name]()              # attribute set to reference the event

        for l in self.listeners:
            h = l.hear(event)       # NOTE: listener.hear() method is called
            if h and l.temp:        # after the event_method is called
                self.remove_listener(name, l.response_name)

    def check_activity(self, name):
        found = False
        if name in self.event_methods:
            found = True

        if name in [l.name for l in self.listeners]:
            found = True

        return found

    def handle_action(self, action):
        self.clock.add_timers(action)

    def update(self):
        self.clock.tick()


class EventInterface:
    """
    The ZsEventInterface is a parent class used to provide an API frontend
    for using the zs_src.events module without directly importing the classes.

    The ZsEntity object is given an EventHandler object and 'event' attribute.
    Any object using this interface can reference the event attribute in
    event_methods for access to the event that was handled. It can also add
    or remove event_methods and listeners.

    NOTE: Remember that event_methods must be 'registered' by the EventHandler
    through the 'add_event_methods()' method, or else the event_method
    WILL NOT BE CALLED! This is the first thing to check when debugging event
    behavior that isn't working right.

    However, this is not an oversight. The EventHandler needs a way to
    dynamically add or remove event_methods so the relevant behaviors can be
    turned on or off at runtime. This is extremely important for programming
    game logic in the ZSquirrel1 API.
    """
    def __init__(self, name):
        self.event_handler = EventHandler(name)
        self.event = None

    # The following methods provide convenient and direct ways to interface with
    # the EventHandler object. All of the 'response' arguments can be passed in
    # any valid format that Event.interpret() can take.
    def add_event_methods(self, *event_names):
        self.event_handler.add_event_methods(self, *event_names)

    def remove_event_methods(self, *event_names):
        self.event_handler.remove_event_methods(*event_names)

    def add_timer(self, name, duration, temp=True,
                  on_tick=None, on_switch_off=None):
        timer = Timer(name, duration, temp=temp)
        if on_tick:
            timer.on_tick = on_tick
        if on_switch_off:
            timer.on_switch_off = on_switch_off

        self.event_handler.clock.add_timers(timer)

    # NOTE: calling the 'handle_event' method is exactly the same as calling
    # the bound event_method directly, after creating an event object and
    # assigning it to the object's 'event' attribute. I DO NOT RECOMMEND
    # ever doing this, but the point is that the event_method is called
    # immediately, not on the next frame.
    def handle_event(self, event):
        self.event_handler.handle_event(event)

    # NOTE: It's important to understand the difference between the
    # 'queue_events()' method and 'handle_event()', namely: if you pass
    # a single event to 'queue_events()' it will be composed into an Action
    # object which is then added to the event_handler's Clock object. I.E.:
    # the event_method will be called on the next frame, not at the same
    # stack frame where 'queue_events()' is called.
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

    # NOTE: if no 'target' argument is passed to this method, the default
    # target will become the entity object itself.
    def set_event_listener(self, trigger_name, response,
                           target=None, temp=False):
        if not target:
            response = Event.interpret(response)
            target = response.get("target", self)

        listener = EventListener(trigger_name, target, response, temp=temp)
        self.event_handler.add_listeners(listener)

    def set_event_passer(self, event_name, target, temp=False):
        passer = EventListener(event_name, target, temp=temp)
        self.event_handler.add_listeners(passer)

    # NOTE: if no 'target' argument is passed to this method, the default
    # target will become the entity object itself.
    def set_event_conditional(self, trigger_name, conditions,
                              response=None, target=None, temp=False):
        if not target:
            response = Event.interpret(response)
            target = response.get("target", self)

        if not type(conditions) is list:
            conditions = [conditions]

        listener = ConditionalListener(
            conditions, trigger_name, target, response, temp=temp)
        self.event_handler.add_listeners(listener)

    def remove_event_listener(self, event_name, response_name=None):
        self.event_handler.remove_listener(
            event_name, response_name=response_name)

