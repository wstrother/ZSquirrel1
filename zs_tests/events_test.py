from random import seed, randint, random

from zs_src.events import Event, Action, EventHandler, EventInterface
from zs_tests.zs_unit_test import ZsUnitTest


class EventUnitTest(ZsUnitTest):
    ABC = "abcdefghijklmnopqrstuvwxyz"

    @staticmethod
    def get_char():
        abc = EventUnitTest.ABC
        return abc[randint(0, len(abc) - 1)]

    @staticmethod
    def get_value():
        i = randint(0, 2)
        if i == 0:
            chars = "abcdefghijklmnopqrstuvwxyz"
            return chars[randint(0, len(chars) - 1)]
        elif i == 1:
            return randint(0, 9)
        elif i == 2:
            return random() * randint(1, 9)

    def do_tests(self, r=5):
        l = self.log
        l("!s", Event)
        seed(r)

        for i in range(r ** 2):
            l("!r")
            args = self.get_event_args(r)
            l("test_event with args " + self.get_event_str(args))

            l("")
            self.test_init_args(args)

        l("! ")

    def get_event_args(self, r):
        args = []
        keys = []
        for x in range(r):
            key, value = self.get_char(), self.get_value()
            if key not in keys:
                args.append((key, value))
                keys.append(key)

        return args

    @staticmethod
    def get_event_str(args, name="test_event"):
        es = name
        for arg in args:
            key, value = arg
            es += " {}={}".format(key, value)

        return es

    @staticmethod
    def get_event_dict(args):
        d = {"name": "test_event"}
        for arg in args:
            key, value = arg
            d[key] = value

        return d

    @staticmethod
    def get_event_tuple(args):
        t = ("test_event",)
        for arg in args:
            key, value = arg
            t += ((key, value), )

        return t

    def test_init_args(self, args):
        l = self.log
        l("!m", self.test_init_args)

        get_event = Event.interpret
        s, d, t = self.get_event_str(args), self.get_event_dict(args), self.get_event_tuple(args)
        s_event = get_event(s)
        d_event = get_event(d)
        t_event = get_event(t)

        for arg in args:
            key, value = arg
            assert s_event.get(key) == value
            l("s_event key {}, value {} stored ok".format(key, value))

            assert d_event.get(key) == value
            l("d_event key {}, value {} stored ok".format(key, value))

            assert t_event.get(key) == value
            l("t_event key {}, value {} stored ok".format(key, value))
        l("event initialized ok with string, dict, and tuple args")


class ActionUnitTest(EventUnitTest):
    class MockTarget:
        def __init__(self):
            self.events_handled = []
            self.actions_handled = []
            self.event_handler = self.MockEventHandler(self)

        def handle_event(self, event):
            self.events_handled.append(event)

        class MockEventHandler:
            def __init__(self, mock_target):
                self.target = mock_target

            def handle_action(self, action):
                self.target.actions_handled.append(action)

    def do_tests(self, r=5):
        l = self.log
        l("!s", Action)
        seed(r)

        for i in range(r ** 2):
            args = self.get_event_args(r)

            l("!r")
            l(self.get_event_str(args))

            l("")
            self.test_init_args(args)
            l("init args ok")

            l("")
            self.test_action_methods(args)
            l("methods ok")
        l(" ")

    def test_init_args(self, args):
        l = self.log
        l("!m", self.test_init_args)

        es = self.get_event_str(args)
        target = self.MockTarget()
        args.append(("target", target))
        event = Event.interpret(args)

        action = Action(event)
        assert action.maximum == 1
        l("duration ok")

        assert action.unit == "f"
        l("unit ok")

        assert action.target == target
        l("target ok")

        assert action.event == event
        l("event ok")

        l("action initialized ok with event {}".format(es))

    def test_action_methods(self, args):
        l = self.log
        l("!m", self.test_action_methods)

        target = args[-1][1]
        event = Event.interpret(args)
        action = Action(event)

        # start
        action.start()
        assert action.is_full()
        assert action in target.actions_handled
        l("start ok")

        # chain_actions
        chain = []
        for i in range(5):
            link = Action(Event("test_event", target=self.MockTarget()))
            chain.append(link)
        action.chain_actions(*chain)

        last = action
        for link in chain:
            assert last.link == link
            last = link
        l("chain_actions ok")

        # on tick
        action.on_tick()
        assert event in target.events_handled
        l("on_tick ok")

        # on switch off
        action.on_switch_off()
        assert action.link in action.link.target.actions_handled
        l("on_switch_off ok")


