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
    SHOULD_CHECK_COLLISIONS = True

    def __init__(self):
        super(BaseSprite, self).__init__()

        self.rect = pygame.Rect(0, 0, 0, 0)
        self.image = None
        self.visible = 1
        self.dirty = 2

        self.collision_rects = []
        self.collision_masks = []
        self._colliding_objects = set()

        self.collidable = True
        self.can_move = False
        self.use_quadtrees = False

    def start(self):
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

        self.update_collision_rects()

    def _move(self, dx=0, dy=0):
        self.rect.move_ip(dx, dy)
        self.rect.left = max(self.rect.left, 0)
        self.rect.right = min(self.rect.right, self.layer.parent.size[0])
        self.check_collisions(dx, dy)

    def check_collisions(self, dx=0, dy=0):
        old_colliding_objects = set(self._colliding_objects)
        self._colliding_objects = set()

        for obj, self_rect, obj_rect in self.get_collisions():
            if (self_rect == self.rect and
                self.should_adjust_position_with(obj, dx, dy)):
                self.position_beside(obj_rect, dx, dy)

            obj.handle_collision(self, obj_rect, dx, dy)
            self.on_collision(dx, dy, obj, self_rect, obj_rect)
            self._colliding_objects.add(obj)

        for obj in old_colliding_objects.difference(self._colliding_objects):
            obj.handle_stop_colliding(self)

    def should_adjust_position_with(self, obj, dx, dy):
        return True

    def position_beside(self, rect, dx, dy):
        if dy < 0:
            self.rect.top = rect.bottom
        elif dy > 0:
            self.rect.bottom = rect.top
        elif dx < 0:
            self.rect.left = rect.right
        elif dx > 0:
            self.rect.right = rect.left

    def get_collisions(self, tree=None, ignore_collidable_flag=False):
        if not self.SHOULD_CHECK_COLLISIONS and not ignore_collidable_flag:
            raise StopIteration

        if tree is None:
            tree = self.layer.quad_tree

        num_checks = 0

        if self.collision_rects:
            self_rect = self.collision_rects[0].unionall(
                self.collision_rects[1:])
        else:
            self_rect = self.rect

        # We want more detailed collision info, so we use our own logic
        # instead of calling spritecollide.
        for obj in tree.get_sprites(self_rect):
            num_checks += 1
            self_rect, obj_rect = \
                self._check_collision(self, obj, ignore_collidable_flag)

            if self_rect and obj_rect:
                yield obj, self_rect, obj_rect

        #print 'Performing %s checks' % num_checks

    def _check_collision(self, left, right, ignore_collidable_flag):
        if (left == right or
            left.layer.index != right.layer.index or
            (not ignore_collidable_flag and
             ((not left.collidable or not right.collidable) or
              (not left.SHOULD_CHECK_COLLISIONS and
               not right.SHOULD_CHECK_COLLISIONS)))):
            return None, None

        left_rects = left.collision_rects or [left.rect]
        right_rects = right.collision_rects or [right.rect]

        for left_index, left_rect in enumerate(left_rects):
            right_index = left_rect.collidelist(right_rects)

            if right_index == -1:
                continue

            right_rect = right_rects[right_index]

            return left_rect, right_rect

        return None, None

    def update_collision_rects(self):
        pass

    def handle_collision(self, obj, rect, dx, dy):
        print '%s collided with %s' % (self, obj)
        pass

    def handle_stop_colliding(self, obj):
        pass

    def on_collision(self, dx, dy, obj, self_rect, obj_rect):
        pass

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

    SPRITESHEET_FRAMES = {
        Direction.DOWN: {
            'default': [(64, 0)],
            'walking': [(0, 0), (64, 0), (128, 0), (64, 0)],
            'running': [(0, 0), (128, 0)],
        },
        Direction.LEFT: {
            'default': [(64, 96)],
            'walking': [(0, 96), (64, 96), (128, 96), (64, 96)],
            'running': [(0, 96), (128, 96)],
        },
        Direction.RIGHT: {
            'default': [(64, 192)],
            'walking': [(0, 192), (64, 192), (128, 192), (64, 192)],
            'running': [(0, 192), (128, 192)],
        },
        Direction.UP: {
            'default': [(64, 288)],
            'walking': [(0, 288), (64, 288), (128, 288), (64, 288)],
            'running': [(0, 288), (128, 288)],
        },
    }
    SPRITE_SIZE = (64, 96)
    MOVE_SPEED = 4
    RUN_SPEED = 8
    ANIM_MS = 150

    def __init__(self, name=None):
        super(Sprite, self).__init__()

        # Signals
        self.moved = Signal()

        # State
        self.quad_trees = set()
        self.layer = None
        self.name = name or self.NAME
        assert self.name

        self.direction = Direction.DOWN
        self.velocity = (0, 0)
        self.speed = self.MOVE_SPEED

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

    def move_by(self, dx, dy, check_collisions=True):
        super(Sprite, self).move_by(dx, dy, check_collisions=check_collisions)
        self.moved.emit(dx, dy)

    def set_direction(self, direction):
        if self.direction != direction:
            self.direction = direction
            self.update_velocity()
            self.update_image()

    def recompute_direction(self):
        if self.velocity[1] > 0:
            self.set_direction(Direction.DOWN)
        elif self.velocity[1] < 0:
            self.set_direction(Direction.UP)
        elif self.velocity[0] > 0:
            self.set_direction(Direction.RIGHT)
        elif self.velocity[0] < 0:
            self.set_direction(Direction.LEFT)

    def update_velocity(self):
        x, y = {
            Direction.LEFT: (-1, None),
            Direction.RIGHT: (1, None),
            Direction.UP: (None, -1),
            Direction.DOWN: (None, 1),
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
