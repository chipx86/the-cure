import random

import pygame

from thecure.resources import load_spritesheet_frame
from thecure.signals import Signal
from thecure.timer import Timer


class Direction(object):
    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3

    @classmethod
    def random(self):
        return random.randint(0, 3)


class BaseSprite(pygame.sprite.DirtySprite):
    SHOULD_CHECK_COLLISIONS = True
    DEFAULT_HEALTH = 0
    DRAW_ABOVE = False

    def __init__(self):
        super(BaseSprite, self).__init__()

        self.rect = pygame.Rect(0, 0, 0, 0)
        self.image = None
        self.visible = 1
        self.dirty = 2
        self.health = self.DEFAULT_HEALTH

        self.collision_rects = []
        self.collision_masks = []
        self._colliding_objects = set()

        self.collidable = True
        self.can_move = False
        self.use_quadtrees = False

    def start(self):
        pass

    def damage(self, damage_value):
        pass

    def move_to(self, x, y, check_collisions=False):
        self.move_by(x - self.rect.x, y - self.rect.y, check_collisions)

    def move_by(self, dx, dy, check_collisions=True):
        if check_collisions:
            if dx:
                self._move(dx=dx)

            if dy:
                self._move(dy=dy)
        else:
            self.rect.move_ip(dx, dy)

    def _move(self, dx=0, dy=0):
        old_pos = self.rect.topleft

        self.rect.move_ip(dx, dy)
        self.rect.left = max(self.rect.left, 0)
        self.rect.right = min(self.rect.right, self.layer.parent.size[0])

        if not self.check_collisions(dx, dy):
            self.rect.topleft = old_pos

    def check_collisions(self, dx=0, dy=0):
        self._colliding_objects = set()
        allow_move = True

        for obj, self_rect, obj_rect in self.get_collisions():
            obj.on_collision(dx, dy, self, obj_rect, self_rect)

            if not self.on_collision(dx, dy, obj, self_rect, obj_rect):
                allow_move = False

            self._colliding_objects.add(obj)

        return allow_move

    def get_absolute_collision_rects(self):
        if self.collision_rects:
            return [rect.move(self.rect.topleft)
                    for rect in self.collision_rects]
        else:
            return [self.rect]

    def get_collisions(self, ignore_collidable_flag=False):
        num_checks = 0

        if self.collision_rects:
            self_rect = self.collision_rects[0].unionall(
                self.collision_rects[1:])
            self_rect.move_ip(self.rect.topleft)
        else:
            self_rect = self.rect

        for obj in self.layer.quad_tree.get_sprites(self_rect):
            num_checks += 1
            self_rect, obj_rect = \
                self._check_collision(self, obj, ignore_collidable_flag)

            if self_rect and obj_rect:
                yield obj, self_rect, obj_rect

    def _check_collision(self, left, right, ignore_collidable_flag):
        if (left == right or
            (not ignore_collidable_flag and
             ((not left.collidable or not right.collidable))) or
            left.layer.index != right.layer.index):
            return None, None

        left_rects = left.get_absolute_collision_rects()
        right_rects = right.get_absolute_collision_rects()

        for left_index, left_rect in enumerate(left_rects):
            right_index = left_rect.collidelist(right_rects)

            if right_index == -1:
                continue

            return left_rect, right_rects[right_index]

        return None, None

    def on_collision(self, dx, dy, obj, self_rect, obj_rect):
        return False

    def update_image(self):
        raise NotImplementedError

    def on_added(self, layer):
        pass

    def on_removed(self, layer):
        pass

    def tick(self):
        pass


