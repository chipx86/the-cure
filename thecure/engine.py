import sys

import pygame
from pygame.locals import *

from thecure import set_engine
from thecure.cutscenes import OpeningCutscene
from thecure.cutscenes import TutorialCutscene
from thecure.levels import get_levels
from thecure.resources import get_font_filename
from thecure.signals import Signal
from thecure.sprites import Player
from thecure.timer import Timer
from thecure.ui import GameUI


class Camera(object):
    SCREEN_PAD = 64

    def __init__(self, engine):
        self.engine = engine
        self.rect = self.engine.screen.get_rect()
        self.old_player_rect = None

    def update(self):
        if self.engine.paused:
            return

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

        self.old_player_rect = player_rect.copy()


class TheCureEngine(object):
    FPS = 30
    DEBUG_COLOR = (255, 0, 0)
    DEBUG_POS = (30, 50)

    def __init__(self, screen):
        set_engine(self)

        # Signals
        self.tick = Signal()

        # State and objects
        self.active_level = None
        self.active_cutscene = None
        self.paused = False
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.player = Player()
        self.levels = []
        self.level_draw_pos = (0, 0)
        self.level_draw_area = None
        self.camera = None

        self.ui = GameUI(self)

        # Debug flags
        self.debug_rects = False
        self.show_debug_info = False

    def run(self):
        self.active_cutscene = OpeningCutscene()
        self.active_cutscene.done.connect(self._setup_game)
        self.active_cutscene.start()

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

        self.active_cutscene = None

        self.player.reset()
        self.player.layer = None

        self.active_level = None
        self.levels = [level(self) for level in get_levels()]
        self.switch_level(0)

        self.paused = True

        self.show_tutorial()

    def show_tutorial(self):
        def on_done():
            self.active_cutscene = None
            self.paused = False

        self.active_cutscene = TutorialCutscene()
        self.active_cutscene.start()
        self.active_cutscene.done.connect(on_done)

    def switch_level(self, num):
        assert num < len(self.levels)

        if self.active_level:
            self.active_level.stop()
            self.active_level.main_layer.remove(self.player)

        self.player.reset()
        self.active_level = self.levels[num]
        self.active_level.reset()
        self.active_level.main_layer.add(self.player)

        self.surface = pygame.Surface(self.screen.get_size())

        self.player.move_to(*self.active_level.start_pos)
        self.camera.update()

        self.active_level.start()

    def dead(self):
        if self.player.lives == 1:
            s = 'You have 1 more chance to get this right.'
        else:
            s = 'You have %d more chances to get this right.' % \
                self.player.lives

        widget = self.ui.show_textbox(s)
        self.paused = True
        self.player.stop()
        widget.closed.connect(self.restart_level)

    def restart_level(self):
        self.paused = False
        self.player.move_to(*self.active_level.start_pos)
        self.player.start()

    def game_over(self):
        widget = self.ui.show_textbox(
            ['You died. Maybe it was for the best.',
             'Game over.'])
        self.paused = True
        widget.closed.connect(self._setup_game)

    def _mainloop(self):
        while 1:
            for event in pygame.event.get():
                if not self._handle_event(event):
                    return

            if not self.paused:
                self.tick.emit()

            self._draw()
            self.clock.tick(self.FPS)

    def _handle_event(self, event):
        if event.type == QUIT:
            self.quit()
            return False

        if (self.ui and not self.active_cutscene and
            self.ui.handle_event(event)):
            return True

        if event.type == KEYDOWN and event.key == K_F2:
            self.show_debug_info = not self.show_debug_info
        elif event.type == KEYDOWN and event.key == K_F3:
            self.debug_rects = not self.debug_rects
        elif self.active_cutscene:
            self.active_cutscene.handle_event(event)
        elif event.type == KEYDOWN and event.key == K_ESCAPE:
            self.ui.confirm_quit()
        elif self.active_level:
            if event.type == KEYDOWN and event.key == K_RETURN:
                if self.paused:
                    self._unpause()
                else:
                    self._pause()
            elif not self.paused and not self.player.handle_event(event):
                player_rects = self.player.get_absolute_collision_rects()

                for eventbox in self.active_level.event_handlers:
                    for player_rect in player_rects:
                        if (player_rect.collidelist(eventbox.rects) != -1 and
                            eventbox.handle_event(event)):
                            break

        return True

    def _pause(self):
        self.paused = True
        self.ui.pause()

    def _unpause(self):
        self.paused = False
        self.ui.unpause()

    def _draw(self):
        if self.camera:
            self.camera.update()

        if self.active_cutscene:
            self.screen.set_clip(None)
            self.active_cutscene.draw(self.screen)

        if self.active_level:
            self.active_level.draw(self.surface, self.camera.rect)
            self.screen.blit(self.surface,
                             self.level_draw_pos,
                             self.level_draw_area)

        self.ui.draw(self.screen)

        if self.show_debug_info:
            debug_str = '%0.f FPS    X: %s    Y: %s' % (
                self.clock.get_fps(),
                self.player.rect.left, self.player.rect.top)

            self.screen.blit(
                self.ui.font.render(debug_str, True, self.DEBUG_COLOR),
                self.DEBUG_POS)

        pygame.display.flip()
