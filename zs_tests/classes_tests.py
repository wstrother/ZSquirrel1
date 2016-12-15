from random import seed, randint

from zs_src.classes import Meter, StateMeter, Timer, Clock, MemberTable
from zs_tests.zs_unit_test import ZsUnitTest


class MeterUnitTest(ZsUnitTest):
    @staticmethod
    def get_meter_str(args):
        return "Meter with value: {} \tmaximum: {} \tminimum: {}".format(*args)

    def do_tests(self, r=5):
        l = self.log
        l("!s", Meter)

        for minimum in range(r):
            for maximum in range(r):
                for value in range(r):
                    l("!r")
                    args = value, maximum, minimum
                    l(self.get_meter_str(args))

                    if maximum < minimum:
                        self.test_bad_init_args(args)
                    else:
                        if minimum <= value <= maximum:
                            self.test_good_init_args(args)
                        else:
                            self.test_adjusted_init_args(args)

                        l("")
                        self.test_dynamic_value_adjustment(args)
                l("!r")

        l("! ")

    def test_good_init_args(self, args):
        l = self.log
        l("!m", self.test_good_init_args)

        value, maximum, minimum = args
        meter = Meter("test meter", value, maximum=maximum, minimum=minimum)

        assert meter.value == value
        l("value ok")

        assert meter.minimum == minimum
        l("minimum ok")

        assert meter.maximum == maximum
        l("maximum ok")

        assert meter.get_span() == maximum - minimum
        l("get_span ok")

        error_caught = False
        try:
            assert meter.get_ratio() == (value - minimum) / (maximum - minimum)
        except ArithmeticError:
            error_caught = True
        if meter.get_span() == 0:
            assert error_caught
        l("get_ratio ok")

        assert meter.is_empty() == (value == minimum)
        l("is_empty ok")

        assert meter.is_full() == (value == maximum)
        l("is_full ok")

        assert meter.reset() == minimum
        l("reset ok")

        assert meter.refill() == maximum
        l("refill ok")

    def test_bad_init_args(self, args):
        l = self.log
        l("!m", self.test_bad_init_args)

        error_caught = False
        try:
            value, maximum, minimum = args
            Meter("", value, maximum=maximum, minimum=minimum)
        except ValueError:
            error_caught = True

        assert error_caught
        l("raise ValueError ok")

    def test_adjusted_init_args(self, args):
        l = self.log
        l("!m", self.test_adjusted_init_args)

        value, maximum, minimum = args
        meter = Meter("test meter", value, maximum=maximum, minimum=minimum)

        if value > maximum:
            assert meter.value == maximum
            l("high range value adjusted ok")

        if value < minimum:
            assert meter.value == minimum
            l("low range value adjusted ok")

    def test_dynamic_value_adjustment(self, args):
        self.log_method_header(self.test_dynamic_value_adjustment)
        l = lambda x: self.log("\t" + x)

        value, maximum, minimum = args
        meter = Meter("test meter", value, maximum=maximum, minimum=minimum)

        meter.value = minimum - 1
        assert meter.value == minimum
        l("low range adjustment ok")

        meter.value = maximum + 1
        assert meter.value == maximum
        l("high range adjustment ok")


