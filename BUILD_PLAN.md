# Xynthra Platformer — Build Plan (milestone by milestone)

This is the **execution checklist** for Claude Code. It expands the roadmap in `CLAUDE.md` into runnable steps. Authoritative spec and asset details live in `CLAUDE.md`; this file says *what to build, in what order, and how to know it's done*.

## How to use this document

- Work **one milestone at a time, in order**. After finishing a milestone, **STOP** and let the human smoke-test it before starting the next.
- To run a milestone, tell Claude Code: **"Read CLAUDE.md and BUILD_PLAN.md, then implement Milestone N. Stop when its 'Done when' checks pass."**
- Every tunable number goes in `settings.py`; every sheet/animation definition goes in `assets.py`. Never hard-code these in gameplay logic.
- Map input to **abstract actions** (`core/input.py`), never raw keys in gameplay code.
- When something breaks, do **root-cause debugging** before patching (reproduce → trace → one hypothesis at a time).
- "Done when" items are acceptance checks. If any fails, the milestone is **not** complete.

## Global definition of done (applies to every milestone)

1. `python main.py` launches and the new feature works.
2. No tracebacks during a short manual play.
3. New constants are in `settings.py`; sheet/anim defs in `assets.py`.
4. The milestone's specific "Done when" checks all pass.
5. Add a one-line note to a running `PROGRESS.md` on how to exercise the new feature.

---

## Milestone 1 — Skeleton

**Goal:** A window with a stable fixed-timestep loop and a state manager.

**Prompt:** "Implement Milestone 1: window, fixed-timestep loop, state manager, settings, input abstraction."

**Build:**
- `settings.py` with the constants listed below.
- `main.py`: create a 960×540 internal surface, integer-scale-blit it to the window; fixed-timestep loop (accumulator) updating at 60 Hz, rendering decoupled; clean quit.
- `core/state.py`: state manager with `Menu`, `Play`, `GameOver`; only `Play` needs to draw (a clear background). Allow switching states.
- `core/input.py`: map keys → abstract actions (see Controls in `CLAUDE.md`); expose `pressed/held/released` per action.
- Optional sanity check: load the player **idle** animation (see Placeholder Assets) and draw one frame.

**settings.py (add):** `WIDTH=960`, `HEIGHT=540`, `FPS=60`, `FIXED_DT=1/60`, `TILE=32`, window scale factor, background color.

**Done when:**
- Window opens at the correct size and closes cleanly (no hang, no traceback).
- The update step runs at a fixed 60 Hz regardless of render rate (verify by logging update count vs. seconds).
- Pressing the mapped keys flips the corresponding action state (print to confirm).

**Smoke test:** Run `python main.py`; window shows the Play background; ESC/close quits cleanly.

**STOP.**

---

## Milestone 2 — Movement + collision + player animation

**Goal:** Xynthra runs, faces direction, jumps (variable height), crouches, collides with tiles, and animates from the sprite sheet.

**Prompt:** "Implement Milestone 2: tilemap, AABB physics, player movement with variable jump, crouch, and the sprite animation state machine."

**Build:**
- `world/tilemap.py`: grid + per-tile collision flags; a small hand-made test level.
- `core/physics.py`: AABB vs. tiles, gravity, **horizontal-then-vertical** resolution (no tunneling).
- `assets.py`: table mapping each animation → `(row, frame_count, fps, loop?)` for the player sheet; loader slices **80×64** cells, **composites Hair5 over Skin1**, caches **left-facing (default) and right-facing (flipped)** copies. Anchor by feet.
- `core/animation.py`: advances frames on the fixed timestep.
- `entities/player.py`: movement (run accel/friction, air control), **variable-height jump** (full impulse, cut on early release), **coyote time**, **jump buffer**, **crouch** (shrink hitbox; no crouch frame — squash idle or use a shape). A state machine picks idle/walk/run/jump/fall and flips by facing.

