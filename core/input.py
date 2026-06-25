"""Input abstraction: physical keys -> abstract actions.

Gameplay code asks about actions ("jump", "left", "shoot"), never raw keys, so
rebinding is just editing ``settings.ACTION_KEYS``. State is driven purely by
events, so it is fully testable headlessly (no ``pygame.key.get_pressed``).
"""

import pygame

import settings


class InputManager:
    def __init__(self, action_keys=None):
        self.action_keys = action_keys if action_keys is not None else settings.ACTION_KEYS
        # reverse lookup: physical key -> [actions]
        self._key_to_actions = {}
        for action, keys in self.action_keys.items():
            for key in keys:
                self._key_to_actions.setdefault(key, []).append(action)
        self._keys_down = set()          # physical keys currently held
        self._actions_pressed = set()    # actions that went down this frame
        self._actions_released = set()   # actions that went up this frame

    def begin_frame(self):
        """Call once per frame before processing events."""
        self._actions_pressed.clear()
        self._actions_released.clear()

    def process_event(self, event):
        if event.type == pygame.KEYDOWN:
            actions = self._key_to_actions.get(event.key, [])
            before = {a: self.is_held(a) for a in actions}
            self._keys_down.add(event.key)
            for a in actions:
                if not before[a] and self.is_held(a):
                    self._actions_pressed.add(a)
        elif event.type == pygame.KEYUP:
            actions = self._key_to_actions.get(event.key, [])
            before = {a: self.is_held(a) for a in actions}
            self._keys_down.discard(event.key)
            for a in actions:
                if before[a] and not self.is_held(a):
                    self._actions_released.add(a)

    def is_held(self, action):
        return any(k in self._keys_down for k in self.action_keys.get(action, ()))

    def just_pressed(self, action):
        return action in self._actions_pressed

    def just_released(self, action):
        return action in self._actions_released

    def reset(self):
        self._keys_down.clear()
        self._actions_pressed.clear()
        self._actions_released.clear()
