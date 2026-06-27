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
WINDOW_SCALE = 3                       # MAX integer window scale (auto-fit picks <= this)
FULLSCREEN = False                     # start in fullscreen (toggle in-game with F11)
WINDOW_TASKBAR_MARGIN = 96             # px reserved for title bar + taskbar when fitting
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
    "fullscreen": [pygame.K_F11],
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
PLAYER_W = 30
PLAYER_H = 80

# --- Player sprite sheets (Milestone 2 placeholders) ---
import os as _os, sys as _sys
# When frozen by PyInstaller, data files live under sys._MEIPASS; otherwise
# next to this file. This lets the .exe find Graphics/ the same as source.
BASE_DIR = getattr(_sys, "_MEIPASS", _os.path.dirname(_os.path.abspath(__file__)))
GANDALF_DIR = _os.path.join(BASE_DIR, "Graphics", "GandalfHardcore")
PLAYER_BODY_SHEET = _os.path.join(GANDALF_DIR, "Character_skin_colors", "Female_Skin1.png")
PLAYER_HAIR_SHEET = _os.path.join(GANDALF_DIR, "Female_Hair", "Female_Hair5.png")
PLAYER_HAND_SHEET = _os.path.join(GANDALF_DIR, "Female_Hand", "Flower.png")  # held item (faces left)
SPRITE_FRAME_W = 80
SPRITE_FRAME_H = 64
SPRITE_SCALE = 2                   # integer nearest-neighbor upscale (crisp, no deform)
DEFAULT_FACING = "left"            # source art faces left; flip horizontally for right

# --- One-way platforms (Milestone 3) ---
DROP_THROUGH_TIME = 0.30           # crouch+jump ignores one-way platforms this long

# --- Shooting (Milestone 4) ---
PROJECTILE_SPEED = 480.0           # px/s for a fired shot
FIRE_COOLDOWN = 0.25               # seconds between shots
PROJECTILE_DAMAGE = 1              # uncharged shot damage (charge levels come in M5)
PROJECTILE_SIZE = 8                # square hitbox side in px (L1; grows with charge in M5)
PROJECTILE_LIFETIME = 2.0          # seconds before a stray shot despawns
PROJECTILE_COLOR = (250, 230, 120) # placeholder bullet color
SHOOT_POSE_TIME = FIRE_COOLDOWN    # how long the attack/shoot animation holds after firing
# Muzzle offsets as fractions of the player's current hitbox height (from the top):
MUZZLE_Y_STAND = 0.40              # horizontal shot height while standing
MUZZLE_Y_CROUCH = 0.70            # low horizontal shot while crouching

# --- Charge shot (Milestone 5) ---
# Level 1 = uncharged tap; held longer reaches level 2 then 3. Bigger level =
# more damage and a larger projectile hitbox.
CHARGE_L2_TIME = 0.6               # seconds held to reach level 2
CHARGE_L3_TIME = 1.4               # seconds held to reach level 3
CHARGE_DAMAGE = {1: 1, 2: 2, 3: 3}
CHARGE_SIZE = {1: 8, 2: 14, 3: 20} # square hitbox side in px per level
CHARGE_COLORS = {1: (250, 230, 120), 2: (255, 180, 80), 3: (255, 110, 90)}

# HUD charge meter (drawn while charging)
HUD_CHARGE_POS = (16, 506)         # top-left of the meter (bottom-left of screen)
HUD_CHARGE_SIZE = (200, 14)        # width, height in internal pixels
HUD_CHARGE_BG = (24, 26, 34)
HUD_CHARGE_BORDER = (200, 200, 210)
HUD_CHARGE_TICK = (235, 235, 245)