class EventHandlerUnitTest(EventUnitTest):
    class MockTarget:
        def __init__(self):
            self.test_event_called = False
            self.events_handled = []

        def on_test_event(self):
            self.test_event_called = True

        def on_a(self):
            self.events_handled.append("a")

        def on_b(self):
            self.events_handled.append("b")

        def on_c(self):
            self.events_handled.append("c")

    class MockListener:
        def __init__(self, name, response_name, temp=False):
            self.name = name
            self.trigger = name
            self.response_name = response_name
            self.events_heard = []
            self.temp = temp

        def hear(self, event):
            heard = event.name == self.name
            if heard:
                self.events_heard.append(event.name)

            return heard

        def __repr__(self):
            n, r, t = self.name, self.response_name, self.temp
            return "{} / {} temp = {}".format(n, r, t)

    class MockClock:
        def __init__(self):
            self.timers = []
            self.ticked = 0

        def tick(self, dt):
            self.ticked += dt

        def add_timers(self, *timers):
            for timer in timers:
                self.timers.append(timer)

        def remove_timer(self, name):
            t = [timer for timer in self.timers if timer.name != name]
            self.timers = t

    def print_listeners(self, listeners):
        self.log("\n{} listeners total".format(len(listeners)))
        for l in listeners:
            self.log("\t {}".format(l))

    def do_tests(self, r=5):
        l = self.log
        l("!s", EventHandler)
        seed(r)

        self.test_event_methods()
        l("")

        self.test_listener_methods(r)
        l("")

        self.test_clock_methods(r)
        l("")

        self.test_handle_event_method(r)
        l("! ")

    def test_event_methods(self):
        l = self.log
        l("!m", self.test_event_methods)

        target = self.MockTarget()
        eh = EventHandler("test_event handler")

        error_caught = False
        try:
            eh.add_event_methods(target, "test_event", "bad_name")
        except ValueError:
            error_caught = True
        assert error_caught
        l("bad event method name caught ok")
        assert eh.event_methods == {}
        l("no partial assignment to event_methods list")

        eh.add_event_methods(target, "test_event")
        assert eh.event_methods["test_event"] == target.on_test_event
        l("add_event_methods ok")

        eh.remove_event_methods("test_event")
        assert eh.event_methods == {}
        l("remove_event_methods ok")

    def get_mock_listeners(self, r):
        listeners = []
        abc = EventUnitTest.ABC
        for x in range(r):
            name = abc[x % len(abc)]
            r1, r2 = "abc"[x % 3], "abc"[(x + 1) % 3]
            listeners.append(self.MockListener(name, r1, False))
            listeners.append(self.MockListener(name, r2, True))

        return listeners

    def test_listener_methods(self, r):
        l = self.log
        l("!m", self.test_listener_methods)

        eh = EventHandler("test_event handler")

        listeners = self.get_mock_listeners(r)

        eh.add_listeners(*listeners)
        for listener in listeners:
            assert listener in eh.listeners
        l("add_listeners ok")

        abc = EventUnitTest.ABC
        for char in abc:
            eh.remove_listener(char)
            get_names = lambda handler: [y.name for y in handler.listeners]
            assert char not in get_names(eh)
        l("remove_listeners with no response_name arg ok")

        eh.add_listeners(*listeners)
        self.print_listeners(eh.listeners)
        for x in range(r):
            char = abc[x % len(abc)]
            eh.remove_listener(char, "a")
            l("\nremoving {} / {}".format(char, "a"))
            self.print_listeners(eh.listeners)

            match_list = [li for li in listeners if li.name == char]
            for listener in match_list:
                assert (listener.response_name == "a") == (listener not in eh.listeners)
        l("remove_listeners with response_name arg ok")
        eh.listeners = []

    def test_clock_methods(self, r):
        l = self.log
        l("!m", self.test_clock_methods)

        eh = EventHandler("test_event handler")

        eh.clock = self.MockClock()
        action = "test_action"
        eh.handle_action(action)
        assert action in eh.clock.timers
        l("handle_action ok")

        eh.update(r)
        assert eh.clock.ticked == r
        l("update ok")

    def test_handle_event_method(self, r):
        l = self.log
        l("!m", self.test_handle_event_method)

        eh = EventHandler("test_event handler")
        target = self.MockTarget()

        listeners = self.get_mock_listeners(r)
        eh.add_listeners(*listeners)
        eh.add_event_methods(target, *"abc")
        self.print_listeners(eh.listeners)

        abc = EventUnitTest.ABC
        for char in abc:
            l("\n-------\nhandling event {}".format(char))
            eh.handle_event(char)
            if char in "abc":
                assert char in target.events_handled
                l("event {} handled by target ok".format(char))

            for listener in listeners:
                if listener.name == char:
                    assert char in listener.events_heard
                    l("{} heard by {}".format(char, listener))

                    if listener.temp:
                        assert listener not in eh.listeners
                        l("temp listener removed ok")

            self.print_listeners(eh.listeners)
            l("")


