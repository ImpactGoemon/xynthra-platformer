"""Milestone 9 tests — Big enemy: constants/art, detection (idle until in range),
pursuit toward the player, jumping to reach her, contact -> swallow trigger, and
player-shot damage (5 HP). Plus the player's swallowed state. Headless (SDL dummy)."""

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
from entities.projectile import Projectile
from world.tilemap import Tilemap

DT = S.FIXED_DT

# floor at ty=9 (top = 288)
FLOOR_MAP = [".........."] * 9 + ["##########"]
# a wide floor for pursuit/jump tests
WIDE_FLOOR = ["." * 40] * 9 + ["#" * 40]


def _map(rows):
    return Tilemap(rows)


class FakePlayer:
    """Minimal stand-in: Big reads player.aabb (centerx, top, h, bottom)."""
    def __init__(self, cx, cy=240):
        self.aabb = AABB(cx - 15, cy - 80, 30, 80)
        self.swallowed = False
        self.swallowed_by = None

    def enter_swallow(self, enemy):
        if self.swallowed:
            return False
        self.swallowed = True
        self.swallowed_by = enemy
        return True


def _grounded_big(x=6 * S.TILE, player_cx=10, rows=None):
    tm = _map(rows if rows is not None else FLOOR_MAP)
    fp = FakePlayer(player_cx)
    e = Big(x, 0)                    # spawn high, fall to the floor
    for _ in range(160):
        e.update(DT, tm, fp)
    assert e.on_ground
    return e, tm, fp


# ----------------------------------------------------------------- constants/art
def test_big_constants():
    assert S.BIG_HP == 5
    assert S.BIG_DETECT_RADIUS > 0 and S.BIG_SPEED > 0
    # ~1.85x the Small enemy footprint
    assert S.BIG_W > S.SMALL_W and S.BIG_H > S.SMALL_H


def test_big_animations_build():
    from assets import build_big_animations
    anims = build_big_animations()
    assert set(["idle", "run", "jump", "fall", "defeat"]).issubset(anims)
    assert anims["idle"]["left"][0].get_width() > 0


# ----------------------------------------------------------------- detection
def test_big_idle_until_player_in_range():
    # player far to the right, beyond the detection radius
    far = 6 * S.TILE + int(S.BIG_DETECT_RADIUS) + 120
    e, tm, fp = _grounded_big(x=6 * S.TILE, player_cx=far)
    assert not e.detected
    assert abs(e.vx) < 1e-6          # stays put when nobody is near


def test_big_detects_and_pursues_right():
    # player within range, to the right -> Big should detect and move right
    near = 6 * S.TILE + 120
    e, tm, fp = _grounded_big(x=6 * S.TILE, player_cx=near, rows=WIDE_FLOOR)
    assert e.detected
    for _ in range(20):
        e.update(DT, tm, fp)
    assert e.vx > 0                  # accelerating toward her
    assert e.facing == "right"


def test_big_detects_and_pursues_left():
    e, tm, fp = _grounded_big(x=20 * S.TILE, player_cx=20 * S.TILE - 120,
                              rows=WIDE_FLOOR)
    assert e.detected
    for _ in range(20):
        e.update(DT, tm, fp)
    assert e.vx < 0
    assert e.facing == "left"


def test_big_stays_detected_once_seen():
    e, tm, fp = _grounded_big(x=6 * S.TILE, player_cx=6 * S.TILE + 120,
                              rows=WIDE_FLOOR)
    assert e.detected
    fp.aabb = AABB(9999, 0, 30, 80)  # teleport player far away
    for _ in range(10):
        e.update(DT, tm, fp)
    assert e.detected                # detection latches; it keeps hunting


# ----------------------------------------------------------------- jumping
def test_big_jumps_when_player_above():
    tm = _map(WIDE_FLOOR)
    e = Big(6 * S.TILE, 0)
    fp = FakePlayer(6 * S.TILE, cy=240)
    for _ in range(160):             # settle on the floor
        e.update(DT, tm, fp)
    assert e.on_ground
    # put the player high above, within detection radius
    fp.aabb = AABB(e.aabb.centerx - 15, 40 - 80, 30, 80)  # bottom = 40, well above
    airborne_seen = False
    for _ in range(60):
        e.update(DT, tm, fp)
        if not e.on_ground:
            airborne_seen = True
    assert airborne_seen             # it jumped to try to reach her


