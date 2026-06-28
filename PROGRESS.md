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

## Milestone 6 — Damage model + test hazard ✅ (2026-06-26)

Player HP (max 10) with NES-style hit reactions. `Player.take_damage(amount,
source_x)` deducts HP, applies knockback **away from the source** (~200 px/s
horizontal + 250 px/s up), locks input ~0.20 s, and grants **1.5 s mercy
invincibility** during which the sprite **blinks** and no further hits land.
HP 0 sets the `dead` flag and the Play state switches to Game Over. A **HUD
health row** (red pips, top-left) shows current HP.

To exercise collision + damage, the Play state spawns a **test enemy projectile
from the player's right** every ~2 s (red square, 1 damage) that travels left;
on contact it damages the player, applies knockback, and is consumed.

- **Run:** `python main.py` — stand still and a red shot comes in from the right;
  HP pips drop, she's knocked back and blinks; at 0 HP it's Game Over.
- **Test:** `python -m pytest tests/ -q` — 72/72 passing (M1–M6).
- Files: `settings.py`, `entities/player.py` (HP/knockback/i-frames/blink),
  `ui/hud.py` (`draw_health`), `main.py` (enemy hazard, collision, Game Over),
  `tests/test_milestone6.py` (new).

_Next: Milestone 7 — health, healing pickups (swallow, cap 3), hold-4s digest (+3 HP), belly states + HUD._

### Tweaks (2026-06-26)

- **Death animation before Game Over:** on HP 0 the player plays the **defeat**
  animation row to completion (~1 s, `DEFEAT_HOLD`) while the Play state holds;
  only then does it switch to the Game Over screen. The defeat sprite doesn't
  blink. (`entities/player.py` `_enter_death`/`_update_dead`, `main.py`.)
- **Attack pose on press, not frozen while charging:** the attack/shoot pose
  plays the moment **J** is pressed (and again on a charged release), but it no
  longer stays frozen while **J** is held — the short non-looping pose expires
  back to idle/run during the charge. (`entities/player.py` `_fire`/`_update_state`.)
- **Tests:** 76/76 passing (M1–M6 + these tweaks).

## Milestone 7 — Healing pickups + belly + HUD ✅ (2026-06-26)

Xynthra can **swallow** pickups (the "shrunken ladies") to store heals, capped at
**3** (`belly`). Standing **idle** and holding **Heal (H)** for **4 s** digests one
for **+3 HP** (capped at 10); any movement, jump, crouch, or taking a hit
interrupts it. A **belly indicator** (3 slots) and a **digest progress bar** were
added to the HUD, plus a small on-body belly marker (one pip per stored pickup).

Per request:
- **Pickups are the Schoolgirl Girl_1 idle sprite**, tight-cropped from the sheet.
- Each pickup is scaled to **1/4 of Xynthra's visible height** (88 px → ~22 px).
- The **test enemy shot only fires while Xynthra is on the highest platform** (the
  top one-way ledge), so it only appears where a left-travelling shot can reach
  her there; on lower platforms no shots spawn.

- **Run:** `python main.py` — walk into a small schoolgirl to swallow her (belly
  fills); stand still and hold **H** to heal; climb to the top ledge to face the
  enemy shot.
- **Test:** `python -m pytest tests/ -q` — 85/85 passing (M1–M7).
- Files: `settings.py`, `assets.py` (`build_pickup_image`), `entities/pickup.py`
  (new), `entities/player.py` (belly/heal), `ui/hud.py` (`draw_belly`,
  `draw_heal_progress`), `world/level1.py` (`PICKUP_SPAWNS`), `main.py`,
  `tests/test_milestone7.py` (new).

_Next: Milestone 8 — Small enemies (turret + jumper), projectile + contact damage._

### Fix (2026-06-26): digestion feedback at full HP

Digestion was gated on `hp < max`, so holding **H** at full health did nothing and
the bar never appeared (looked broken). Now the digest bar shows whenever **H** is
held while idle with a stored pickup, giving feedback at any HP; a completed digest
only consumes a pickup when it actually heals, so full HP wastes nothing.
(`entities/player.py` `_update_healing`; test in `tests/test_milestone7.py`.) 86/86.

### Fix (2026-06-26, revised): digest bar gated to HP < max

The previous "show the bar at any HP" change had a bug: after healing 9 -> 10 while
still holding **H**, the bar kept re-filling at full HP. Reverted to gating the
digest on `hp < max`, so the bar appears only while a heal is actually possible and
disappears the instant HP hits max. (`entities/player.py` `_update_healing`;
tests `test_no_heal_bar_at_full_hp`, `test_heal_bar_disappears_when_hp_reaches_max`.)
87/87.

## Milestone 8 — Small enemies (turret + jumper) ✅ (2026-06-26)

Added the **Small** enemy (3 HP, ~1x size) in two variants:
- **Turret** — stationary, fires a horizontal shot toward Xynthra every ~2 s.
- **Jumper** — jumps every ~2.5 s and fires a horizontal shot at the jump apex.

