"""Milestone 2 tests — headless (SDL dummy). See TEST_PLAN_M2.md."""

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pygame

import settings as S
from core.animation import Animator
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


def _map(rows):
    return Tilemap(rows)


# floor at ty=3 (top = 96 px)
FLOOR_MAP = ["..........", "..........", "..........", "##########"]


# ----------------------------------------------------------------- 1 tilemap
def test_tilemap_solidity_and_bounds():
    tm = _map(FLOOR_MAP)
    assert tm.is_solid(0, 3) and not tm.is_solid(0, 0)
    assert not tm.is_solid(-1, 3) and not tm.is_solid(0, 999)
    assert tm.pixel_width == 10 * S.TILE


# ----------------------------------------------------------------- 2,3 gravity/floor
def test_fall_lands_on_ground():
    tm = _map(FLOOR_MAP)
    p = Player(2 * S.TILE, 0)
    for _ in range(180):
        p.update(DT, tm, FakeInput())
    assert p.on_ground is True
    assert abs(p.aabb.bottom - 96) < 0.5
    assert abs(p.vy) < 1.0


def test_no_tunnel_high_speed():
    tm = _map(FLOOR_MAP)
    box = AABB(2 * S.TILE, 96 - 52 - 4, S.PLAYER_W, S.PLAYER_H)  # just above floor
    flags, vx, vy = move_and_collide(box, 0.0, 100000.0, DT, tm)
    assert flags["ground"] is True
    assert abs(box.bottom - 96) < 0.5  # stopped at floor, did not pass through
    assert vy == 0.0


# ----------------------------------------------------------------- 4,5 walls/ceiling
def test_wall_blocks_horizontal():
    rows = ["....#", "....#", "....#", "#####"]
    tm = _map(rows)
    p = Player(1 * S.TILE, 40)
    inp = FakeInput(held={"right"})
    for _ in range(150):
        p.update(DT, tm, inp)
    assert abs(p.aabb.right - 4 * S.TILE) < 1.0  # rests against wall at x=128
    assert p.vx == 0.0


def test_ceiling_blocks_jump():
    rows = ["#####", ".....", ".....", "#####"]
    tm = _map(rows)
    box = AABB(2 * S.TILE, 40, S.PLAYER_W, S.PLAYER_H)
    flags, vx, vy = move_and_collide(box, 0.0, -100000.0, DT, tm)
    assert flags["ceiling"] is True
    assert abs(box.top - 32) < 0.5  # stopped at ceiling bottom
    assert vy == 0.0


# ----------------------------------------------------------------- 6 variable jump
def _settle(p, tm, n=20):
    for _ in range(n):
        p.update(DT, tm, FakeInput())


def test_jump_full_vs_short():
    tm = _map(FLOOR_MAP)
    full = Player(2 * S.TILE, 40)
    short = Player(2 * S.TILE, 40)
    _settle(full, tm)
    _settle(short, tm)
    # frame 1: both press + hold jump
    full.update(DT, tm, FakeInput(held={"jump"}, pressed={"jump"}))
    short.update(DT, tm, FakeInput(held={"jump"}, pressed={"jump"}))
    full_top = full.aabb.top
    short_top = short.aabb.top
    for _ in range(40):
        full.update(DT, tm, FakeInput(held={"jump"}))   # keep holding
        short.update(DT, tm, FakeInput())               # released early
        full_top = min(full_top, full.aabb.top)
        short_top = min(short_top, short.aabb.top)
    assert full_top < short_top - 5  # holding rises noticeably higher


# ----------------------------------------------------------------- 7 coyote
def test_coyote_time():
    rows = [
        "..........", "..........", "..........", "####......",
        "..........", "..........", "..........", "..........",
        "..........", "..........", "##########",
    ]
    tm = _map(rows)
    p = Player(0, 40)
    _settle(p, tm, 20)
    assert p.on_ground
    # walk right off the platform edge
    left_ground_at = None
    for i in range(200):
        p.update(DT, tm, FakeInput(held={"right"}))
        if not p.on_ground:
            left_ground_at = i
            break
    assert left_ground_at is not None
    # immediately (within coyote window) press jump -> should jump
    p.update(DT, tm, FakeInput(held={"right", "jump"}, pressed={"jump"}))
    assert p.vy < 0  # jumped despite being airborne


