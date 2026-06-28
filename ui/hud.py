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


def draw_health(surface, player):
    """Draw the player's HP as a row of pips (filled = remaining). Milestone 6."""
    x0, y0 = S.HUD_HEALTH_POS
    pw, ph = S.HUD_HEALTH_PIP
    gap = S.HUD_HEALTH_GAP
    max_hp = S.PLAYER_MAX_HP
    for i in range(max_hp):
        x = x0 + i * (pw + gap)
        color = S.HUD_HEALTH_FULL if i < player.hp else S.HUD_HEALTH_EMPTY
        pygame.draw.rect(surface, color, (x, y0, pw, ph))
        pygame.draw.rect(surface, S.HUD_HEALTH_BORDER, (x, y0, pw, ph), 1)


def draw_belly(surface, player):
    """Draw the belly indicator: BELLY_MAX slots, filled per stored pickup."""
    x0, y0 = S.HUD_BELLY_POS
    sw, sh = S.HUD_BELLY_SLOT
    gap = S.HUD_BELLY_GAP
    for i in range(S.BELLY_MAX):
        x = x0 + i * (sw + gap)
        color = S.HUD_BELLY_FULL if i < player.belly else S.HUD_BELLY_EMPTY
        pygame.draw.rect(surface, color, (x, y0, sw, sh))
        pygame.draw.rect(surface, S.HUD_BELLY_BORDER, (x, y0, sw, sh), 1)


def draw_heal_progress(surface, player):
    """Draw the digest progress bar while the player is healing (no-op otherwise)."""
    if not getattr(player, "healing", False):
        return
    x, y = S.HUD_HEAL_POS
    w, h = S.HUD_HEAL_SIZE
    pygame.draw.rect(surface, S.HUD_HEAL_BG, (x, y, w, h))
    fw = int(round(w * player.heal_fraction))
    if fw > 0:
        pygame.draw.rect(surface, S.HUD_HEAL_FILL, (x, y, fw, h))
    pygame.draw.rect(surface, S.HUD_HEAL_BORDER, (x, y, w, h), 1)


def draw_struggle(surface, player):
    """Draw the centered struggle bar while the player is swallowed (no-op else).
    The fill turns to the danger color when the bar is low."""
    if not getattr(player, "swallowed", False):
        return
    w, h = S.HUD_STRUGGLE_SIZE
    x = S.WIDTH // 2 - w // 2
    y = S.HUD_STRUGGLE_Y
    pygame.draw.rect(surface, S.HUD_STRUGGLE_BG, (x, y, w, h))
    frac = player.struggle_fraction
    color = S.HUD_STRUGGLE_LOW if frac <= S.HUD_STRUGGLE_LOW_FRAC else S.HUD_STRUGGLE_FILL
    fw = int(round(w * frac))
    if fw > 0:
        pygame.draw.rect(surface, color, (x, y, fw, h))
    pygame.draw.rect(surface, S.HUD_STRUGGLE_BORDER, (x, y, w, h), 2)
