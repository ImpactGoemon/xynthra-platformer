"""Enemies — built on the shared ``Actor`` humanoid base.

- **Small** (M8): 3 HP, ~1x size. ``turret`` (stationary, fires every ~2 s) or
  ``jumper`` (jumps every ~2.5 s, fires at the apex). Deals 1 contact damage.
- **Big** (M9): 5 HP, ~1.85x size. Idle until it detects Xynthra, then pursues
  (run + jump) and on contact **swallows** her instead of a normal hit.

Player shots reduce HP; at 0 HP they play the defeat animation then are removed
(``alive`` -> False). Source art faces left (flip for right).
"""

import math

import settings as S
from core.physics import approach
from entities.actor import Actor
from entities.projectile import Projectile


class Enemy(Actor):
    def __init__(self, x_feet, y_feet, hp, w, h, animations=None, contact_damage=1):
        super().__init__(Actor.feet_aabb(x_feet, y_feet, w, h),
                         animations, hp, contact_damage)
        self.swallows = False          # True for enemies whose contact swallows (Big)
        self.has_swallowed = False     # True while it is holding a swallowed player

    # -------------------------------------------------------------- damage/death
    def take_damage(self, amount):
        if self.dead:
            return False
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self._enter_death()
        return True

    def _enter_death(self):
        self.vx = 0.0
        super()._enter_death()

    # -------------------------------------------------------------- helpers
    def _physics(self, dt, tilemap):
        self._apply_gravity(dt)
        self._collide(dt, tilemap)

    def _shoot_at(self, player, speed, damage, size, color):
        d = -1 if player.aabb.centerx <= self.aabb.centerx else 1
        a = self.aabb
        ox = a.right if d > 0 else a.left
        oy = a.top + a.height * 0.4
        self.fired.append(Projectile(ox, oy, d, 0, speed=speed, damage=damage,
                                     size=size, color=color, owner="enemy"))

    def _update_state(self):
        if self.dead:
            return
        if not self.on_ground:
            self._play_state("jump" if self.vy < 0 else "fall")
        else:
            self._play_state("idle")

    # -------------------------------------------------------------- update
    def update(self, dt, tilemap, player):
        self.fired = []
        if self.dead:
            self._tick_death(dt, tilemap)
            if self.death_done:
                self.alive = False
            return
        self._face(player)
        if self.has_swallowed:
            # holding a swallowed player: stand idle (no pursuit)
            self.vx = approach(self.vx, 0.0, S.GROUND_FRICTION * dt)
        else:
            self._ai(dt, tilemap, player)
        self._physics(dt, tilemap)
        self._update_state()
        if self.animator:
            self.animator.update(dt)

    def _ai(self, dt, tilemap, player):
        """Override in subclasses."""


class Small(Enemy):
    """3 HP, ~1x size. variant = 'turret' (stationary shooter) or 'jumper'."""

    def __init__(self, x_feet, y_feet, variant="turret", animations=None):
        super().__init__(x_feet, y_feet, S.SMALL_HP, S.SMALL_W, S.SMALL_H,
                         animations, S.SMALL_CONTACT_DAMAGE)
        self.variant = variant
        self.fire_timer = S.SMALL_TURRET_INTERVAL
        self.jump_timer = S.SMALL_JUMPER_INTERVAL
        self.fired_this_jump = True

    def _shoot(self, player):
        self._shoot_at(player, S.SMALL_PROJECTILE_SPEED, S.SMALL_PROJECTILE_DAMAGE,
                       S.SMALL_PROJECTILE_SIZE, S.SMALL_PROJECTILE_COLOR)

    def _ai(self, dt, tilemap, player):
        if self.variant == "turret":
            self.fire_timer -= dt
            if self.fire_timer <= 0.0:
                self.fire_timer += S.SMALL_TURRET_INTERVAL
                self._shoot(player)
        else:  # jumper
            if self.on_ground:
                self.jump_timer -= dt
                if self.jump_timer <= 0.0:
                    self.jump_timer += S.SMALL_JUMPER_INTERVAL
                    self.vy = S.SMALL_JUMP_VELOCITY
                    self.on_ground = False
                    self.fired_this_jump = False
            # fire once at the apex (upward motion just turned to falling)
            elif not self.fired_this_jump and self.vy >= 0.0:
                self._shoot(player)
                self.fired_this_jump = True


class Big(Enemy):
    """5 HP, ~1.85x size. Idle until it detects Xynthra within BIG_DETECT_RADIUS,
    then pursues (run toward her, jump when blocked by a wall or when she is
    above). On contact it swallows her (``swallows = True``). Cannot be knocked
    back; deals no normal contact damage."""

    def __init__(self, x_feet, y_feet, animations=None):
        super().__init__(x_feet, y_feet, S.BIG_HP, S.BIG_W, S.BIG_H,
                         animations, S.BIG_CONTACT_DAMAGE)
        self.swallows = True
        self.detected = False
        self.jump_cd = 0.0

    def _ai(self, dt, tilemap, player):
        self.jump_cd = max(0.0, self.jump_cd - dt)
        a, pa = self.aabb, player.aabb
        dx = pa.centerx - a.centerx
        dy = (pa.top + pa.h / 2.0) - (a.top + a.h / 2.0)
        dist = math.hypot(dx, dy)

        if not self.detected and dist <= S.BIG_DETECT_RADIUS:
            self.detected = True

        if not self.detected:
            # idle: slow to a stop until she comes into range
            self.vx = approach(self.vx, 0.0, S.BIG_ACCEL * dt)
            return

        # pursue: accelerate toward her at the run speed
        target = -S.BIG_SPEED if dx < 0 else S.BIG_SPEED
        self.vx = approach(self.vx, target, S.BIG_ACCEL * dt)

        # jump to reach her: grounded and either blocked by a wall in the travel
        # direction or she is clearly above us
        if self.on_ground and self.jump_cd <= 0.0:
            blocked = (target < 0 and self._flags.get("wall_l")) or \
                      (target > 0 and self._flags.get("wall_r"))
            player_above = pa.bottom < a.top - S.BIG_PLAYER_ABOVE_MARGIN
            if blocked or player_above:
                self.vy = S.BIG_JUMP_VELOCITY
                self.on_ground = False
                self.jump_cd = S.BIG_JUMP_COOLDOWN

    def _update_state(self):
        if self.dead:
            return
        if not self.on_ground:
            self._play_state("jump" if self.vy < 0 else "fall")
        elif abs(self.vx) > S.RUN_ANIM_SPEED:
            self._play_state("run")
        else:
            self._play_state("idle")
