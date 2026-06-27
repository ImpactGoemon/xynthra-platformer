"""Tilemap: a grid of characters with collision flags.

'#' = solid tile (blocks all sides). '=' = one-way platform (solid from above
only; pass up through; drop through with crouch+jump). '.' = empty.
Out-of-bounds is empty so the player can fall off the edges.
"""

import pygame

import settings


class Tilemap:
    SOLID = "#"
    ONEWAY = "="

    def __init__(self, rows, tile=None):
        self.tile = settings.TILE if tile is None else tile
        self.rows = [list(r) for r in rows]
        self.h = len(self.rows)
        self.w = max((len(r) for r in self.rows), default=0)

    def char(self, tx, ty):
        if ty < 0 or ty >= self.h:
            return "."
        row = self.rows[ty]
        if tx < 0 or tx >= len(row):
            return "."
        return row[tx]

    def is_solid(self, tx, ty):
        return self.char(tx, ty) == self.SOLID

    def is_oneway(self, tx, ty):
        return self.char(tx, ty) == self.ONEWAY

    @property
    def pixel_width(self):
        return self.w * self.tile

    @property
    def pixel_height(self):
        return self.h * self.tile

    def _rects(self, kind):
        for ty in range(self.h):
            row = self.rows[ty]
            for tx in range(len(row)):
                if row[tx] == kind:
                    yield pygame.Rect(tx * self.tile, ty * self.tile, self.tile, self.tile)

    def solid_rects(self):
        yield from self._rects(self.SOLID)

    def oneway_rects(self):
        yield from self._rects(self.ONEWAY)
