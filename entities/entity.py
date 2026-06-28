"""Entity — the common root for everything that lives in the level and is drawn.

An Entity just owns an axis-aligned bounding box (``aabb``) and an ``alive`` flag,
plus a ``draw(surface, offset)`` contract. Humanoid characters (Xynthra, enemies)
extend ``Actor``; static collectibles (pickups) and projectiles can be plain
Entities. This keeps the shared *behaviour* in Actor without forcing physics or
health onto things that do not need them.
"""


class Entity:
    def __init__(self, aabb):
        self.aabb = aabb
        self.alive = True

    def draw(self, surface, offset=(0, 0)):  # pragma: no cover - overridden
        raise NotImplementedError
