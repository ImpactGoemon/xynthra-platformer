# Xynthra Platformer — Project Guide

This file is the source of truth for Claude Code working in this repo. It is derived from `XYNTHRA_PLATFORMER_Design_Plan.docx`. Build the game **milestone by milestone** (see "Build Roadmap"); do not jump ahead. Confirm each milestone runs before starting the next.

> Content note: the design has an adult/fetish theme (soft vore — swallowing/digestion). All characters are adult and fictional. Treat these purely as game systems: a heal-resource mechanic and a lose/escape state. The bundled placeholder character is a generic sprite, not final art — no rendering of explicit content.

---

## What we are building

A 2D **platformer-shooter**, single-level **demo / proof of concept**, tuned to be **easy**. Custom engine **from scratch in Python with pygame** (no game-engine frameworks). Win by reaching the level exit; unlimited retries from level start.

## Tech baseline (fixed)

- Python 3 + `pygame` only for the engine. Standard library otherwise.
- Internal resolution **960×540** (16:9), integer-scaled to the window.
- **60 FPS**, **fixed timestep** for physics/update; render decoupled.
- Tile size **32×32 px**. Units: pixels and seconds (velocity px/s, accel px/s²). Origin top-left, +Y down.
- **Placeholder art**: the player (Xynthra) uses the bundled sprite sheets in `Graphics/GandalfHardcore/` — see **Placeholder Assets** below. States the sheet doesn't cover, and all enemies/pickups/UI, fall back to simple colored shapes or reused frames for now.
- **Audio**: build the hooks/system, but no audio files yet (stub calls).

## How to work in this repo

- Build **one system per milestone**; keep each runnable. Don't implement future milestones early.
- Prefer small, testable modules with clear responsibilities (see Project Structure).
- All tunable numbers live in one place (`settings.py`/constants) so they're easy to adjust.
- Input is mapped to **abstract actions**, never raw keys in gameplay code (so rebinding is trivial).
- Sprite-sheet definitions (rows, frame counts, fps) live in one place too (e.g. `assets.py`), not scattered in gameplay code.
- When a bug appears, find the **root cause before fixing** (systematic-debugging): reproduce, trace data flow, one hypothesis at a time.
- After each milestone, do a quick manual smoke test and note how to run it.

## Suggested project structure

```
Xynthra_Plat/
  main.py            # entry point: window, fixed-timestep loop, state manager
  settings.py        # all tunable constants (resolution, physics, balance)
  assets.py          # sprite-sheet table: path, row->animation, frame counts, fps
  core/
    input.py         # key -> action mapping, action state
    physics.py       # AABB collision, gravity, one-way platforms, knockback
    camera.py        # follow + look-ahead + smoothing, clamped to level bounds
    animation.py     # frame/state animation driver; loads & slices sprite sheets
    state.py         # scene/state manager (Menu, Play, GameOver)
  entities/
    player.py        # Xynthra: movement, shooting, health, belly, struggle
    projectile.py
    enemy.py         # base + Small / Big / Juggernaut
    pickup.py        # healing object (shrunken lady)
  world/
    tilemap.py       # level data, layers, collision flags, exit trigger
    level1.py        # the demo level layout
  ui/
    hud.py           # health, belly state, charge meter, struggle bar, game over
  audio/
    audio.py         # SFX/music hooks (stubbed)
  Graphics/          # bundled placeholder art (already present)
```

(Adjust if you have a better idea, but keep the separation of concerns.)

## Run / test

- Run the game: `python main.py`
- Keep a headless-friendly structure where reasonable so logic can be unit-tested without a window.

---

## Placeholder Assets — player (Xynthra)

The player is drawn with bundled sprite sheets used as **placeholders** (not final art). Files live under `Graphics/GandalfHardcore/`:

- **Body:** `Character_skin_colors/Female_Skin1.png`
- **Hair:** `Female_Hair/Female_Hair5.png`
- Both are **800×448** and pixel-aligned. **Draw the hair sheet on top of the body sheet at the same cell** — two layers compositing to one character. (Sibling folders hold other skins/hairs; treat them as optional palette swaps.)

**Sheet layout:** **7 rows**, each **64 px tall**; frames sit on an **80 px column grid** (cell **80×64**), left-packed (frame *i* = column *i*). Source character **faces left** — flip horizontally to face right. (Pick left as the stored "default" facing; flip when moving right.) Anchor sprites by the **feet** (bottom of the 64px cell) so they sit on the ground regardless of pose height.

