"""Milestone 3 tests — one-way platforms, drop-through, crouch squash. Headless."""

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pygame

import settings as S
from core.physics import AABB, move_and_collide
from entities.player import Player
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


# one-way platform row at ty=3 (top = 96), solid floor far below at ty=9 (288)
ONEWAY_MAP = [
    "..........",
    "..........",
    "..........",
    "==========",   # one-way at y=96
    "..........",
    "..........",
    "..........",
    "..........",
    "..........",
    "##########",   # solid floor at y=288
]


def _map(rows):
    return Tilemap(rows)


def _settle(p, tm, n, inp=None):
    for _ in range(n):
        p.update(DT, tm, inp or FakeInput())


# ----------------------------------------------------------------- tilemap
def test_tilemap_oneway_vs_solid():
    tm = _map(ONEWAY_MAP)
    assert tm.is_oneway(0, 3) and not tm.is_solid(0, 3)
    assert tm.is_solid(0, 9) and not tm.is_oneway(0, 9)


# ----------------------------------------------------------------- land from above
def test_oneway_land_from_above():
    tm = _map(ONEWAY_MAP)
    p = Player(2 * S.TILE, 0)            # falls from the top onto the one-way row
    _settle(p, tm, 120)
    assert p.on_ground is True
    assert p.on_oneway is True
    assert abs(p.aabb.bottom - 96) < 0.5  # resting on the one-way top


# ----------------------------------------------------------------- pass up through
def test_oneway_pass_up_from_below():
    tm = _map(ONEWAY_MAP)
    # box just below the one-way, moving up fast -> should pass, not bonk
    box = AABB(2 * S.TILE, 96 + 10, S.PLAYER_W, S.PLAYER_H)
    flags, vx, vy = move_and_collide(box, 0.0, -2000.0, DT, tm)
    assert flags["ceiling"] is False
    assert box.top < 96 + 10            # moved upward through the platform


# ----------------------------------------------------------------- drop through
def test_drop_through_with_crouch_jump():
    tm = _map(ONEWAY_MAP)
    p = Player(2 * S.TILE, 0)
    _settle(p, tm, 120)                  # land on the one-way
    assert p.on_oneway and p.aabb.bottom <= 96.5
    start_bottom = p.aabb.bottom
    # crouch + jump -> drop through
    p.update(DT, tm, FakeInput(held={"down"}, pressed={"jump"}))
    assert p.drop_through_top is not None
    # fall for a bit; she should end up below the one-way platform
    _settle(p, tm, 30, FakeInput(held={"down"}))
    assert p.aabb.top > 96               # now below the platform's top
    assert p.aabb.bottom > start_bottom


def test_drop_through_only_one_platform():
    # two stacked one-way ledges + solid floor; dropping from the top one must
    # land on the SECOND, not plummet to the floor.
    # ledges spaced wider than the player (80px); first ledge well below spawn
    rows = [
        ".........",   # 0
        ".........",   # 1
        ".........",   # 2
        ".........",   # 3
        "=========",   # 4 top one-way,  top = 128
        ".........",   # 5
        ".........",   # 6
        ".........",   # 7
        "=========",   # 8 second one-way, top = 256
        ".........",   # 9
        ".........",   # 10
        ".........",   # 11
        "#########",   # 12 floor, top = 384
    ]
    tm = _map(rows)
    p = Player(2 * S.TILE, 0)
    _settle(p, tm, 300)                  # land on the top ledge (y=128)
    assert abs(p.aabb.bottom - 128) < 1.5 and p.on_oneway
    p.update(DT, tm, FakeInput(held={"down"}, pressed={"jump"}))  # drop
    _settle(p, tm, 300)                  # fall and settle
    assert abs(p.aabb.bottom - 256) < 1.5   # caught by the second ledge
    assert p.aabb.bottom < 384              # did NOT reach the floor


# ----------------------------------------------------------------- solid regression
def test_solid_blocks_from_below():
    # solid ceiling must still bonk the head
    rows = ["##########", "..........", "..........", "..........",
            "..........", "..........", "##########"]
    tm = _map(rows)
    box = AABB(2 * S.TILE, 40, S.PLAYER_W, S.PLAYER_H)
    flags, vx, vy = move_and_collide(box, 0.0, -100000.0, DT, tm)
    assert flags["ceiling"] is True
    assert abs(box.top - 32) < 0.5


def test_oneway_does_not_block_rising_player():
    # a normal jump up through a one-way keeps rising (no ground catch mid-rise)
    tm = _map(ONEWAY_MAP)
    box = AABB(2 * S.TILE, 96 + 20, S.PLAYER_W, S.PLAYER_H)
    flags, vx, vy = move_and_collide(box, 0.0, -1500.0, DT, tm)
    assert flags["ground"] is False and flags["ceiling"] is False


# ----------------------------------------------------------------- crouch squash
def test_crouch_squash_render():
    from assets import build_player_animations
    p = Player(0, 0, build_player_animations())
    p.crouching = False
    full_h = p.sprite_image().get_height()
    p.crouching = True
    crouch_h = p.sprite_image().get_height()
    assert crouch_h < full_h
    assert abs(crouch_h - full_h * S.CROUCH_HEIGHT_FACTOR) <= 2


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
