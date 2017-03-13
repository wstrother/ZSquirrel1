from zs_constants.zs import REPR_SIG_FIGS


class Meter:
    """
    Meter objects have a minimum, value, and maximum attribute (int or float)
    The normalize method is called when one of these attributes is assigned to
    ensuring that value stays in the proper range.

    Use of property objects as attributes allows for some automatic edge case
    handling. Be aware that by design Meter objects will try to make assignments
    work rather than throw errors. E.G. passing a minimum lower than maximum
    to __init__ raises ValueError, but the 'maximum' / 'minimum' setters will
    automatically normalize assignments to an acceptable range.

    Meter is designed to make composed attributes and to allow for flexible
    dynamic use so if you want to ensure edge case errors, that logic will
    need to be implemented by the relevant Entity in the game engine.
    """
    # Meter(name, value) ->                     minimum = 0, value = value, maximum = value
    # Meter(name, value, maximum) ->            minimum = 0, value = value, maximum = maximum
    # Meter(name, minimum, value, maximum) ->   minimum = 0, value = value, maximum = maximum
    def __init__(self, name, *args):
        value = args[0]
        maximum = args[0]
        minimum = 0
        if len(args) == 2:
            maximum = args[1]
        if len(args) == 3:
            minimum = args[0]
            value = args[1]
            maximum = args[2]

        self.name = name
        self._value = value
        self._maximum = maximum
        self._minimum = minimum

        if maximum < minimum:     # minimum should always be leq than maximum
            raise ValueError("bad maximum / minimum values passed to meter object")
        self.normalize()

    def __repr__(self):
        sf = REPR_SIG_FIGS
        n, v, m, r = (self.name,
                      round(self.value, sf),
                      round(self._maximum, sf),
                      round(self.get_ratio(), sf))

        return "{}: {}/{} r: {}".format(n, v, m, r)

    # getters and setters
    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value
        self.normalize()

    @property
    def minimum(self):
        return self._minimum

    @minimum.setter
    def minimum(self, value):
        if value > self.maximum:
            value = self.maximum

        self._minimum = value
        self.normalize()

    @property
    def maximum(self):
        return self._maximum

    @maximum.setter
    def maximum(self, value):
        if value < self.minimum:
            value = self.minimum

        self._maximum = value
        self.normalize()

    # methods
    def normalize(self):        # sets value to be inside min / max range
        in_bounds = True

        if self._value > self.maximum:
            self._value = self.maximum
            in_bounds = False

        if self._value < self.minimum:
            self._value = self.minimum
            in_bounds = False

        # this return value is mainly for debugging
        # and unit testing
        return in_bounds

    def refill(self):
        self.value = self.maximum

        return self.value

    def reset(self):
        self.value = self.minimum

        return self.value

    def get_ratio(self):
        span = self.get_span()
        value_span = self.value - self.minimum

        if span != 0:
            return value_span / span
        else:
            # calling "get_ratio" on a Meter object with a span of 0
            # will raise an ArithmeticError. There's no real way to
            # handle this edge case dynamically without creating
            # very weird, unintuitive behavior
            raise ArithmeticError("meter object has span of 0")

    def get_span(self):
        return self.maximum - self.minimum

    def is_full(self):
        return self.value == self.maximum

    def is_empty(self):
        return self.value == self.minimum

    def next(self):
        if self.is_full():
            self.reset()
        else:
            self.value += 1
            if self.value > self.maximum:
                dv = self.value - self.maximum
                self.value = dv

        return self.value

    def prev(self):
        if self.is_empty():
            self.refill()
        else:
            self.value -= 1
            if self.value < self.minimum:
                dv = self.value - self.minimum
                self.value = self.maximum - dv

        return self.value

    def shift(self, val):
        dv = abs(val) % (self.get_span() + 1)
        if val > 0:
            for x in range(dv):
                self.next()
        if val < 0:
            for x in range(dv):
                self.prev()

        return self.value

FRAMES = "f"
SECONDS = "s"


