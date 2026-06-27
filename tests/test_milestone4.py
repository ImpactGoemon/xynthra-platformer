"""Milestone 4 tests — shooting: directional fire, cooldown, crouch/down rules,
projectile travel + despawn, shoot pose. Headless (SDL dummy)."""

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pygame

import settings as S
from core.physics import AABB
from entities.player import Player
from entities.projectile import Projectile
from world.tilemap import Tilemap

DT = S.FIXED_DT


class FakeInput:
    def __init__(self, held=(), pressed=()):
        self.held = set(held)
        self.pressed = set(pressed)

    def is_held(self, a):
        return a in self.held

    def just_pressed(self, a):
        return a in self.pressed

    def just_released(self, a):
        return False


# floor at ty=9 (top=288); spawn high so she lands on it
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


def _settle(p, tm, n, inp=None):
    for _ in range(n):
        p.update(DT, tm, inp or FakeInput())


def _grounded_player():
    tm = _map(GROUND_MAP)
    p = Player(2 * S.TILE, 0)
    _settle(p, tm, 120)
    assert p.on_ground
    return p, tm


# ----------------------------------------------------------------- settings
def test_projectile_constants():
    assert S.PROJECTILE_SPEED > 0
    assert S.FIRE_COOLDOWN > 0
    assert S.PROJECTILE_DAMAGE >= 1
    assert S.PROJECTILE_SIZE >= 1


# ----------------------------------------------------------------- horizontal fire
def test_fire_horizontal_right():
    p, tm = _grounded_player()
    p.facing = "right"
    p.update(DT, tm, FakeInput(held={"right"}, pressed={"shoot"}))
    assert len(p.fired) == 1
    shot = p.fired[0]
    assert shot.vx > 0 and abs(shot.vy) < 1e-6
    assert abs(abs(shot.vx) - S.PROJECTILE_SPEED) < 1e-6


def test_fire_horizontal_left():
    p, tm = _grounded_player()
    p.facing = "left"
    p.update(DT, tm, FakeInput(held={"left"}, pressed={"shoot"}))
    assert len(p.fired) == 1
    assert p.fired[0].vx < 0 and abs(p.fired[0].vy) < 1e-6


# ----------------------------------------------------------------- cooldown
def test_fire_cooldown_blocks_second_shot():
    p, tm = _grounded_player()
    p.update(DT, tm, FakeInput(pressed={"shoot"}))
    assert len(p.fired) == 1
    # immediately press again within the cooldown window -> no new shot
    p.update(DT, tm, FakeInput(pressed={"shoot"}))
    assert len(p.fired) == 0


def test_fire_again_after_cooldown():
    p, tm = _grounded_player()
    p.update(DT, tm, FakeInput(pressed={"shoot"}))
    assert len(p.fired) == 1
    # wait out the cooldown with no press
    steps = int(S.FIRE_COOLDOWN / DT) + 2
    _settle(p, tm, steps)
    p.update(DT, tm, FakeInput(pressed={"shoot"}))
    assert len(p.fired) == 1


# ----------------------------------------------------------------- up shot
def test_up_shot():
    p, tm = _grounded_player()
    p.update(DT, tm, FakeInput(held={"up"}, pressed={"shoot"}))
    assert len(p.fired) == 1
    assert p.fired[0].vy < 0 and abs(p.fired[0].vx) < 1e-6


# ----------------------------------------------------------------- down shot rules
def test_down_shot_airborne_only():
    tm = _map(GROUND_MAP)
    p = Player(2 * S.TILE, 0)        # starts in the air, falling
    assert not p.on_ground
    p.update(DT, tm, FakeInput(held={"down"}, pressed={"shoot"}))
    assert len(p.fired) == 1
    assert p.fired[0].vy > 0 and abs(p.fired[0].vx) < 1e-6


def test_down_on_ground_is_low_horizontal():
    p, tm = _grounded_player()
    p.facing = "right"
    # holding down on the ground -> crouch low horizontal shot, not a down shot
    p.update(DT, tm, FakeInput(held={"down"}, pressed={"shoot"}))
    assert len(p.fired) == 1
    shot = p.fired[0]
    assert abs(shot.vy) < 1e-6 and shot.vx > 0


def test_crouch_shot_is_lower_than_standing():
    p, tm = _grounded_player()
    p.facing = "right"
    p.update(DT, tm, FakeInput(held={"right"}, pressed={"shoot"}))
    stand_y = p.fired[0].centery
    # wait out cooldown, then crouch and fire
    _settle(p, tm, int(S.FIRE_COOLDOWN / DT) + 2, FakeInput(held={"down"}))
    p.update(DT, tm, FakeInput(held={"down", "right"}, pressed={"shoot"}))
    assert p.crouching
    crouch_y = p.fired[0].centery
    assert crouch_y > stand_y           # +Y is down, so lower on screen


# ----------------------------------------------------------------- projectile travel
def test_projectile_moves():
    tm = _map(GROUND_MAP)
    shot = Projectile(10, 50, 1, 0)
    x0 = shot.centerx
    shot.update(DT, tm)
    assert shot.centerx > x0
    assert shot.alive


def test_projectile_despawns_on_solid():
    tm = _map(GROUND_MAP)
    # aim a shot straight into the floor tile (top=288)
    shot = Projectile(2 * S.TILE, 287, 0, 1)
    for _ in range(10):
        shot.update(DT, tm)
        if not shot.alive:
            break
    assert not shot.alive


def test_projectile_despawns_out_of_bounds():
    tm = _map(GROUND_MAP)
    shot = Projectile(tm.pixel_width - 2, 50, 1, 0)
    for _ in range(20):
        shot.update(DT, tm)
    assert not shot.alive


def test_projectile_lifetime_despawn():
    tm = _map([".........."] * 10)   # no solids, open map
    shot = Projectile(5, 5, 0, 0)    # zero velocity, just ages out
    steps = int(S.PROJECTILE_LIFETIME / DT) + 2
    for _ in range(steps):
        shot.update(DT, tm)
    assert not shot.alive


# ----------------------------------------------------------------- shoot pose
def test_shoot_plays_attack_pose():
    from assets import build_player_animations
    tm = _map(GROUND_MAP)
    p = Player(2 * S.TILE, 0, build_player_animations())
    _settle(p, tm, 120)
    assert p.on_ground
    p.update(DT, tm, FakeInput(pressed={"shoot"}))
    assert p.state == "attack"
    assert p.shoot_timer > 0.0


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
