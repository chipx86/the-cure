from thecure.resources import load_spritesheet_frame
from thecure.sprites import BaseSprite


class Tile(BaseSprite):
    WIDTH = 64
    HEIGHT = 64

    def __init__(self, filename, tile_offset):
        super(Tile, self).__init__()

        self.filename = filename
        self.tile_offset = tile_offset
        self.rect.size = (self.WIDTH, self.HEIGHT)

    def update_image(self):
        self.image = load_spritesheet_frame(self.filename, self.tile_offset,
                                            12, 16)
        assert self.image