**settings.py (add):** `RUN_SPEED=220`, `GROUND_ACCEL=1800`, `GROUND_FRICTION=2200`, `AIR_ACCEL=1440` (~80%), `GRAVITY=2000`, `MAX_FALL=900`, `JUMP_VELOCITY=-640`, `JUMP_CUT_VELOCITY=-250`, `COYOTE_TIME=0.10`, `JUMP_BUFFER=0.12`, `CROUCH_HEIGHT_FACTOR=0.6`. **assets.py:** `FRAME_W=80`, `FRAME_H=64`, row map idle=0(5), walk=1(8), run=2(8), jump=3(4), fall=4(4), attack=5(6), defeat=6(10); default facing **left**.

**Done when:**
- Player runs left/right, sprite **flips** to face travel direction, and animation switches idle↔walk/run with speed.
- Tapping jump = short hop; holding = full height. Coyote time and jump buffer feel forgiving. Jump shows the jump anim ascending, fall anim descending.
- Crouch shrinks the hitbox. No tunneling through tiles at max fall speed.

**Smoke test:** Move, run, jump (tap vs hold), crouch; watch the animation match each state and the facing flip.

**STOP.**

---

## Milestone 3 — One-way (drop-through) platforms

**Goal:** Platforms solid from above; **Crouch+Jump** drops through.

**Prompt:** "Implement Milestone 3: one-way platforms with crouch+jump drop-through."

**Build:** Tag certain tiles/platforms as one-way (collide only when moving down and feet above the top). On **Crouch+Jump**, disable collision with the platform underfoot for `DROP_THROUGH_TIME`.

**settings.py (add):** `DROP_THROUGH_TIME=0.30`.

**Done when:** She lands on one-way platforms from above, can't be blocked from below, and Crouch+Jump drops her cleanly through the one she's standing on.

**Smoke test:** Stand on a one-way platform, Crouch+Jump → fall through; jump up through it from below → pass then land.

**STOP.**

---

## Milestone 4 — Shooting

**Goal:** Directional projectiles with cooldown.

**Prompt:** "Implement Milestone 4: projectiles, directional fire rules, crouch shot, cooldown."

**Build:** `entities/projectile.py` + firing in `player.py`. Fire **horizontal and vertical only**; **down-shot only while airborne**; **crouch shot** = low horizontal from crouched pose. `FIRE_COOLDOWN` between shots. Use the **attacking** row as the shoot-pose placeholder. Spawn position/direction from `facing` + up/down held.

**settings.py (add):** `PROJECTILE_SPEED=480`, `FIRE_COOLDOWN=0.25`.

**Done when:** Shots fire in the 4 valid directions per rules; down-shot blocked on the ground; crouch shot fires low; cooldown limits fire rate; muzzle follows facing.

**Smoke test:** Shoot left/right/up; jump and shoot down; crouch and shoot.

**STOP.**

---

## Milestone 5 — Charge system

**Goal:** 3 charge levels with growing damage and hitbox + HUD meter.

**Prompt:** "Implement Milestone 5: 3-level charge shot with hold timings, damage, hitbox scaling, and a HUD charge meter."

**Build:** Hold the shoot action to charge. L1 (tap)=1 dmg/8px; L2 (≥0.6s)=2 dmg/14px; L3 (≥1.4s)=3 dmg/20px. Bigger level → bigger projectile hitbox. `ui/hud.py` shows a charge meter while holding.

**settings.py (add):** `CHARGE_L2_TIME=0.6`, `CHARGE_L3_TIME=1.4`, `CHARGE_DMG=(1,2,3)`, `CHARGE_HITBOX=(8,14,20)`.

**Done when:** Charge level rises with hold time; release fires the correct damage/size; HUD meter reflects current charge.

**Smoke test:** Tap (L1), hold ~0.7s (L2), hold ~1.5s (L3); confirm meter + projectile size.

**STOP.**

---

## Milestone 6 — Damage model (knockback + i-frames)

**Goal:** Player HP, knockback, mercy invincibility with blink.

**Prompt:** "Implement Milestone 6: HP, NES-style knockback on normal hits, 1.5s mercy invincibility with sprite blink. Add a test hazard."