# ----------------------------------------------------------------- 8 jump buffer
def test_jump_buffer():
    tm = _map(FLOOR_MAP)
    p = Player(2 * S.TILE, 0)
    # start a few px above the floor, falling, not yet grounded
    p.aabb.bottom = 96 - 6
    p.on_ground = False
    p.vy = 0.0
    # press jump once while still airborne -> buffered (held to avoid the
    # variable-height cut zeroing the test); no further presses
    p.update(DT, tm, FakeInput(held={"jump"}, pressed={"jump"}))
    landed = False
    for _ in range(7):  # within JUMP_BUFFER (0.12s ~ 7 frames)
        p.update(DT, tm, FakeInput(held={"jump"}))
        if p.on_ground:
            landed = True
            break
    assert landed
    # next grounded frame: the buffered jump should fire
    p.update(DT, tm, FakeInput(held={"jump"}))
    assert p.vy < 0


# ----------------------------------------------------------------- 9 crouch
def test_crouch_shrinks_hitbox():
    tm = _map(FLOOR_MAP)
    p = Player(2 * S.TILE, 40)
    _settle(p, tm)
    feet = p.aabb.bottom
    p.update(DT, tm, FakeInput(held={"down"}))
    assert p.crouching
    assert abs(p.aabb.height - S.PLAYER_H * S.CROUCH_HEIGHT_FACTOR) < 0.01
    assert abs(p.aabb.bottom - feet) < 0.01  # feet unchanged
    p.update(DT, tm, FakeInput())
    assert not p.crouching
    assert abs(p.aabb.height - S.PLAYER_H) < 0.01
    assert abs(p.aabb.bottom - feet) < 0.5


# ----------------------------------------------------------------- 10,11,12 anim states
def test_facing_flips():
    tm = _map(FLOOR_MAP)
    p = Player(3 * S.TILE, 40)
    _settle(p, tm)
    p.update(DT, tm, FakeInput(held={"right"}))
    assert p.facing == "right"
    p.update(DT, tm, FakeInput(held={"left"}))
    assert p.facing == "left"


def test_state_idle_run():
    tm = _map(FLOOR_MAP)
    p = Player(3 * S.TILE, 40)
    _settle(p, tm)
    assert p.state == "idle"
    for _ in range(20):
        p.update(DT, tm, FakeInput(held={"right"}))
    assert p.state == "run"


def test_state_jump_fall():
    p = Player(0, 0)
    p.on_ground = False
    p.vy = -100
    p._update_state()
    assert p.state == "jump"
    p.vy = 100
    p._update_state()
    assert p.state == "fall"


# ----------------------------------------------------------------- 13 sprite pipeline
def test_build_animations():
    from assets import PLAYER_ANIMATIONS, build_player_animations
    anims = build_player_animations()
    assert set(anims) == set(PLAYER_ANIMATIONS)
    for name, (row, frames, fps, loop) in PLAYER_ANIMATIONS.items():
        a = anims[name]
        assert a["frames"] == frames
        assert len(a["left"]) == frames and len(a["right"]) == frames
        assert a["left"][0].get_size() == (S.SPRITE_FRAME_W, S.SPRITE_FRAME_H)
        assert a["right"][0].get_size() == (S.SPRITE_FRAME_W, S.SPRITE_FRAME_H)


# ----------------------------------------------------------------- 14 animator
def test_animator_loop_and_clamp():
    def frames(n):
        return [pygame.Surface((4, 4)) for _ in range(n)]

    anims = {
        "loopy": {"left": frames(3), "right": frames(3), "fps": 10, "loop": True, "frames": 3},
        "once": {"left": frames(3), "right": frames(3), "fps": 10, "loop": False, "frames": 3},
    }
    an = Animator(anims)
    an.play("loopy")
    for _ in range(5):  # 5 frame-advances over 3-frame loop
        an.update(1 / 10)
    assert 0 <= an.frame < 3  # wrapped, never out of range
    an.play("once")
    for _ in range(10):
        an.update(1 / 10)
    assert an.frame == 2 and an.finished is True


# ----------------------------------------------------------------- 15 play state smoke
def test_play_state_smoke():
    import main
    game = main.Game()
    try:
        ps = main.PlayState(game)
        game.states.change(ps)
        assert hasattr(ps, "player")  # on_enter wired the player
        start = ps.player.aabb.bottom
        for _ in range(60):
            game.states.update(S.FIXED_DT)
        surf = pygame.Surface(S.INTERNAL_SIZE)
        game.states.draw(surf)  # should not raise
        assert ps.player.on_ground  # fell and landed on the level floor
        assert ps.player.aabb.bottom != start
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
