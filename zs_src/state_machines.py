from collections import OrderedDict
from os.path import join

from zs_constants.paths import STATE_MACHINES
from zs_src.events import EventInterface, Event


class State:
    def __init__(self, name, index):
        self.name = name
        self.index = index
        self.transitions = OrderedDict()

    def add_transition(self, event):
        t = Event.interpret(event)
        self.transitions[t.name] = t


class StateMachine(EventInterface):
    def __init__(self, name, file_name=None):
        super(StateMachine, self).__init__(name)
        self.name = name
        self.states = []
        self.index = 0
        self.buffer_state = None

        if file_name:
            TransitionManager(
                file_name
            ).set_up_state_machine(self)

    def add_state(self, state):
        self.states.append(state)

    def get_state(self):
        return self.states[self.index]

    def set_state(self, index):
        self.buffer_state = None
        self.index = index

    def get_transitions(self):
        return self.get_state().transitions

    def check_transition(self, event):
        check = self.event_handler.event_methods[event.name]()

        if event.get("not"):
            return not check
        else:
            return check

    def update(self):
        if self.buffer_state is not None:
            e = Event("auto", to_index=self.buffer_state)
            if self.check_transition(e):
                self.set_state(e.to_index)
                return

        transitions = self.get_transitions()

        for name in transitions:
            t = transitions[name]
            to_index = t.to_index
            check = self.check_transition(t)

            if check:
                buffer = t.get("buffer")

                if not buffer:
                    self.set_state(to_index)

                else:
                    self.buffer_state = to_index


class AnimationMachine(StateMachine):
    def __init__(self, file_name, sprite):
        super(AnimationMachine, self).__init__(
            sprite.name + " machine", file_name)

        self.sprite = sprite
        self.buffer_state = None

    @property
    def controller(self):
        if self.sprite:
            return self.sprite.controller

    def set_state(self, index):
        self.sprite.state_frame = 0
        self.sprite.graphics.reset_animations()

        super(AnimationMachine, self).set_state(index)


class TransitionManager:
    def __init__(self, file_name):
        states = OrderedDict()
        current = ""
        path = join(STATE_MACHINES, file_name)
        file = open(path, "r")

        for line in file:
            if line[-1] == "\n":
                line = line[:-1]

            # State name
            if not line[0] == "\t":
                current = line
                states[line] = []

            #       transitions
            else:
                states[current].append(line[1:])
        file.close()

        self.state_dict = states

    def set_up_state_machine(self, state_machine):
        states = self.state_dict

        def get_index(key):
            return list(states.keys()).index(key)

        for name in states:
            transitions = states[name]
            index = get_index(name)
            state = State(name, index)

            for t in transitions:
                t_name, t_args = t.split(": ")
                n = t_name[0:4] == "not_"

                if n:
                    t_name = t_name[4:]

                t_args = t_args.split(", ")
                to_index = get_index(t_args[0])

                buffer = "buffer" in t_args

                event = (t_name,
                         ("buffer", buffer),
                         ("to_index", to_index),
                         ("not", n))

                state.add_transition(event)

            state_machine.add_state(state)


class SpriteDemoMachine(AnimationMachine):
    def __init__(self, sprite):
        super(SpriteDemoMachine, self).__init__("demo_sprite.txt", sprite)

        self.add_event_methods(
            "press_direction", "press_jump", "press_down",
            "neutral_dpad", "v_acceleration_0", "ground_collision",
            "auto", "tap_direction", "press_opposite_direction",
            "run_momentum", "falling"
        )

    @property
    def dpad(self):
        if self.controller:
            return self.controller.devices["dpad"]

    def on_tap_direction(self):
        if self.controller:
            check = self.controller.check_command
            tap = check("double tap left") or check("double tap right")

            a, b = self.controller.devices["a"], self.controller.devices["b"]
            if a.held > 20 and b.held > 20:
                tap = True

            return tap

    def on_press_direction(self):
        if self.controller:
            x, y = self.dpad.get_direction()
            return x != 0

    def on_press_jump(self):
        if self.controller:
            jump = bool(self.controller.devices["b"].held == 1)

            return jump

    def on_press_down(self):
        if self.controller:
            down = self.dpad.get_direction()[1] == 1
            return down

    def on_release_down(self):
        if self.controller:
            dpad = self.dpad
            down = dpad.get_direction()[1] > 0

            return not down

    def on_neutral_dpad(self):
        if self.controller:
            neutral = self.dpad.get_direction() == (0, 0)
            return neutral

    def on_v_acceleration_0(self):
        vy = self.sprite.velocity.j_hat
        ay = self.sprite.acceleration.j_hat

        apex = vy >= 0 and ay >= 0

        return apex

    def on_ground_collision(self):
        return self.sprite.is_grounded()

    def on_run_momentum(self):
        v = self.sprite.velocity
        if abs(v.i_hat) > 14 and self.controller:
            dpad = self.sprite.controller.devices["dpad"]
            x = dpad.get_direction()[0]
            dx = self.sprite.direction[0]
            vx = v.i_hat
            right = vx > 0 and x > 0 and dx > 0
            left = vx < 0 and x < 0 and dx < 0

            return left or right

    def on_press_opposite_direction(self):
        if self.controller:
            dpad = self.dpad
            direction = self.sprite.direction

            opposite = direction[0] * dpad.get_value()[0] == -1
            return opposite

    def on_falling(self):
        return not self.sprite.is_grounded()

    def on_auto(self):
        if self.sprite.graphics:
            return self.sprite.animation_completed()
