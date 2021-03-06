import math

import pygame
from pygame.locals import *

from thecure import get_engine
from thecure.sprites.base import Direction, Sprite, WalkingSprite, Human
from thecure.sprites.behaviors import ChaseMixin, WanderMixin, AttackLineMixin
from thecure.timer import Timer


STANDARD_SPRITESHEET_FRAMES = {
    Direction.SOUTH: {
        'default': [(1, 0)],
        'wandering': [(0, 0), (1, 0), (2, 0), (1, 0)],
    },
    Direction.WEST: {
        'default': [(1, 1)],
        'wandering': [(0, 1), (1, 1), (2, 1), (1, 1)],
    },
    Direction.EAST: {
        'default': [(1, 2)],
        'wandering': [(0, 2), (1, 2), (2, 2), (1, 2)],
    },
    Direction.NORTH: {
        'default': [(1, 3)],
        'wandering': [(0, 3), (1, 3), (2, 3), (1, 3)],
    },
}


class Enemy(WalkingSprite):
    DEFAULT_HEALTH = 10
    LETHAL = True

    def on_collision(self, dx, dy, obj, self_rect, obj_rect):
        if obj.name == 'player':
            return True


class InfectedHuman(WanderMixin, ChaseMixin, Human, Enemy):
    MOVE_SPEED = 1
    CHASE_SPEED = 2
    WANDER_KEY_NAME = 'walking'


class Snake(WanderMixin, AttackLineMixin, Enemy):
    NAME = 'snake'
    MOVE_SPEED = 1
    SPRITESHEET_ROWS = 4
    SPRITESHEET_COLS = 3
    SPRITESHEET_FRAMES = STANDARD_SPRITESHEET_FRAMES


class Slime(WanderMixin, AttackLineMixin, Enemy):
    NAME = 'slime'
    MOVE_SPEED = 1
    ATTACK_SPEED = 4
    ATTACK_DISTANCE = 150
    POST_ATTACK_MS = 2000
    ATTACK_TICKS_PAD = 2
    PAUSE_CHANCE = 0.3
    SPRITESHEET_ROWS = 4
    SPRITESHEET_COLS = 3
    SPRITESHEET_FRAMES = STANDARD_SPRITESHEET_FRAMES


class Bee(WanderMixin, AttackLineMixin, ChaseMixin, Enemy):
    NAME = 'bee'
    DEFAULT_HEALTH = 1
    MOVE_SPEED = 1
    CHASE_SPEED = 2
    ATTACK_SPEED = 12
    APPROACH_DISTANCE = 250
    ATTACK_DISTANCE = 150
    POST_ATTACK_MS = 2000
    ATTACK_TICKS_PAD = 2
    PAUSE_CHANCE = 0
    FOLLOWING_KEY_NAME = "wandering"
    SHOW_EXCLAMATION = False
    DRAW_ABOVE = True
    SPRITESHEET_ROWS = 4
    SPRITESHEET_COLS = 3
    SPRITESHEET_FRAMES = STANDARD_SPRITESHEET_FRAMES

    def on_collision(self, dx, dy, obj, self_rect, obj_rect):
        return True


class Gargoyle(WanderMixin, ChaseMixin, Enemy):
    NAME = 'gargoyle'
    MOVE_SPEED = 1
    DEFAULT_HEALTH = 20
    CHASE_SPEED = 2
    PAUSE_CHANCE = 0.3
    WANDER_KEY_NAME = 'walking'
    STOP_FOLLOWING_DISTANCE = 500
    DRAW_ABOVE = True
    SPRITESHEET_ROWS = 4
    SPRITESHEET_COLS = 3
    SPRITESHEET_FRAMES = {
        Direction.SOUTH: {
            'default': [(1, 0)],
            'walking': [(0, 0), (1, 0), (2, 0), (1, 0)],
        },
        Direction.WEST: {
            'default': [(1, 1)],
            'walking': [(0, 1), (1, 1), (2, 1), (1, 1)],
        },
        Direction.EAST: {
            'default': [(1, 2)],
            'walking': [(0, 2), (1, 2), (2, 2), (1, 2)],
        },
        Direction.NORTH: {
            'default': [(1, 3)],
            'walking': [(0, 3), (1, 3), (2, 3), (1, 3)],
        },
    }

    def update_collision_rects(self):
        self.collision_rects = [
            pygame.Rect(0, self.rect.height / 2,
                        self.rect.width, self.rect.height / 2),
        ]

    def on_collision(self, dx, dy, obj, self_rect, obj_rect):
        return True


class Troll(WanderMixin, ChaseMixin, Enemy):
    NAME = 'troll'
    MOVE_SPEED = 1
    DEFAULT_HEALTH = 20
    CHASE_SPEED = 2
    PAUSE_CHANCE = 0.3
    WANDER_KEY_NAME = 'walking'
    STOP_FOLLOWING_DISTANCE = 500
    SPRITESHEET_ROWS = 4
    SPRITESHEET_COLS = 3
    SPRITESHEET_FRAMES = {
        Direction.SOUTH: {
            'default': [(1, 0)],
            'walking': [(0, 0), (1, 0), (2, 0), (1, 0)],
        },
        Direction.WEST: {
            'default': [(1, 1)],
            'walking': [(0, 1), (1, 1), (2, 1), (1, 1)],
        },
        Direction.EAST: {
            'default': [(1, 2)],
            'walking': [(0, 2), (1, 2), (2, 2), (1, 2)],
        },
        Direction.NORTH: {
            'default': [(1, 3)],
            'walking': [(0, 3), (1, 3), (2, 3), (1, 3)],
        },
    }

    def update_collision_rects(self):
        self.collision_rects = [
            pygame.Rect(0, self.rect.height / 2,
                        self.rect.width, self.rect.height / 2),
        ]
