"""Actor — the shared *humanoid character* base for Xynthra and the enemies.

It bundles the behaviour that Player and Enemy were duplicating:
- kinematics: ``_apply_gravity`` + ``_collide`` (AABB vs tiles, sets on_ground /
  on_oneway and stores the last collision flags for wall-aware AI),
- facing toward a target (``_face``),
- the defeat sequence: ``_enter_death`` + ``_tick_death`` (settle + play the
  defeat animation, then flag ``death_done``),
- a feet-anchored, facing-flipped sprite ``draw`` (with a colored-rect fallback)
  built on an overridable ``sprite_image``.

Subclasses keep their own ``update`` orchestration (the Player reads input; the
Enemy runs an AI), but build it from these primitives. Pickups/projectiles are
plain ``Entity`` objects, not Actors — they share the root, not this behaviour.
"""

import pygame

import settings as S
from core.animation import Animator
from core.physics import AABB, approach, move_and_collide
from entities.entity import Entity


class Actor(Entity):
    def __init__(self, aabb, animations=None, hp=0, contact_damage=0):
        super().__init__(aabb)
        self.vx = 0.0
        self.vy = 0.0
        self.facing = "left"           # source art faces left; flip for right
        self.on_ground = False
        self.on_oneway = False
        self._flags = {}               # last move_and_collide flags (wall-aware AI)
        self.hp = hp
        self.contact_damage = contact_damage
        self.dead = False              # in the defeat animation
        self.death_timer = 0.0
        self.death_done = False        # True once the defeat animation finishes
        self.fired = []                # projectiles spawned this frame (drained by PlayState)
        self.state = "idle"
        self.animator = Animator(animations) if animations else None
        if self.animator:
            self.animator.play("idle")

    @staticmethod
    def feet_aabb(x_feet, y_feet, w, h):
        """Build an AABB anchored by the feet (bottom-centre)."""
        return AABB(x_feet - w / 2.0, y_feet - h, w, h)

    # ------------------------------------------------------------------ kinematics
    def _apply_gravity(self, dt):
        self.vy += S.GRAVITY * dt
        if self.vy > S.MAX_FALL:
            self.vy = S.MAX_FALL

    def _collide(self, dt, tilemap, drop_through_top=None):
        """Move the AABB against tiles; update on_ground/on_oneway and store flags."""
        flags, self.vx, self.vy = move_and_collide(
            self.aabb, self.vx, self.vy, dt, tilemap,
            drop_through_top=drop_through_top)
        self.on_ground = flags["ground"]
        self.on_oneway = flags.get("ground_oneway", False)
        self._flags = flags
        return flags

    def _face(self, target):
        self.facing = "left" if target.aabb.centerx <= self.aabb.centerx else "right"

    # ------------------------------------------------------------------ death
    def _enter_death(self):
        self.dead = True
        self.death_timer = S.DEFEAT_HOLD
        self.death_done = False
        self.state = "defeat"
        if self.animator:
            self.animator.play("defeat", restart=True)

    def _tick_death(self, dt, tilemap):
        """Ignore input, settle under gravity + friction, and play the defeat
        animation to completion before signalling ``death_done``."""
        self.death_timer = max(0.0, self.death_timer - dt)
        self._apply_gravity(dt)
        friction = S.GROUND_FRICTION if self.on_ground else S.AIR_ACCEL
        self.vx = approach(self.vx, 0.0, friction * dt)
        self._collide(dt, tilemap)
        if self.animator:
            self.animator.update(dt)
        if (self.animator and self.animator.finished) or self.death_timer <= 0.0:
            self.death_done = True

    # ------------------------------------------------------------------ animation
    def _play_state(self, state):
        if state != self.state:
            self.state = state
            if self.animator:
                self.animator.play(state)

    def sprite_image(self):
        """Current animation frame for the facing (or None if art is missing).
        Overridden by Player to add the crouch squash."""
        return self.animator.image(self.facing) if self.animator else None

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
                 round(self.aabb.w), round(self.aabb.h)))
