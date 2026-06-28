"""Milestone 8 tests — Small enemy (turret + jumper): HP/death, fire cadence and
direction, jumper jump+apex fire, contact damage, player-shot damage, enemy art.
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
from entities.enemy import Small
from entities.projectile import Projectile
from world.tilemap import Tilemap

DT = S.FIXED_DT

# floor at ty=9 (top = 288)
FLOOR_MAP = [".........."] * 9 + ["##########"]


def _map(rows):
    return Tilemap(rows)


class FakePlayer:
    """Minimal stand-in: enemies only read player.aabb.centerx."""
    def __init__(self, cx, cy=240):
        self.aabb = AABB(cx - 15, cy - 80, 30, 80)
        self.hits = 0

    def take_damage(self, amount, source_x):
        self.hits += 1
        return True


def _grounded_enemy(variant, x=6 * S.TILE, player_cx=10):
    tm = _map(FLOOR_MAP)
    fp = FakePlayer(player_cx)
    e = Small(x, 0, variant)        # spawn high, fall to the floor
    for _ in range(120):
        e.update(DT, tm, fp)
    assert e.on_ground
    return e, tm, fp


# ----------------------------------------------------------------- constants/art
def test_small_constants():
    assert S.SMALL_HP == 3
    assert S.SMALL_CONTACT_DAMAGE == 1 and S.SMALL_PROJECTILE_DAMAGE == 1
    assert S.SMALL_TURRET_INTERVAL > 0 and S.SMALL_JUMPER_INTERVAL > 0


def test_enemy_animations_build():
    from assets import build_enemy_animations
    anims = build_enemy_animations()
    assert set(["idle", "jump", "fall", "defeat"]).issubset(anims)
    assert anims["idle"]["left"][0].get_width() > 0


# ----------------------------------------------------------------- HP / death
def test_enemy_takes_damage_and_dies():
    e, tm, fp = _grounded_enemy("turret")
    assert e.take_damage(1) and e.hp == 2 and not e.dead
    e.take_damage(1)
    assert e.hp == 1 and not e.dead
    e.take_damage(1)
    assert e.hp == 0 and e.dead         # 3 hits -> defeat
    # plays out the defeat animation, then is flagged for removal
    for _ in range(int(S.DEFEAT_HOLD / DT) + 4):
        e.update(DT, tm, fp)
    assert e.death_done and not e.alive


# ----------------------------------------------------------------- turret
def test_turret_fires_toward_player():
    e, tm, fp = _grounded_enemy("turret", x=6 * S.TILE, player_cx=10)  # player to the left
    fired = None
    for _ in range(int(S.SMALL_TURRET_INTERVAL / DT) + 5):
        e.update(DT, tm, fp)
        if e.fired:
            fired = e.fired[0]
            break
    assert fired is not None
    assert fired.vx < 0 and abs(fired.vy) < 1e-6   # aimed left, at the player
    assert fired.owner == "enemy"


def test_turret_cadence():
    e, tm, fp = _grounded_enemy("turret")
    shots = 0
    for _ in range(int(5.0 / DT)):
        e.update(DT, tm, fp)
        shots += len(e.fired)
    assert shots >= 2          # ~ one every 2 s over 5 s


# ----------------------------------------------------------------- jumper
def test_jumper_jumps_and_fires_at_apex():
    e, tm, fp = _grounded_enemy("jumper")
    airborne_seen = False
    shot_while_airborne = False
    shots = 0
    for _ in range(int(5.0 / DT)):
        e.update(DT, tm, fp)
        if not e.on_ground:
            airborne_seen = True
        if e.fired:
            shots += len(e.fired)
            if not e.on_ground:
                shot_while_airborne = True
    assert airborne_seen          # it jumped
    assert shots >= 1 and shot_while_airborne   # fired in the air (at the apex)


# ----------------------------------------------------------------- PlayState
def test_enemy_contact_damages_player():
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
        ps.enemies.append(Small(a.centerx, a.bottom, "turret"))  # overlapping her
        hp0 = ps.player.hp
        ps.update(DT)
        assert ps.player.hp < hp0
        assert ps.player.iframes > 0
    finally:
        pygame.quit()


def test_player_shot_damages_enemy():
    import main
    g = main.Game()
    try:
        g.input.begin_frame()
        g.input.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RETURN}))
        g.states.update(DT)
        ps = g.states.current
        assert len(ps.enemies) >= 1
        e = ps.enemies[0]
        hp0 = e.hp
        pr = Projectile(e.aabb.centerx, e.aabb.top + e.aabb.height / 2, 0, 0,
                        owner="player")
        ps.projectiles.append(pr)
        ps.update(DT)
        assert e.hp == hp0 - pr.damage
        assert pr.alive is False                # consumed on hit
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
