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

    def __init__(self, engine):
        self.engine = engine
        self.layers = []
        self.layer_map = {}
        self.event_handlers = []
        self.eventboxes = {}

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
            self.layer_map[layer_name] = layer

            if layer_data['is_main']:
                self.main_layer = layer

            for tile_data in loader.iter_tiles(layer_name):
                tile = Tile(filename='tiles/' + tile_data['tile_file'],
                            tile_offset=(tile_data['tile_x'],
                                         tile_data['tile_y']))
                tile.move_to(tile_data['col'] * Tile.WIDTH,
                             tile_data['row'] * Tile.HEIGHT)
                layer.add(tile)

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

    def reset(self):
        self.setup()

    def setup(self):
        pass

    def start(self):
        for layer in self.layers:
            layer.start()

    def draw(self, screen, clip_rect):
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