# ----------------------------------------------------------------- HP / death
def test_big_takes_five_hits_to_die():
    e, tm, fp = _grounded_big()
    for _ in range(4):
        e.take_damage(1)
    assert e.hp == 1 and not e.dead
    e.take_damage(1)
    assert e.hp == 0 and e.dead      # 5 hits -> defeat
    for _ in range(int(S.DEFEAT_HOLD / DT) + 4):
        e.update(DT, tm, fp)
    assert e.death_done and not e.alive


# ----------------------------------------------------------------- swallow
def test_big_contact_swallows_player():
    fp = FakePlayer(0)
    e = Big(0, 200)
    fp.aabb = AABB(e.aabb.centerx - 15, e.aabb.top, 30, 80)  # overlap the Big
    assert getattr(e, "swallows", False) is True
    # mimic the PlayState contact rule
    from main import _overlap
    assert _overlap(e.aabb, fp.aabb)
    fp.enter_swallow(e)
    assert fp.swallowed and fp.swallowed_by is e


def test_playstate_big_contact_sets_swallowed():
    import main
    g = main.Game()
    try:
        g.input.begin_frame()
        g.input.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RETURN}))
        g.states.update(DT)
        ps = g.states.current
        for _ in range(120):
            ps.player.update(DT, ps.tilemap, g.input)
        a = ps.player.aabb
        ps.enemies.append(Big(a.centerx, a.bottom))   # overlap her
        assert ps.player.swallowed is False
        ps.update(DT)
        assert ps.player.swallowed is True
    finally:
        pygame.quit()


def test_swallowed_player_freezes():
    tm = _map(FLOOR_MAP)
    p = Player(100, 100)
    e = Big(100, 200)
    assert p.enter_swallow(e)
    x0, y0 = p.aabb.x, p.aabb.y

    class _Inp:
        def is_held(self, a): return a in ("right", "shoot")
        def just_pressed(self, a): return a == "jump"
        def just_released(self, a): return False

    for _ in range(30):
        p.update(DT, tm, _Inp())
    assert p.aabb.x == x0 and p.aabb.y == y0   # held in place
    assert not p.fired                          # cannot shoot while swallowed


def test_player_sprite_hidden_when_swallowed():
    # while swallowed the player sprite is not drawn (she is inside the enemy)
    surf = pygame.Surface((120, 120))
    surf.fill((0, 0, 0))
    p = Player(10, 10)                       # no animations -> would draw a fallback rect
    p.swallowed = True
    p.draw(surf, (0, 0))
    assert surf.get_at((int(p.aabb.x) + 2, int(p.aabb.y) + 2))[:3] == (0, 0, 0)
    p.swallowed = False                      # sanity: normally it DOES draw
    p.draw(surf, (0, 0))
    assert surf.get_at((int(p.aabb.x) + 2, int(p.aabb.y) + 2))[:3] != (0, 0, 0)


def test_playstate_swallow_freezes_enemy():
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
        big.aabb.x = a.centerx - big.aabb.w / 2.0   # overlap the player
        big.aabb.bottom = a.bottom
        big.detected = True
        ps.update(DT)
        assert ps.player.swallowed and big.has_swallowed
        # it should stop pursuing (no back-and-forth) and idle in place
        for _ in range(int(1.0 / DT)):
            ps.update(DT)
        assert abs(big.vx) < 1.0
        assert ps.player.swallowed                  # still held
    finally:
        pygame.quit()


# ----------------------------------------------------------------- PlayState shot
def test_player_shot_damages_big():
    import main
    g = main.Game()
    try:
        g.input.begin_frame()
        g.input.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RETURN}))
        g.states.update(DT)
        ps = g.states.current
        bigs = [e for e in ps.enemies if isinstance(e, Big)]
        assert bigs, "expected a Big enemy in the level"
        e = bigs[0]
        hp0 = e.hp
        pr = Projectile(e.aabb.centerx, e.aabb.top + e.aabb.height / 2, 0, 0,
                        owner="player")
        ps.projectiles.append(pr)
        ps.update(DT)
        assert e.hp == hp0 - pr.damage
        assert pr.alive is False
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
