import pygame

from thecure.signals import Signal
from thecure.timer import Timer


class Effect(object):
    def __init__(self):
        self.timer = None
        self.timer_ms = 150

        # Signals
        self.started = Signal()
        self.stopped = Signal()

    def pre_start(self):
        pass

    def pre_stop(self):
        pass

    def start(self):
        assert not self.timer
        self.pre_start()
        self.timer = Timer(self.timer_ms, self.on_tick)
        self.timer.start()
        self.started.emit()

    def stop(self):
        assert self.timer
        self.pre_stop()
        self.timer.stop()
        self.timer = None
        self.stopped.emit()

    def on_tick(self):
        pass


class ScreenEffect(Effect):
    def __init__(self, layer, rect):
        super(ScreenEffect, self).__init__()
        self.rect = rect
        self.image = pygame.Surface(rect.size).convert_alpha()


class ScreenFadeEffect(ScreenEffect):
    def __init__(self, *args, **kwargs):
        super(ScreenFadeEffect, self).__init__(*args, **kwargs)
        self.color = (0, 0, 0)
        self.fade_from_alpha = 0
        self.fade_to_alpha = 255
        self.fade_time_ms = 2000
        self.timer_ms = 30

    def pre_start(self):
        self.alpha = self.fade_from_alpha
        self.alpha_delta = ((self.fade_to_alpha - self.fade_from_alpha) /
                            (self.fade_time_ms / self.timer_ms))
        self.image.fill(
            (self.color[0], self.color[1], self.color[2], self.alpha))

    def on_tick(self):
        self.image.fill(
            (self.color[0], self.color[1], self.color[2], self.alpha))

        self.alpha += self.alpha_delta

        if ((self.fade_from_alpha > self.fade_to_alpha and
             self.alpha <= self.fade_to_alpha) or
            (self.fade_from_alpha < self.fade_to_alpha and
             self.alpha >= self.fade_to_alpha)):
            self.stop()


class ScreenFlashEffect(ScreenEffect):
    def __init__(self, *args, **kwargs):
        super(ScreenFlashEffect, self).__init__(*args, **kwargs)
        self.fade_out = True
        self.color = (255, 255, 255)

        self.flash_peaked = Signal()

    def pre_start(self):
        self.hit_peak = False
        self.alpha = 100

        self._fill(0)

    def _fill(self, alpha):
        self.image.fill((self.color[0], self.color[1], self.color[2], alpha))

    def on_tick(self):
        self._fill(self.alpha)

        if self.hit_peak:
            self.alpha = max(self.alpha - 30, 0)
        else:
            self.alpha = min(self.alpha + 30, 255)

        if self.alpha == 255:
            self.hit_peak = True
            self.flash_peaked.emit()

            if not self.fade_out:
                self.stop()
        elif self.alpha <= 0:
            self.stop()
