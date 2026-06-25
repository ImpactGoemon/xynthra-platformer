"""Xynthra — Milestone 2 movement + animation state machine.

Run accel/friction, air control, variable-height jump with coyote time and jump
buffer, crouch (shrinks hitbox), and an animation state machine that picks
idle/run/jump/fall and flips by facing. Shooting/health/etc. arrive later.
"""

import pygame

import settings as S
from core.animation import Animator
from core.physics import AABB, move_and_collide


def _approach(value, target, max_delta):
    if value < target:
        return min(value + max_delta, target)
    return max(value - max_delta, target)


class Player:
    def __init__(self, x, y, animations=None):
        self.aabb = AABB(x, y, S.PLAYER_W, S.PLAYER_H)
        self.vx = 0.0
        self.vy = 0.0
        self.facing = S.DEFAULT_FACING        # "left" by default (source art)
        self.on_ground = False
        self.crouching = False
        self.coyote = 0.0
        self.jump_buffer = 0.0
        self.state = "idle"
        self.animator = Animator(animations) if animations else None
        if self.animator:
            self.animator.play("idle")

    @property
    def stand_height(self):
        return S.PLAYER_H

    @property
    def crouch_height(self):
        return S.PLAYER_H * S.CROUCH_HEIGHT_FACTOR

    def update(self, dt, tilemap, inp):
        want_left = inp.is_held("left")
        want_right = inp.is_held("right")
        want_crouch = inp.is_held("down")
        jump_pressed = inp.just_pressed("jump")
        jump_held = inp.is_held("jump")

        # --- horizontal accel / friction ---
        accel = S.GROUND_ACCEL if self.on_ground else S.AIR_ACCEL
        if want_left and not want_right:
            self.facing = "left"
            self.vx = _approach(self.vx, -S.RUN_SPEED, accel * dt)
        elif want_right and not want_left:
            self.facing = "right"
            self.vx = _approach(self.vx, S.RUN_SPEED, accel * dt)
        else:
            friction = S.GROUND_FRICTION if self.on_ground else S.AIR_ACCEL
            self.vx = _approach(self.vx, 0.0, friction * dt)

        # --- gravity ---
        self.vy += S.GRAVITY * dt
        if self.vy > S.MAX_FALL:
            self.vy = S.MAX_FALL

        # --- coyote time + jump buffer ---
        self.coyote = S.COYOTE_TIME if self.on_ground else max(0.0, self.coyote - dt)
        self.jump_buffer = S.JUMP_BUFFER if jump_pressed else max(0.0, self.jump_buffer - dt)

        # --- crouch resizes hitbox (anchored at the feet) ---
        self._apply_crouch(want_crouch)

        # --- jump (buffered + coyote) ---
        if self.jump_buffer > 0.0 and self.coyote > 0.0:
            self.vy = S.JUMP_VELOCITY
            self.jump_buffer = 0.0
            self.coyote = 0.0
            self.on_ground = False

        # --- variable height: cut the rise on early release ---
        if self.vy < 0 and not jump_held and self.vy < S.JUMP_CUT_VELOCITY:
            self.vy = S.JUMP_CUT_VELOCITY

        # --- move + collide ---
        flags, self.vx, self.vy = move_and_collide(self.aabb, self.vx, self.vy, dt, tilemap)
        self.on_ground = flags["ground"]

        # --- animation state ---
        self._update_state()
        if self.animator:
            self.animator.update(dt)

    def _apply_crouch(self, want):
        if want and self.on_ground and not self.crouching:
            bottom = self.aabb.bottom
            self.aabb.height = self.crouch_height
            self.aabb.bottom = bottom
            self.crouching = True
        elif (not want or not self.on_ground) and self.crouching:
            bottom = self.aabb.bottom
            self.aabb.height = self.stand_height
            self.aabb.bottom = bottom
            self.crouching = False

    def _update_state(self):
        if not self.on_ground:
            state = "jump" if self.vy < 0 else "fall"
        elif self.crouching:
            state = "idle"          # no crouch frame in the sheet (squashed idle)
        elif abs(self.vx) > S.RUN_ANIM_SPEED:
            state = "run"
        else:
            state = "idle"
        if state != self.state:
            self.state = state
            if self.animator:
                self.animator.play(state)

    def draw(self, surface, offset=(0, 0)):
        ox, oy = offset
        if self.animator:
            img = self.animator.image(self.facing)
            x = self.aabb.centerx - img.get_width() / 2.0 - ox
            y = self.aabb.bottom - img.get_height() - oy
            surface.blit(img, (round(x), round(y)))
        else:
            pygame.draw.rect(
                surface, S.MARKER_COLOR,
                (round(self.aabb.x - ox), round(self.aabb.y - oy),
                 round(self.aabb.w), round(self.aabb.h)),
            )