**Build:** `MAX_HP`; on a **normal damaging hit**, apply knockback away from source (~`KNOCKBACK_X` horizontal + `KNOCKBACK_Y` up), reduce control for `KNOCKBACK_CONTROL_LOCK`, then `IFRAME_TIME` invincibility during which the sprite **blinks** and no further hits land. Add a temporary hazard tile to take damage from.

**settings.py (add):** `MAX_HP=10`, `KNOCKBACK_X=200`, `KNOCKBACK_Y=-250`, `KNOCKBACK_CONTROL_LOCK=0.20`, `IFRAME_TIME=1.5`, `BLINK_HZ=10`.

**Done when:** Touching the hazard deals damage once, knocks her back away from it, starts a 1.5s blinking i-frame window, and a second touch during i-frames does nothing.

**Smoke test:** Walk into the hazard; observe knockback direction, blink, and invulnerability window.

**STOP.**

---

## Milestone 7 — Health + healing + belly

**Goal:** Collect healing objects (swallow), digest while idle, belly states + HUD.

**Prompt:** "Implement Milestone 7: pickups (swallow, cap 3), idle hold-4s digest (+3 HP), 4 belly states, HUD health + belly."

**Build:** `entities/pickup.py` (collect = swallow, increments stored count, cap `MAX_STORED`). Healing: must be **idle**, **hold heal key 4s** to digest one (`+HEAL_AMOUNT` HP); interrupted if she moves or takes damage. **4 belly states** (0/1/2/3) — not in the sheet, so draw a **simple belly overlay/marker** tied to stored count. HUD shows health + belly.

**settings.py (add):** `MAX_STORED=3`, `HEAL_HOLD_TIME=4.0`, `HEAL_AMOUNT=3`.

**Done when:** Picking up adds to belly (caps at 3, overlay updates); holding heal while idle for 4s consumes one and adds 3 HP (clamped to max); moving/getting hit mid-heal cancels it.

**Smoke test:** Collect 3 pickups (belly fills), take damage, heal once (idle 4s), interrupt a heal by moving.

**STOP.**

---

## Milestone 8 — Enemy: Small

**Goal:** Turret + Jumper variants that damage the player.

**Prompt:** "Implement Milestone 8: Small enemy, both variants (turret + jumper), projectile and contact damage."

**Build:** `entities/enemy.py` base + Small. **Turret:** stationary, shoots horizontally every `TURRET_FIRE_INTERVAL`. **Jumper:** jumps every `JUMPER_INTERVAL`, fires at apex. 3 HP; projectile damage 1; **contact damage 1** (normal hit → knockback + i-frames from Milestone 6). Does not swallow. Death anim (placeholder) then removal. Colored-shape placeholder is fine for enemies.

**settings.py (add):** `SMALL_HP=3`, `TURRET_FIRE_INTERVAL=2.0`, `JUMPER_INTERVAL=2.5`, `SMALL_PROJECTILE_DMG=1`, `SMALL_CONTACT_DMG=1`.

**Done when:** Turret fires on interval; Jumper jumps and fires at apex; player shots reduce enemy HP (dies at 0); touching a Small deals 1 + knockback + i-frames.

**Smoke test:** Stand near a turret (take shots), approach a jumper, kill each with charged/normal shots.

**STOP.**

---

## Milestone 9 — Enemy: Big

**Goal:** Detect, pursue, and trigger a swallow on contact.

**Prompt:** "Implement Milestone 9: Big enemy — detection, pursuit (run/jump), contact triggers swallow."

**Build:** Big: 5 HP, ~1.85× size, idle until it **detects** the player (`BIG_DETECT_RADIUS` / line of sight), then pursues (run + jump to reach). On contact, trigger the swallow state (the minigame itself is Milestone 10 — for now just enter "swallowed"). Move speed `BIG_SPEED`.

**settings.py (add):** `BIG_HP=5`, `BIG_DETECT_RADIUS=400`, `BIG_SPEED=180`.

**Done when:** Big stays idle until the player is within detection, then chases and jumps toward her; contact puts the player into the swallowed state.

**Smoke test:** Approach a Big from outside its range, watch it detect + pursue, let it touch you.

**STOP.**

---

## Milestone 10 — Swallow / struggle minigame + lose/retry