**Row map (top → bottom):**

| Row | Animation | Frames |
|-----|-----------|--------|
| 0 | idle | 5 |
| 1 | walking | 8 |
| 2 | running | 8 |
| 3 | jumping (ascending) | 4 |
| 4 | falling (descending) | 4 |
| 5 | attacking | 6 |
| 6 | defeat | 10 |

**Map sheet → game states:** idle → **idle**; running → **run** (walking is available for a slower/aim move if wanted); jumping → **jump**; falling → **fall**; defeat → **defeated / digested game-over**; attacking → reuse as the **shoot / charge** pose for now.

**Not in this sheet** (use the nearest frame or a simple shape until real art exists): crouch, up-shot / down-shot, crouch-shot, heal/digest, swallow-pickup, struggling-inside-enemy, and the **4 belly states** — draw a simple belly overlay/marker tied to the stored count rather than swapping frames. Enemies (Small/Big/Juggernaut) and pickups stay as colored shapes for now.

**Loader sketch:** put one table in `assets.py` mapping each animation to `(row, frame_count, fps, loop?)`; on load, slice 80×64 cells, composite hair over body, and cache left- and right-facing copies. `animation.py` advances frames on the fixed timestep and the player's state machine picks the active animation.

---

## Game specification (authoritative)

### Player — Xynthra (proposed numbers, all tunable)

Movement: run speed **220 px/s**; ground accel/friction **1800 / 2200 px/s²**; air control **~80%** of ground accel; gravity **2000 px/s²**; max fall **900 px/s**. Jump is **variable height**: full jump impulse **−640 px/s**; on early release cut upward velocity to **−250 px/s** (short hop). Coyote time **0.10 s**, jump buffer **0.12 s**. Crouch reduces hitbox height **−40%**.

Shooting: fires **horizontally and vertically only**; **down-shot only while airborne**. **Can shoot while crouching** = a low horizontal shot from the crouched pose (no up-shot while crouched). Projectile speed **480 px/s**; fire cooldown **0.25 s**.

Charge shot — **3 levels** (level 1 = normal/uncharged): L1 tap → 1 dmg, 8 px hitbox; L2 hold ≥ **0.6 s** → 2 dmg, 14 px; L3 hold ≥ **1.4 s** → 3 dmg, 20 px. Larger level = larger hitbox.

Health & healing: **Max HP 10**. Stores **0–3** healing objects (shrunken ladies, collected by swallowing). To heal she must be **idle** and **hold the heal key 4 s** to digest one (**+3 HP**); interrupted if she moves or takes damage. **Belly has 4 visual states** (empty / 1 / 2 / 3) tied to stored count.

Drop-through platforms: one-way, solid from above. **Crouch + Jump** disables collision with the platform underfoot for **~0.30 s** so she falls through.

Damage reaction (every normal/damaging hit): **knockback** away from source, NES-style (Castlevania/Mega Man/Ninja Gaiden) — proposed ~200 px/s horizontal + ~250 px/s up, control reduced ~0.20 s; then **1.5 s mercy invincibility** with the sprite **blinking** (no further hits land during it).

Lose: HP reaches 0, **or** digested (fail the struggle minigame). Win: reach the **level exit**. Retry: **unlimited**, from level start.

