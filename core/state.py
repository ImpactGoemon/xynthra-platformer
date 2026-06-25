"""Scene/state manager.

A simple stack of states (Menu / Play / GameOver / ...). The manager dispatches
events, fixed updates, and draws to the active (top) state. Concrete states live
in ``main.py`` for Milestone 1.
"""


class State:
    def __init__(self, game):
        self.game = game

    def on_enter(self):
        pass

    def on_exit(self):
        pass

    def handle_event(self, event):
        pass

    def update(self, dt):
        pass

    def draw(self, surface):
        pass


class StateManager:
    def __init__(self):
        self._stack = []

    @property
    def current(self):
        return self._stack[-1] if self._stack else None

    def change(self, state):
        """Replace the whole stack with a single state."""
        while self._stack:
            self._stack.pop().on_exit()
        self._stack.append(state)
        state.on_enter()

    def push(self, state):
        self._stack.append(state)
        state.on_enter()

    def pop(self):
        if self._stack:
            top = self._stack.pop()
            top.on_exit()
            return top
        return None

    def handle_event(self, event):
        if self.current:
            self.current.handle_event(event)

    def update(self, dt):
        if self.current:
            self.current.update(dt)

    def draw(self, surface):
        if self.current:
            self.current.draw(surface)
