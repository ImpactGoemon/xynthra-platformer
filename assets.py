"""Sprite-sheet table + loader for the player placeholder art.

The player is the GandalfHardcore Skin1 body with Hair5 composited on top
(hair drawn over body, same cell). Sheet is 7 rows x 64px, 80px columns.
See CLAUDE.md "Placeholder Assets". Source faces LEFT; right-facing frames are
horizontally flipped copies.
"""

import pygame

import settings

# name -> (row, frame_count, fps, loop)
PLAYER_ANIMATIONS = {
    "idle":   (0, 5, 8, True),
    "walk":   (1, 8, 10, True),
    "run":    (2, 8, 12, True),
    "jump":   (3, 4, 10, False),
    "fall":   (4, 4, 10, False),
    "attack": (5, 6, 14, False),
    "defeat": (6, 10, 10, False),
}


def _load(path):
    img = pygame.image.load(path)
    try:
        return img.convert_alpha()  # needs a display; falls back when headless
    except pygame.error:
        return img


def _build_character_animations(body_path, hair_path, hand_path=None, scale=None):
    """Composite body + hair (+ optional held item), slice cells, and cache
    left + right-facing scaled frames for every animation in PLAYER_ANIMATIONS.
    Source art faces left; right-facing frames are horizontal flips. ``scale``
    overrides the default SPRITE_SCALE (used by the larger Big enemy)."""
    fw, fh = settings.SPRITE_FRAME_W, settings.SPRITE_FRAME_H
    sheet = _load(body_path).copy()
    sheet.blit(_load(hair_path), (0, 0))  # hair layer over body
    if hand_path:
        try:
            sheet.blit(_load(hand_path), (0, 0))  # held-item layer (the flower)
        except Exception as exc:  # noqa: BLE001 - missing item sheet is non-fatal
            print(f"[assets] hand sheet not loaded: {exc}")

    anims = {}
    if scale is None:
        scale = getattr(settings, "SPRITE_SCALE", 1)
    for name, (row, frames, fps, loop) in PLAYER_ANIMATIONS.items():
        left = []
        for i in range(frames):
            rect = pygame.Rect(i * fw, row * fh, fw, fh)
            cell = sheet.subsurface(rect).copy()
            if scale != 1:
                # transform.scale = fast nearest scaling (crisp pixels, no blur)
                cell = pygame.transform.scale(cell, (fw * scale, fh * scale))
            left.append(cell)
        right = [pygame.transform.flip(c, True, False) for c in left]
        anims[name] = {"left": left, "right": right, "fps": fps,
                       "loop": loop, "frames": frames}
    return anims


def build_player_animations():
    """Xynthra: Skin1 body + Hair5 hair + the flower."""
    return _build_character_animations(
        settings.PLAYER_BODY_SHEET, settings.PLAYER_HAIR_SHEET,
        getattr(settings, "PLAYER_HAND_SHEET", None))


def build_enemy_animations():
    """Small enemy: Skin4 body + Hair3 hair + the flower."""
    return _build_character_animations(
        settings.ENEMY_SKIN_SHEET, settings.ENEMY_HAIR_SHEET,
        getattr(settings, "ENEMY_HAND_SHEET", None))


def build_big_animations():
    """Big enemy: Skin2 body + Hair2 hair + the flower, drawn at a larger scale."""
    return _build_character_animations(
        settings.BIG_SKIN_SHEET, settings.BIG_HAIR_SHEET,
        getattr(settings, "BIG_HAND_SHEET", None),
        scale=getattr(settings, "BIG_SPRITE_SCALE", None))


def _content_bounds(surface):
    """Tight bounding rect of the non-transparent pixels in a surface."""
    mask = pygame.mask.from_surface(surface)
    rects = mask.get_bounding_rects()
    if not rects:
        return surface.get_rect()
    r = rects[0]
    for rr in rects[1:]:
        r = r.union(rr)
    return r


def _xynthra_idle_height():
    """Drawn (scaled) content height of Xynthra's idle frame, used to size pickups."""
    anims = build_player_animations()
    return _content_bounds(anims["idle"]["left"][0]).height


def build_pickup_image():
    """Schoolgirl Girl_1 idle (frame 0), tight-cropped and scaled to ~1/4 of
    Xynthra's visible height. Returns a Surface, or None if the sheet is absent."""
    try:
        sheet = _load(settings.PICKUP_SHEET)
    except Exception as exc:  # noqa: BLE001 - missing pickup art is non-fatal
        print(f"[assets] pickup sheet not loaded: {exc}")
        return None
    fw, fh = settings.PICKUP_FRAME_W, settings.PICKUP_FRAME_H
    frame = sheet.subsurface(pygame.Rect(0, 0, fw, fh)).copy()
    tight = frame.subsurface(_content_bounds(frame)).copy()
    target_h = max(1, round(_xynthra_idle_height() * settings.PICKUP_SIZE_FRACTION))
    scale = target_h / tight.get_height()
    w = max(1, round(tight.get_width() * scale))
    return pygame.transform.scale(tight, (w, target_h))