Swallow / struggle minigame — triggered by contact with a **Big** enemy or a connecting **Juggernaut melee grab** (NOT grenades). A **struggle bar** depletes continuously; pressing **Space** refills it. She also takes **1 dmg every 2.5 s** while inside. Digested if the **bar empties** OR **HP hits 0**. **Escape** = fill the bar; on escape the enemy is **stunned 3 s** (and a Juggernaut's shield is ineffective while stunned). Bar depletion: Big ~**4.0 s** empty / Juggernaut ~**2.5 s**; start fill **50%**; refill **+8%** per press.

### Enemies

Shared: detection, contact rules, death animation then removal. Any enemy Xynthra escapes is **stunned 3 s**. (Enemies are colored-shape placeholders for now.)

- **Small** — 3 HP, ~1× size. Two variants: **Turret** (stationary, shoots horizontally every ~2.0 s) and **Jumper** (jumps every ~2.5 s, fires at apex). Projectile damage 1. **Contact damage 1** (normal hit → knockback + i-frames). Does not swallow.
- **Big** — 5 HP, ~1.85× size. Idle until it detects Xynthra (~400 px / line of sight), then pursues (run + jump). On contact → swallow → struggle. Move speed ~180 px/s.
- **Juggernaut** — 10 HP, ~3.5× size. **Shield** guards head or feet (blocks shots there; unguarded zone is the damage window; shield disabled 3 s while stunned). **Cannot jump.** When it can't reach her: throws arcing **grenades** (~range > 250 px, every ~3.0 s, **normal damage ~2**, knockback + i-frames, **no struggle**). When it can reach her: **short grab** (~60 px) and **energy-whip grab** at waist (~180 px) → swallow → struggle.

### Controls (rebindable)

Move ← / → (or A/D) · Aim up/down ↑ / ↓ · Jump Space · Crouch ↓ held (Jump while crouched = drop-through) · Shoot/charge J (hold to charge) · Heal H (hold 4 s, idle) · Struggle Space (only while swallowed).

---

## Build Roadmap (use each as a prompt)

Run these in order. Each is written so you can paste it to Claude Code (or just say "do milestone N"). Each ends runnable.

1. **Skeleton.** Create `main.py` with a window (960×540, scaled), a fixed-timestep game loop at 60 FPS, a state manager (Menu/Play/GameOver), and `settings.py` with the constants above. Map keys to abstract actions in `core/input.py`. Show a placeholder "Play" state — as a sanity check you may load the player **idle** animation (see Placeholder Assets) and draw it, otherwise a clear background. Verify: window opens, closes cleanly, fixed timestep is stable.
2. **Movement + collision.** Implement `world/tilemap.py` (grid, collision flags) and `core/physics.py` (AABB vs tiles, gravity, horizontal-then-vertical resolution). Implement `assets.py` + `core/animation.py` to load the player sheet (body + Hair5) and the player **state machine** that selects idle/walk/run/jump/fall and flips by facing. Player runs, faces direction, and jumps with **variable height + coyote time + jump buffer**, plus crouch (shrinks hitbox; no crouch frame in the sheet — squash the idle frame or use a shape). Build a small test level. Verify: movement feels right, animations match state, no tunneling.
3. **One-way platforms.** Add drop-through platforms (solid from above; **Crouch+Jump** falls through for ~0.30 s).
4. **Shooting.** `entities/projectile.py` + firing: horizontal/vertical only, **down-shot only airborne**, **crouch shot** (low horizontal), 0.25 s cooldown. Use the **attacking** row as the shoot-pose placeholder.
5. **Charge system.** 3 charge levels with hold timings, damage, and growing hitboxes; HUD charge meter.
6. **Damage model.** Player HP, **knockback** on normal hits, **1.5 s mercy i-frames** with blink (blink the sprite). A test hazard to take damage from.
7. **Health + healing + belly.** `pickup.py` (collect = swallow, cap 3), idle **hold-4s** digest (+3 HP). Belly's 4 states aren't in the sheet — draw a simple **belly overlay/marker** tied to stored count; HUD health + belly.
8. **Enemy: Small.** Both variants (turret + jumper), projectile damage 1, **contact damage 1**.
9. **Enemy: Big.** Detection (~400 px), pursuit (run/jump), contact → swallow trigger.
10. **Swallow/struggle minigame.** Struggle bar (deplete + Space refill), **1 dmg / 2.5 s**, digest on empty or HP 0, escape on full, **enemy stun 3 s**; on defeat use the player **defeat** row, then GameOver + retry-from-start flow.
11. **Enemy: Juggernaut.** Shield head/feet (+stun disable), grenades (normal damage, no struggle), short grab + whip grab → swallow.
12. **Level + polish.** Build the demo level layout with a reachable **exit** (win), camera follow + look-ahead + bounds, and stub the audio hooks. Balance for **easy**.

### Definition of done (per milestone)

- The game still launches with `python main.py` and the new system works.
- No crashes/tracebacks during a quick manual play.
- New constants are in `settings.py`, and sheet/animation definitions in `assets.py` — not hard-coded in logic.
- A one-line note on how to exercise the new feature.

---

*Full prose spec: `XYNTHRA_PLATFORMER_Design_Plan.docx` (English) / `XYNTHRA_PLATFORMER_Plan_es-419.docx` (Spanish). This CLAUDE.md is the condensed, build-oriented version Code should follow.*
