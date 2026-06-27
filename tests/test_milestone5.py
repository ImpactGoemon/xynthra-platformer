"""Milestone 5 tests — 3-level charge shot + HUD charge meter. Headless."""

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pygame

import settings as S
from entities.player import Player
from world.tilemap import Tilemap

DT = S.FIXED_DT


class FakeInput:
    def __init__(self, held=(), pressed=(), released=()):
        self.held = set(held)
        self.pressed = set(pressed)
        self.released = set(released)

    def is_held(self, a):
        return a in self.held

    def just_pressed(self, a):
        return a in self.pressed

    def just_released(self, a):
        return a in self.released


GROUND_MAP = [
    "..........",
    "..........",
    "..........",
    "..........",
    "..........",
    "..........",
    "..........",
    "..........",
    "..........",
    "##########",
]


def _map(rows):
    return Tilemap(rows)


def _grounded_player():
    tm = _map(GROUND_MAP)
    p = Player(2 * S.TILE, 0)
    for _ in range(120):
        p.update(DT, tm, FakeInput())
    assert p.on_ground
    return p, tm


def _charge_fire(p, tm, hold_frames, extra=()):
    """Tap -> hold -> release. Returns (level1_shots, release_shots)."""
    held = set(extra) | {"shoot"}
    p.update(DT, tm, FakeInput(held=held, pressed={"shoot"}))
    l1 = list(p.fired)
    for _ in range(hold_frames):
        p.update(DT, tm, FakeInput(held=held))
    p.update(DT, tm, FakeInput(held=set(extra), released={"shoot"}))
    return l1, list(p.fired)


# ----------------------------------------------------------------- constants
def test_charge_constants():
    assert S.CHARGE_L2_TIME == 0.6 and S.CHARGE_L3_TIME == 1.4
    assert S.CHARGE_DAMAGE == {1: 1, 2: 2, 3: 3}
    assert S.CHARGE_SIZE[1] < S.CHARGE_SIZE[2] < S.CHARGE_SIZE[3]


def test_charge_level_helper():
    assert Player._charge_level(0.0) == 1
    assert Player._charge_level(0.59) == 1
    assert Player._charge_level(0.6) == 2
    assert Player._charge_level(1.39) == 2
    assert Player._charge_level(1.4) == 3


# ----------------------------------------------------------------- tap = level 1
def test_tap_fires_level1():
    p, tm = _grounded_player()
    l1, release = _charge_fire(p, tm, hold_frames=2)   # ~0.03s hold
    assert len(l1) == 1
    assert l1[0].damage == 1 and l1[0].size == S.CHARGE_SIZE[1]
    assert len(release) == 0          # released below level 2 -> no charged shot


def test_short_hold_no_charged_shot():
    p, tm = _grounded_player()
    _, release = _charge_fire(p, tm, hold_frames=18)   # ~0.30s < 0.6s
    assert len(release) == 0


# ----------------------------------------------------------------- level 2 / 3
def test_hold_release_level2():
    p, tm = _grounded_player()
    _, release = _charge_fire(p, tm, hold_frames=42)   # ~0.70s -> level 2
    assert len(release) == 1
    assert release[0].damage == 2 and release[0].size == S.CHARGE_SIZE[2]


def test_hold_release_level3():
    p, tm = _grounded_player()
    _, release = _charge_fire(p, tm, hold_frames=92)   # ~1.53s -> level 3
    assert len(release) == 1
    assert release[0].damage == 3 and release[0].size == S.CHARGE_SIZE[3]


def test_charged_hitbox_grows_with_level():
    p, tm = _grounded_player()
    _, r2 = _charge_fire(p, tm, hold_frames=42)
    # cooldown irrelevant for charged release; new player for a clean L3
    p2, tm2 = _grounded_player()
    _, r3 = _charge_fire(p2, tm2, hold_frames=92)
    assert r2[0].size < r3[0].size


# ----------------------------------------------------------------- charge state
def test_charging_state_and_level_property():
    p, tm = _grounded_player()
    p.update(DT, tm, FakeInput(held={"shoot"}, pressed={"shoot"}))
    for _ in range(45):                                # hold ~0.75s
        p.update(DT, tm, FakeInput(held={"shoot"}))
    assert p.charging is True
    assert p.charge_time >= S.CHARGE_L2_TIME
    assert p.charge_level == 2
    # release clears the charge
    p.update(DT, tm, FakeInput(released={"shoot"}))
    assert p.charging is False and p.charge_time == 0.0


# ----------------------------------------------------------------- direction
def test_charged_shot_follows_aim_up():
    p, tm = _grounded_player()
    _, release = _charge_fire(p, tm, hold_frames=42, extra={"up"})
    assert len(release) == 1
    assert release[0].vy < 0 and abs(release[0].vx) < 1e-6


# ----------------------------------------------------------------- HUD
def test_charge_meter_draws_without_error():
    from ui.hud import draw_charge_meter
    surf = pygame.Surface((S.WIDTH, S.HEIGHT))
    p, tm = _grounded_player()
    # not charging -> no-op (and definitely no crash)
    draw_charge_meter(surf, p)
    p.update(DT, tm, FakeInput(held={"shoot"}, pressed={"shoot"}))
    for _ in range(20):
        p.update(DT, tm, FakeInput(held={"shoot"}))
    assert p.charging and p.charge_time > 0
    draw_charge_meter(surf, p)        # should render without raising


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
