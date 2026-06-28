"""Xynthra — the player, built on the shared ``Actor`` humanoid base.

Adds the player-specific layer on top of Actor: input-driven run/air control,
variable-height jump with coyote time + jump buffer, crouch (hitbox + visible
squash), one-way drop-through, directional shooting with a 3-level charge, a
damage model (knockback + mercy i-frames + blink), healing/belly, and the
swallowed held-state. Physics, facing, the defeat sequence, and the base sprite
draw come from Actor.

Shooting/charge note: the attack (shoot) pose plays on press and again on a
charged release, but it does NOT stay frozen while charging — the short
non-looping pose expires back to idle/run during the hold.
"""

import pygame

import settings as S
from core.physics import AABB, approach
from entities.actor import Actor
from entities.projectile import Projectile


class Player(Actor):
    def __init__(self, x, y, animations=None):
        super().__init__(AABB(x, y, S.PLAYER_W, S.PLAYER_H), animations,
                         hp=S.PLAYER_MAX_HP)
        self.facing = S.DEFAULT_FACING
        self.crouching = False
        self.coyote = 0.0
        self.jump_buffer = 0.0
        self.drop_through_top = None
        self.shoot_cd = 0.0          # time until the next press-shot is allowed
        self.shoot_timer = 0.0       # how long the shoot/attack pose holds after a shot
        self.charging = False        # holding the shoot button to charge
        self.charge_time = 0.0       # seconds the current charge has been held
        self.iframes = 0.0           # mercy invincibility remaining
        self.control_lock = 0.0      # input ignored (knockback) remaining
        self.belly = 0               # stored healing pickups (0..BELLY_MAX)
        self.heal_timer = 0.0        # progress holding Heal while idle
        self.healing = False         # currently digesting a pickup
        self.swallowed = False       # inside an enemy (struggle minigame is M10)
        self.swallowed_by = None     # the enemy that swallowed her

    @property
    def stand_height(self):
        return S.PLAYER_H

    @property
    def crouch_height(self):
        return S.PLAYER_H * S.CROUCH_HEIGHT_FACTOR

    @property
    def visible(self):
        """False on the 'off' phase of the i-frame blink (used by draw). The
        defeat sprite never blinks, so a dying/dead player stays visible."""
        if self.dead or self.iframes <= 0.0:
            return True
        return int(self.iframes / S.BLINK_INTERVAL) % 2 == 0

    def take_damage(self, amount, source_x):
        """Apply a normal damaging hit: knockback away from ``source_x`` plus
        mercy i-frames. No-op (returns False) while already invincible or dead.
        On a fatal hit, starts the defeat animation."""
        if self.iframes > 0.0 or self.dead:
            return False
        self.hp = max(0, self.hp - amount)
        direction = -1.0 if source_x >= self.aabb.centerx else 1.0
        self.vx = direction * S.KNOCKBACK_VX
        self.vy = S.KNOCKBACK_VY
        self.control_lock = S.KNOCKBACK_CONTROL_LOCK
        self.iframes = S.IFRAME_TIME
        self.on_ground = False
        self.heal_timer = 0.0        # a hit interrupts digesting
        self.healing = False
        if self.hp <= 0:
            self._enter_death()
        return True

    def _enter_death(self):
        self.charging = False
        self.shoot_timer = 0.0
        super()._enter_death()

    def swallow(self):
        """Store a healing pickup (the shrunken lady). Capped at BELLY_MAX."""
        if self.belly >= S.BELLY_MAX:
            return False
        self.belly += 1
        return True

    def enter_swallow(self, enemy):
        """Get swallowed by an enemy (Big contact). Milestone 9 just enters the
        held state and freezes movement; the struggle minigame is Milestone 10.
        No-op while already swallowed, in i-frames, or dead."""
        if self.swallowed or self.dead or self.iframes > 0.0:
            return False
        self.swallowed = True
        self.swallowed_by = enemy
        self.vx = 0.0
        self.vy = 0.0
        self.charging = False
        self.charge_time = 0.0
        self.shoot_timer = 0.0
        self.healing = False
        self.heal_timer = 0.0
        return True

    @property
    def heal_fraction(self):
        return min(self.heal_timer / S.HEAL_HOLD, 1.0) if S.HEAL_HOLD else 0.0

    def _update_healing(self, dt, inp, want_left, want_right, want_crouch, jump_pressed):
        """Hold Heal while idle (with a stored pickup AND below max HP) to
        digest one over HEAL_HOLD seconds for +HEAL_AMOUNT HP. The progress bar
        is only shown while a heal is actually possible, so it disappears the
        instant HP reaches max. Any movement, jump, crouch, or hit interrupts it."""
        moving = (want_left or want_right or want_crouch or jump_pressed
                  or not self.on_ground or abs(self.vx) > S.HEAL_MOVE_EPS)
        can_heal = (inp.is_held("heal") and self.belly > 0
                    and self.hp < S.PLAYER_MAX_HP and not moving)
        if can_heal:
            self.healing = True
            self.heal_timer += dt
            if self.heal_timer >= S.HEAL_HOLD:
                self.hp = min(S.PLAYER_MAX_HP, self.hp + S.HEAL_AMOUNT)
                self.belly -= 1
                self.heal_timer = 0.0
        else:
            self.healing = False
            self.heal_timer = 0.0

    def update(self, dt, tilemap, inp):
        if self.dead:
            self._tick_death(dt, tilemap)
            return
        if self.swallowed:
            # Milestone 9 placeholder: held in place (no input, no physics).
            # Milestone 10 replaces this with the struggle minigame.
            if self.animator:
                self.animator.update(dt)
            return

        self.iframes = max(0.0, self.iframes - dt)
        self.control_lock = max(0.0, self.control_lock - dt)

        want_left = inp.is_held("left")
        want_right = inp.is_held("right")
        want_crouch = inp.is_held("down")
        jump_pressed = inp.just_pressed("jump")
        jump_held = inp.is_held("jump")

        locked = self.control_lock > 0.0
        if not locked:
            accel = S.GROUND_ACCEL if self.on_ground else S.AIR_ACCEL
            if want_left and not want_right:
                self.facing = "left"
                self.vx = approach(self.vx, -S.RUN_SPEED, accel * dt)
            elif want_right and not want_left:
                self.facing = "right"
                self.vx = approach(self.vx, S.RUN_SPEED, accel * dt)
            else:
                friction = S.GROUND_FRICTION if self.on_ground else S.AIR_ACCEL
                self.vx = approach(self.vx, 0.0, friction * dt)

        self._apply_gravity(dt)

        self.coyote = S.COYOTE_TIME if self.on_ground else max(0.0, self.coyote - dt)
        self.jump_buffer = S.JUMP_BUFFER if jump_pressed else max(0.0, self.jump_buffer - dt)

        self._apply_crouch(want_crouch and not locked)

        if not locked:
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

        self._collide(dt, tilemap, self.drop_through_top)
        if self.on_ground or self.vy < 0:
            self.drop_through_top = None

        self._update_shooting(dt, inp)
        self._update_healing(dt, inp, want_left, want_right, want_crouch, jump_pressed)

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
        """Press fires a level-1 shot (and plays the attack pose) and starts
        charging; holding builds the charge without re-holding the pose;
        releasing fires the charged shot (level 2+) and plays the pose again."""
        self.fired = []
        self.shoot_cd = max(0.0, self.shoot_cd - dt)
        self.shoot_timer = max(0.0, self.shoot_timer - dt)

        pressed = inp.just_pressed("shoot")
        held = inp.is_held("shoot")
        released = inp.just_released("shoot")

        if self.charging and held:
            self.charge_time += dt

        if pressed and self.shoot_cd <= 0.0:
            self._fire(inp, 1)
            self.charging = True
            self.charge_time = 0.0

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
        self.shoot_timer = S.SHOOT_POSE_TIME   # attack pose on every shot

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
        # the attack row is the shoot pose; it plays briefly on each shot and
        # expires on its own (charging alone does NOT hold the attack frame)
        if self.shoot_timer > 0.0 and self.on_ground:
            state = "attack"
        self._play_state(state)

    def _draw_belly(self, surface, offset):
        """Simple belly marker: one small pip per stored pickup (placeholder
        for the 4 belly states, since the sheet has no belly frames)."""
        if self.belly <= 0 or self.dead:
            return
        ox, oy = offset
        s, gap = 4, 2
        n = self.belly
        total = n * s + (n - 1) * gap
        x = self.aabb.centerx - ox - total / 2.0
        y = self.aabb.top + self.aabb.height * 0.55 - oy
        for _ in range(n):
            pygame.draw.rect(surface, S.HUD_BELLY_FULL, (round(x), round(y), s, s))
            x += s + gap

    def sprite_image(self):
        if not self.animator:
            return None
        img = self.animator.image(self.facing)
        if self.crouching and not self.dead:
            w = img.get_width()
            h = max(1, int(round(img.get_height() * S.CROUCH_HEIGHT_FACTOR)))
            img = pygame.transform.scale(img, (w, h))
        return img

    def draw(self, surface, offset=(0, 0)):
        if self.swallowed:
            return                              # inside an enemy: sprite hidden
        if not self.visible:
            return                              # blink "off" frame during i-frames
        super().draw(surface, offset)           # feet-anchored sprite (uses sprite_image)
        self._draw_belly(surface, offset)
