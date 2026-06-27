"""Projectile — a fired shot that travels straight until it hits a wall.

Milestone 4: horizontal/vertical bullets only (no gravity). A projectile dies
when it overlaps a solid tile, leaves the level bounds, or outlives its lifetime.
One-way platforms do NOT block shots (you can fire through ledges). Damage, hitbox
size, and color are passed in so the charge system (Milestone 5) can grow them.
"""

import math

import settings as S
from core.physics import AABB


class Projectile:
    def __init__(self, cx, cy, dx, dy, speed=None, damage=None, size=None,
                 color=None, owner="player"):
        size = S.PROJECTILE_SIZE if size is None else size
        speed = S.PROJECTILE_SPEED if speed is None else speed
        self.size = size
        self.damage = S.PROJECTILE_DAMAGE if damage is None else damage
        self.color = S.PROJECTILE_COLOR if color is None else color
        self.owner = owner
        # normalize direction so diagonal speeds (unused now) stay consistent
        mag = math.hypot(dx, dy) or 1.0
        self.vx = (dx / mag) * speed
        self.vy = (dy / mag) * speed
        # centered hitbox
        self.aabb = AABB(cx - size / 2.0, cy - size / 2.0, size, size)
        self.alive = True
        self.age = 0.0

    @property
    def centerx(self):
        return self.aabb.x + self.size / 2.0

    @property
    def centery(self):
        return self.aabb.y + self.size / 2.0

    def _hits_solid(self, tilemap):
        T = tilemap.tile
        a = self.aabb
        x0 = int(math.floor(a.left / T)); x1 = int(math.floor((a.right - 1e-6) / T))
        y0 = int(math.floor(a.top / T));  y1 = int(math.floor((a.bottom - 1e-6) / T))
        for ty in range(y0, y1 + 1):
            for tx in range(x0, x1 + 1):
                if tilemap.is_solid(tx, ty):
                    return True
        return False

    def update(self, dt, tilemap):
        if not self.alive:
            return
        self.age += dt
        self.aabb.x += self.vx * dt
        self.aabb.y += self.vy * dt

        if self.age >= S.PROJECTILE_LIFETIME:
            self.alive = False
            return
        if (self.aabb.right < 0 or self.aabb.left > tilemap.pixel_width
                or self.aabb.bottom < 0 or self.aabb.top > tilemap.pixel_height):
            self.alive = False
            return
        if self._hits_solid(tilemap):
            self.alive = False

    def draw(self, surface, offset=(0, 0)):
        import pygame
        ox, oy = offset
        pygame.draw.rect(
            surface, self.color,
            (round(self.aabb.x - ox), round(self.aabb.y - oy),
             self.size, self.size),
        )
