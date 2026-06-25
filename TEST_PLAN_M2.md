# Milestone 2 — Test Plan

Verifies tilemap collision, AABB physics (no tunneling, horizontal-then-vertical
resolution), the player movement feel (variable jump, coyote time, jump buffer,
crouch), the sprite pipeline (slice 80×64, composite Hair5 over Skin1, flip by
facing), and the animation state machine. Headless via SDL dummy.

Run: `python -m pytest tests/ -q`  (or `python tests/test_milestone2.py`)

## Acceptance criteria (BUILD_PLAN.md, Milestone 2)

- Player runs, sprite flips to face travel direction, anim switches idle↔run.
- Tap jump = short hop; hold = full height; coyote time + jump buffer forgiving.
- Jump shows jump anim ascending, fall anim descending.
- Crouch shrinks hitbox. No tunneling through tiles at max fall speed.

## Test cases

| # | Test | Asserts |
|---|------|---------|
| 1 | `test_tilemap_solidity_and_bounds` | '#' solid; out-of-bounds is empty |
| 2 | `test_fall_lands_on_ground` | Gravity brings player to rest on the floor; on_ground true |
| 3 | `test_no_tunnel_high_speed` | Huge downward velocity stops at the floor (no pass-through) |
| 4 | `test_wall_blocks_horizontal` | Moving into a wall stops X and zeroes vx |
| 5 | `test_ceiling_blocks_jump` | Upward move into ceiling stops and zeroes vy |
| 6 | `test_jump_full_vs_short` | Holding jump rises higher than tapping (variable height) |
| 7 | `test_coyote_time` | Can jump within COYOTE_TIME after leaving a ledge |
| 8 | `test_jump_buffer` | Jump pressed just before landing fires on land |
| 9 | `test_crouch_shrinks_hitbox` | Crouch lowers height, keeps feet; standing restores height |
| 10 | `test_facing_flips` | Move right→facing "right"; move left→facing "left" |
| 11 | `test_state_idle_run` | Idle when still; "run" when moving on ground |
| 12 | `test_state_jump_fall` | Airborne rising→"jump"; falling→"fall" |
| 13 | `test_build_animations` | 7 anims; per-anim frame counts match; frames are 80×64; right=flipped |
| 14 | `test_animator_loop_and_clamp` | Looping anim wraps; non-loop clamps to last frame + finished flag |
| 15 | `test_play_state_smoke` | PlayState builds level+player and updates headlessly without error |

## Exit condition

0 failures, 0 errors across Milestone 1 **and** Milestone 2 suites.
