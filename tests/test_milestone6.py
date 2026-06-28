"""Milestone 6 tests — HP, knockback, mercy i-frames + blink, and a damaging
enemy projectile from the right exercising collision/damage. Headless."""

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
from entities.projectile import Projectile
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
    assert p.on_ground
    return p, tm


def _key(et, k):
    return pygame.event.Event(et, {"key": k})


# ----------------------------------------------------------------- constants
def test_damage_constants():
    assert S.PLAYER_MAX_HP == 10
    assert S.IFRAME_TIME > 0 and S.KNOCKBACK_VX > 0 and S.KNOCKBACK_VY < 0
    assert S.ENEMY_PROJECTILE_DAMAGE >= 1


# ----------------------------------------------------------------- knockback
def test_damage_and_knockback_from_right():
    p, tm = _grounded_player()
    hp0 = p.hp
    hit = p.take_damage(2, p.aabb.centerx + 100)   # source on the right
    assert hit is True
    assert p.hp == hp0 - 2
    assert p.vx < 0                                # pushed left, away from source
    assert p.vy < 0                                # popped up
    assert p.iframes > 0 and p.control_lock > 0


def test_knockback_from_left_pushes_right():
    p, tm = _grounded_player()
    p.take_damage(1, p.aabb.centerx - 100)
    assert p.vx > 0


# ----------------------------------------------------------------- i-frames
def test_iframes_block_repeat_hit():
    p, tm = _grounded_player()
    assert p.take_damage(1, p.aabb.centerx + 100) is True
    hp1 = p.hp
    assert p.take_damage(5, p.aabb.centerx + 100) is False   # still invincible
    assert p.hp == hp1


def test_iframes_expire_then_damage_again():
    p, tm = _grounded_player()
    p.take_damage(1, p.aabb.centerx + 100)
    hp1 = p.hp
    for _ in range(int(S.IFRAME_TIME / DT) + 3):
        p.update(DT, tm, FakeInput())
    assert p.iframes == 0.0
    assert p.take_damage(1, p.aabb.centerx + 100) is True
    assert p.hp == hp1 - 1


# ----------------------------------------------------------------- control lock
def test_control_lock_ignores_input():
    p, tm = _grounded_player()
    p.take_damage(1, p.aabb.centerx + 100)         # knocked left
    assert p.vx < 0
    p.update(DT, tm, FakeInput(held={"right"}))     # try to run right during lock
    assert p.vx < 0                                # input ignored; still moving left


# ----------------------------------------------------------------- blink
def test_visible_blinks_during_iframes():
    p = Player(0, 0)
    assert p.visible is True                       # no i-frames
    p.iframes = S.BLINK_INTERVAL * 0.5             # phase 0
    assert p.visible is True
    p.iframes = S.BLINK_INTERVAL * 1.5             # phase 1
    assert p.visible is False


# ----------------------------------------------------------------- death
def test_hp_clamps_and_dead_flag():
    p, tm = _grounded_player()
    assert p.take_damage(999, p.aabb.centerx + 100) is True
    assert p.hp == 0 and p.dead is True
    assert p.take_damage(1, p.aabb.centerx + 100) is False   # dead -> no more hits


# ----------------------------------------------------------------- enemy hazard
def test_enemy_projectile_damages_player_in_playstate():
    import main
    g = main.Game()
    try:
        g.input.begin_frame()
        g.input.process_event(_key(pygame.KEYDOWN, pygame.K_RETURN))
        g.states.update(DT)
        ps = g.states.current
        assert isinstance(ps, main.PlayState)
        # land the player WITHOUT running hazard logic (avoid auto-spawn noise)
        for _ in range(120):
            ps.player.update(DT, ps.tilemap, g.input)
        ps.enemy_timer = 1e9                         # suppress auto-spawn for the test
        a = ps.player.aabb
        hp0 = ps.player.hp
        # inject an enemy bullet overlapping the player, coming from the right
        ps.hazards.append(Projectile(
            a.centerx, a.top + a.height * 0.5, -1, 0,
            speed=S.ENEMY_PROJECTILE_SPEED, damage=S.ENEMY_PROJECTILE_DAMAGE,
            size=S.ENEMY_PROJECTILE_SIZE, color=S.ENEMY_PROJECTILE_COLOR,
            owner="enemy"))
        ps.update(DT)
        assert ps.player.hp == hp0 - S.ENEMY_PROJECTILE_DAMAGE
        assert len(ps.hazards) == 0                  # bullet consumed on contact
        assert ps.player.iframes > 0
    finally:
        pygame.quit()


def test_enemy_projectile_auto_spawns_and_can_hit():
    import main
    g = main.Game()
    try:
        g.input.begin_frame()
        g.input.process_event(_key(pygame.KEYDOWN, pygame.K_RETURN))
        g.states.update(DT)
        ps = g.states.current
        # the enemy shot only fires on the highest platform -> put her there
        ps.player.aabb.x = 6 * S.TILE
        ps.player.aabb.bottom = ps.highest_top
        ps.player.vx = 0.0
        ps.player.vy = 0.0
        ps.player.on_ground = True
        # run a few seconds; standing on the highest platform she should lose HP
        for _ in range(int(6.0 / DT)):
            ps.update(DT)
            if isinstance(g.states.current, main.GameOverState):
                break
        assert ps.player.hp < S.PLAYER_MAX_HP        # took at least one hit
    finally:
        pygame.quit()


# ----------------------------------------------------------------- death anim
def test_death_sets_defeat_state():
    p, tm = _grounded_player()
    assert p.take_damage(999, p.aabb.centerx + 100) is True
    assert p.dead and p.state == "defeat"
    assert p.death_done is False          # not finished yet


def test_death_done_only_after_hold():
    p, tm = _grounded_player()
    p.take_damage(999, p.aabb.centerx + 100)
    p.update(DT, tm, FakeInput())
    assert p.death_done is False           # still animating
    for _ in range(int(S.DEFEAT_HOLD / DT) + 3):
        p.update(DT, tm, FakeInput())
    assert p.death_done is True


def test_death_plays_defeat_animation():
    from assets import build_player_animations
    tm = _map(GROUND_MAP)
    p = Player(2 * S.TILE, 0, build_player_animations())
    for _ in range(120):
        p.update(DT, tm, FakeInput())
    p.take_damage(999, p.aabb.centerx + 100)
    assert p.animator.name == "defeat"
    for _ in range(int(S.DEFEAT_HOLD / DT) + 6):
        p.update(DT, tm, FakeInput())
    assert p.animator.finished and p.death_done


def test_playstate_waits_for_defeat_before_gameover():
    import main
    g = main.Game()
    try:
        g.input.begin_frame()
        g.input.process_event(_key(pygame.KEYDOWN, pygame.K_RETURN))
        g.states.update(DT)
        ps = g.states.current
        for _ in range(120):
            ps.player.update(DT, ps.tilemap, g.input)
        ps.enemy_timer = 1e9
        ps.player.take_damage(999, ps.player.aabb.centerx + 100)
        ps.update(DT)
        assert g.states.current is ps                 # still in Play during defeat
        for _ in range(int(S.DEFEAT_HOLD / DT) + 6):
            g.states.current.update(DT)
            if isinstance(g.states.current, main.GameOverState):
                break
        assert isinstance(g.states.current, main.GameOverState)
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
