"""A small test level for movement/collision (Milestones 2-3).

'#'=solid, '='=one-way platform (stand from above; jump up through; crouch+jump
to drop through), '.'=empty, 'P'=spawn (treated as empty).
"""

from world.tilemap import Tilemap

TEST_LEVEL = [
    "##############################",
    "#............................#",
    "#............................#",
    "#......P.....................#",
    "#....======..................#",
    "#............................#",
    "#............########........#",
    "#......======................#",
    "#............................#",
    "#.................======......#",
    "#............................#",
    "#............................#",
    "##############################",
]


def build_level():
    rows = [row.replace("P", ".") for row in TEST_LEVEL]
    tm = Tilemap(rows)
    spawn = (1 * tm.tile, 1 * tm.tile)
    for ty, row in enumerate(TEST_LEVEL):
        tx = row.find("P")
        if tx != -1:
            spawn = (tx * tm.tile, ty * tm.tile)
            break
    return tm, spawn
