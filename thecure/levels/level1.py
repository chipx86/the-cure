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

        self.eventboxes['kids'].object_entered.connect(
            lambda obj: self.show_monologue_once('kids',
                'Even the kids are infected. What have I done...'))

    def show_monologue_once(self, eventbox_name, text):
        self.engine.ui_manager.show_monologue(text)
        self.eventboxes[eventbox_name].disconnect()
        del self.eventboxes[eventbox_name]
