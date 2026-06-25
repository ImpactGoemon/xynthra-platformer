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


def build_player_animations():
    """Slice cells, composite hair over body, cache left + right-facing frames."""
    fw, fh = settings.SPRITE_FRAME_W, settings.SPRITE_FRAME_H
    body = _load(settings.PLAYER_BODY_SHEET)
    hair = _load(settings.PLAYER_HAIR_SHEET)

    sheet = body.copy()
    sheet.blit(hair, (0, 0))  # hair layer over body

    anims = {}
    for name, (row, frames, fps, loop) in PLAYER_ANIMATIONS.items():
        left = []
        for i in range(frames):
            rect = pygame.Rect(i * fw, row * fh, fw, fh)
            left.append(sheet.subsurface(rect).copy())
        right = [pygame.transform.flip(c, True, False) for c in left]
        # "left" is the source/default facing; "right" is the flipped copy.
        anims[name] = {
            "left": left,
            "right": right,
            "fps": fps,
            "loop": loop,
            "frames": frames,
        }
    return anims
