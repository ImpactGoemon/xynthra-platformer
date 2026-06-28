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


# Healing pickups (shrunken ladies), anchored by feet (x, y) in pixels.
# Placed on lower platforms so collecting them means leaving the highest one.
PICKUP_SPAWNS = [
    (304, 224),   # on the row-7 one-way ledge
    (528, 192),   # on the row-6 solid block
    (656, 288),   # on the row-9 one-way ledge
]


# Small enemies: (x_feet, y_feet, variant) on the floor (top = 384).
SMALL_SPAWNS = [
    (430, 384, "jumper"),
    (860, 384, "turret"),
]


# Big enemies: (x_feet, y_feet) on the floor (top = 384). Placed far from the
# player spawn so it stays idle until she walks into its detection radius.
BIG_SPAWNS = [
    (720, 384),
]
