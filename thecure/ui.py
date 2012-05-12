import pygame
from pygame.locals import *

from thecure.resources import get_font_filename, load_image, \
                              load_spritesheet_frame
from thecure.signals import Signal
from thecure.sprites import Player
from thecure.timer import Timer


class UIWidget(object):
    def __init__(self, ui):
        self.ui = ui
        self.rect = pygame.Rect(0, 0, 0, 0)


class TextBox(UIWidget):
    BG_COLOR = (0, 0, 0, 220)
    BORDER_COLOR = (255, 255, 255, 120)
    TEXT_COLOR = (255, 255, 255)
    BORDER_WIDTH = 1

    def __init__(self, ui, text, line_spacing=10, stay_open=False,
                 bg_color=BG_COLOR, border_color=BORDER_COLOR,
                 text_color=TEXT_COLOR):
        super(TextBox, self).__init__(ui)
        self.text = text
        self.line_spacing = line_spacing
        self.surface = None
        self.stay_open = stay_open
        self.bg_color = bg_color
        self.border_color = border_color
        self.text_color = text_color

        self.closed = Signal()

    def _render_text(self):
        if isinstance(self.text, list):
            lines = self.text
        else:
            lines = [self.text]

        surfaces = []
        total_height = 0

        for line in lines:
            text_surface = self.ui.small_font.render(line, True,
                                                     self.text_color)
            total_height += text_surface.get_height() + self.line_spacing
            surfaces.append(text_surface)

        total_height -= self.line_spacing

        y = (self.rect.height - total_height) / 2

        for surface in surfaces:
            self.surface.blit(surface,
                              ((self.rect.width - surface.get_width()) / 2, y))

            y += surface.get_height() + self.line_spacing

    def close(self):
        self.ui.close(self)

    def draw(self, surface):
        if not self.surface:
            self.surface = pygame.Surface(self.rect.size).convert_alpha()
            self.surface.fill(self.bg_color)
            pygame.draw.rect(self.surface, self.border_color,
                             (0, 0, self.rect.width, self.rect.height),
                             self.BORDER_WIDTH)
            pygame.draw.rect(self.surface, self.border_color,
                             (3, 3, self.rect.width - 6, self.rect.height - 6),
                             self.BORDER_WIDTH)
            self._render_text()

        surface.blit(self.surface, self.rect.topleft)


class StatusArea(UIWidget):
    IMAGE_SPACING = 5
    SIDE_SPACING = 15
    PADDING = 5

    def __init__(self, *args, **kwargs):
        super(StatusArea, self).__init__(*args, **kwargs)

        self.full_heart = load_spritesheet_frame('hearts', (0, 0), 1, 3)
        self.half_heart = load_spritesheet_frame('hearts', (0, 1), 1, 3)
        self.empty_heart = load_spritesheet_frame('hearts', (0, 2), 1, 3)
        self.life_image = load_image('sprites/life')

        self.rect.size = (self.ui.size[0],
                          self.life_image.get_height() + 2 * self.PADDING)

        self.surface = pygame.Surface(self.rect.size).convert_alpha()

        player = self.ui.engine.player
        player.health_changed.connect(self.render)
        player.lives_changed.connect(self.render)

        self.render()

    def render(self):
        self.surface.fill((0, 0, 0, 0))

        heart_width = self.full_heart.get_width()
        player = self.ui.engine.player
        x = self.SIDE_SPACING
        y = (self.rect.height - self.full_heart.get_height()) / 2

        for i in range(Player.MAX_HEALTH):
            if player.health > i:
                heart_image = self.full_heart
            else:
                heart_image = self.empty_heart

            self.surface.blit(heart_image, (x, y))

            x += heart_width + self.IMAGE_SPACING

        y = (self.rect.height - self.life_image.get_height()) / 2
        life_width = self.life_image.get_width()
        x += self.SIDE_SPACING

        for i in range(Player.MAX_LIVES):
            if player.lives > i:
                self.surface.blit(self.life_image, (x, y))

            x += life_width + self.IMAGE_SPACING

    def draw(self, surface):
        surface.blit(self.surface, self.rect.topleft)


