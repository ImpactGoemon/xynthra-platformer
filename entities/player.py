"""Xynthra — movement, collision, animation, shooting, and charge shots.

Run accel/friction, air control, variable-height jump with coyote time + jump
buffer, crouch (shrinks hitbox + visible squash), one-way drop-through, an
animation state machine (idle/run/jump/fall) that flips by facing, and
directional shooting with a 3-level charge: tapping fires a level-1 shot and
begins charging; releasing after the level-2/3 hold time fires a larger,
stronger shot.
"""

import pygame

import settings as S
from core.animation import Animator
from core.physics import AABB, move_and_collide
from entities.projectile import Projectile


def _approach(value, target, max_delta):
    if value < target:
        return min(value + max_delta, target)
    return max(value - max_delta, target)


class Player:
    def __init__(self, x, y, animations=None):
        self.aabb = AABB(x, y, S.PLAYER_W, S.PLAYER_H)
        self.vx = 0.0
        self.vy = 0.0
        self.facing = S.DEFAULT_FACING
        self.on_ground = False
        self.on_oneway = False
        self.crouching = False
        self.coyote = 0.0
        self.jump_buffer = 0.0
        self.drop_through_top = None
        self.shoot_cd = 0.0          # time until the next press-shot is allowed
        self.shoot_timer = 0.0       # how long the shoot/attack pose holds
        self.charging = False        # holding the shoot button to charge
        self.charge_time = 0.0       # seconds the current charge has been held
        self.fired = []              # projectiles spawned this frame; PlayState drains it
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

        self.vy += S.GRAVITY * dt
        if self.vy > S.MAX_FALL:
            self.vy = S.MAX_FALL

        self.coyote = S.COYOTE_TIME if self.on_ground else max(0.0, self.coyote - dt)
        self.jump_buffer = S.JUMP_BUFFER if jump_pressed else max(0.0, self.jump_buffer - dt)

        self._apply_crouch(want_crouch)

        if jump_pressed and want_crouch and self.on_ground and self.on_oneway:
            # drop through only the ledge she is on (its top == her feet)
            self.drop_through_top = self.aabb.bottom
            self.jump_buffer = 0.0
            self.coyote = 0.0
            self.on_ground = False
        elif self.jump_buffer > 0.0 and self.coyote > 0.0:
            self.vy = S.JUMP_VELOCITY
            self.jump_buffer = 0.0
            self.coyote = 0.0
            self.on_ground = False
            self.drop_through_top = None

        if self.vy < 0 and not jump_held and self.vy < S.JUMP_CUT_VELOCITY:
            self.vy = S.JUMP_CUT_VELOCITY

        flags, self.vx, self.vy = move_and_collide(
            self.aabb, self.vx, self.vy, dt, tilemap,
            drop_through_top=self.drop_through_top,
        )
        self.on_ground = flags["ground"]
        self.on_oneway = flags.get("ground_oneway", False)
        if self.on_ground or self.vy < 0:
            self.drop_through_top = None

        self._update_shooting(dt, inp)

        self._update_state()
        if self.animator:
            self.animator.update(dt)

    # ------------------------------------------------------------------ shooting
    @staticmethod
    def _charge_level(t):
        if t >= S.CHARGE_L3_TIME:
            return 3
        if t >= S.CHARGE_L2_TIME:
            return 2
        return 1

    @property
    def charge_level(self):
        return self._charge_level(self.charge_time) if self.charging else 1

    def _update_shooting(self, dt, inp):
        """Press fires a level-1 shot and starts charging; holding builds the
        charge; releasing past the level-2/3 threshold fires the bigger shot.
        Aim-Up shoots up, Aim-Down shoots down only while airborne (Aim-Down on
        the ground is the low crouch shot)."""
        self.fired = []
        self.shoot_cd = max(0.0, self.shoot_cd - dt)
        self.shoot_timer = max(0.0, self.shoot_timer - dt)

        pressed = inp.just_pressed("shoot")
        held = inp.is_held("shoot")
        released = inp.just_released("shoot")

        # advance an active charge while the button stays down
        if self.charging and held:
            self.charge_time += dt

        # press: immediate level-1 shot, then begin charging
        if pressed and self.shoot_cd <= 0.0:
            self._fire(inp, 1)
            self.charging = True
            self.charge_time = 0.0

        # release: fire the charged shot if it reached level 2+
        if released and self.charging:
            level = self._charge_level(self.charge_time)
            if level >= 2:
                self._fire(inp, level)
            self.charging = False
            self.charge_time = 0.0

    def _fire(self, inp, level):
        aim_up = inp.is_held("up")
        aim_down = inp.is_held("down")
        if aim_up:
            dx, dy = 0, -1
        elif aim_down and not self.on_ground:
            dx, dy = 0, 1                      # down-shot only while airborne
        else:
            dx, dy = (-1 if self.facing == "left" else 1), 0

        a = self.aabb
        if dy < 0:                             # up
            ox, oy = a.centerx, a.top
        elif dy > 0:                           # down
            ox, oy = a.centerx, a.bottom
        else:                                  # horizontal (low when crouched)
            frac = S.MUZZLE_Y_CROUCH if self.crouching else S.MUZZLE_Y_STAND
            ox = a.right if self.facing == "right" else a.left
            oy = a.top + a.height * frac

        self.fired.append(Projectile(
            ox, oy, dx, dy,
            damage=S.CHARGE_DAMAGE[level],
            size=S.CHARGE_SIZE[level],
            color=S.CHARGE_COLORS[level],
        ))
        self.shoot_cd = S.FIRE_COOLDOWN
        self.shoot_timer = S.SHOOT_POSE_TIME

    # ------------------------------------------------------------------ helpers
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
            state = "idle"
        elif abs(self.vx) > S.RUN_ANIM_SPEED:
            state = "run"
        else:
            state = "idle"
        # the attack row doubles as the shoot/charge pose (placeholder); on the
        # ground it overrides idle/run/crouch while shooting or charging
        if (self.shoot_timer > 0.0 or self.charging) and self.on_ground:
            state = "attack"
        if state != self.state:
            self.state = state
            if self.animator:
                self.animator.play(state)

    def sprite_image(self):
        """Current frame, vertically squashed while crouching (placeholder crouch)."""
        if not self.animator:
            return None
        img = self.animator.image(self.facing)
        if self.crouching:
            w = img.get_width()
            h = max(1, int(round(img.get_height() * S.CROUCH_HEIGHT_FACTOR)))
            img = pygame.transform.scale(img, (w, h))
        return img

    def draw(self, surface, offset=(0, 0)):
        ox, oy = offset
        img = self.sprite_image()
        if img is not None:
            x = self.aabb.centerx - img.get_width() / 2.0 - ox
            y = self.aabb.bottom - img.get_height() - oy
            surface.blit(img, (round(x), round(y)))
        else:
            pygame.draw.rect(
                surface, S.MARKER_COLOR,
                (round(self.aabb.x - ox), round(self.aabb.y - oy),
                 round(self.aabb.w), round(self.aabb.h)),
            )
