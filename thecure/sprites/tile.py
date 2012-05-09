from thecure.resources import load_spritesheet_frame
from thecure.sprites import Sprite


class Tile(Sprite):
    NAME = 'tile'
    WIDTH = 64
    HEIGHT = 64

    NEED_TICKS = False

    def __init__(self, filename, tile_offset):
        super(Tile, self).__init__()

        self.filename = filename
        self.tile_offset = tile_offset
        self.rect.size = (self.WIDTH, self.HEIGHT)

    def __str__(self):
        return 'Tile %s:%s at %s' % (self.filename, self.tile_offset,
                                     self.rect.topleft)

    def update_image(self):
        self.image = load_spritesheet_frame(self.filename, self.tile_offset,
                                            frame_size=self.rect.size)
        assert self.image
