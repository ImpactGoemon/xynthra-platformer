"""Refactor tests — the shared Entity/Actor hierarchy and its helpers.

Verifies the OOP structure (Player, Small, Big inherit Actor; Pickup is a plain
Entity, NOT an Actor) and that the extracted shared helpers behave correctly."""

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import settings as S
from core.physics import AABB, approach
from entities.entity import Entity
from entities.actor import Actor
from entities.player import Player
from entities.enemy import Small, Big
from entities.pickup import Pickup
from world.tilemap import Tilemap

DT = S.FIXED_DT
FLOOR_MAP = [".........."] * 9 + ["##########"]


class FakeInput:
    def is_held(self, a):
        return False

    def just_pressed(self, a):
        return False

    def just_released(self, a):
        return False


# ----------------------------------------------------------------- hierarchy
def test_humanoids_are_actors():
    assert issubclass(Player, Actor)
    assert issubclass(Small, Actor) and issubclass(Big, Actor)
    # ... and Actors are Entities
    assert issubclass(Actor, Entity)


def test_pickup_is_entity_not_actor():
    assert issubclass(Pickup, Entity)
    assert not issubclass(Pickup, Actor)     # shares the root, not humanoid behaviour
    pk = Pickup(100, 100)
    assert isinstance(pk, Entity) and not isinstance(pk, Actor)
    assert hasattr(pk, "aabb") and hasattr(pk, "alive")
    assert not hasattr(pk, "vx")             # no physics


def test_instances_share_actor_api():
    for obj in (Player(0, 0), Small(0, 0, "turret"), Big(0, 0)):
        assert isinstance(obj, Actor) and isinstance(obj, Entity)
        for attr in ("aabb", "vx", "vy", "facing", "on_ground", "hp",
                     "dead", "death_done", "fired", "state"):
            assert hasattr(obj, attr), (type(obj).__name__, attr)


# ----------------------------------------------------------------- shared helpers
def test_approach_helper():
    assert approach(0.0, 10.0, 3.0) == 3.0
    assert approach(10.0, 0.0, 3.0) == 7.0
    assert approach(1.0, 0.0, 5.0) == 0.0     # never overshoots


def test_feet_aabb_anchors_by_feet():
    a = Actor.feet_aabb(100, 200, 30, 80)
    assert a.bottom == 200 and abs(a.centerx - 100) < 1e-6 and a.top == 120


def test_apply_gravity_and_collide_land():
    tm = Tilemap(FLOOR_MAP)               # floor top = 288
    e = Small(2 * S.TILE, 0, "turret")    # spawn high
    for _ in range(120):
        e.update(DT, tm, _Dummy(0))
    assert e.on_ground and abs(e.aabb.bottom - 288) < 1.0


def test_face_helper():
    e = Small(200, 100, "turret")
    e._face(_Dummy(10))                   # target to the left
    assert e.facing == "left"
    e._face(_Dummy(400))                  # target to the right
    assert e.facing == "right"


def test_tick_death_shared_sequence():
    tm = Tilemap(FLOOR_MAP)
    e = Small(2 * S.TILE, 0, "turret")
    for _ in range(120):
        e.update(DT, tm, _Dummy(0))
    e.take_damage(S.SMALL_HP)             # fatal
    assert e.dead and not e.death_done
    for _ in range(int(S.DEFEAT_HOLD / DT) + 4):
        e.update(DT, tm, _Dummy(0))
    assert e.death_done and not e.alive


# ----------------------------------------------------------------- player override
def test_player_sprite_image_crouch_override():
    from assets import build_player_animations
    p = Player(0, 0, build_player_animations())
    p.crouching = False
    full = p.sprite_image().get_height()
    p.crouching = True
    assert p.sprite_image().get_height() < full   # crouch squash still applied


class _Dummy:
    """A minimal target with an aabb (enemies read target.aabb.centerx)."""
    def __init__(self, cx):
        self.aabb = AABB(cx - 15, 200, 30, 80)


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
