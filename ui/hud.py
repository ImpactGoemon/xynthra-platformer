"""HUD overlays. Milestone 5: a charge meter shown while the player charges a
shot. The bar fills from 0 to the level-3 hold time; tick marks show where the
level-2 and level-3 thresholds sit, and the fill is tinted by the current level.
"""

import pygame

import settings as S


def draw_charge_meter(surface, player):
    """Draw the charge meter while the player is charging. No-op otherwise."""
    if not getattr(player, "charging", False):
        return

    x, y = S.HUD_CHARGE_POS
    w, h = S.HUD_CHARGE_SIZE
    full = max(1e-6, S.CHARGE_L3_TIME)
    frac = min(player.charge_time / full, 1.0)
    level = player.charge_level

    # background + fill
    pygame.draw.rect(surface, S.HUD_CHARGE_BG, (x, y, w, h))
    fill_w = int(round(w * frac))
    if fill_w > 0:
        pygame.draw.rect(surface, S.CHARGE_COLORS[level], (x, y, fill_w, h))

    # threshold ticks for level 2 and level 3
    for t in (S.CHARGE_L2_TIME, S.CHARGE_L3_TIME):
        tx = x + int(round(w * min(t / full, 1.0)))
        pygame.draw.line(surface, S.HUD_CHARGE_TICK, (tx, y), (tx, y + h), 1)

    # border on top
    pygame.draw.rect(surface, S.HUD_CHARGE_BORDER, (x, y, w, h), 1)
