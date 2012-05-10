import math

import pygame
from pygame.locals import *

from thecure.eventbox import EventBox
from thecure.layers import Layer
from thecure.levels.loader import LevelLoader
from thecure.sprites import Tile


class Level(object):
    name = None
    start_pos = (0, 0)
    size = (0, 0)

    CHUNK_SIZE = (10, 10)

    def __init__(self, engine):
        self.engine = engine
        self.layers = []
        self.layer_map = {}
        self.chunks = []
        self.cur_chunk = None
        self.event_handlers = []
        self.eventboxes = {}
        self._prev_clip_rect = None
        self._loaded_chunk_ranges = None
        self._loaded_tiles = {}

        self.load_level()

        self.engine.tick.connect(self.on_tick)

    def load_level(self):
        """Load the level from a file, given the current level name."""
        assert self.name

        loader = LevelLoader(self.name)
        level_width = loader.get_width()
        level_height = loader.get_height()
        self.size = (level_width * Tile.WIDTH,
                     level_height * Tile.HEIGHT)

        chunk_rows = int(math.ceil(float(level_height) / self.CHUNK_SIZE[1]))
        chunk_cols = int(math.ceil(float(level_width) / self.CHUNK_SIZE[0]))

        self.chunks = [
            [
                {}
                for col in xrange(chunk_cols)
            ]
            for row in xrange(chunk_rows)
        ]

        for layer_data in loader.iter_layers():
            layer_name = layer_data['name']

            layer = Layer(layer_name, layer_data['index'], self)
            self.layers.append(layer)
            self.layer_map[layer_name] = layer

            if layer_data['is_main']:
                self.main_layer = layer

            chunk_row = 0
            chunk_col = 0

            for tile_data in loader.iter_tiles(layer_name):
                row = tile_data['row']
                col = tile_data['col']
                chunk_row = row / self.CHUNK_SIZE[1]
                chunk_col = col / self.CHUNK_SIZE[0]

                if layer_name not in self.chunks[chunk_row][chunk_col]:
                    self.chunks[chunk_row][chunk_col][layer_name] = []

                self.chunks[chunk_row][chunk_col][layer_name].append(tile_data)

        for name, eventbox_data in loader.iter_eventboxes():
            rect = pygame.Rect(eventbox_data['rect'])
            rect.x *= Tile.WIDTH
            rect.y *= Tile.HEIGHT
            rect.width *= Tile.WIDTH
            rect.height *= Tile.HEIGHT

            eventbox = EventBox(self)
            eventbox.rects.append(rect)
            eventbox.watch_object_moves(self.engine.player)
            self.eventboxes[name] = eventbox

    def _load_chunk(self, chunk_row, chunk_col):
        key = (chunk_row, chunk_col)

        if key in self._loaded_tiles:
            return

        loaded_tiles = []

        for layer_name, tiles in self.chunks[chunk_row][chunk_col].iteritems():
            layer = self.layer_map[layer_name]

            for tile_data in tiles:
                tile = Tile(filename='tiles/' + tile_data['tile_file'],
                            tile_offset=(tile_data['tile_x'],
                                         tile_data['tile_y']))
                tile.move_to(tile_data['col'] * Tile.WIDTH,
                             tile_data['row'] * Tile.HEIGHT)
                layer.add(tile)
                loaded_tiles.append(tile)

        self._loaded_tiles[key] = loaded_tiles

    def _swap_chunks(self, rect):
        chunk_ranges = self._get_chunk_ranges(rect)

        if chunk_ranges == self._loaded_chunk_ranges:
            return

        discards = set()

        if self._loaded_chunk_ranges is not None:
            for row in xrange(self._loaded_chunk_ranges[0],
                              self._loaded_chunk_ranges[2] + 1):
                for col in xrange(self._loaded_chunk_ranges[1],
                                  self._loaded_chunk_ranges[3] + 1):
                    discards.add((row, col))

        for row in xrange(chunk_ranges[0], chunk_ranges[2] + 1):
            for col in xrange(chunk_ranges[1], chunk_ranges[3] + 1):
                self._load_chunk(row, col)

                coord = (row, col)

                if coord in discards:
                    discards.remove(coord)

        self._loaded_chunk_ranges = chunk_ranges

        for coord in discards:
            for tile in self._loaded_tiles[coord]:
                tile.remove()

            del self._loaded_tiles[coord]

    def _get_chunk_ranges(self, rect):
        width_divisor = float(Tile.WIDTH * self.CHUNK_SIZE[0])
        height_divisor = float(Tile.HEIGHT * self.CHUNK_SIZE[1])

        row = rect.y / height_divisor
        col = rect.x / width_divisor

        return (int(row),
                int(col),
                int(row + rect.height / height_divisor),
                int(col + rect.width / width_divisor))

    def reset(self):
        self.setup()

    def setup(self):
        pass

    def start(self):
        for layer in self.layers:
            layer.start()

    def draw(self, screen, clip_rect):
        if self._prev_clip_rect != clip_rect:
            self._swap_chunks(clip_rect)

        offset = (-clip_rect.left, -clip_rect.top)

        for layer in self.layers:
            for sprite in sorted(layer.iterate_in_rect(clip_rect),
                                 key=lambda s: (s.rect.top, s.rect.left)):
                if sprite.visible and sprite.dirty:
                    screen.blit(sprite.image, sprite.rect.move(offset))

                    if sprite.dirty == 1:
                        sprite.dirty = 0

        if self.engine.debug_rects:
            for sprite in self.main_layer.iterate_in_rect(clip_rect):
                if sprite.visible:
                    rects = sprite.get_absolute_collision_rects()

                    for rect in rects:
                        if clip_rect.colliderect(rect):
                            pygame.draw.rect(screen, (0, 0, 255),
                                             rect.move(offset), 1)

            for eventbox in self.event_handlers:
                for rect in eventbox.rects:
                    if rect.colliderect(clip_rect):
                        pygame.draw.rect(screen, (255, 0, 0),
                                         rect.move(offset), 1)

        self._prev_clip_rect = clip_rect.copy()

    def register_for_events(self, obj):
        self.event_handlers.append(obj)

    def unregister_for_events(self, obj):
        self.event_handlers.remove(obj)

    def remove_eventbox(self, name):
        self.eventboxes[name].disconnect()
        del self.eventboxes[name]

    def connect_eventbox_enter(self, name, cb, only_once=False):
        self.eventboxes[name].object_entered.connect(
            lambda obj: self._on_eventbox_entered(name, cb, only_once))

    def _on_eventbox_entered(self, name, cb, only_once):
        cb()

        if only_once:
            self.remove_eventbox(name)

    def add_monologue(self, eventbox_name, text, timeout_ms=None):
        self.connect_eventbox_enter(
            eventbox_name,
            lambda: self.engine.ui_manager.show_monologue(text, timeout_ms),
            True)

    def on_tick(self):
        for layer in self.layers:
            layer.tick()
