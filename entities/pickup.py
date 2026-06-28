"""Pickup — a "shrunken lady" Xynthra can swallow to store a heal.

A pickup is a plain ``Entity`` (an aabb + a static image), NOT an Actor: it has
no physics, health, or AI. Drawn as the Schoolgirl Girl_1 idle sprite scaled to
~1/4 of Xynthra's height (see assets.build_pickup_image), anchored by its feet.
On contact the Play state calls ``player.swallow()`` and removes the pickup.
"""

import pygame

import settings as S
from core.physics import AABB
from entities.entity import Entity


class Pickup(Entity):
    def __init__(self, x_feet, y_feet, image=None):
        self.image = image
        if image is not None:
            w, h = image.get_size()
        else:
            w, h = S.PICKUP_FALLBACK_SIZE
        super().__init__(AABB(x_feet - w / 2.0, y_feet - h, w, h))
        self.collected = False

    def draw(self, surface, offset=(0, 0)):
        ox, oy = offset
        x = round(self.aabb.x - ox)
        y = round(self.aabb.y - oy)
        if self.image is not None:
            surface.blit(self.image, (x, y))
        else:
            pygame.draw.rect(
                surface, S.PICKUP_FALLBACK_COLOR,
                (x, y, round(self.aabb.w), round(self.aabb.h)))
