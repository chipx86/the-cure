import pygame
from pygame.locals import *

from thecure.resources import load_spritesheet_frame
from thecure.signals import Signal


class Direction(object):
    LEFT = 0
    RIGHT = 1
    UP = 2
    DOWN = 3


class Sprite(pygame.sprite.DirtySprite):
    SPRITESHEET_FRAMES = {
        Direction.DOWN: [(0, 0), (32, 0), (64, 0)],
        Direction.LEFT: [(0, 48), (32, 48), (64, 48)],
        Direction.RIGHT: [(0, 96), (32, 96), (64, 96)],
        Direction.UP: [(0, 144), (32, 144), (64, 144)],
    }
    SPRITE_SIZE = (32, 48)
    MOVE_SPEED = 6

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
            self.SPRITESHEET_FRAMES[self.direction][0], self.SPRITE_SIZE)

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
        pass


class Player(Sprite):
    MAX_LIVES = 3
    MAX_HEALTH = 3

    def __init__(self):
        super(Player, self).__init__('player')

        # Signals
        self.health_changed = Signal()
        self.lives_changed = Signal()

    def reset(self):
        self.health = self.MAX_HEALTH
        self.lives = self.MAX_LIVES
        self.update_image()

    def handle_event(self, event):
        if event.type == KEYDOWN:
            if event.key == K_RIGHT:
                self.move_direction(x=1)
            elif event.key == K_LEFT:
                self.move_direction(x=-1)
            elif event.key == K_UP:
                self.move_direction(y=-1)
            elif event.key == K_DOWN:
                self.move_direction(y=1)

    def move_direction(self, x=None, y=None):
        if x:
            x = self.MOVE_SPEED * x
        else:
            x = self.velocity[0]

        if y:
            y = self.MOVE_SPEED * x
        else:
            y = self.velocity[1]

        self.velocity = (x, y)
        self.update_image()