class StateMeterUnitTest(ZsUnitTest):
    CHARS = "abcdefghijklmnopqrstuvwxyz"

    @staticmethod
    def get_meter_str(states):
        return "state meter with states: {}".format(states)

    def do_tests(self):
        l = self.log
        l("!s", StateMeter)
        chars = StateMeterUnitTest.CHARS

        for x in range(len(chars)):
            states = " ".join(chars[:x])
            l("!r")
            l(self.get_meter_str(states))

            if len(states.split()) > 1:
                self.test_good_init_args(states)
                l("")
                self.test_modulo_methods(states)

            else:
                self.test_bad_init_args(states)
        l("! ")

    def test_good_init_args(self, states):
        l = self.log
        l("!m", self.test_good_init_args)

        chars = StateMeterUnitTest.CHARS
        get_state = lambda i: chars[i]

        meter = StateMeter("test state meter", states.split())

        for x in range(len(states.split())):
            char = get_state(x)
            assert meter.state == char
            l("state {}: {} ok".format(x, char))
            meter.value += 1
        l("state property ok")

        for x in range(len(chars)):
            char = get_state(x)

            error_caught = False
            try:
                meter.set_state(char)
            except ValueError:
                error_caught = True

            if char in states.split():
                assert meter.value == x
                l("set_state to {}, value: {} ok".format(char, x))

            else:
                assert error_caught
                l("set_state to {}, value error caught ok".format(char))

    def test_bad_init_args(self, states):
        l = self.log
        l("!m", self.test_bad_init_args)

        error_caught = False
        try:
            StateMeter("test state meter", states.split())
        except ValueError:
            error_caught = True

        assert error_caught
        l("Bad states arg, (insufficient length) for states: {} caught ok".format(states))

    def test_modulo_methods(self, states):
        l = self.log
        l("!m", self.test_modulo_methods)

        meter = StateMeter("test state meter", states.split())
        maximum = len(states.split())

        for x in range(maximum * 2):
            assert meter.next() == (x + 1) % maximum
            # l(x)
        l("next ok")

        for x in range(0, maximum * 2):
            assert meter.prev() == -(x + 1) % maximum
            # l(x)
        l("prev ok")

        for x in range(-maximum * 2, maximum * 2):
            assert meter.shift(x) == x % maximum
            # l(x)
            meter.reset()
        l("shift ok")


class TimerUnitTest(ZsUnitTest):
    ALL_UNIT_STR = "sfx"
    GOOD_UNIT_STR = "sf"

    @staticmethod
    def get_timer_str(duration, unit):
        return "timer with duration: {}, unit: {}".format(duration, unit)

    def do_tests(self, r=5, dt=.25):
        l = self.log
        l("!s", Timer)
        u_all, u_good = TimerUnitTest.ALL_UNIT_STR, TimerUnitTest.GOOD_UNIT_STR

        for duration in range(-1, r):
            for unit in u_all:
                l("!r")
                l(self.get_timer_str(duration, unit))
                if duration <= 0 or unit not in u_good:
                    self.test_bad_init_args(duration, unit)

                else:
                    self.test_good_init_args(duration, unit)
                    l("")
                    self.test_tick_method(duration, unit, dt)

        l("! ")

    def test_good_init_args(self, duration, unit):
        l = self.log
        l("!m", self.test_good_init_args)

        timer = Timer("test timer", duration, unit=unit)

        assert timer.unit == unit
        l("unit ok")

        assert timer.value == duration
        l("value ok")

        assert timer.is_on()
        timer.value = 0
        assert not timer.is_on()
        l("is_on ok")

        assert timer.is_off()
        timer.value = duration
        assert not timer.is_off()
        l("is_off ok")

        timer.value = 0
        timer.reset()
        assert timer.value == duration
        l("reset ok")

    def test_bad_init_args(self, duration, unit):
        l = self.log
        l("!m", self.test_bad_init_args)

        bad_duration = duration <= 0
        bad_unit = unit not in TimerUnitTest.GOOD_UNIT_STR

        bd_caught = False
        if bad_duration:
            try:
                Timer("test timer", duration)
            except ValueError as ve:
                if ve.args[1] == 0:
                    bd_caught = True

            assert bd_caught
            l("Bad duration value error caught ok")

        bu_caught = False
        if bad_unit:
            try:
                Timer("test timer", 1, unit=unit)
            except ValueError as ve:
                if ve.args[1] == 1:
                    bu_caught = True

            assert bu_caught
            l("Bad unit value error caught ok")

    def test_tick_method(self, duration, unit, dt):
        l = self.log
        l("!m", self.test_tick_method)

        timer = Timer("test timer", duration, unit=unit)
        while timer.is_on():
            if timer.unit == "f":
                dt = 1

            if timer.value - dt > 0:
                assert not timer.tick(dt)
            else:
                assert timer.tick(dt)
            l("dt: {}, value: {:.{}f} tick ok".format(dt, timer.value, 4))

            assert timer.get_ratio() == 1 - (timer.value / duration)
            l("get ratio {:.{}f} ok".format(timer.get_ratio(), 4))


