# Milestone 1 — Test Plan

Verifies the engine skeleton: settings, fixed-timestep loop, input abstraction,
state manager, and a headless run of the game loop. Tests run **headless** via
the SDL "dummy" video/audio drivers, so no real window is needed (CI-friendly).

Run: `python -m pytest tests/ -q`  (or `python tests/test_milestone1.py`)

## Acceptance criteria (from BUILD_PLAN.md, Milestone 1)

1. Window opens at the correct size and closes cleanly (no hang, no traceback).
2. The update step runs at a fixed 60 Hz regardless of render rate.
3. Mapped keys flip the corresponding action state.

## Test cases

| # | Test | What it asserts |
|---|------|-----------------|
| 1 | `test_settings_constants` | WIDTH=960, HEIGHT=540, FPS=60, FIXED_DT=1/60, TILE=32; types correct |
| 2 | `test_action_keys_mapping` | Actions exist; jump & struggle share Space; left bound to ←/A |
| 3 | `test_timestep_single_step` | One `FIXED_DT` of elapsed time yields exactly 1 step |
| 4 | `test_timestep_accumulates` | Two half-steps yield 1 step; leftover kept in accumulator |
| 5 | `test_timestep_multiple_steps` | 3×dt yields 3 steps |
| 6 | `test_timestep_clamp` | A huge frame_time is clamped (no spiral of death) |
| 7 | `test_timestep_determinism` | Many small frames ≈ total_time/dt steps (fixed-rate property) |
| 8 | `test_input_press_hold_release` | KEYDOWN→just_pressed+held; next frame→held only; KEYUP→just_released |
| 9 | `test_input_multikey_action` | Action stays held until *all* its keys are released |
| 10 | `test_state_manager_change` | `change` swaps state, fires on_exit/on_enter, dispatches update/draw |
| 11 | `test_state_manager_push_pop` | push/pop maintain the stack and `current` |
| 12 | `test_game_headless_runs` | `Game().run(max_frames=5)` runs 5 frames, no exception, surfaces sized right |
| 13 | `test_game_quit_event` | A posted QUIT event stops the loop |
| 14 | `test_menu_to_play_transition` | "confirm" in Menu transitions to Play |
| 15 | `test_fixed_update_runs` | Driving the loop advances `update_count` at the fixed rate |

## Exit condition

All tests pass (0 failures, 0 errors). Any failure is root-caused and fixed
before the milestone is considered done.
