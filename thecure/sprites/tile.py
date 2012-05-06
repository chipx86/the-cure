import pygame

from thecure.resources import load_spritesheet_frame


class Tile(pygame.sprite.DirtySprite):
    WIDTH = 32
    HEIGHT = 32

    def __init__(self, filename, tile_offset):
        super(Tile, self).__init__()

        self.filename = filename
        self.tile_offset = tile_offset
        self.rect = pygame.Rect(0, 0, self.WIDTH, self.HEIGHT)
        self.image = None
        self.visible = 1
        self.dirty = 2

        self.can_move = False
        self.can_collide = False

    def start(self):
        pass

    def tick(self):
        pass

    def move_to(self, x, y):
        self.rect.move_ip(x - self.rect.x, y - self.rect.y)

    def update_image(self):
        self.image = load_spritesheet_frame(
            self.filename,
            (self.tile_offset[0] * self.WIDTH,
             self.tile_offset[1] * self.HEIGHT),
            (self.WIDTH, self.HEIGHT))
        assert self.image

    def on_added(self, layer):
        pass

    def on_removed(self, layer):
        pass

