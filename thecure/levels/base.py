import pygame
from pygame.locals import *

from thecure.layers import Layer
from thecure.levels.loader import LevelLoader
from thecure.sprites import Tile


class Level(object):
    name = None
    start_pos = (0, 0)
    size = (0, 0)

    def __init__(self, engine):
        self.engine = engine
        self.layers = []
        self.group = pygame.sprite.LayeredDirty()

        self.load_level()

        self.engine.tick.connect(self.on_tick)

    def load_level(self):
        """Load the level from a file, given the current level name."""
        assert self.name

        loader = LevelLoader(self.name)
        self.size = (loader.get_width() * Tile.WIDTH,
                     loader.get_height() * Tile.HEIGHT)

        for layer_data in loader.iter_layers():
            layer_name = layer_data['name']

            layer = Layer(layer_name, layer_data['index'], self)
            self.layers.append(layer)

            if layer_data['is_main']:
                self.main_layer = layer

            for tile_data in loader.iter_tiles(layer_name):
                tile = Tile(filename='tiles/' + tile_data['tile_file'],
                            tile_offset=(tile_data['tile_x'],
                                         tile_data['tile_y']))
                layer.add(tile)
                tile.move_to(tile_data['col'] * Tile.WIDTH,
                             tile_data['row'] * Tile.HEIGHT)

    def reset(self):
        self.setup()

    def setup(self):
        pass

    def start(self):
        for sprite in self.group:
            sprite.start()

    def draw(self, screen, clip_rect):
        self.draw_bg(screen)

        offset = (-clip_rect.left, -clip_rect.top)

        for layer in self.layers:
            count = 0
            for sprite in set(layer.iterate_in_rect(clip_rect)):
                if (sprite.visible and sprite.dirty and
                    clip_rect.colliderect(sprite.rect)):
                    screen.blit(sprite.image, sprite.rect.move(offset))

                    if sprite.dirty == 1:
                        sprite.dirty = 0

                    count += 1

        if self.engine.debug_rects:
            for sprite in self.group:
                if sprite.layer.name != 'main':
                    continue

                if sprite.visible:
                    rects = sprite.collision_rects or [sprite.rect]

                    for rect in rects:
                        if clip_rect.colliderect(rect):
                            pygame.draw.rect(screen, (0, 0, 255),
                                             rect.move(offset), 1)

    def draw_bg(self, screen):
        pass

    def on_tick(self):
        self.group.update()

        for sprite in self.group:
            sprite.tick()
