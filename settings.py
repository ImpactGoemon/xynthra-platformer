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

# --- Damage model (Milestone 6) ---
PLAYER_MAX_HP = 10
KNOCKBACK_VX = 200.0               # horizontal knockback speed, away from the source
KNOCKBACK_VY = -250.0              # upward pop on a hit (negative = up)
KNOCKBACK_CONTROL_LOCK = 0.20      # seconds input is ignored after a hit
IFRAME_TIME = 1.5                  # mercy invincibility after taking a hit
BLINK_INTERVAL = 0.12              # sprite blink toggle period during i-frames

# HUD health pips
HUD_HEALTH_POS = (16, 16)          # top-left of the health row
HUD_HEALTH_PIP = (16, 16)          # pip width, height
HUD_HEALTH_GAP = 4                 # gap between pips
HUD_HEALTH_FULL = (228, 72, 72)
HUD_HEALTH_EMPTY = (60, 40, 44)
HUD_HEALTH_BORDER = (20, 16, 18)

# --- Test hazard: enemy projectile (Milestone 6) ---
ENEMY_PROJECTILE_SPEED = 360.0     # px/s, travels left toward the player
ENEMY_PROJECTILE_DAMAGE = 1
ENEMY_PROJECTILE_SIZE = 12
ENEMY_PROJECTILE_COLOR = (255, 90, 90)
ENEMY_FIRE_INTERVAL = 2.0          # seconds between test-hazard shots
ENEMY_SPAWN_DIST = 520.0           # how far to the player's right a shot spawns

# --- Death sequence (Milestone 6 tweak) ---
# The defeat row is 10 frames @ 10 fps == ~1.0 s; hold the Play state on the
# death animation this long before switching to the Game Over screen.
DEFEAT_HOLD = 1.0

# --- Healing / belly + pickups (Milestone 7) ---
BELLY_MAX = 3                      # max stored healing objects (shrunken ladies)
HEAL_HOLD = 4.0                    # seconds to hold Heal (idle) to digest one
HEAL_AMOUNT = 3                    # HP restored per digested pickup
HEAL_MOVE_EPS = RUN_ANIM_SPEED     # |vx| below this still counts as "idle"

# Pickup sprite: Schoolgirl Girl_1 idle, scaled to a fraction of Xynthra's size
PICKUP_SHEET = _os.path.join(BASE_DIR, "Graphics", "Schoolgirls", "Girl_1", "Idle.png")
PICKUP_FRAME_W = 128               # idle sheet is 128x128 cells (9 frames)
PICKUP_FRAME_H = 128
PICKUP_SIZE_FRACTION = 0.25        # pickup drawn at 1/4 of Xynthra's visible height
PICKUP_FALLBACK_SIZE = (10, 22)    # colored-rect size if the sheet can't load
PICKUP_FALLBACK_COLOR = (235, 170, 200)

# HUD belly indicator (stored-count slots) + heal progress bar
HUD_BELLY_POS = (16, 40)           # below the health row
HUD_BELLY_SLOT = (16, 16)
HUD_BELLY_GAP = 4
HUD_BELLY_FULL = (150, 110, 200)
HUD_BELLY_EMPTY = (44, 38, 56)
HUD_BELLY_BORDER = (20, 16, 24)
HUD_HEAL_POS = (16, 64)
HUD_HEAL_SIZE = (120, 8)
HUD_HEAL_BG = (24, 26, 34)
HUD_HEAL_FILL = (120, 220, 140)
HUD_HEAL_BORDER = (200, 200, 210)

# --- Small enemy (Milestone 8) ---
# Enemy sprite: Skin4 body + Hair3 hair + the flower (composited like Xynthra).
ENEMY_SKIN_SHEET = _os.path.join(GANDALF_DIR, "Character_skin_colors", "Female_Skin4.png")
ENEMY_HAIR_SHEET = _os.path.join(GANDALF_DIR, "Female_Hair", "Female_Hair3.png")
ENEMY_HAND_SHEET = PLAYER_HAND_SHEET   # same flower

