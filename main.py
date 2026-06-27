"""Xynthra Platformer — entry point.

Window (960x540, integer-scaled), fixed-timestep loop at 60 Hz, and a state
manager with Menu / Play / GameOver. Milestone 2 adds the playable character
(movement, collision, sprite animation); Milestone 4 adds shooting.

Run:  python main.py
Controls:  arrows/A,D move - Space jump - Down crouch - J shoot - Up/Down aim
           - Enter/Space confirm - Esc quit - F11 fullscreen.
"""

import os

import pygame

import settings as S
from core.input import InputManager
from core.state import State, StateManager
from core.timestep import FixedTimestep
from ui.hud import draw_charge_meter


# ---------------------------------------------------------------- text helper
_FONT_CACHE = {}


def _font(size):
    if size not in _FONT_CACHE:
        try:
            _FONT_CACHE[size] = pygame.font.Font(None, size)  # built-in font
        except Exception:  # noqa: BLE001 - degrade gracefully if font unavailable
            _FONT_CACHE[size] = None
    return _FONT_CACHE[size]


def draw_text_center(surface, text, size, color, cy):
    f = _font(size)
    if not f:
        return
    img = f.render(text, True, color)
    surface.blit(img, (surface.get_width() // 2 - img.get_width() // 2,
                       cy - img.get_height() // 2))


# ---------------------------------------------------------------- states
class MenuState(State):
    def update(self, dt):
        if self.game.input.just_pressed("confirm"):
            self.game.states.change(PlayState(self.game))

    def draw(self, surface):
        surface.fill(S.MENU_BG_COLOR)
        draw_text_center(surface, "XYNTHRA", 110, (235, 225, 180), 190)
        draw_text_center(surface, "Press Enter to Play", 48, (210, 210, 220), 300)
        draw_text_center(
            surface,
            "Move: Arrows / A,D   Jump: Space   Crouch: Down   Shoot: J   Quit: Esc",
            28, (150, 150, 165), 360)


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
        self.projectiles = []

    def update(self, dt):
        self.player.update(dt, self.tilemap, self.game.input)
        if self.player.fired:
            self.projectiles.extend(self.player.fired)
        for p in self.projectiles:
            p.update(dt, self.tilemap)
        self.projectiles = [p for p in self.projectiles if p.alive]

    def draw(self, surface):
        surface.fill(S.PLAY_BG_COLOR)
        ox = _clamp(self.player.aabb.centerx - S.WIDTH / 2,
                    0, max(0, self.tilemap.pixel_width - S.WIDTH))
        oy = _clamp(self.player.aabb.bottom - S.HEIGHT * 0.7,
                    0, max(0, self.tilemap.pixel_height - S.HEIGHT))
        for r in self.tilemap.solid_rects():
            pygame.draw.rect(surface, (70, 76, 92), (r.x - ox, r.y - oy, r.w, r.h))
        # one-way platforms drawn as thin ledges so they read as pass-through
        for r in self.tilemap.oneway_rects():
            pygame.draw.rect(surface, (120, 100, 80), (r.x - ox, r.y - oy, r.w, 8))
        for p in self.projectiles:
            p.draw(surface, (ox, oy))
        self.player.draw(surface, (ox, oy))
        draw_charge_meter(surface, self.player)


class GameOverState(State):
    def update(self, dt):
        if self.game.input.just_pressed("confirm"):
            self.game.states.change(MenuState(self.game))

    def draw(self, surface):
        surface.fill(S.GAMEOVER_BG_COLOR)
        draw_text_center(surface, "GAME OVER", 96, (235, 180, 180), 220)
        draw_text_center(surface, "Press Enter for Menu", 40, (210, 200, 200), 320)


# ---------------------------------------------------------------- game
class Game:
    def __init__(self):
        os.environ.setdefault("SDL_VIDEO_CENTERED", "1")
        pygame.init()
        _FONT_CACHE.clear()  # fonts from a prior pygame session are now invalid
        self.internal = pygame.Surface(S.INTERNAL_SIZE)
        self.fullscreen = bool(S.FULLSCREEN)
        self._setup_display()
        self.clock = pygame.time.Clock()
        self.input = InputManager()
        self.states = StateManager()
        self.timestep = FixedTimestep(S.FIXED_DT, S.MAX_FRAME_TIME)
        self.running = True
        self.update_count = 0
        self.frame_count = 0
        self.states.change(MenuState(self))

    # --- display sizing ---
    def _desktop_size(self):
        try:
            return pygame.display.get_desktop_sizes()[0]
        except Exception:  # noqa: BLE001 - older pygame / headless
            info = pygame.display.Info()
            return (info.current_w, info.current_h)

    @staticmethod
    def _fit_scale(avail_w, avail_h):
        return max(1, min(avail_w // S.WIDTH, avail_h // S.HEIGHT))

    def _setup_display(self):
        dw, dh = self._desktop_size()
        if self.fullscreen and dw > 0 and dh > 0:
            self.window = pygame.display.set_mode((dw, dh), pygame.FULLSCREEN)
            self.scale = self._fit_scale(dw, dh)
        else:
            cap = max(1, S.WINDOW_SCALE)
            avail_h = (dh - S.WINDOW_TASKBAR_MARGIN) if dh > 0 else 0
            self.scale = min(cap, self._fit_scale(dw if dw > 0 else S.WIDTH,
                                                  avail_h if avail_h > 0 else S.HEIGHT))
            self.window = pygame.display.set_mode((S.WIDTH * self.scale, S.HEIGHT * self.scale))
        ww, wh = self.window.get_size()
        sw, sh = S.WIDTH * self.scale, S.HEIGHT * self.scale
        self.dest = pygame.Rect((ww - sw) // 2, (wh - sh) // 2, sw, sh)
        pygame.display.set_caption(S.CAPTION)

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        self._setup_display()

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
            if self.input.just_pressed("fullscreen"):
                self.toggle_fullscreen()

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
        if self.scale == 1 and self.window.get_size() == S.INTERNAL_SIZE:
            self.window.blit(self.internal, (0, 0))
        else:
            self.window.fill((0, 0, 0))  # letterbox bars
            scaled = pygame.transform.scale(self.internal, (self.dest.w, self.dest.h))
            self.window.blit(scaled, self.dest.topleft)
        pygame.display.flip()


def main():
    game = Game()
    try:
        game.run()
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
