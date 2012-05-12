import pygame
from pygame.locals import *

from thecure import get_engine
from thecure.signals import Signal
from thecure.timer import Timer


class Page(object):
    def __init__(self):
        self.done = Signal()

    def start(self):
        pass

    def stop(self):
        pass

    def draw(self, surface):
        pass


class DelayPage(Page):
    def __init__(self, delay_ms):
        super(DelayPage, self).__init__()
        self.delay_ms = delay_ms
        self.timer = None

    def start(self):
        self.timer = Timer(self.delay_ms, self.stop, one_shot=True)

    def stop(self):
        self.timer.stop()
        self.done.emit()


class TextPage(DelayPage):
    def __init__(self, delay_ms, text):
        super(TextPage, self).__init__(delay_ms)
        self.text = text
        self.widget = None

    def start(self):
        ui_manager = get_engine().ui_manager
        attrs = {
            'font': ui_manager.small_font,
        }

        self.widget = ui_manager.show_textbox([
            (attrs, line)
            for line in self.text.split('\n')
        ], bg_color=(0, 0, 0, 220))

        super(TextPage, self).start()

    def stop(self):
        self.widget.close()
        super(TextPage, self).stop()


class Cutscene(object):
    def __init__(self):
        self.pages = []
        self.next_page = 0
        self.current_page = None
        self.allow_escape = True

        # Signals
        self.done = Signal()

    def start(self):
        self.next_page = 0
        self.show_next_page()

    def stop(self):
        self.next_page = -1
        self.current_page.stop()
        self.current_page = None
        self.done.emit()

    def show_next_page(self):
        if self.next_page == len(self.pages):
            self.done.emit()
        elif self.next_page >= 0:
            self.current_page = self.pages[self.next_page]
            self.next_page += 1
            self.current_page.done.connect(self.show_next_page)
            self.current_page.start()

    def draw(self, surface):
        if self.current_page:
            self.current_page.draw(surface)

    def handle_event(self, event):
        if event.type == KEYDOWN:
            if self.allow_escape and event.key == K_ESCAPE:
                self.stop()
            elif event.key in (K_SPACE, K_RETURN, K_RIGHT):
                self.current_page.stop()


class OpeningCutscene(Cutscene):
    def __init__(self):
        super(OpeningCutscene, self).__init__()

        self.pages = [
            TextPage(3000, "I'm Dr. Nick Rogers, Ph.D."),
            TextPage(6000,
                     "I moved to this little town in the mountains with my "
                     "wife, Laura, just 6 short months ago.\n"
                     "I wanted a safe and quiet place to conduct my research."),
            TextPage(3000,
                     "I planned to cure the common cold."),
            TextPage(6000,
                     "The plan was to create an airborne virus, safe for "
                     "humans, that would hunt down and destroy\n"
                     "the viruses that cause the cold symptoms."),
            TextPage(6000,
                     "My experiments on rats and chimps were promising.\n"
                     "I needed to begin human trials, but that would take "
                     "years."),
            TextPage(6000,
                     "This morning... The details are still a bit fuzzy. "
                     "I woke up in my lab up\n"
                     "against the wall with a terrible headache."),
            TextPage(3000,
                     "There was an explosion in the lab, and the virus "
                     "was exposed."),
            TextPage(4000,
                     "Stumbling out of the lab, I saw the townfolk bleeding, "
                     "screaming, faces distorted."),
            TextPage(7000,
                     "I had seen this before. In one of the batches of the "
                     "virus, the chimps began to hallucinate. \n"
                     "Some became aggressive and twisted their faces up in "
                     "agony."),
            TextPage(6000,
                     "I appeared to be fine, and I knew how to cure this. "
                     "Unfortunately, the ingredients were destroyed.\n"
                     "I'd need to venture out and get more."),
        ]


class TutorialCutscene(Cutscene):
    def __init__(self):
        super(TutorialCutscene, self).__init__()

        self.pages = [
            TextPage(6000,
                     'Explore and find the five items you need:\n'
                     'Crate of equipment, mushroom, salt crystal, giant web, '
                     'and a puffy red flower.\n'
                     'Use arrow keys to move and C to shoot.\n'
                     'Then find Laura!')
        ]
