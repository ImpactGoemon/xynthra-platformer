"""Milestone 7 tests — healing pickups (swallow, cap 3), hold-Heal digest,
belly count, pickup sizing (~1/4 Xynthra), and the highest-platform-only hazard.
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
from entities.player import Player
from entities.pickup import Pickup
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


GROUND_MAP = [".........."] * 9 + ["##########"]


def _map(rows):
    return Tilemap(rows)


def _grounded_player():
    tm = _map(GROUND_MAP)
    p = Player(2 * S.TILE, 0)
    for _ in range(120):
        p.update(DT, tm, FakeInput())
    assert p.on_ground and abs(p.vx) < S.HEAL_MOVE_EPS
    return p, tm


def _key(et, k):
    return pygame.event.Event(et, {"key": k})


# ----------------------------------------------------------------- belly / swallow
def test_belly_constants():
    assert S.BELLY_MAX == 3 and S.HEAL_HOLD == 4.0 and S.HEAL_AMOUNT == 3


def test_swallow_caps_at_belly_max():
    p = Player(0, 0)
    assert p.belly == 0
    assert p.swallow() and p.swallow() and p.swallow()
    assert p.belly == 3
    assert p.swallow() is False        # capped
    assert p.belly == 3


# ----------------------------------------------------------------- pickup sizing
def test_pickup_image_is_quarter_of_xynthra():
    from assets import build_pickup_image, _xynthra_idle_height
    img = build_pickup_image()
    assert img is not None
    target = round(_xynthra_idle_height() * S.PICKUP_SIZE_FRACTION)
    assert abs(img.get_height() - target) <= 1
    # and clearly smaller than Xynthra
    assert img.get_height() < _xynthra_idle_height() / 2


# ----------------------------------------------------------------- healing
def test_heal_digests_after_hold():
    p, tm = _grounded_player()
    p.belly = 1
    p.hp = 5
    steps = int(S.HEAL_HOLD / DT) + 2
    for _ in range(steps):
        p.update(DT, tm, FakeInput(held={"heal"}))
    assert p.hp == 8                   # +HEAL_AMOUNT
    assert p.belly == 0


def test_heal_blocked_while_moving():
    p, tm = _grounded_player()
    p.belly = 1
    p.hp = 5
    for _ in range(int(S.HEAL_HOLD / DT) + 2):
        p.update(DT, tm, FakeInput(held={"heal", "right"}))   # moving
    assert p.hp == 5 and p.belly == 1  # no progress while moving
    assert p.heal_timer == 0.0


def test_heal_interrupted_by_damage():
    p, tm = _grounded_player()
    p.belly = 1
    p.hp = 5
    for _ in range(int(2.0 / DT)):     # ~2 s of holding (not yet done)
        p.update(DT, tm, FakeInput(held={"heal"}))
    assert p.heal_timer > 0 and p.hp == 5
    p.take_damage(1, p.aabb.centerx + 100)
    assert p.heal_timer == 0.0 and p.healing is False
    assert p.hp == 4                   # took the hit, no heal applied


def test_heal_needs_belly_and_not_full():
    p, tm = _grounded_player()
    p.belly = 0
    p.hp = 5
    for _ in range(int(S.HEAL_HOLD / DT) + 2):
        p.update(DT, tm, FakeInput(held={"heal"}))
    assert p.hp == 5                   # nothing stored -> no heal
    p.belly = 1
    p.hp = S.PLAYER_MAX_HP
    for _ in range(int(S.HEAL_HOLD / DT) + 2):
        p.update(DT, tm, FakeInput(held={"heal"}))
    assert p.belly == 1                # already full -> no digest


def test_no_heal_bar_at_full_hp():
    # holding Heal at full HP shows NO digest bar and consumes nothing
    p, tm = _grounded_player()
    p.belly = 2
    p.hp = S.PLAYER_MAX_HP
    for _ in range(int(2.0 / DT)):
        p.update(DT, tm, FakeInput(held={"heal"}))
    assert p.healing is False and p.heal_fraction == 0.0
    assert p.belly == 2


def test_heal_bar_disappears_when_hp_reaches_max():
    # heal from 9: one digest tops to max, then the bar must not re-appear
    p, tm = _grounded_player()
    p.belly = 2
    p.hp = S.PLAYER_MAX_HP - 1     # 9
    # hold Heal continuously across the digest and beyond
    healed = False
    for _ in range(int((S.HEAL_HOLD + 1.0) / DT)):
        p.update(DT, tm, FakeInput(held={"heal"}))
        if p.hp == S.PLAYER_MAX_HP:
            healed = True
    assert healed and p.hp == S.PLAYER_MAX_HP
    assert p.belly == 1            # exactly one digested
    # now at full HP, still holding Heal -> no bar, no further digest
    p.update(DT, tm, FakeInput(held={"heal"}))
    assert p.healing is False and p.heal_fraction == 0.0
    assert p.belly == 1


# ----------------------------------------------------------------- pickup collect
def test_pickup_collected_in_playstate():
    import main
    g = main.Game()
    try:
        g.input.begin_frame()
        g.input.process_event(_key(pygame.KEYDOWN, pygame.K_RETURN))
        g.states.update(DT)
        ps = g.states.current
        for _ in range(120):
            ps.player.update(DT, ps.tilemap, g.input)
        a = ps.player.aabb
        ps.pickups.append(Pickup(a.centerx, a.bottom, None))   # overlapping her
        before = ps.player.belly
        ps.update(DT)
        assert ps.player.belly == before + 1
        assert all(not pk.collected for pk in ps.pickups)      # collected one removed
        assert len(ps.pickups) == 3                            # 3 level + 1 - 1 eaten
    finally:
        pygame.quit()


# ----------------------------------------------------------------- hazard gating
def test_hazard_only_on_highest_platform():
    import main
    g = main.Game()
    try:
        g.input.begin_frame()
        g.input.process_event(_key(pygame.KEYDOWN, pygame.K_RETURN))
        g.states.update(DT)
        ps = g.states.current
        ps.enemies = []          # isolate the highest-platform test hazard
        assert ps.highest_top is not None
        # put her on the highest ledge -> a hazard should appear
        ps.player.aabb.x = 6 * S.TILE
        ps.player.aabb.bottom = ps.highest_top
        ps.player.vx = 0.0
        ps.player.vy = 0.0
        ps.player.on_ground = True
        spawned = False
        for _ in range(int(3.0 / DT)):
            ps.update(DT)
            if ps.hazards:
                spawned = True
                break
        assert spawned
        # move her down onto the floor (off the highest platform) -> no new hazards
        ps.hazards.clear()
        ps.player.aabb.x = 2 * S.TILE
        ps.player.aabb.bottom = ps.tilemap.pixel_height - S.TILE
        ps.player.on_ground = True
        ps.player.vx = 0.0
        ps.enemy_timer = 0.01
        off_spawned = False
        for _ in range(int(3.0 / DT)):
            ps.update(DT)
            if ps.hazards:
                off_spawned = True
                break
        assert not off_spawned
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