SMALL_HP = 3
SMALL_W = 30                       # ~1x Xynthra hitbox
SMALL_H = 72
SMALL_CONTACT_DAMAGE = 1           # normal hit -> knockback + i-frames
SMALL_PROJECTILE_DAMAGE = 1
SMALL_PROJECTILE_SPEED = 300.0
SMALL_PROJECTILE_SIZE = 10
SMALL_PROJECTILE_COLOR = (255, 140, 60)
SMALL_TURRET_INTERVAL = 2.0        # turret shoots horizontally every ~2 s
SMALL_JUMPER_INTERVAL = 2.5        # jumper jumps every ~2.5 s, fires at the apex
SMALL_JUMP_VELOCITY = -560.0

# --- Big enemy (Milestone 9) ---
# Big art: Skin2 body + Hair2 hair + the flower, composited like Xynthra but
# drawn at a larger scale so it reads as the bigger (~1.85x) enemy.
BIG_SKIN_SHEET = _os.path.join(GANDALF_DIR, "Character_skin_colors", "Female_Skin2.png")
BIG_HAIR_SHEET = _os.path.join(GANDALF_DIR, "Female_Hair", "Female_Hair2.png")
BIG_HAND_SHEET = PLAYER_HAND_SHEET     # same flower
BIG_SPRITE_SCALE = 4                    # bigger than the player/Small scale (2)

BIG_HP = 5
BIG_W = 56                         # ~1.85x Xynthra's 30 px hitbox width
BIG_H = 133                        # ~1.85x Xynthra's 72/80 px height
BIG_CONTACT_DAMAGE = 0             # contact swallows instead of dealing a normal hit
BIG_SPEED = 180.0                  # pursuit run speed (px/s)
BIG_ACCEL = 1600.0                 # how quickly it reaches pursuit speed / stops
BIG_DETECT_RADIUS = 400.0          # detects the player within this distance, then pursues
BIG_JUMP_VELOCITY = -640.0         # jump impulse when blocked or the player is above
BIG_JUMP_COOLDOWN = 0.8            # min seconds between pursuit jumps
BIG_PLAYER_ABOVE_MARGIN = 8.0      # player must be this far above to trigger a reach jump

# --- Swallowed overlay (Milestone 9 placeholder; struggle minigame is M10) ---
SWALLOW_MSG = "Xynthra is trying to escape!"
SWALLOW_MSG_SIZE = 46
SWALLOW_MSG_COLOR = (240, 210, 150)
SWALLOW_BANNER_COLOR = (12, 10, 16, 150)   # RGBA, semi-transparent banner
SWALLOW_BANNER_H = 64                       # banner height in internal px

# --- Swallow / struggle minigame (Milestone 10) ---
STRUGGLE_START = 0.50              # struggle bar starts half full
STRUGGLE_REFILL = 0.08            # +8% per Struggle (Space) press
STRUGGLE_DRAIN_TIME_BIG = 4.0     # seconds for a full bar to empty (Big)
STRUGGLE_DRAIN_TIME_JUGG = 2.5    # Juggernaut drains faster (M11)
STRUGGLE_DMG = 1                  # internal damage per tick while swallowed
STRUGGLE_DMG_INTERVAL = 2.5       # seconds between internal damage ticks
ENEMY_STUN_TIME = 3.0             # on escape, the enemy is stunned this long

# HUD struggle bar (centered, drawn while swallowed)
HUD_STRUGGLE_SIZE = (260, 18)
HUD_STRUGGLE_Y = 300              # below the swallow message
HUD_STRUGGLE_BG = (28, 22, 26)
HUD_STRUGGLE_FILL = (120, 200, 235)
HUD_STRUGGLE_LOW = (235, 120, 90)  # fill color when the bar is low (danger)
HUD_STRUGGLE_LOW_FRAC = 0.30
HUD_STRUGGLE_BORDER = (220, 220, 230)
HUD_STRUGGLE_HINT = "Mash SPACE to escape!"
HUD_STRUGGLE_HINT_SIZE = 26
HUD_STRUGGLE_HINT_COLOR = (210, 210, 220)

# --- Digestion sequence (Milestone 10 polish) ---
# When the struggle minigame is lost, play a brief digestion placeholder (the
# enemy "digesting" her + a message) before handing off to Game Over.
DIGEST_HOLD = 1.6                  # seconds the digestion placeholder holds
DIGEST_MSG = "Xynthra was digested!"
DIGEST_MSG_SIZE = 50
DIGEST_MSG_COLOR = (235, 150, 170)
DIGEST_BANNER_COLOR = (16, 8, 12, 170)  # RGBA banner behind the message
