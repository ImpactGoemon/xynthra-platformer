"""A small test level for Milestone 2 (movement/collision sandbox).

Returns a Tilemap and a spawn position (pixel coords of the player's top-left).
'#'=solid, '.'=empty, 'P'=spawn marker (treated as empty).
"""

from world.tilemap import Tilemap

TEST_LEVEL = [
    "##############################",
    "#............................#",
    "#............................#",
    "#......P.....................#",
    "#...........####.............#",
    "#............................#",
    "#.................####.......#",
    "#......####..................#",
    "#............................#",
    "#..............#####.........#",
    "#............................#",
    "#............................#",
    "##############################",
]


def build_level():
    rows = [row.replace("P", ".") for row in TEST_LEVEL]
    tm = Tilemap(rows)
    # spawn at the 'P' marker
    spawn = (1 * tm.tile, 1 * tm.tile)
    for ty, row in enumerate(TEST_LEVEL):
        tx = row.find("P")
        if tx != -1:
            spawn = (tx * tm.tile, ty * tm.tile)
            break
    return tm, spawn