class Timer(Meter):
    """
    Timer objects have a set duration stored as either frames or
    seconds, specified by passing 'f' or 's' to the unit argument.

    By default, timers count frames and decrement by 1 every time
    tick() is called, but a dt value can be passed for second based
    timers. I'm considering deprecating the 'unit' attribute and
    second based timers because they are non-deterministic by number
    of frames (the dt value will depend on the user's system and the
    engine fully updating within the requested framerate, which
    won't always necessarily be accurate) so frame timers are preferred
    in most use cases.

    An optional on_tick() method is called on every frame the timer is
    ticked, and the on_switch_off method is called on the frame that the
    Timer's value reaches 0.

    The temp flag determines if the timer will be removed by the Clock
    object that calls it's tick() method.
    """
    def __init__(self, name, duration, unit=FRAMES, temp=True):
        if duration <= 0:
            raise ValueError("bad duration", 0)

        self.is_off = self.is_empty
        self.reset = self.refill

        if unit not in (FRAMES, SECONDS):
            raise ValueError("bad string passed as 'unit' arg", 1)

        super(Timer, self).__init__(name, duration)
        self.temp = temp
        self.unit = unit

    def __repr__(self):
        sf = REPR_SIG_FIGS
        n, v, m, r = (self.name,
                      round(self.value, sf),
                      round(self._maximum, sf),
                      round(self.get_ratio(), sf))

        if self.unit == "f":
            u = "frames"
        else:
            u = "seconds"

        return "{}: {}/{} {} r: {}".format(n, v, m, u, r)

    def is_on(self):
        return not self.is_off()

    def get_ratio(self):
        r = super(Timer, self).get_ratio()

        return 1 - r    # r should increment from 0 to 1 as the timer ticks

    def tick(self, dt):
        before = self.is_on()

        if self.unit == FRAMES:
            self.value -= 1
        if self.unit == SECONDS:    # 'dt' used for second based timers
            self.value -= dt

        self.on_tick()

        after = self.is_off()
        switch_off = before and after

        if switch_off:
            self.on_switch_off()

        return switch_off

    def on_tick(self):
        pass

    def on_switch_off(self):
        pass


class ChargeMeter(Meter):
    def __init__(self, name, maximum, check_func, clear_func=None):
        super(ChargeMeter, self).__init__(name, maximum)
        self.check = check_func
        self.clear_func = clear_func

    def update(self):
        if self.check():
            self.value += 1

        else:
            if self.value and self.clear_func:
                self.clear_func(self)
            self.reset()


class LerpMeter(Meter):
    def __init__(self, name, func):
        super(LerpMeter, self).__init__(name, 0, 1)
        self.func = func

    def get_func_value(self):
        return self.func(self.value)


class Clock:
    """
    A Clock object simply contains a list of timers and calls
    tick() on each once per frame (assuming it's tick() method
    is called once per frame).

    A 'queue' and 'to_remove' list are used to create a one frame
    buffer between add_timers() and remove_timer() calls. This helps
    avoid some bugs that would break the for loop in tick() if another
    part of the stack calls those methods before the tick() method has
    fully executed.

    Timers with the temp flag set are removed when their value reaches 0
    but are reset on the frame their value reaches 0 if the flag is not
    set.
    """
    def __init__(self, name, timers=None):
        self.name = name
        self.timers = []
        self.queue = []
        self.to_remove = []

        if timers:
            self.add_timers(*timers)

    def add_timers(self, *timers):
        for timer in timers:
            self.queue.append(timer)

    def remove_timer(self, name):
        to_remove = []

        for t in self.timers:
            if t not in self.to_remove:     # remove_timer() checks the queue list
                if t.name == name:          # for matches as well as the active
                    to_remove.append(t)     # timers list

        for t in self.queue:
            if t not in self.to_remove:
                if t.name == name:
                    to_remove.append(t)

        self.to_remove += to_remove

    def tick(self, dt=0):
        for t in self.queue:                # add queue timers to active timers list
            if t not in self.to_remove:     # unless that timer is set to be removed
                self.timers.append(t)

        self.queue = []
        tr = self.to_remove
        timers = [t for t in self.timers if t not in tr]

        for t in timers:
            t.tick(dt)

            if t.is_off():              # timers without the temp flag set to True
                if not t.temp:          # will be reset when their value reaches 0
                    t.reset()
                else:
                    self.to_remove.append(t)

        self.timers = [t for t in timers if t not in tr]
        self.to_remove = []