**Goal:** The full struggle loop, digestion, game over, and retry.

**Prompt:** "Implement Milestone 10: struggle bar, HP drain, escape with enemy stun, digestion + game over + retry-from-start."

**Build:** When swallowed (Big contact, or later a Juggernaut grab): show a **struggle bar** starting at `STRUGGLE_START`%, depleting continuously (Big empties in `STRUGGLE_BIG_DEPLETE`s). **Space** refills `STRUGGLE_FILL_PER_PRESS`% per press. Player takes 1 dmg every `STRUGGLE_HP_DRAIN_INTERVAL`s while inside. **Digested (lose)** if the bar empties **or** HP hits 0 → play the **defeat** row + digestion sequence → `GameOver` → retry from level start (unlimited). **Escape** if the bar fills → enemy is **stunned** `STUN_TIME`s (stun anim).

**settings.py (add):** `STRUGGLE_START=50`, `STRUGGLE_BIG_DEPLETE=4.0`, `STRUGGLE_JUG_DEPLETE=2.5`, `STRUGGLE_FILL_PER_PRESS=8`, `STRUGGLE_HP_DRAIN_INTERVAL=2.5`, `STUN_TIME=3.0`.

**Done when:** Bar depletes/refills correctly; HP drains on schedule; mashing to full escapes and stuns the enemy 3s; letting the bar empty (or HP hit 0) triggers defeat → game over → retry restarts the level.

**Smoke test:** Get swallowed; escape once by mashing; get swallowed again and let the bar empty to see defeat → retry.

**STOP.**

---

## Milestone 11 — Enemy: Juggernaut

**Goal:** Shielded heavy with grenades and two grabs.

**Prompt:** "Implement Milestone 11: Juggernaut — head/feet shield (disabled while stunned), grenades (normal damage, no struggle), short grab + whip grab → swallow."

**Build:** Juggernaut: 10 HP, ~3.5× size, **cannot jump**. **Shield** toggles guarding head or feet (blocks shots there; unguarded zone is the damage window); shield **disabled `STUN_TIME`s** if stunned by an escape. When it **can't reach** her: throws arcing **grenades** (range > `GRENADE_RANGE`, every `GRENADE_INTERVAL`s, `GRENADE_DMG` normal damage → knockback + i-frames, **no struggle**). When it **can reach** her: **short grab** (`SHORT_GRAB`px) and **energy-whip grab** at waist (`WHIP_GRAB`px) → swallow → struggle (Milestone 10).

**settings.py (add):** `JUG_HP=10`, `GRENADE_RANGE=250`, `GRENADE_INTERVAL=3.0`, `GRENADE_DMG=2`, `SHORT_GRAB=60`, `WHIP_GRAB=180`.

**Done when:** Shots are blocked at the guarded zone and connect at the unguarded one; far away it lobs grenades that damage but don't swallow; up close a grab swallows → struggle; a successful escape stuns it and disables the shield for 3s.

**Smoke test:** Trade shots (read the shield), back off to draw grenades, get close to be grabbed, escape and punish during stun.

**STOP.**

---

## Milestone 12 — Level + polish

**Goal:** A complete, winnable demo level.

**Prompt:** "Implement Milestone 12: build the demo level with a reachable exit (win), camera follow + look-ahead + bounds, audio hook stubs, and balance for easy."

**Build:** `world/level1.py`: a single level laying out platforms, the three enemy types, pickups, and a reachable **exit trigger** (reaching it = win → a win state). `core/camera.py`: follow with look-ahead + smoothing, clamped to level bounds. `audio/audio.py`: stub SFX/music hooks (no files). Tune for **easy** (forgiving spacing, modest enemy aggression).

**Done when:** The level is completable start-to-exit; camera follows smoothly within bounds; reaching the exit shows a win; audio calls are stubbed (no crashes); difficulty feels easy.

**Smoke test:** Play the whole level start to finish, win at the exit; die once and retry from start.

**STOP — demo complete.**

---

*Order, numbers, and asset details come from `CLAUDE.md` and the design docs. If a number here ever disagrees with `settings.py`, `settings.py` wins once set — update this doc to match.*
