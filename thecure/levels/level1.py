import pygame

from thecure.eventbox import EventBox
from thecure.levels.base import Level
from thecure.sprites import Direction, InfectedHuman


class Level1(Level):
    name = 'level1'
    start_pos = (900, 6200)

    def setup(self):
        boy = InfectedHuman('boy1')
        self.main_layer.add(boy)
        boy.move_to(1536, 5696)
        boy.set_direction(Direction.DOWN)

        girl = InfectedHuman('girl1')
        self.main_layer.add(girl)
        girl.move_to(1536, 5824)
        girl.set_direction(Direction.UP)

        eventbox = EventBox(self)
        eventbox.rects.append(pygame.Rect(832, 5760, 192, 192))
        eventbox.watch_object_moves(self.engine.player)
        eventbox.object_entered.connect(self._on_entered)
        eventbox.object_exited.connect(self._on_exited)

    def _on_entered(self, obj):
        print 'entered'

    def _on_exited(self, obj):
        print 'exited'

    def draw_bg(self, surface):
        surface.fill((237, 243, 255))