class MemberTable:
    """
    A MemberTable object contains a list of 'row' lists that represent
    a table of items. It provides methods for adding and replacing
    items in the table as well as entire rows. It also includes a
    property 'member_list' that returns a list of each item in the
    table, iterating through each item in each row one at a time.
    """
    def __init__(self, name, members=None):
        self.name = name

        if not members:
            members = [[]]
        self.members = members

    # the add_member() method serves as a subclass hook that will define
    # the 'default' adding behavior. By default, it takes a single
    # tuple: (row index, item index) as the only argument and passes it
    # to 'set_member_at_index'
    def add_member(self, item, *args):
        index = args[0]
        self.set_member_at_index(item, index)

    def set_member_at_index(self, item, index):
        row_index, cell_index = index
        m = self.members

        max_i = len(m) - 1
        if row_index > max_i:
            add_rows = row_index - max_i

            for row in range(add_rows):
                m.append([])

        row = m[row_index]
        max_j = len(row) - 1
        if cell_index > max_j:
            add_cols = cell_index - max_j
            for cell in range(add_cols):
                    row.append(None)

        self.members[row_index][cell_index] = item

    def add_row(self, row):
        if not self.members[0]:
            self.members[0] = row
        else:
            self.members.append(row)

    def remove_member(self, index):
        row_index, cell_index = index
        row = self.members[row_index]
        member = row.pop(cell_index)

        if not row:
            self.members.pop(row_index)

        return member

    def remove_row(self, index):
        return self.members.pop(index)

    @property
    def member_list(self):
        m = []
        for row in self.members:
            for item in row:
                m.append(item)

        return m

    # these methods are mainly for debugging and unit tests
    def print_members(self):
        print(self.str_members())

    def str_members(self):
        m = ""
        for row in self.members:
            r = []
            for item in row:
                r.append(str(item))

            line = "|  |".join(r)
            m += "|{}|\n".format(line)

        return m


class CacheList(list):
    def __init__(self, size):
        super(CacheList, self).__init__()
        self._size = size

    def set_size(self):
        if len(self) > self._size:
            for i in range(len(self) - 1):
                self[i] = self[i + 1]
            self.pop()

    def append(self, p_object):
        super(CacheList, self).append(p_object)
        self.set_size()

    def __iadd__(self, other):
        for item in other:
            self.append(item)

        return self

CHECK_COLLISION = "check_collision"
HANDLE_COLLISION = "handle_collision"
ITEM = "item"
ITEM_GROUP = "item_group"
GROUP = "group"
GROUP_PERM = "group_perm"


class CollisionSystem:
    # collision dict = {
    #   "check": check_function
    #   "handle": handle_collision
    #   "item": item1, item2
    #   "item_group": item, group
    #   "group": group1, group2
    #   "group_perm": group,
    # }
    def __init__(self, check, handle, perm, *args):
        if perm == ITEM:
            system = self.item_collision_system
            args += check, handle

        elif perm == ITEM_GROUP:
            system = self.item_group_collision_system
            args += check, handle

        elif perm == GROUP:
            system = self.group_collision_system
            args += check, handle

        elif perm == GROUP_PERM:
            system = self.group_perm_collision_system
            args += check, handle

        else:
            raise ValueError("bad perm arg passed to {}: \n{}".format(
                self, perm))

        self.system = system
        self.args = args

    def apply(self):
        self.system(*self.args)

    @staticmethod
    def item_collision_system(check, handle, item1, item2):
        if check(item1, item2):
            handle(item1, item2)

    @staticmethod
    def item_group_collision_system(check, handle, item, group):
        for other in group:
            if item is not other:
                CollisionSystem.item_collision_system(check, handle, item, other)

    @staticmethod
    def group_perm_collision_system(check, handle, group):
        tested = []

        for item in group:
            tested.append(item)
            check_against = [sprite for sprite in group if sprite not in tested]

            CollisionSystem.item_group_collision_system(check, handle, item, check_against)

    @staticmethod
    def group_collision_system(check, handle, group1, group2):
        for item in group1:
            CollisionSystem.item_group_collision_system(check, handle, item, group2)


