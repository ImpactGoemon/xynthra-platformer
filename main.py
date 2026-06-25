"""Xynthra Platformer — entry point.

Window (960x540, integer-scaled), fixed-timestep loop at 60 Hz, and a state
manager with Menu / Play / GameOver. Milestone 2 adds the playable character
(movement, collision, sprite animation) in the Play state.

Run:  python main.py
Controls:  arrows/A,D move - Space jump - Down crouch - Enter/Space confirm - Esc quit.
"""

import pygame

import settings as S
from core.input import InputManager
from core.state import State, StateManager
from core.timestep import FixedTimestep


# ---------------------------------------------------------------- states
class MenuState(State):
    def update(self, dt):
        if self.game.input.just_pressed("confirm"):
            self.game.states.change(PlayState(self.game))

    def draw(self, surface):
        surface.fill(S.MENU_BG_COLOR)


def _clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


class PlayState(State):
    def on_enter(self):
        from world.level1 import build_level
        from entities.player import Player

        self.tilemap, spawn = build_level()
        animations = None
        try:
            from assets import build_player_animations
            animations = build_player_animations()
        except Exception as exc:  # noqa: BLE001 - degrade to a shape, don't crash
            print(f"[assets] player sprite load failed, using shape: {exc}")
        self.player = Player(spawn[0], spawn[1], animations)

    def update(self, dt):
        self.player.update(dt, self.tilemap, self.game.input)

    def draw(self, surface):
        surface.fill(S.PLAY_BG_COLOR)
        ox = _clamp(self.player.aabb.centerx - S.WIDTH / 2,
                    0, max(0, self.tilemap.pixel_width - S.WIDTH))
        oy = _clamp(self.player.aabb.bottom - S.HEIGHT * 0.7,
                    0, max(0, self.tilemap.pixel_height - S.HEIGHT))
        for r in self.tilemap.solid_rects():
            pygame.draw.rect(surface, (70, 76, 92), (r.x - ox, r.y - oy, r.w, r.h))
        self.player.draw(surface, (ox, oy))


class GameOverState(State):
    def update(self, dt):
        if self.game.input.just_pressed("confirm"):
            self.game.states.change(MenuState(self.game))

    def draw(self, surface):
        surface.fill(S.GAMEOVER_BG_COLOR)


# ---------------------------------------------------------------- game
class Game:
    def __init__(self):
        pygame.init()
        self.internal = pygame.Surface(S.INTERNAL_SIZE)
        self.window = pygame.display.set_mode(
            (S.WIDTH * S.WINDOW_SCALE, S.HEIGHT * S.WINDOW_SCALE)
        )
        pygame.display.set_caption(S.CAPTION)
        self.clock = pygame.time.Clock()
        self.input = InputManager()
        self.states = StateManager()
        self.timestep = FixedTimestep(S.FIXED_DT, S.MAX_FRAME_TIME)
        self.running = True
        self.update_count = 0
        self.frame_count = 0
        self.states.change(MenuState(self))

    def run(self, max_frames=None):
        while self.running:
            frame_time = self.clock.tick(S.FPS) / 1000.0

            self.input.begin_frame()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                self.input.process_event(event)
                self.states.handle_event(event)

            if self.input.just_pressed("quit"):
                self.running = False

            for _ in range(self.timestep.advance(frame_time)):
                self.states.update(S.FIXED_DT)
                self.update_count += 1

            self.states.draw(self.internal)
            self._present()

            self.frame_count += 1
            if max_frames is not None and self.frame_count >= max_frames:
                self.running = False
        return self.frame_count

    def _present(self):
        if S.WINDOW_SCALE == 1:
            self.window.blit(self.internal, (0, 0))
        else:
            pygame.transform.scale(self.internal, self.window.get_size(), self.window)
        pygame.display.flip()


def main():
    game = Game()
    try:
        game.run()
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