class Sprite(BaseSprite):
    NAME = None
    MOVE_SPEED = 4
    RUN_SPEED = 8
    ANIM_MS = 150
    DEATH_BLINK_MS = 250
    MAX_BLINKS = 4
    LETHAL = False

    SPRITESHEET_ROWS = 1
    SPRITESHEET_COLS = 1
    SPRITESHEET_FRAMES = {
        Direction.SOUTH: {
            'default': [(0, 0)],
        },
        Direction.WEST: {
            'default': [(0, 0)],
        },
        Direction.EAST: {
            'default': [(0, 0)],
        },
        Direction.NORTH: {
            'default': [(0, 0)],
        },
    }

    NEED_TICKS = True

    def __init__(self, name=None):
        super(Sprite, self).__init__()

        # Signals
        self.moved = Signal()
        self.dead = Signal()

        # State
        self.quad_trees = set()
        self.layer = None
        self.name = name or self.NAME
        assert self.name

        self.started = False
        self.direction = Direction.SOUTH
        self.velocity = (0, 0)
        self.speed = self.MOVE_SPEED

        self.can_move = True
        self.use_quadtrees = True
        self.autoset_velocity = True

        self.frame_state = 'default'
        self.anim_frame = 0
        self.anim_timer = None

    def start(self):
        self.anim_timer = Timer(ms=self.ANIM_MS,
                                cb=self._on_anim_tick,
                                start_automatically=False)
        self.started = True

    def stop(self):
        self.stop_moving()
        self.started = False

    def damage(self, damage_value):
        if self.health > 0:
            self.health -= damage_value

            if self.health <= 0:
                self.die()
                return True

        return False

    def die(self, on_done=None):
        self.stop()
        self.blink(self.DEATH_BLINK_MS, lambda: self._stop_and_die(on_done))

    def _stop_and_die(self, on_done):
        self.dead.emit()
        self.remove()

        if on_done:
            on_done()

    def blink(self, ms, on_done):
        self.blink_count = 0
        self.visible = 0
        self.blink_timer = Timer(ms=ms, cb=lambda: self._on_blinked(on_done))

    def _on_blinked(self, on_done):
        self.blink_count += 1

        if self.visible:
            self.visible = 0
        else:
            self.visible = 1

        if self.blink_count == self.MAX_BLINKS:
            self.visible = 1
            self.blink_timer.stop()

            if on_done:
                on_done()

    def remove(self):
        self.stop()
        self.collidable = False
        self.visible = 0
        self.dirty = 1
        self.layer.remove(self)
        self.layer = None

    def update_image(self):
        self.image = self.generate_image()
        assert self.image

        self.rect.size = self.image.get_size()
        self.update_collision_rects()

    def generate_image(self):
        return load_spritesheet_frame(
            self.name,
            self._get_spritesheet_frames()[self.anim_frame],
            self.SPRITESHEET_ROWS,
            self.SPRITESHEET_COLS)

    def _get_spritesheet_frames(self):
        return self.SPRITESHEET_FRAMES[self.direction][self.frame_state]

    def move_by(self, dx, dy, check_collisions=True):
        super(Sprite, self).move_by(dx, dy, check_collisions=check_collisions)
        self.moved.emit(dx, dy)

    def set_direction(self, direction):
        if self.direction != direction:
            self.direction = direction
            self.update_velocity()
            self.update_image()

    def start_animation(self, name):
        self.frame_state = name
        self.anim_frame = 0

        if self.anim_timer:
            self.anim_timer.stop()

        self.anim_timer = Timer(ms=self.ANIM_MS,
                                cb=self._on_anim_tick)

    def stop_moving(self):
        self.velocity = (0, 0)
        self.frame_state = 'default'
        self.anim_frame = 0

        if self.anim_timer:
            self.anim_timer.stop()

        self.anim_timer = None

    def recompute_direction(self):
        if abs(self.velocity[0]) > abs(self.velocity[1]):
            if self.velocity[0] > 0:
                self.set_direction(Direction.EAST)
            elif self.velocity[0] < 0:
                self.set_direction(Direction.WEST)
        elif abs(self.velocity[1]) >= abs(self.velocity[0]):
            if self.velocity[1] > 0:
                self.set_direction(Direction.SOUTH)
            elif self.velocity[1] < 0:
                self.set_direction(Direction.NORTH)

    def update_collision_rects(self):
        pass

    def update_velocity(self):
        if not self.started or not self.autoset_velocity:
            return

        x, y = {
            Direction.WEST: (-1, None),
            Direction.EAST: (1, None),
            Direction.NORTH: (None, -1),
            Direction.SOUTH: (None, 1),
        }[self.direction]

        if x:
            x *= self.speed
        else:
            x = self.velocity[0]

        if y:
            y *= self.speed
        else:
            y = self.velocity[1]

        self.velocity = (x, y)

    def tick(self):
        if self.started and self.velocity != (0, 0):
            self.move_by(*self.velocity)

    def _on_anim_tick(self):
        frames = self._get_spritesheet_frames()

        self.anim_frame += 1

        if self.anim_frame == len(frames):
            self.anim_frame = 0

        self.dirty = 2
        self.update_image()


class WalkingSprite(Sprite):
    SPRITESHEET_FRAMES = {
        Direction.SOUTH: {
            'default': [(1, 0)],
            'walking': [(0, 0), (1, 0), (2, 0), (1, 0)],
            'running': [(0, 0), (2, 0)],
        },
        Direction.WEST: {
            'default': [(1, 1)],
            'walking': [(0, 1), (1, 1), (2, 1), (1, 1)],
            'running': [(0, 1), (2, 1)],
        },
        Direction.EAST: {
            'default': [(1, 2)],
            'walking': [(0, 2), (1, 2), (2, 2), (1, 2)],
            'running': [(0, 2), (2, 2)],
        },
        Direction.NORTH: {
            'default': [(1, 3)],
            'walking': [(0, 3), (1, 3), (2, 3), (1, 3)],
            'running': [(0, 3), (2, 3)],
        },
    }
    SPRITESHEET_ROWS = 4
    SPRITESHEET_COLS = 3


class Human(object):
    def update_collision_rects(self):
        self.collision_rects = [
            pygame.Rect(0, self.rect.height / 2,
                        self.rect.width, self.rect.height / 2),
        ]
