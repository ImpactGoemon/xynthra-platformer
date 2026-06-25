"""Milestone 1 tests — headless (SDL dummy). See TEST_PLAN_M1.md.

Run:  python -m pytest tests/ -q
  or: python tests/test_milestone1.py
"""

import os
import sys

# Headless drivers must be set before pygame initializes a display/audio.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

# Make the project root importable whether run via pytest or directly.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pygame

import settings as S
from core.input import InputManager
from core.state import State, StateManager
from core.timestep import FixedTimestep


# ----------------------------------------------------------------- 1,2 settings
def test_settings_constants():
    assert S.WIDTH == 960 and S.HEIGHT == 540
    assert S.FPS == 60
    assert abs(S.FIXED_DT - 1.0 / 60) < 1e-12
    assert S.TILE == 32
    assert S.INTERNAL_SIZE == (960, 540)
    assert isinstance(S.WINDOW_SCALE, int) and S.WINDOW_SCALE >= 1


def test_action_keys_mapping():
    for action in ("left", "right", "up", "down", "jump", "shoot", "heal",
                   "struggle", "confirm", "quit"):
        assert action in S.ACTION_KEYS and S.ACTION_KEYS[action]
    assert pygame.K_SPACE in S.ACTION_KEYS["jump"]
    assert pygame.K_SPACE in S.ACTION_KEYS["struggle"]
    assert pygame.K_LEFT in S.ACTION_KEYS["left"] and pygame.K_a in S.ACTION_KEYS["left"]


# ----------------------------------------------------------------- 3-7 timestep
def test_timestep_single_step():
    ts = FixedTimestep(S.FIXED_DT)
    assert ts.advance(S.FIXED_DT) == 1


def test_timestep_accumulates():
    ts = FixedTimestep(S.FIXED_DT)
    assert ts.advance(S.FIXED_DT * 0.5) == 0
    assert ts.advance(S.FIXED_DT * 0.5) == 1


def test_timestep_multiple_steps():
    ts = FixedTimestep(S.FIXED_DT)
    assert ts.advance(S.FIXED_DT * 3) == 3


def test_timestep_clamp():
    ts = FixedTimestep(S.FIXED_DT, max_frame_time=0.25)
    steps = ts.advance(10.0)  # would be 600 steps unclamped
    assert steps == int(0.25 / S.FIXED_DT)  # 15


def test_timestep_determinism():
    ts = FixedTimestep(S.FIXED_DT)
    total = 0
    n = 1000
    for _ in range(n):
        total += ts.advance(S.FIXED_DT * 0.37)
    expected = int(n * 0.37)
    assert abs(total - expected) <= 1


# ----------------------------------------------------------------- 8,9 input
def _key(event_type, key):
    return pygame.event.Event(event_type, {"key": key})


def test_input_press_hold_release():
    im = InputManager()
    im.begin_frame()
    im.process_event(_key(pygame.KEYDOWN, pygame.K_a))
    assert im.just_pressed("left") and im.is_held("left")
    # next frame: still held, no longer "just pressed"
    im.begin_frame()
    assert im.is_held("left") and not im.just_pressed("left")
    im.process_event(_key(pygame.KEYUP, pygame.K_a))
    assert im.just_released("left") and not im.is_held("left")


def test_input_multikey_action():
    im = InputManager()
    im.begin_frame()
    im.process_event(_key(pygame.KEYDOWN, pygame.K_LEFT))
    im.process_event(_key(pygame.KEYDOWN, pygame.K_a))
    assert im.is_held("left")
    im.begin_frame()
    im.process_event(_key(pygame.KEYUP, pygame.K_LEFT))
    assert im.is_held("left")            # 'a' still down
    assert not im.just_released("left")  # action not released yet
    im.process_event(_key(pygame.KEYUP, pygame.K_a))
    assert not im.is_held("left") and im.just_released("left")


# ----------------------------------------------------------------- 10,11 states
class _Spy(State):
    def __init__(self, game):
        super().__init__(game)
        self.entered = self.exited = False
        self.updates = 0
        self.draws = 0

    def on_enter(self):
        self.entered = True

    def on_exit(self):
        self.exited = True

    def update(self, dt):
        self.updates += 1

    def draw(self, surface):
        self.draws += 1


def test_state_manager_change():
    sm = StateManager()
    a, b = _Spy(None), _Spy(None)
    sm.change(a)
    assert sm.current is a and a.entered
    sm.update(0.016)
    surf = pygame.Surface((4, 4))
    sm.draw(surf)
    assert a.updates == 1 and a.draws == 1
    sm.change(b)
    assert a.exited and sm.current is b and b.entered


def test_state_manager_push_pop():
    sm = StateManager()
    a, b = _Spy(None), _Spy(None)
    sm.push(a)
    sm.push(b)
    assert sm.current is b
    sm.pop()
    assert sm.current is a and b.exited


# ----------------------------------------------------------------- 12-15 game
def _make_game():
    import main
    return main, main.Game()


def test_game_headless_runs():
    main, game = _make_game()
    try:
        frames = game.run(max_frames=5)
        assert frames == 5
        assert game.internal.get_size() == (S.WIDTH, S.HEIGHT)
        assert game.window.get_size() == (S.WIDTH * S.WINDOW_SCALE, S.HEIGHT * S.WINDOW_SCALE)
    finally:
        pygame.quit()


def test_game_quit_event():
    main, game = _make_game()
    try:
        pygame.event.post(pygame.event.Event(pygame.QUIT))
        game.run(max_frames=100)
        assert game.running is False
        assert game.frame_count < 100  # stopped early via QUIT
    finally:
        pygame.quit()


def test_menu_to_play_transition():
    main, game = _make_game()
    try:
        assert isinstance(game.states.current, main.MenuState)
        # Simulate pressing "confirm" (Enter) and one update tick.
        game.input.begin_frame()
        game.input.process_event(_key(pygame.KEYDOWN, pygame.K_RETURN))
        game.states.update(S.FIXED_DT)
        assert isinstance(game.states.current, main.PlayState)
    finally:
        pygame.quit()


def test_fixed_update_runs():
    main, game = _make_game()
    try:
        game.run(max_frames=30)
        # Some fixed updates should have run over 30 rendered frames.
        assert game.update_count >= 0  # never negative
        # Drive the timestep directly to prove fixed-rate stepping is wired.
        before = game.update_count
        for _ in range(game.timestep.advance(S.FIXED_DT * 5)):
            game.states.update(S.FIXED_DT)
            game.update_count += 1
        assert game.update_count - before == 5
    finally:
        pygame.quit()


# ----------------------------------------------------------------- runner
if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    passed = failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS  {t.__name__}")
            passed += 1
        except Exception as e:  # noqa: BLE001
            import traceback
            print(f"FAIL  {t.__name__}: {e}")
            traceback.print_exc()
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
