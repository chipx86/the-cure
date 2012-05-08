import pygame
from pygame.locals import *

from thecure.resources import get_font_filename, load_image
from thecure.signals import Signal
from thecure.sprites import Player
from thecure.timer import Timer


class Widget(object):
    def __init__(self, ui_manager):
        self.ui_manager = ui_manager
        self.ui_manager.widgets.append(self)
        self.rect = pygame.Rect(0, 0, 0, 0)

        self.closed = Signal()

    def move_to(self, x, y):
        self.rect.left = x
        self.rect.top = y

    def resize(self, w, h):
        self.rect.width = w
        self.rect.height = h

    def close(self):
        self.ui_manager.close(self)

    def draw(self, surface):
        raise NotImplemented


class TextBox(Widget):
    BG_COLOR = (0, 0, 0, 190)
    BORDER_COLOR = (255, 255, 255, 120)
    BORDER_WIDTH = 1

    def __init__(self, ui_manager, text, line_spacing=10, stay_open=False):
        super(TextBox, self).__init__(ui_manager)
        self.text = text
        self.line_spacing = line_spacing
        self.surface = None
        self.stay_open = stay_open

    def _render_text(self):
        if isinstance(self.text, list):
            lines = self.text
        else:
            lines = [self.text]

        surfaces = []
        total_height = 0

        for line in lines:
            if isinstance(line, list):
                columns = line
            else:
                columns = [line]

            column_surfaces = []
            line_height = 0

            for column in columns:
                attrs = None

                if not isinstance(column, tuple):
                    column = {}, column

                attrs, text = column
                font = attrs.get('font', self.ui_manager.font)

                text_surface = font.render(text, True, (255, 255, 255))
                column_surfaces.append((attrs, text_surface))
                column_height = text_surface.get_height()

                if 'padding_top' in attrs:
                    column_height += attrs['padding_top']

                column_height += self.line_spacing

                line_height = max(line_height, column_height)

            if column_surfaces:
                surfaces.append((line_height, column_surfaces))
                total_height += line_height

        # Get rid of that last spacing.
        total_height -= self.line_spacing

        y = (self.rect.height - total_height) / 2

        for line_height, column_surfaces in surfaces:
            column_width = self.rect.width / len(column_surfaces)
            x = 0

            for attrs, column_surface in column_surfaces:
                self.surface.blit(
                    column_surface,
                    (x + (column_width - column_surface.get_width()) / 2,
                     y + attrs.get('padding_top', 0)))
                x += column_width

            y += line_height

    def draw(self, surface):
        if not self.surface:
            self.surface = pygame.Surface(self.rect.size).convert_alpha()
            self.surface.fill(self.BG_COLOR)
            pygame.draw.rect(self.surface, self.BORDER_COLOR,
                             (0, 0, self.rect.width, self.rect.height),
                             self.BORDER_WIDTH)
            self._render_text()

        surface.blit(self.surface, self.rect.topleft)


class UIManager(object):
    SCREEN_PADDING = 20
    TEXTBOX_HEIGHT = 100
    CONTROL_PANEL_HEIGHT = 40

    MONOLOGUE_X = 300
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

        self.default_font_file = get_font_filename()
        self.font = pygame.font.Font(self.default_font_file, 20)
        self.small_font = pygame.font.Font(self.default_font_file, 16)

        self.paused_textbox = None
        self.confirm_quit_box = None

    def show_textbox(self, text, **kwargs):
        textbox = TextBox(self, text, **kwargs)
        textbox.resize(self.size[0] - 2 * self.SCREEN_PADDING,
                       self.TEXTBOX_HEIGHT)
        textbox.move_to(self.SCREEN_PADDING,
                        self.size[1] - textbox.rect.height -
                        self.SCREEN_PADDING)
        return textbox

    def show_monologue(self, text, timeout_ms=None, **kwargs):
        textbox = TextBox(self, text, stay_open=True, **kwargs)
        textbox.resize(self.size[0] - 2 * self.SCREEN_PADDING -
                       self.MONOLOGUE_X,
                       self.MONOLOGUE_HEIGHT)

        clip_rect = self.engine.camera.rect
        offset = (-clip_rect.x, -clip_rect.y)

        textbox.move_to(self.MONOLOGUE_X,
                        self.engine.player.rect.move(offset).bottom +
                        self.MONOLOGUE_Y_OFFSET)

        timer = Timer(ms=timeout_ms or self.MONOLOGUE_TIMEOUT_MS,
                      cb=lambda: self.close(textbox),
                      one_shot=True)

        return textbox

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
                if event.key == K_ESCAPE:
                    self.confirm_quit_box.close()
                    self.confirm_quit_box = None
                    handled = True
                    self.engine.paused = False
                elif event.key == K_q:
                    self.engine.quit()
                    handled = True
                else:
                    return True
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
            "Do you want to quit?",
            ({'font': self.small_font},
             "Press 'Q' to quit."),
            ({'font': self.small_font},
             "Press 'Escape' to cancel.")
        ])

    def draw(self, surface):
        for element in self.widgets:
            element.draw(surface)