class ZsEventInterfaceUnitTest(EventHandlerUnitTest):
    class MockEventHandler:
        def __init__(self):
            self.name = "Mock event handler"
            self.event_methods = {}
            self.listeners = []
            self.clock = EventHandlerUnitTest.MockClock()

            self.events_handled = []
            self.actions_handled = []
            self.remove_listener_called = False

        def add_event_methods(self, target, *event_names):
            for name in event_names:
                self.event_methods[name] = target

        def remove_event_methods(self, *event_names):
            for name in event_names:
                if name in self.event_methods:
                    self.event_methods.pop(name)

        def add_listeners(self, *listeners):
            for l in listeners:
                self.listeners.append(l)

        def remove_listener(self, name, response_name=None):
            self.remove_listener_called = name, response_name

        def handle_event(self, event):
            self.events_handled.append(event.name)

        def handle_action(self, action):
            self.actions_handled.append(action.name)
            self.clock.add_timers(action)

    class MockAction:
        def __init__(self, name):
            self.name = name

    class MockEvent:
        def __init__(self, name):
            self.name = name

    def do_tests(self, r=5):
        l = self.log
        l("!s", EventInterface)
        seed(r)

        ei = EventInterface("test interface")
        eh = self.MockEventHandler()
        ei.event_handler = eh

        ei.handle_event(self.MockEvent("test_event"))
        assert "test_event" in eh.events_handled
        l("handle_event ok")

        ei.add_event_methods(*"abc")
        for char in "abc":
            assert char in eh.event_methods
        l("add_event_methods ok")

        ei.remove_event_methods(*"abc")
        assert eh.event_methods == {}
        l("remove_event_methods ok")

        ei.queue_events(*"abc")
        assert "a" in eh.actions_handled
        assert "b" not in eh.actions_handled and "c" not in eh.actions_handled
        l("queue_events ok")
        l("")

        ei.cancel_events("a")
        found = False
        for timer in eh.clock.timers:
            if timer.name == "a":
                found = True
        assert not found
        l("cancel_event ok")

        self.test_event_listener_methods()
        l("! ")

    def test_event_listener_methods(self):
        abc = EventUnitTest.ABC
        l = self.log
        l("!m", self.test_event_listener_methods)

        ei = EventInterface("test interface")
        eh = self.MockEventHandler()
        ei.event_handler = eh

        entries = []
        for event_name in abc:
            response_name = self.get_char()
            temp = randint(0, 1) == True

            if randint(0, 1):
                target = ei
                ei.set_event_listener(event_name, response_name, None, temp)
            else:
                target = self.MockTarget
                ei.set_event_listener(event_name, response_name, target, temp)
            new_entry = event_name, response_name, target, temp
            entries.append(new_entry)

        for x in range(len(abc)):
            event_name, response_name, target, temp = entries[x]
            listener = eh.listeners[x]

            assert listener.trigger == event_name
            assert listener.response_name == response_name
            assert listener.response.target is target
            assert listener.temp == temp
            l("listener for {} added ok".format(listener.trigger))
        l("set_event_listener ok")

        eh.listeners = []
        entries = []
        for event_name in abc:
            temp = randint(0, 1) == True
            target = self.MockTarget()

            ei.set_event_passer(event_name, target, temp)
            new_entry = event_name, target, temp
            entries.append(new_entry)

        for x in range(len(abc)):
            event_name, target, temp = entries[x]
            listener = eh.listeners[x]

            assert listener.trigger == event_name
            assert listener.target == target
            assert listener.temp == temp
            l("event_passer for {} added ok".format(listener.trigger))
        l("set_event_passer ok")

        ei.remove_event_listener("test_event", "test_response")
        assert eh.remove_listener_called == ("test_event", "test_response")
        l("remove_listener ok")

TESTS = (
    EventUnitTest, ActionUnitTest,
    EventHandlerUnitTest, ZsEventInterfaceUnitTest
)


def do_tests():
    for t in TESTS:
        t().do_tests()
