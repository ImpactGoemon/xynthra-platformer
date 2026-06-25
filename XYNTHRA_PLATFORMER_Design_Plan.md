# Xynthra Platformer — Technical Design Plan

**Status:** Revision 2 — author decisions incorporated. Still planning only; **no code written yet.**
**Source:** `XYNTHRA_PLATFORMER.docx` + author answers/changes (Drive copy, 2026-06-22).
**Engine:** Custom, built from scratch in Python with `pygame`.

> Content note: the design includes an adult/fetish theme (soft vore — swallowing/digestion). All characters are adult and fictional. This plan treats those elements as game systems (a heal-resource mechanic and a lose/escape state) and keeps the rest of the document focused on engineering.

---

## 1. Scope

A single-level demo of a 2D platformer-shooter — a **proof of concept**, tuned to be **easy**. The goal is a vertical slice: one playable character with full moveset, the three enemy types, the health/healing loop, the swallow/escape loop, and a lose → retry flow.

**Confirmed scope decisions (author):**
- **Win condition:** reach the **level exit**.
- **Difficulty:** easy; this is a proof of concept.
- **Art:** **placeholder sprites** — the bundled `Graphics/GandalfHardcore/` sheets (Skin1 body + Hair5 hair, layered) drive the player's idle/walk/run/jump/fall/attack/defeat. States not in the set (crouch, shooting poses, heal, swallow/struggle, the belly states) use the nearest frame or simple shapes until real art. Enemies, pickups, and UI stay as simple shapes for now.
- **Retry:** **unlimited** retries, always from the **start of the level**.
- **Audio:** in scope as a system, but **no audio assets created yet** (hooks/stubs only).

Values marked **(proposed)** are confirmed as acceptable starting defaults (author approved working with the proposed numbers); they remain tunable.

---

## 2. Target technical baseline

| Item | Value | Notes |
|------|-------|-------|
| Internal resolution | 960 × 540 | 16:9, integer-scaled to the window |
| Framerate | 60 FPS | Fixed timestep for physics |
| Tile size | 32 × 32 px | Grid for tilemap + collision |
| Units | pixels, seconds | Velocities in px/s, accel in px/s² |
| Coordinate origin | top-left, +Y down | pygame convention |

---

## 3. Engine architecture (modules)

A clean separation so systems can be built and debugged independently:

