"""AABB physics: gravity-free movement + tile collision resolution.

A tiny float AABB (no pygame.Rect, for portability) and a swept-ish resolver
that moves horizontally then vertically, sub-stepping so fast movers can't
tunnel through thin tiles. Pure logic — unit-testable without a window.
"""

import math

import pygame


class AABB:
    __slots__ = ("x", "y", "w", "h")

    def __init__(self, x, y, w, h):
        self.x = float(x)
        self.y = float(y)
        self.w = float(w)
        self.h = float(h)

    # edges
    @property
    def left(self):
        return self.x

    @left.setter
    def left(self, v):
        self.x = v

    @property
    def right(self):
        return self.x + self.w

    @right.setter
    def right(self, v):
        self.x = v - self.w

    @property
    def top(self):
        return self.y

    @top.setter
    def top(self, v):
        self.y = v

    @property
    def bottom(self):
        return self.y + self.h

    @bottom.setter
    def bottom(self, v):
        self.y = v - self.h

    @property
    def centerx(self):
        return self.x + self.w / 2.0

    @property
    def height(self):
        return self.h

    @height.setter
    def height(self, v):
        self.h = v

    @property
    def width(self):
        return self.w


def _solid_tiles(aabb, tm):
    T = tm.tile
    x0 = int(math.floor(aabb.left / T))
    x1 = int(math.floor((aabb.right - 1e-6) / T))
    y0 = int(math.floor(aabb.top / T))
    y1 = int(math.floor((aabb.bottom - 1e-6) / T))
    out = []
    for ty in range(y0, y1 + 1):
        for tx in range(x0, x1 + 1):
            if tm.is_solid(tx, ty):
                out.append(pygame.Rect(tx * T, ty * T, T, T))
    return out


def move_and_collide(aabb, vx, vy, dt, tilemap):
    """Move the AABB by (vx,vy)*dt against solid tiles.

    Returns ``(flags, vx, vy)`` where flags has ground/ceiling/wall_l/wall_r and
    the returned velocities are zeroed on the axes that collided.
    """
    flags = {"ground": False, "ceiling": False, "wall_l": False, "wall_r": False}
    max_disp = max(abs(vx), abs(vy)) * dt
    steps = max(1, int(max_disp // (tilemap.tile * 0.5)) + 1)
    sdt = dt / steps

    for _ in range(steps):
        # horizontal
        aabb.x += vx * sdt
        tiles = _solid_tiles(aabb, tilemap)
        if tiles:
            if vx > 0:
                aabb.right = min(t.left for t in tiles)
                vx = 0.0
                flags["wall_r"] = True
            elif vx < 0:
                aabb.left = max(t.right for t in tiles)
                vx = 0.0
                flags["wall_l"] = True
        # vertical
        aabb.y += vy * sdt
        tiles = _solid_tiles(aabb, tilemap)
        if tiles:
            if vy > 0:
                aabb.bottom = min(t.top for t in tiles)
                vy = 0.0
                flags["ground"] = True
            elif vy < 0:
                aabb.top = max(t.bottom for t in tiles)
                vy = 0.0
                flags["ceiling"] = True

    return flags, vx, vy
