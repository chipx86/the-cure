import pygame

from thecure.eventbox import EventBox
from thecure.levels.base import Level
from thecure.sprites import Direction, InfectedHuman


class Overworld(Level):
    name = 'overworld'
    start_pos = (3968, 6400)

    def setup(self):
        pass
