"""All tunable constants for Xynthra Platformer.

Milestone 1 introduces display/loop/input constants. Later milestones add
physics, combat, and balance values here — gameplay code must read from this
module rather than hard-coding numbers.
"""

import pygame

# --- Display / loop (Milestone 1) ---
WIDTH = 960
HEIGHT = 540
INTERNAL_SIZE = (WIDTH, HEIGHT)        # the game renders at this resolution
WINDOW_SCALE = 1                       # integer scale factor applied to the window
FPS = 60                               # render/tick cap
FIXED_DT = 1.0 / FPS                   # seconds per fixed update step
MAX_FRAME_TIME = 0.25                  # clamp frame_time to avoid the "spiral of death"
TILE = 32                              # pixels per tile (used from Milestone 2)

CAPTION = "Xynthra Platformer"

# Background colors per state (placeholder art for Milestone 1)
MENU_BG_COLOR = (18, 20, 28)
PLAY_BG_COLOR = (32, 36, 48)
GAMEOVER_BG_COLOR = (40, 16, 20)
MARKER_COLOR = (220, 200, 120)         # placeholder rectangle in Play

# --- Input: abstract actions -> physical keys (rebindable) ---
# Gameplay code queries actions ("jump", "left", ...), never raw keys.
ACTION_KEYS = {
    "left":     [pygame.K_LEFT, pygame.K_a],
    "right":    [pygame.K_RIGHT, pygame.K_d],
    "up":       [pygame.K_UP],
    "down":     [pygame.K_DOWN],
    "jump":     [pygame.K_SPACE],
    "shoot":    [pygame.K_j],
    "heal":     [pygame.K_h],
    "struggle": [pygame.K_SPACE],          # only meaningful while swallowed
    "confirm":  [pygame.K_RETURN, pygame.K_SPACE],
    "quit":     [pygame.K_ESCAPE],
}

# --- Physics / movement (Milestone 2) ---
RUN_SPEED = 220.0
GROUND_ACCEL = 1800.0
GROUND_FRICTION = 2200.0
AIR_ACCEL = 1440.0                 # ~80% of ground accel
GRAVITY = 2000.0
MAX_FALL = 900.0
JUMP_VELOCITY = -640.0
JUMP_CUT_VELOCITY = -250.0         # short-hop cap applied on early jump release
COYOTE_TIME = 0.10
JUMP_BUFFER = 0.12
CROUCH_HEIGHT_FACTOR = 0.6         # crouch hitbox = 60% of standing height
RUN_ANIM_SPEED = 10.0              # |vx| above this plays the run animation

# Player hitbox (sprite is drawn larger and anchored by the feet)
PLAYER_W = 28
PLAYER_H = 52

# --- Player sprite sheets (Milestone 2 placeholders) ---
import os as _os
BASE_DIR = _os.path.dirname(_os.path.abspath(__file__))
GANDALF_DIR = _os.path.join(BASE_DIR, "Graphics", "GandalfHardcore")
PLAYER_BODY_SHEET = _os.path.join(GANDALF_DIR, "Character_skin_colors", "Female_Skin1.png")
PLAYER_HAIR_SHEET = _os.path.join(GANDALF_DIR, "Female_Hair", "Female_Hair5.png")
SPRITE_FRAME_W = 80
SPRITE_FRAME_H = 64
DEFAULT_FACING = "left"            # source art faces left; flip horizontally for right
