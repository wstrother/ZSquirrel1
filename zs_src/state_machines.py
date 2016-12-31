from collections import OrderedDict
from os.path import join

from zs_constants.paths import STATE_MACHINES
from zs_src.events import ZsEventInterface, Event


class ZsState:
    def __init__(self, name, index):
        self.name = name
        self.index = index
        self.transitions = {}

    def add_transition(self, event):
        t = Event.interpret(event)
        self.transitions[t.name] = t


class ZsStateMachine(ZsEventInterface):
    def __init__(self, name):
        super(ZsStateMachine, self).__init__(name)
        self.name = name
        self.states = []
        self.index = 0
        self.buffer_state = None

    def add_state(self, state):
        self.states.append(state)

    def get_state(self):
        return self.states[self.index]

    def set_state(self, index):
        self.index = index

        print(self.get_state().name)

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
                self.buffer_state = None
                self.set_state(e.to_index)
                print("\t buffered")
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


class AnimationMachine(ZsStateMachine):
    def __init__(self, file_name):
        super(AnimationMachine, self).__init__("animation machine")

        self.sprite = None
        self.buffer_state = None

        states = OrderedDict()
        current = ""
        path = join(STATE_MACHINES, file_name)
        file = open(path, "r")

        for line in file:
            if line[-1] == "\n":
                line = line[:-1]

            if not line[0] == "\t":
                current = line
                states[line] = []

            else:
                states[current].append(line[1:])
        file.close()

        self.set_up_states(states)

    def set_state(self, index):
        super(AnimationMachine, self).set_state(index)

        self.sprite.graphics.reset_animations()

    def set_up_states(self, state_dict):
        def get_index(key):
            return list(state_dict.keys()).index(key)

        for name in state_dict:
            transitions = state_dict[name]
            index = get_index(name)
            state = ZsState(name, index)

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
            self.add_state(state)
