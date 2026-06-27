# Build Progress

## Milestone 1 — Skeleton ✅ (2026-06-25)

Window (960×540, integer-scaled), fixed-timestep loop @60 Hz, state manager
(Menu/Play/GameOver), `settings.py` constants, and action-based input.

- **Run:** `python main.py` — Enter/Space goes Menu → Play; Esc quits.
- **Test:** `python -m pytest tests/ -q` (headless via SDL dummy) — 15/15 passing.
- Files: `settings.py`, `main.py`, `core/timestep.py`, `core/input.py`, `core/state.py`, `tests/test_milestone1.py`.

_Next: Milestone 2 — movement + collision + player animation._

## Milestone 2 — Movement + collision + animation ✅ (2026-06-25)

Tilemap + AABB physics (horizontal-then-vertical, sub-stepped so no tunneling),
player movement (run accel/friction, air control, variable-height jump with
coyote time + jump buffer, crouch), the sprite pipeline (slice 80×64, composite
Hair5 over Skin1, flip by facing), and an animation state machine
(idle/run/jump/fall). Player faces left by default and flips right.

- **Run:** `python main.py` — Enter to start; move/run/jump/crouch around the test level.
- **Test:** `python -m pytest tests/ -q` — 30/30 passing (M1 + M2).
- Files: `assets.py`, `core/animation.py`, `core/physics.py`, `world/tilemap.py`,
  `world/level1.py`, `entities/player.py`, `tests/test_milestone2.py`.

_Next: Milestone 3 — one-way (drop-through) platforms._

## Milestone 3 — One-way platforms + crouch squash ✅ (2026-06-26)

One-way platforms (`=` tiles): land on them from above, jump up through them
from below, and **Crouch + Jump** to drop through (0.30 s window). Physics now
classifies solid vs one-way tiles and reports `ground_oneway`. Also added a
visible **crouch squash** — the sprite scales to 60% height while crouching
(placeholder until real crouch art), so pressing Down now has a visible effect.

- **Run:** `python main.py` — brown bars = one-way ledges, gray = solid.
  Crouch+Jump on a brown ledge to drop through; Down to crouch (visible squash).
- **Test:** `python -m pytest tests/ -q` — 37/37 passing (M1+M2+M3).
- Files: `core/physics.py`, `world/tilemap.py`, `world/level1.py`,
  `entities/player.py`, `main.py`, `tests/test_milestone3.py`.

_Next: Milestone 4 — shooting (projectiles, directional fire, crouch shot, cooldown)._

## Milestone 4 — Shooting ✅ (2026-06-26)

Directional shooting with a fire cooldown. Pressing **J** fires a projectile:
horizontal in the facing direction, **up** while holding Aim-Up, and **down**
only while airborne (Aim-Down on the ground is the **low crouch shot** instead).
Shots travel straight (no gravity), pass through one-way ledges, and despawn on
a solid tile, off the level edge, or after a lifetime. Fire rate is gated by a
0.25 s cooldown. The **attack** sprite row doubles as the shoot pose (she raises
the flower) for ~0.25 s after each shot.

- **Run:** `python main.py` — Enter to start, **J** to shoot; hold Up to shoot
  up, jump then hold Down + J to shoot down, crouch (Down) + J for the low shot.
- **Test:** `python -m pytest tests/ -q` — 52/52 passing (M1+M2+M3+M4).
- Files: `settings.py`, `entities/projectile.py` (new), `entities/player.py`,
  `main.py`, `tests/test_milestone4.py` (new).

_Next: Milestone 5 — charge system (3 levels, growing hitboxes, HUD charge meter)._

## Milestone 5 — Charge system + HUD meter ✅ (2026-06-26)

Three-level charge shot. Tapping **J** fires a level-1 shot and starts charging;
holding builds the charge, and releasing fires a bigger, stronger shot once the
hold passes the level-2 (0.6 s) or level-3 (1.4 s) threshold. Higher levels deal
more damage (1 → 2 → 3) and use a larger projectile hitbox (8 → 14 → 20 px) with
a hotter color. A **HUD charge meter** (bottom-left) fills while charging and
marks the level-2/3 thresholds. The attack/shoot sprite pose now also holds
while charging.

- **Run:** `python main.py` — tap **J** for a quick shot; hold **J** to charge
  (watch the bottom-left meter) and release for a larger charged shot.
- **Test:** `python -m pytest tests/ -q` — 62/62 passing (M1–M5).
- Files: `settings.py`, `entities/projectile.py` (color/size/damage per level),
  `entities/player.py` (charge-and-fire), `ui/hud.py` (new), `ui/__init__.py`
  (new), `main.py`, `tests/test_milestone5.py` (new).

_Next: Milestone 6 — damage model (player HP, knockback, 1.5 s mercy i-frames with blink)._
