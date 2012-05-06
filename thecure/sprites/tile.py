import pygame

from thecure.resources import load_spritesheet_frame
from thecure.sprites import BaseSprite


class Tile(BaseSprite):
    WIDTH = 32
    HEIGHT = 32

    def __init__(self, filename, tile_offset):
        super(Tile, self).__init__()

        self.filename = filename
        self.tile_offset = tile_offset
        self.rect.size = (self.WIDTH, self.HEIGHT)

    def update_image(self):
        self.image = load_spritesheet_frame(
            self.filename,
            (self.tile_offset[0] * self.WIDTH,
             self.tile_offset[1] * self.HEIGHT),
            (self.WIDTH, self.HEIGHT))
        assert self.image
