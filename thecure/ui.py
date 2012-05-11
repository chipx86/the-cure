import pygame
from pygame.locals import *

from thecure.resources import get_font_filename, load_image, \
                              load_spritesheet_frame
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
    TEXT_COLOR = (255, 255, 255)
    BORDER_WIDTH = 1

    def __init__(self, ui_manager, text, line_spacing=10, stay_open=False,
                 bg_color=BG_COLOR, border_color=BORDER_COLOR,
                 text_color=TEXT_COLOR):
        super(TextBox, self).__init__(ui_manager)
        self.text = text
        self.line_spacing = line_spacing
        self.surface = None
        self.stay_open = stay_open
        self.bg_color = bg_color
        self.border_color = border_color
        self.text_color = text_color

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

                text_surface = font.render(text, True, self.text_color)
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
            self.surface.fill(self.bg_color)
            pygame.draw.rect(self.surface, self.border_color,
                             (0, 0, self.rect.width, self.rect.height),
                             self.BORDER_WIDTH)
            self._render_text()

        surface.blit(self.surface, self.rect.topleft)


class ControlPanel(Widget):
    IMAGE_SPACING = 5
    SIDE_SPACING = 15
    PADDING = 5

    def __init__(self, *args, **kwargs):
        super(ControlPanel, self).__init__(*args, **kwargs)

        self.full_heart = load_spritesheet_frame('hearts', (0, 0), 1, 3)
        self.half_heart = load_spritesheet_frame('hearts', (0, 1), 1, 3)
        self.empty_heart = load_spritesheet_frame('hearts', (0, 2), 1, 3)
        self.life_image = load_image('sprites/life')

        self.resize(self.ui_manager.size[0],
                    self.life_image.get_height() + 2 * self.PADDING)
        self.surface = pygame.Surface(self.rect.size).convert_alpha()

        player = self.ui_manager.engine.player
        player.health_changed.connect(self.render)
        player.lives_changed.connect(self.render)

        self.render()

    def render(self):
        self.surface.fill((0, 0, 0, 0))

        heart_width = self.full_heart.get_width()
        player = self.ui_manager.engine.player
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


class UIManager(object):
    SCREEN_PADDING = 20
    TEXTBOX_HEIGHT = 120
    CONTROL_PANEL_HEIGHT = 40

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

        self.default_font_file = get_font_filename()
        self.font = pygame.font.Font(self.default_font_file, 20)
        self.small_font = pygame.font.Font(self.default_font_file, 16)

        self.paused_textbox = None
        self.confirm_quit_box = None

    def add_control_panel(self):
        self.control_panel = ControlPanel(self)
        self.control_panel.move_to(0, 0)

    def show_textbox(self, text, **kwargs):
        textbox = TextBox(self, text, **kwargs)
        textbox.resize(self.size[0] - 2 * self.SCREEN_PADDING,
                       self.TEXTBOX_HEIGHT)
        textbox.move_to(self.SCREEN_PADDING,
                        self.size[1] - textbox.rect.height -
                        self.SCREEN_PADDING)
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

        lines = text[0].split('\n')
        textbox = TextBox(self, lines, stay_open=True, **kwargs)
        textbox.resize(self.size[0] - 2 * self.SCREEN_PADDING -
                       self.MONOLOGUE_X,
                       self.MONOLOGUE_HEIGHT * len(lines))
        self.active_monologue = textbox

        clip_rect = self.engine.camera.rect
        offset = (-clip_rect.x, -clip_rect.y)

        if actor is None:
            actor = self.engine.player

        textbox.move_to(self.MONOLOGUE_X,
                        actor.rect.move(offset).bottom + y_offset)

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
