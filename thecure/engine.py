import sys

import pygame
from pygame.locals import *

from thecure import set_engine
from thecure.levels import get_levels
from thecure.resources import get_font_filename
from thecure.signals import Signal
from thecure.sprites import Player


class Camera(object):
    SCREEN_PAD = 64

    def __init__(self, engine):
        self.engine = engine
        self.rect = self.engine.screen.get_rect()
        self.old_player_rect = None

    def update(self):
        player_rect = self.engine.player.rect

        if player_rect == self.old_player_rect:
            return

        if player_rect.centerx > self.rect.centerx + self.SCREEN_PAD:
            self.rect.centerx = player_rect.centerx - self.SCREEN_PAD
        elif player_rect.centerx < self.rect.centerx - self.SCREEN_PAD:
            self.rect.centerx = player_rect.centerx + self.SCREEN_PAD

        if player_rect.centery > self.rect.centery + self.SCREEN_PAD:
            self.rect.centery = player_rect.centery - self.SCREEN_PAD
        elif player_rect.centery < self.rect.centery - self.SCREEN_PAD:
            self.rect.centery = player_rect.centery + self.SCREEN_PAD

        self.rect.clamp_ip(
            pygame.Rect(0, 0, *self.engine.active_level.size))

        old_player_rect = player_rect


class TheCureEngine(object):
    FPS = 30
    DEBUG_COLOR = (255, 0, 0)
    DEBUG_POS = (30, 10)

    def __init__(self, screen):
        set_engine(self)

        # Signals
        self.tick = Signal()

        # Useful objects
        self._debug_font = pygame.font.Font(get_font_filename(), 16)

        # State and objects
        self.active_level = None
        self.paused = False
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.player = Player()
        self.levels = []
        self.level_draw_pos = (0, 0)
        self.level_draw_area = None

        # Debug flags
        self.debug_rects = False
        self.show_debug_info = False

    def run(self):
        self._setup_game()
        self._mainloop()

    def quit(self):
        pygame.quit()
        sys.exit(0)

    def set_level_draw_area(self, x, y, w, h):
        self.level_draw_pos = (x, y)
        self.level_draw_area = pygame.Rect(0, 0, w, h)

    def _setup_game(self):
        self.camera = Camera(self)
        self.tick.clear()

        self.player.reset()

        self.levels = [level(self) for level in get_levels()]
        self.switch_level(0)

        self.paused = False

    def switch_level(self, num):
        assert num < len(self.levels)

        if self.active_level:
            self.active_level.main_layer.remove(player)

        self.active_level = self.levels[num]
        self.active_level.reset()
        self.active_level.main_layer.add(self.player)
        self.player.reset()

        self.surface = pygame.Surface(self.active_level.size)

        self.player.move_to(*self.active_level.start_pos)
        self.camera.update()
        self.player.show()

        self.active_level.start()

    def _mainloop(self):
        while 1:
            for event in pygame.event.get():
                if not self._handle_event(event):
                    return

            self.tick.emit()
            self._draw()
            self.clock.tick(self.FPS)

    def _handle_event(self, event):
        if event.type == QUIT:
            self.quit()
            return False

        if event.type == KEYDOWN and event.key == K_ESCAPE:
            self.quit()
            return False
        if event.type == KEYDOWN and event.key == K_F2:
            self.show_debug_info = not self.show_debug_info
        elif event.type == KEYDOWN and event.key == K_F3:
            self.debug_rects = not self.debug_rects
        elif self.active_level:
            self.player.handle_event(event)

        return True

    def _draw(self):
        if self.camera:
            self.camera.update()

        if self.active_level:
            self.surface.set_clip(self.camera.rect)
            self.active_level.draw(self.surface)
            self.screen.blit(self.surface.subsurface(self.camera.rect),
                             self.level_draw_pos,
                             self.level_draw_area)

        if self.show_debug_info:
            debug_str = '%0.f FPS    X: %s    Y: %s' % (
                self.clock.get_fps(),
                self.player.rect.left, self.player.rect.top)

            self.screen.blit(
                self._debug_font.render(debug_str, True, self.DEBUG_COLOR),
                self.DEBUG_POS)

        pygame.display.flip()