Both deal **1 contact damage** (normal hit -> knockback + i-frames) and do not
swallow. Player shots reduce their HP; at 0 HP they play the **defeat** animation
then are removed. Enemy shots feed the existing hazard pipeline (damage + i-frames).

Per request the enemy art is composited like Xynthra but from **Skin4 + Hair3 +
the flower** (`assets._build_character_animations` was factored out so the player
and enemy share one builder).

- **Run:** `python main.py` — walk right to meet a jumper and a turret on the
  floor; shoot them (3 hits each); their shots and bodies hurt on contact.
- **Test:** `python -m pytest tests/ -q` — 95/95 passing (M1–M8).
- Files: `settings.py`, `assets.py` (generic builder + `build_enemy_animations`),
  `entities/enemy.py` (new: `Enemy` + `Small`), `world/level1.py` (`SMALL_SPAWNS`),
  `main.py`, `tests/test_milestone8.py` (new).

_Next: Milestone 9 — Big enemy (detection, pursuit, contact -> swallow trigger)._

## Milestone 9 — Big enemy (detect, pursue, swallow trigger) ✅ (2026-06-27)

Added the **Big** enemy (5 HP, ~1.85x size). It stays **idle** until the player
comes within `BIG_DETECT_RADIUS` (400 px), then **pursues**: accelerates toward
her at `BIG_SPEED` (180 px/s) and **jumps** (`BIG_JUMP_VELOCITY`) when blocked by
a wall in its path or when she is clearly above it (detection latches once seen).
On **contact it swallows** the player instead of dealing a normal hit
(`Big.swallows = True`) — the player enters a new **swallowed** state
(`Player.enter_swallow`) that freezes her in place. The struggle minigame /
escape / digestion is **Milestone 10**; for now being swallowed is a held state.

Per the shared builder, Big art is **Skin2 + Hair2 + the flower** composited at a
larger sprite scale (`BIG_SPRITE_SCALE = 4`) so it reads as the bigger enemy.
The base `Enemy._physics` now stores the last collision flags so the Big's AI can
jump when it hits a wall.

- **Run:** `python main.py` — walk right toward the Big; outside ~400 px it idles,
  then it detects you, chases (jumping over the solid block / up to ledges), and
  on contact swallows you (held in place until M10 adds the escape minigame).
  Shoot it 5 times to kill it.
- **Test:** `python -m pytest tests/ -q` — 107/107 passing (M1–M9).
- Files: `settings.py`, `assets.py` (`build_big_animations`, scale override),
  `entities/enemy.py` (`Big`, stored collision flags), `entities/player.py`
  (`swallowed` state + `enter_swallow`), `world/level1.py` (`BIG_SPAWNS`),
  `main.py` (Big spawn + contact-swallow rule), `tests/test_milestone9.py` (new).

_Next: Milestone 10 — swallow/struggle minigame (struggle bar, HP drain, escape + enemy stun, digestion -> game over -> retry)._

## Refactor — Entity/Actor OOP hierarchy ✅ (2026-06-27)

Behavior-preserving refactor (no gameplay change). Extracted the duplicated
Player/Enemy code into a shared hierarchy:

- `entities/entity.py` — `Entity` root: `aabb`, `alive`, `draw()` contract.
- `entities/actor.py` — `Actor(Entity)`, the **humanoid character base**: kinematics
  (`_apply_gravity` / `_collide`, on_ground/on_oneway + stored collision flags),
  `_face`, the defeat sequence (`_enter_death` / `_tick_death`), `_play_state`, and a
  feet-anchored, facing-flipped sprite `draw` over an overridable `sprite_image`.
- `Player(Actor)`, `Enemy(Actor)` → `Small` / `Big`. **Pickup(Entity)** shares the
  root but NOT humanoid behaviour (it's static — no physics/health/AI), per the
  recommended composition-over-inheritance design.
- `approach()` moved into `core/physics.py` (was duplicated verbatim in player.py
  and enemy.py).

All public attribute/method names were preserved, so existing code and tests are
unchanged. Added `tests/test_actor.py` (hierarchy + shared-helper checks).

- **Test:** `python -m pytest tests/ -q` — 116/116 passing (M1–M9 + refactor).
- Files: `core/physics.py`, `entities/entity.py` (new), `entities/actor.py` (new),
  `entities/player.py`, `entities/enemy.py`, `entities/pickup.py`,
  `tests/test_actor.py` (new), `CLAUDE.md`.

### Polish (2026-06-27): swallowed-state placeholder

While swallowed (Big contact, pre-M10): the player **sprite is hidden** (she's
inside the enemy), the swallowing enemy now **stands idle** instead of pursuing
(new `Enemy.has_swallowed` flag; set by PlayState on a successful `enter_swallow`),
and a centered **"Xynthra is trying to escape!"** banner overlay is drawn. The
real struggle/escape minigame is still Milestone 10. (`entities/enemy.py`,
`entities/player.py` draw, `main.py` overlay, `settings.py` SWALLOW_* constants;
tests in `tests/test_milestone9.py`.) 118/118 passing.
