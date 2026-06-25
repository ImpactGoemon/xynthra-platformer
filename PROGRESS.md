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
