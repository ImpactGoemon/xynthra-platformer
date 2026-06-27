"""AABB physics: movement + tile collision (solid + one-way platforms).

Solid tiles block all sides. One-way platforms block only when landing from
above; you pass up through them and can drop through. Drop-through ignores ONLY
platforms at/above ``drop_through_top`` (the ledge you left), so the next ledge
below still catches you. Horizontal then vertical, sub-stepped against tunneling.
"""

import math

import pygame


class AABB:
    __slots__ = ("x", "y", "w", "h")

    def __init__(self, x, y, w, h):
        self.x = float(x); self.y = float(y); self.w = float(w); self.h = float(h)

    @property
    def left(self): return self.x
    @left.setter
    def left(self, v): self.x = v
    @property
    def right(self): return self.x + self.w
    @right.setter
    def right(self, v): self.x = v - self.w
    @property
    def top(self): return self.y
    @top.setter
    def top(self, v): self.y = v
    @property
    def bottom(self): return self.y + self.h
    @bottom.setter
    def bottom(self, v): self.y = v - self.h
    @property
    def centerx(self): return self.x + self.w / 2.0
    @property
    def height(self): return self.h
    @height.setter
    def height(self, v): self.h = v
    @property
    def width(self): return self.w


def _overlapping(aabb, tm):
    T = tm.tile
    x0 = int(math.floor(aabb.left / T)); x1 = int(math.floor((aabb.right - 1e-6) / T))
    y0 = int(math.floor(aabb.top / T));  y1 = int(math.floor((aabb.bottom - 1e-6) / T))
    out = []
    for ty in range(y0, y1 + 1):
        for tx in range(x0, x1 + 1):
            if tm.is_solid(tx, ty):
                out.append((pygame.Rect(tx * T, ty * T, T, T), "solid"))
            elif tm.is_oneway(tx, ty):
                out.append((pygame.Rect(tx * T, ty * T, T, T), "oneway"))
    return out


def move_and_collide(aabb, vx, vy, dt, tilemap, drop_through_top=None):
    """Move the AABB against tiles.

    ``drop_through_top``: if not None, one-way platforms whose top is at or above
    this y are ignored (the single ledge being dropped through). Lower ledges
    still catch the player.

    Returns ``(flags, vx, vy)``; flags has ground/ceiling/wall_l/wall_r and
    ground_oneway (True when only a one-way platform supports her).
    """
    flags = {"ground": False, "ceiling": False, "wall_l": False,
             "wall_r": False, "ground_oneway": False}
    max_disp = max(abs(vx), abs(vy)) * dt
    steps = max(1, int(max_disp // (tilemap.tile * 0.5)) + 1)
    sdt = dt / steps

    for _ in range(steps):
        aabb.x += vx * sdt
        solids = [t for t, k in _overlapping(aabb, tilemap) if k == "solid"]
        if solids:
            if vx > 0:
                aabb.right = min(t.left for t in solids); vx = 0.0; flags["wall_r"] = True
            elif vx < 0:
                aabb.left = max(t.right for t in solids); vx = 0.0; flags["wall_l"] = True

        prev_bottom = aabb.bottom
        aabb.y += vy * sdt
        over = _overlapping(aabb, tilemap)
        if vy > 0:
            blockers = []
            for t, k in over:
                if k == "solid":
                    blockers.append((t, k))
                elif k == "oneway":
                    dropping = (drop_through_top is not None
                                and t.top <= drop_through_top + 0.5)
                    if not dropping and prev_bottom <= t.top + 0.5:
                        blockers.append((t, k))
            if blockers:
                aabb.bottom = min(t.top for t, _ in blockers); vy = 0.0
                flags["ground"] = True
                flags["ground_oneway"] = all(k == "oneway" for _, k in blockers)
        elif vy < 0:
            solids = [t for t, k in over if k == "solid"]
            if solids:
                aabb.top = max(t.bottom for t in solids); vy = 0.0; flags["ceiling"] = True

    return flags, vx, vy