class ClockUnitTest(ZsUnitTest):
    class MockTimer:
        def __init__(self, name, duration, temp):
            self.name = name
            self.temp = temp
            self.duration = duration
            self.value = duration

        def is_off(self):
            return self.value == 0

        def tick(self, dt):
            self.value -= dt
            if self.value < 0:
                self.value = 0

        def reset(self):
            self.value = self.duration

        def __str__(self):
            n, v, d, t = self.name, self.value, self.duration, self.temp
            return "{} value: {:.{}f}, duration: {}, temp: {}".format(n, v, 2, d, t)

    @staticmethod
    def get_timer_name(s):
        seed(s)
        chars = "abcde"
        r = randint(0, len(chars) - 1)
        return "Test timer {}".format(chars[r])

    def do_tests(self, r=5, dt=.25, s=1):
        l = self.log
        l("!s", Timer)

        mt = ClockUnitTest.MockTimer
        tn = self.get_timer_name
        get_timers = lambda d, t: [mt(tn(x * d * s + int(t)), x, t) for x in range(1, d)]

        for duration in range(r):
            l("!r")
            timer_list = get_timers(duration, False) + get_timers(duration, True)
            for timer in timer_list:
                l("{}".format(timer))

            l("")
            self.test_init_args(timer_list)
            if timer_list:
                l("")
                self.test_tick_method(timer_list, r * 2, dt)
                l("")
                self.test_remove_timers(timer_list)

        l("! ")

    def test_init_args(self, timer_list):
        l = self.log
        l("!m", self.test_init_args)

        if timer_list:
            clock = Clock("test clock", timers=timer_list)
        else:
            clock = Clock("test clock")
        assert clock.queue == timer_list
        l("add_timers ok")

    def test_tick_method(self, timer_list, r, dt):
        l = self.log
        l("!m", self.test_tick_method)

        clock = Clock("test clock", timers=timer_list)

        clock.tick(0)
        assert clock.timers == timer_list and clock.queue == []
        l("queue transferred to timers ok")

        for x in range(r):
            clock.tick(dt)

            for timer in clock.timers:
                l("{}".format(timer))

            for timer in timer_list:
                assert (timer.is_off()) == (timer not in clock.timers)
            l("timers updated ok")

    def test_remove_timers(self, timer_list):
        l = self.log
        l("!m", self.test_remove_timers)

        clock = Clock("test clock", timers=timer_list)
        name_list = list(set([timer.name for timer in timer_list]))

        for name in name_list:
            clock.remove_timer(name)
        assert set(clock.to_remove) == set(timer_list)
        l("remove_timers ok")


class MemberTableUnitTest(ZsUnitTest):
    @staticmethod
    def get_member_str(members):
        m = ""
        for row in members:
            r = []
            for item in row:
                r.append("{:4}".format(str(item)))

            line = "|  |".join(r)
            m += "|{}|\n".format(line)

        return m

    def do_tests(self, r=5):
        l = self.log
        l("!s", MemberTable)
        seed(r)

        for i in range(r ** 2):
            m = []
            for x in range(2, r + 2):
                row = [0] * randint(1, x)
                m.append(row)

            l("!r")
            l(self.get_member_str(m))
            self.test_init_args(m)

        l("! ")

    def test_init_args(self, members):
        l = self.log
        l("!m", self.test_init_args)

        table = MemberTable("test member table", members)
        assert table.members == members
        l("members ok")

        for x in range(0, len(members)):
            member = randint(1, x + 2)

            table.add_member(member, (x, x))
            assert table.members[x][x] == member
            l("add member {} at row: {}, cell: {} ok".format(member, x, x))
        l(self.get_member_str(table.members))


TESTS = (
    MeterUnitTest, StateMeterUnitTest,
    TimerUnitTest, ClockUnitTest,
    MemberTableUnitTest
)


def do_tests():
    for t in TESTS:
        t().do_tests()
