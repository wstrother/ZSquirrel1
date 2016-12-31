from zs_src.events import ZsEventInterface


class ContextManager(ZsEventInterface):
    def __init__(self, environment):
        super(ContextManager, self).__init__("context manager")
        self.add_event_methods("auto")

        self._do_transition = False
        self.environment = environment
        self.sprite_dict = self.set_up_sprite_dict()

    def check_state_transition(self, event):
        self.handle_event(event)

        b = self._do_transition
        if b:
            self._do_transition = False

        return b

    def do_transition(self):
        self._do_transition = True

    @property
    def controllers(self):
        return self.environment.controllers

    @property
    def controller(self):
        return self.controllers[0]

    def get_sprite(self, key):
        return self.sprite_dict[key]

    def set_up_sprite_dict(self):
        return {}

    def on_auto(self):
        machine = self.event.state_machine
        to_index = self.event.to_index

        completed = machine.sprite.graphics.animation_completed()
        if completed:
            machine.set_state(to_index)