- **App / main loop** — window, fixed-timestep update, render, clock.
- **Scene/State manager** — `Menu`, `Play`, `GameOver` states; transitions and retry.
- **Input** — maps physical keys to abstract actions (move, jump, shoot, charge, crouch, heal, struggle); single source of truth so rebinding is trivial later.
- **Physics & collision** — AABB vs. tilemap, gravity, one-way (drop-through) platforms, resolution order (horizontal then vertical), knockback impulses.
- **Tilemap** — level data + layered rendering (background / terrain / props / foreground), collision flags per tile, **exit trigger**.
- **Entities** — `Player`, `Projectile`, `Enemy` (Small/Big/Juggernaut), `Pickup`. State-machine driven.
- **Animation** — frame sequences per state; drives belly states, swallow/struggle/digestion, **i-frame blink**, and **enemy stun**.
- **Combat** — projectile manager, hitbox/hurtbox overlap, damage application, charge logic, knockback, invincibility windows.
- **AI** — per-enemy behavior state machines (idle/patrol/detect/pursue/attack/blocked/**stunned**).
- **Camera** — follow with look-ahead + smoothing, clamped to level bounds (per `2d-games`).
- **HUD/UI** — health, belly state, charge meter, struggle bar, game-over overlay.
- **Audio** — SFX/music hooks; stubbed for now (no assets yet).

---

## 4. Player character — Xynthra

### 4.1 Movement (proposed values)

| Parameter | Value | Notes |
|-----------|-------|-------|
| Run speed | 220 px/s | left/right; facing flips with direction |
| Ground accel / friction | 1800 / 2200 px/s² | snappy stop |
| Air control | ~80% of ground accel | "steer while in air" |
| Gravity | 2000 px/s² | |
| Max fall speed | 900 px/s | terminal velocity |
| Jump (full, hold) | initial −640 px/s | reaches ~3.25 tiles |
| Short hop (tap) | cut to −250 px/s on early release | variable jump height |
| Coyote time | 0.10 s | jump shortly after leaving edge (`2d-games`) |
| Jump buffer | 0.12 s | jump press registered just before landing |
| Crouch | hitbox height −40% | also the drop-through trigger |

### 4.2 Shooting

- Fires **horizontally and vertically only**. Down-shot is **only** allowed while airborne.
- Aim direction from facing + up/down held.
- **Can shoot while crouching:** fires a low horizontal shot from the crouched pose. Up-shots are unavailable while crouched; down-shots remain airborne-only.

| Parameter | Value | |
|-----------|-------|---|
| Projectile speed | 480 px/s | |
| Fire cooldown | 0.25 s | between non-charged shots |

### 4.3 Charge shot — **confirmed: 3 levels**

Level 1 is the normal/uncharged shot. Each level has a larger hitbox.

| Level | Charge hold | Damage | Hitbox |
|-------|-------------|--------|--------|
| 1 (normal, uncharged) | tap | 1 | 8 px |
| 2 | ≥ 0.6 s | 2 | 14 px |
| 3 | ≥ 1.4 s | 3 | 20 px |

### 4.4 Health, healing & belly states

| Parameter | Value | |
|-----------|-------|---|
| Max HP | 10 | |
| Heal objects stored | 0–3 | the swallowed shrunken ladies |
| Heal action | hold key 4 s **while idle** | interrupted if she moves or takes damage |
| Heal amount | +3 HP per object digested | |
| Belly visual states | 4 | empty / 1 / 2 / 3 — tied to stored count |

Healing objects are pickups; collecting one plays a swallow animation and increments the stored count (capped at 3).

### 4.5 Drop-through platforms

One-way platforms: solid from above by default. **Crouch + Jump** disables collision with the platform underfoot for ~0.30 s so she falls through.

### 4.6 Damage reaction — knockback & invincibility (NEW)

Whenever Xynthra takes a **normal hit** (anything that deals damage rather than swallowing her — enemy projectiles, Small-enemy contact, Juggernaut grenades):

- **Knockback:** she is pushed away from the damage source, classic NES style (reference: *Castlevania*, *Mega Man*, *Ninja Gaiden*). Brief loss of control during the knockback.
  - **(proposed)** horizontal impulse ~200 px/s away from source + ~250 px/s upward; control reduced for ~0.20 s.
- **Mercy invincibility:** **1.5 s** of i-frames after being hit; the sprite **blinks** to signal it. No further damage lands during this window.

### 4.7 Lose / win & retry

- **Lose:** HP reaches 0, **or** Xynthra is **digested** (fails the struggle minigame — see §4.8).
- **Win:** reach the **level exit**.
- **Retry:** on game over, the player may retry an **unlimited** number of times, always restarting from the **beginning of the level**.

### 4.8 Swallow / struggle minigame

**Triggered by:** contact with a **Big** enemy, or a connecting **Juggernaut melee grab** (short grab or energy-whip). **Juggernaut grenades do NOT trigger it** — they are normal damaging hits (§5.3).

While swallowed:
- A **struggle bar** appears and **depletes continuously**; pressing the struggle key refills it a bit. Bigger enemy = faster depletion (shorter window).
- Xynthra also takes **1 damage every 2.5 s** while inside the enemy.
- **Two ways to be digested (lose):** the struggle bar reaches **empty**, **or** the periodic drain reduces **HP to 0**. Either runs the digestion + game-over sequence.
- **Escape:** fill the struggle bar before either failure condition. On escape:
  - The enemy is **stunned for 3 s** (stunned animation plays).
  - **While stunned, a Juggernaut's shield is ineffective** — shots hit normally for those 3 s.
- **Struggle key:** **Space** (context-only; shared with Jump, but Jump is irrelevant while swallowed).

| Struggle parameter | Big | Juggernaut |
|--------------------|-----|------------|
| Bar depletion (proposed) | empties in ~4.0 s with no input | ~2.5 s |
| Fill per press (proposed) | +8% | +8% |
| Start fill | 50% | 50% |
| HP drain while inside | 1 dmg / 2.5 s | 1 dmg / 2.5 s |

---

## 5. Enemies

Shared: detection, contact rules, death animation then removal. **Any enemy that Xynthra escapes from is stunned for 3 s** (stunned animation; Juggernaut shield disabled during stun). Sizes are relative to Xynthra's sprite.

### 5.1 Small — 3 HP, ~1× size
Two variants:
- **Turret:** stationary, shoots horizontally at intervals (**proposed** every 2.0 s).
- **Jumper:** jumps at intervals (**proposed** every 2.5 s), fires at the apex.
- **Projectile damage:** 1.
- **Contact damage:** touching a Small enemy deals **1 damage** to Xynthra (normal hit → knockback + i-frames). Small enemies do **not** swallow.

### 5.2 Big — 5 HP, ~1.85× size
- Idle until it **detects** Xynthra (**proposed** radius 400 px / line of sight).
- Pursues: runs and jumps as needed to reach her.
- On contact → swallow animation → struggle minigame (§4.8).
- Move speed **proposed** 180 px/s.

### 5.3 Juggernaut — 10 HP, ~3.5× size
- **Shield** toggles to guard **head** or **feet**, blocking shots aimed there; the unguarded zone is the damage window. **Shield is disabled for 3 s if it is stunned** by a successful escape.
- **Cannot jump.** Tries to reach Xynthra on the ground.
- **Grenades (when it can't reach her):** arcing throw (**proposed** range > 250 px, every 3.0 s). These deal **normal damage** (**proposed** 2) as a standard hit → **knockback + i-frames**, and do **NOT** trigger the struggle minigame.
- **Melee (when it can reach her):** two grabs —
  - short-range **grab** (**proposed** ~60 px),
  - long-range **energy-whip** grab at waist height (**proposed** ~180 px).
  - Either connecting grab → swallow → struggle minigame.

---

## 6. Presentation states (asset/animation checklist)

**Player placeholder = bundled sprite sheets** in `Graphics/GandalfHardcore/`: body `Character_skin_colors/Female_Skin1.png` + hair `Female_Hair/Female_Hair5.png` (layered, hair over body). Both 800×448, **7 rows × 64 px**, **80 px columns**. Rows top→bottom: **idle (5), walking (8), running (8), jumping (4), falling (4), attacking (6), defeat (10)**; source faces left (flip for right); anchor by feet. Map: idle→idle, running→run, jumping→jump, falling→fall, attacking→shoot/charge pose, defeat→defeated/game-over. The states below that aren't in the sheet use the nearest frame or simple shapes. Eventual full art list:

- **Xynthra:** idle, run, jump, fall, crouch, shoot (h/up/down), shoot-crouched, charge (per level), take-damage (+knockback), **i-frame blink**, heal/digest, swallow-pickup, struggling-inside-enemy, defeated.
- **Belly:** 4 fill states layered onto base poses.
- **Small/Big/Juggernaut:** idle, attack(s), pursue (Big), shield toggle (Juggernaut), **stunned**, swallow-with-pleased-expression, satisfied-full loop, death.
- **UI:** health, belly icon, charge meter, struggle bar, "Game Over" overlay + retry prompt.
- **Level:** exit marker/trigger.

---

## 7. Controls (proposed — fully rebindable)

| Action | Key |
|--------|-----|
| Move | ← / → (or A / D) |
| Aim up / down | ↑ / ↓ |
| Jump | Space |
| Crouch | ↓ held (Jump while crouched = drop-through) |
| Shoot / charge | J (hold to charge) |
| Heal | H (hold 4 s, idle) |
| Struggle (mash) | Space (only while swallowed) |

---

## 8. Suggested build order (milestones)

1. **Skeleton:** window, fixed-timestep loop, state manager, input abstraction.
2. **Movement + collision:** tilemap, AABB, gravity, run/jump (variable height, coyote, buffer), crouch.
3. **One-way platforms:** drop-through.
4. **Shooting:** projectiles, directional fire rules (incl. crouch shot), fire cooldown.
5. **Charge system:** 3 levels, damage, hitbox scaling, HUD meter.
6. **Damage model:** HP, normal-hit knockback, 1.5 s mercy i-frames + blink.
7. **Health + healing + belly states:** pickups, idle-hold digest, HUD.
8. **Enemy: Small** (both variants) + projectile/contact damage.
9. **Enemy: Big** — detection, pursuit, contact-swallow.
10. **Swallow/struggle minigame** — bar, HP drain, escape, enemy stun + lose/retry flow.
11. **Enemy: Juggernaut** — shield (+stun disable), grenades (normal damage), two grabs.
12. **Level exit / win condition; camera; layout; audio hooks (stubbed); polish.**

(`systematic-debugging` is the working method when bugs appear — root cause before fixes.)

---

## 9. Resolved decisions & change log (author, rev 2)

**Answers to open questions:**
1. Charge shot — **3 levels**; Level 1 is the normal/uncharged shot.
2. Level goal — **reach the exit**.
3. Numbers — **use the proposed values** as starting defaults.
4. Art — **placeholder shapes** for now.
5. Retry — **unlimited**, from **level start**.
6. Audio — **in scope** as a system, **no assets yet** (stub).
7. Difficulty — **easy**; proof of concept.

**Required changes applied:**
- Xynthra takes **1 damage on contact** with a Small enemy (§5.1).
- **Struggle key is Space** (§4.8, §7).
- During the struggle minigame, Xynthra takes **1 damage every 2.5 s**; HP reaching 0 runs digestion + game over (§4.8).
- **Juggernaut grenades deal normal damage** and do **not** trigger the struggle minigame (§5.3, §4.8).
- On escaping an enemy's stomach, that enemy is **stunned for 3 s** (stunned animation); a **Juggernaut's shield is ineffective while stunned** (§4.8, §5).
- **Knockback** on taking normal damage (NES *Castlevania* / *Mega Man* / *Ninja Gaiden* reference) (§4.6).
- **1.5 s mercy invincibility** after taking damage, with **sprite blink** (§4.6).
- **New:** Xynthra can shoot while crouching (§4.2).

---

*Planning document only. No engine or gameplay code has been written. With these decisions locked, the build can proceed milestone by milestone per §8 on your go-ahead.*
