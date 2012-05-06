import pygame

from thecure.resources import load_spritesheet_frame
from thecure.signals import Signal
from thecure.timer import Timer


class Direction(object):
    LEFT = 0
    RIGHT = 1
    UP = 2
    DOWN = 3


class BaseSprite(pygame.sprite.DirtySprite):
    def __init__(self):
        super(BaseSprite, self).__init__()

        self.rect = pygame.Rect(0, 0, 0, 0)
        self.image = None
        self.visible = 1
        self.dirty = 2

        self.can_move = False
        self.use_quadtrees = False

    def start(self):
        pass

    def move_to(self, x, y):
        self.move_by(x - self.rect.x, y - self.rect.y)

    def move_by(self, dx, dy):
        self.rect.move_ip(dx, dy)

    def update_image(self):
        raise NotImplementedError

    def on_added(self, layer):
        pass

    def on_removed(self, layer):
        pass

    def tick(self):
        pass


class Sprite(BaseSprite):
    SPRITESHEET_FRAMES = {
        Direction.DOWN: {
            'default': [(64, 0)],
            'walking': [(0, 0), (64, 0), (128, 0), (64, 0)],
        },
        Direction.LEFT: {
            'default': [(64, 96)],
            'walking': [(0, 96), (64, 96), (128, 96), (64, 96)],
        },
        Direction.RIGHT: {
            'default': [(64, 192)],
            'walking': [(0, 192), (64, 192), (128, 192), (64, 192)],
        },
        Direction.UP: {
            'default': [(64, 288)],
            'walking': [(0, 288), (64, 288), (128, 288), (64, 288)],
        },
    }
    SPRITE_SIZE = (64, 96)
    MOVE_SPEED = 4
    ANIM_MS = 150

    def __init__(self, name):
        super(Sprite, self).__init__()

        # Signals
        self.moved = Signal()

        # State
        self.quad_trees = set()
        self.layer = None
        self.name = name
        self.direction = Direction.DOWN
        self.velocity = (0, 0)

        self.can_move = True
        self.use_quadtrees = True

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

    def move_by(self, dx, dy):
        super(Sprite, self).move_by(dx, dy)
        self.moved.emit(dx, dy)

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
