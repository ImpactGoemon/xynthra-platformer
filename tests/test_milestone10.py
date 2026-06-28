"""Milestone 10 tests — swallow/struggle minigame: bar drain + Space refill,
1 dmg / 2.5 s, escape (fill -> enemy stun + i-frames), digest (empty or HP 0 ->
defeat), no external damage while swallowed, and enemy idle while stunned.
Headless (SDL dummy)."""

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
from entities.enemy import Big
from world.tilemap import Tilemap

DT = S.FIXED_DT
FLOOR_MAP = [".........."] * 9 + ["##########"]


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


class FakeEnemy:
    """Stand-in swallower: only the swallow-related attributes are read."""
    def __init__(self, cx=64):
        self.aabb = AABB(cx - 28, 100, 56, 133)
        self.struggle_drain = S.STRUGGLE_DRAIN_TIME_BIG
        self.has_swallowed = True
        self.stun_timer = 0.0


class FakePlayer:
    def __init__(self, cx):
        self.aabb = AABB(cx - 15, 200, 30, 80)

    def take_damage(self, *a):
        return True


def _map(rows):
    return Tilemap(rows)


def _swallowed():
    tm = _map(FLOOR_MAP)
    p = Player(2 * S.TILE, 200)
    e = FakeEnemy()
    assert p.enter_swallow(e)
    return p, e, tm


# ----------------------------------------------------------------- constants
def test_struggle_constants():
    assert S.STRUGGLE_START == 0.5 and S.STRUGGLE_REFILL == 0.08
    assert S.STRUGGLE_DRAIN_TIME_BIG > 0 and S.STRUGGLE_DMG_INTERVAL == 2.5
    assert S.ENEMY_STUN_TIME == 3.0


# ----------------------------------------------------------------- bar
def test_enter_swallow_starts_bar_half():
    p, e, tm = _swallowed()
    assert p.swallowed and p.swallowed_by is e
    assert abs(p.struggle - S.STRUGGLE_START) < 1e-9
    assert abs(p.struggle_fraction - 0.5) < 1e-9


def test_bar_drains_without_input():
    p, e, tm = _swallowed()
    s0 = p.struggle
    p.update(DT, tm, FakeInput())
    assert p.struggle < s0


def test_struggle_press_refills():
    p, e, tm = _swallowed()
    s0 = p.struggle
    p.update(DT, tm, FakeInput(pressed={"struggle"}))
    assert p.struggle > s0          # +8% beats one frame of drain


# ----------------------------------------------------------------- escape
def test_escape_on_full_stuns_enemy():
    p, e, tm = _swallowed()
    p.struggle = 0.95
    p.update(DT, tm, FakeInput(pressed={"struggle"}))   # -> >= 1.0 -> escape
    assert not p.swallowed and p.swallowed_by is None
    assert e.has_swallowed is False and e.stun_timer > 0.0
    assert p.iframes > 0.0          # brief mercy after escaping


# ----------------------------------------------------------------- damage
def test_internal_damage_every_interval():
    p, e, tm = _swallowed()
    hp0 = p.hp
    for _ in range(int(S.STRUGGLE_DMG_INTERVAL / DT) + 2):
        p.struggle = 0.5           # pin so it neither escapes nor digests
        p.update(DT, tm, FakeInput())
    assert p.hp == hp0 - S.STRUGGLE_DMG
    assert p.swallowed             # still inside


# ----------------------------------------------------------------- digest
def test_digest_on_empty_bar():
    p, e, tm = _swallowed()
    p.struggle = 0.05
    for _ in range(int(0.05 * S.STRUGGLE_DRAIN_TIME_BIG / DT) + 5):
        p.update(DT, tm, FakeInput())
        if p.digesting:
            break
    # bar empties -> digestion placeholder (not dead yet), player hidden inside
    assert p.digesting and p.hp == 0 and not p.swallowed and not p.dead
    # play out the digestion -> hands off to game over (dead + death_done)
    for _ in range(int(S.DIGEST_HOLD / DT) + 3):
        p.update(DT, tm, FakeInput())
    assert p.dead and p.death_done and not p.digesting


def test_digest_on_hp_zero():
    p, e, tm = _swallowed()
    p.hp = 1
    for _ in range(int(S.STRUGGLE_DMG_INTERVAL / DT) + 2):
        p.struggle = 0.6           # keep the bar up; death comes from the dmg tick
        p.update(DT, tm, FakeInput())
        if p.digesting:
            break
    assert p.digesting and p.hp == 0     # HP-0 inside also triggers digestion


# ----------------------------------------------------------------- invulnerable
def test_no_external_damage_while_swallowed():
    p, e, tm = _swallowed()
    hp0 = p.hp
    assert p.take_damage(5, p.aabb.centerx + 100) is False
    assert p.hp == hp0


def test_digestion_then_dead_for_gameover():
    p, e, tm = _swallowed()
    p.struggle = 0.02
    # drain to empty -> digesting
    for _ in range(30):
        p.update(DT, tm, FakeInput())
        if p.digesting:
            break
    assert p.digesting and not p.dead
    assert p.digest_timer > 0.0
    # external hits and re-swallow are ignored during digestion
    assert p.take_damage(3, p.aabb.centerx) is False
    assert p.enter_swallow(e) is False
    # after the hold it becomes dead+death_done (Play state -> Game Over)
    for _ in range(int(S.DIGEST_HOLD / DT) + 3):
        p.update(DT, tm, FakeInput())
    assert p.dead and p.death_done


# ----------------------------------------------------------------- enemy stun
def test_big_idles_while_stunned():
    tm = _map([".........."] * 9 + ["##########"])
    b = Big(3 * S.TILE, 0)
    fp = FakePlayer(10)            # to the left -> would normally pursue
    for _ in range(120):
        b.update(DT, tm, fp)
    b.detected = True
    b.stun_timer = S.ENEMY_STUN_TIME
    for _ in range(int(1.0 / DT)):
        b.update(DT, tm, fp)
    assert abs(b.vx) < 1.0         # stunned -> no pursuit
    assert b.stun_timer > 0.0


# ----------------------------------------------------------------- PlayState
def test_playstate_escape_stuns_and_frees():
    import main
    g = main.Game()
    try:
        g.input.begin_frame()
        g.input.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RETURN}))
        g.states.update(DT)
        ps = g.states.current
        for _ in range(120):
            ps.player.update(DT, ps.tilemap, g.input)
        big = next(e for e in ps.enemies if getattr(e, "swallows", False))
        a = ps.player.aabb
        big.aabb.x = a.centerx - big.aabb.w / 2.0
        big.aabb.bottom = a.bottom
        big.detected = True
        ps.update(DT)
        assert ps.player.swallowed and big.has_swallowed
        # nudge the bar near full, then a Struggle press escapes
        ps.player.struggle = 0.99
        g.input.begin_frame()
        g.input.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_SPACE}))
        ps.update(DT)
        assert not ps.player.swallowed
        assert big.stun_timer > 0.0 and big.has_swallowed is False
        # while stunned + i-frames she is not instantly re-swallowed
        ps.update(DT)
        assert not ps.player.swallowed
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