class GameUI(object):
    PADDING = 40
    TEXTBOX_HEIGHT = 150
    STATUS_AREA_HEIGHT = 40

    MONOLOGUE_X = 250
    MONOLOGUE_Y_OFFSET = 50
    MONOLOGUE_HEIGHT = 50
    MONOLOGUE_TIMEOUT_MS = 3000

    def __init__(self, engine):
        pygame.font.init()

        self.ready = Signal()

        self.engine = engine
        self.size = engine.screen.get_size()
        self.surface = pygame.Surface(self.size).convert_alpha()
        self.widgets = []
        self.timers = []

        self.active_monologue = None
        self.monologue_timer = None
        self.paused_textbox = None
        self.confirm_quit_box = None

        self.default_font_file = get_font_filename()
        self.font = pygame.font.Font(self.default_font_file, 20)
        self.small_font = pygame.font.Font(self.default_font_file, 16)

        self.status_area = StatusArea(self)
        self.widgets.append(self.status_area)

    def show_textbox(self, text, **kwargs):
        textbox = TextBox(self, text, **kwargs)
        textbox.rect = pygame.Rect(
            self.PADDING, (self.size[1] - self.TEXTBOX_HEIGHT) / 2,
            self.size[0] - 2 * self.PADDING, self.TEXTBOX_HEIGHT)
        self.widgets.append(textbox)

        return textbox

    def show_monologue(self, text, timeout_ms=None, on_done=None,
                       y_offset=MONOLOGUE_Y_OFFSET, actor=None, **kwargs):
        def _next_monologue():
            self.close(self.active_monologue)

            if len(text) > 1:
                self.show_monologue(text[1:], timeout_ms, on_done, **kwargs)
            elif on_done:
                on_done()

        if not isinstance(text, list):
            text = [text]

        self.close_monologues()

        if actor is None:
            actor = self.engine.player

        clip_rect = self.engine.camera.rect
        offset = (-clip_rect.x, -clip_rect.y)

        lines = text[0].splitlines()
        textbox = TextBox(self, lines[0], stay_open=True, **kwargs)
        self.widgets.append(textbox)
        textbox.rect = pygame.Rect(
            self.MONOLOGUE_X,
            actor.rect.move(offset).bottom + y_offset,
            self.size[0] - 2 * self.PADDING - self.MONOLOGUE_X,
            self.MONOLOGUE_HEIGHT * len(lines))
        self.active_monologue = textbox

        self.monologue_timer = Timer(ms=timeout_ms or self.MONOLOGUE_TIMEOUT_MS,
                                     cb=_next_monologue,
                                     one_shot=True)

        return textbox

    def close_monologues(self):
        if self.active_monologue:
            self.monologue_timer.stop()
            self.close(self.active_monologue)

    def show_dialogue(self, actors, lines, timeout_ms=None, on_done=None,
                      **kwargs):
        def _next_dialogue():
            self.close(self.active_monologue)

            if len(lines) > 1:
                self.show_dialogue(actors, lines[1:], timeout_ms,
                                   on_done, **kwargs)
            elif on_done:
                on_done()

        person, text = lines[0]

        if person == 'player':
            self.show_monologue(text, timeout_ms, _next_dialogue)
        else:
            self.show_monologue(text, timeout_ms, _next_dialogue,
                                actor=actors[person],
                                y_offset=-3.5 * self.MONOLOGUE_Y_OFFSET,
                                bg_color=(232, 174, 174),
                                text_color=(0, 0, 0),
                                border_color=(0, 0, 0))

    def close(self, widget):
        try:
            self.widgets.remove(widget)
            widget.closed.emit()
        except ValueError:
            # It was already closed
            pass

    def handle_event(self, event):
        handled = False

        if event.type == KEYDOWN:
            if self.confirm_quit_box:
                handled = True

                if event.key in (K_ESCAPE, K_n):
                    self.confirm_quit_box.close()
                    self.confirm_quit_box = None
                    self.engine.paused = False
                elif event.key == K_y:
                    self.engine.quit()
            elif event.key in (K_ESCAPE, K_RIGHT, K_SPACE, K_RETURN):
                for widget in self.widgets:
                    if (isinstance(widget, TextBox) and
                        widget != self.paused_textbox and
                        not widget.stay_open):
                        widget.close()
                        handled = True

        return handled

    def pause(self):
        assert not self.paused_textbox
        self.paused_textbox = self.show_textbox('Paused')

    def unpause(self):
        if self.paused_textbox:
            self.paused_textbox.close()
            self.paused_textbox = None

    def confirm_quit(self):
        if self.confirm_quit_box:
            self.confirm_quit_box.close()
            return

        self.engine.paused = True
        self.confirm_quit_box = self.show_textbox([
            "Giving up already?",
            "'Y' to give up.",
            "'N' to keep playing."
        ])

    def draw(self, surface):
        for element in self.widgets:
            element.draw(surface)
