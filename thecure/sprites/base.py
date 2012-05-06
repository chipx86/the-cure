import pygame

from thecure.resources import load_spritesheet_frame
from thecure.signals import Signal
from thecure.timer import Timer


class Direction(object):
    LEFT = 0
    RIGHT = 1
    UP = 2
    DOWN = 3


class Sprite(pygame.sprite.DirtySprite):
    SPRITESHEET_FRAMES = {
        Direction.DOWN: {
            'default': [(32, 0)],
            'walking': [(0, 0), (32, 0), (64, 0), (32, 0)],
        },
        Direction.LEFT: {
            'default': [(32, 48)],
            'walking': [(0, 48), (32, 48), (64, 48), (32, 48)],
        },
        Direction.RIGHT: {
            'default': [(32, 96)],
            'walking': [(0, 96), (32, 96), (64, 96), (32, 96)],
        },
        Direction.UP: {
            'default': [(32, 144)],
            'walking': [(0, 144), (32, 144), (64, 144), (32, 144)],
        },
    }
    SPRITE_SIZE = (32, 48)
    MOVE_SPEED = 2
    ANIM_MS = 150

    def __init__(self, name):
        super(Sprite, self).__init__()

        # Signals
        self.moved = Signal()

        # State
        self.rect = pygame.Rect(0, 0, 0, 0)
        self.quad_trees = set()
        self.layer = None
        self.name = name
        self.image = None
        self.visible = 1
        self.dirty = 2
        self.direction = Direction.DOWN
        self.velocity = (0, 0)

        self.frame_state = 'default'
        self.anim_frame = 0
        self.anim_timer = None

    def start(self):
        self.anim_timer = Timer(ms=self.ANIM_MS,
                                cb=self._on_anim_tick,
                                start_automatically=False)

    def show(self):
        if not self.visible:
            self.visible = 1
            self.dirty = 2
            self.layer.update_sprite(self)

    def hide(self):
        if self.visible:
            self.visible = 0
            self.dirty = 1
            self.layer.update_sprite(self)

    def remove(self):
        self.hide()
        self.layer.remove(self)

    def update_image(self):
        self.image = self.generate_image()
        assert self.image

        self.rect.size = self.SPRITE_SIZE

    def generate_image(self):
        return load_spritesheet_frame(
            self.name,
            self._get_spritesheet_frames()[self.anim_frame], self.SPRITE_SIZE)

    def move_to(self, x, y):
        self.move_by(x - self.rect.x, y - self.rect.y)

    def move_by(self, dx, dy):
        self.rect.move_ip(dx, dy)
        self.moved.emit(dx, dy)

    def on_added(self, layer):
        pass

    def on_removed(self, layer):
        pass

    def tick(self):
        if self.velocity != (0, 0):
            self.move_by(*self.velocity)

    def _get_spritesheet_frames(self):
        return self.SPRITESHEET_FRAMES[self.direction][self.frame_state]

    def _on_anim_tick(self):
        frames = self._get_spritesheet_frames()

        self.anim_frame += 1

        if self.anim_frame == len(frames):
            self.anim_frame = 0

        self.dirty = 2
        self.update_image()
