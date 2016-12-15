from zs_constants.zs import REPR_SIG_FIGS


class Meter:
    """
    Meter objects have a minimum, value, and maximum attribute (int or float)
    The normalize method is called when one of these attributes is assigned to
    ensuring that value stays in the proper range.
    """
    def __init__(self, name, value, maximum=None, minimum=0):
        self.name = name
        self._value = value
        self._minimum = minimum
        if maximum is None:
            self._maximum = value
        else:
            self._maximum = maximum

        if self._maximum < minimum:
            raise ValueError("bad maximum / minimum values passed to meter object")
        self.normalize()    # by default, a value outside the meter's range gets handled
        #   to change this behavior, add "assert" to this statement and all Meter based
        #   classes will throw an exception if initial value is out of range. Unit testing
        #   should be adjusted accordingly.

    def __repr__(self):
        sf = REPR_SIG_FIGS
        n, v, m = self.name, round(self.value, sf), round(self._maximum, sf)

        return "{}: {}/{}".format(n, v, m)

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

    @property
    def maximum(self):
        return self._maximum

    # methods
    def normalize(self):
        in_bounds = True

        if self._value > self.maximum:
            self._value = self.maximum
            in_bounds = False

        if self._value < self.minimum:
            self._value = self.minimum
            in_bounds = False

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

        return self.value

    def prev(self):
        if self.is_empty():
            self.refill()
        else:
            self.value -= 1

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


class StateMeter(Meter):
    """
    StateMeter creates an enumerable object out of an iterable object containing strings.
    The states are passed as a string with spaces separating state names.
    The state attribute and value attribute can both be assigned to.
    """
    def __init__(self, name, states):
        maximum = len(states) - 1
        if maximum < 1:
            raise ValueError("Empty states list passed")
        super(StateMeter, self).__init__(name, 0, maximum=maximum)
        self._states = states

    def __repr__(self):
        n, v, m, s = self.name, self.value, self.maximum, self.state

        return "{}: {}/{} '{}'".format(n, v, m, s)

    @property
    def state(self):
        i = round(self.value)
        try:
            return self._states[i]
        except IndexError:
            raise IndexError("State meter value outside state list range")

    @property
    def states(self):
        return self._states

    def set_state(self, state):
        if state in self._states:
            i = self._states.index(state)
            self.value = i
        else:
            raise ValueError("improper state passed")


class Timer(Meter):
    """
    Timer objects have a duration and a unit of either 's' for seconds or 'f'
    for frames. Frame durations should only be integer amounts. The temp flag
    determines if a Clock object will erase the timer after it goes off, and
    loop flag determines if the Clock will reset it automatically.
    """
    def __init__(self, name, duration, unit="f", temp=True):
        if duration <= 0:
            raise ValueError("bad duration", 0)

        self.is_off = self.is_empty
        self.reset = self.refill
        value = duration

        if unit not in "fs" or len(unit) > 1:
            raise ValueError("bad string passed as 'unit' arg", 1)

        super(Timer, self).__init__(name, value, maximum=duration)
        self.temp = temp
        self.unit = unit

    def __repr__(self):
        s = super(Timer, self).__repr__()

        return s + " " + self.unit

    def is_on(self):
        return not self.is_off()

    def get_ratio(self):
        r = super(Timer, self).get_ratio()

        return 1 - r        # r should always go from 0 to 1

    def tick(self, dt):
        before = self.is_on()

        if self.unit == "f":
            self.value -= 1
        if self.unit == "s":    # 'dt' used for second based timers
            self.value -= dt

        # print("Ticking " + str(self))
        self.on_tick()

        after = self.is_off()
        switch_off = before and after

        if switch_off:
            # print("Switching off " + str(self))
            self.on_switch_off()

        return switch_off

    def on_tick(self):
        pass

    def on_switch_off(self):
        pass


class Clock:
    """
    Clock objects contain a list of Timers and tick() them all at once.
    A queue list prevents any new timers from ticking in the same frame
    that they are added to the clock Object. (e.g. chained actions)
    Timers can be removed by name, and timers with the temp flag set to
    True always get removed when they go off. Timers with the loop flag
    set to True will get reset automatically when they go off.
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
            # print(("adding", self.queue))

    def remove_timer(self, name):
        to_remove = []
        for t in self.timers:
            match = t.name == name
            if not match:
                to_remove.append(t)

        for t in self.queue:
            match = t.name == name
            if not match:
                to_remove.append(t)

        self.to_remove += to_remove

    def tick(self, dt):
        for timer in self.queue:            # add queued timers and
            self.timers.append(timer)       # reset the queue list
        self.queue = []

        # if len(self.timers) > 0:
        #     print((self.name, self.timers))

        for i in range(len(self.timers)):   # tick all the timers and
            t = self.timers[i]              # check the temp and loop
            t.tick(dt)                      # flags

            if t.is_off():
                if not t.temp:
                    t.reset()
                else:
                    self.to_remove.append(t)

        self.timers = [t for t in self.timers if t not in self.to_remove]
        self.to_remove = []


class MemberTable:
    """
    A MemberTable object contains a list of lists that represent a table of
    items. It provides methods for adding and replacing items in the table
    as well as handling size and positioning based on the items in the table.
    """
    def __init__(self, name, members=None):
        self.name = name

        if not members:
            members = [[]]
        self.members = members

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


