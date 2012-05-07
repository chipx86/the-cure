import pygame
from pygame.locals import *

from thecure.signals import Signal
from thecure.sprites.base import Direction, Sprite, WalkingSprite
from thecure.timer import Timer


class Bullet(Sprite):
    NAME = 'bullet'
    MOVE_SPEED = 10
    OFFSET_X = 6
    OFFSET_Y = 12
    DAMAGE_VALUE = 5

    def __init__(self, owner_sprite):
        super(Bullet, self).__init__()
        self.owner_sprite = owner_sprite

    def move_by(self, *args, **kwargs):
        super(Bullet, self).move_by(*args, **kwargs)

        if (self.started and
            (self.rect.x == 0 or
             self.rect.right == self.layer.parent.size[0] or
             self.rect.y == 0 or
             self.rect.bottom == self.layer.parent.size[1])):
            # We've hit the edge of the screen, so disappear.
            self.remove()

    def move_beside(self, sprite, direction):
        if direction == Direction.UP:
            self.move_to(sprite.rect.right - self.rect.width - self.OFFSET_X,
                         sprite.rect.y - self.rect.height / 2)
        elif direction == Direction.DOWN:
            self.move_to(sprite.rect.x + self.OFFSET_X,
                         sprite.rect.bottom - 2 * self.rect.height)
        elif direction == Direction.LEFT:
            self.move_to(sprite.rect.x + self.rect.width / 2,
                         sprite.rect.y + self.OFFSET_Y +
                         (sprite.rect.height - self.rect.height) / 2)
        elif direction == Direction.RIGHT:
            self.move_to(sprite.rect.right - 2 * self.rect.width,
                         sprite.rect.y + self.OFFSET_Y +
                         (sprite.rect.height - self.rect.height) / 2)

    def should_adjust_position_with(self, obj, dx, dy):
        return False

    def on_collision(self, dx, dy, obj, self_rect, obj_rect):
        if obj != self.owner_sprite:
            self.remove()

            if obj.health > 0:
                obj.damage(self.DAMAGE_VALUE)

        return True


class Player(WalkingSprite):
    MAX_LIVES = 3
    MAX_HEALTH = 3

    SHOOT_MS = 500

    SPRITESHEET_FRAMES = {
        Direction.DOWN: dict(
            WalkingSprite.SPRITESHEET_FRAMES[Direction.DOWN], **{
                'shooting': [(2, 0)],
            }),
        Direction.LEFT: dict(
            WalkingSprite.SPRITESHEET_FRAMES[Direction.LEFT], **{
                'shooting': [(0, 1)],
            }),
        Direction.RIGHT: dict(
            WalkingSprite.SPRITESHEET_FRAMES[Direction.RIGHT], **{
                'shooting': [(0, 2)],
            }),
        Direction.UP: dict(
            WalkingSprite.SPRITESHEET_FRAMES[Direction.UP], **{
                'shooting': [(2, 3)],
            }),
    }

    def __init__(self):
        super(Player, self).__init__('player')

        # Signals
        self.health_changed = Signal()
        self.lives_changed = Signal()

        # State
        self.running = False
        self.shooting = False
        self.shoot_timer = Timer(ms=self.SHOOT_MS,
                                 cb=self.shoot,
                                 start_automatically=False)

    def update_collision_rects(self):
        self.collision_rects = [
            pygame.Rect(0, self.rect.height / 2,
                        self.rect.width, self.rect.height / 2),
        ]

    def reset(self):
        self.health = self.MAX_HEALTH
        self.lives = self.MAX_LIVES
        self._update_animation()

    def handle_event(self, event):
        if event.type == KEYDOWN:
            if event.key == K_RIGHT:
                self.move_direction(Direction.RIGHT)
            elif event.key == K_LEFT:
                self.move_direction(Direction.LEFT)
            elif event.key == K_UP:
                self.move_direction(Direction.UP)
            elif event.key == K_DOWN:
                self.move_direction(Direction.DOWN)
            elif event.key == K_c:
                self.set_shooting(True)
            elif event.key in (K_LSHIFT, K_RSHIFT):
                self.set_running(True)
        elif event.type == KEYUP:
            if event.key == K_RIGHT:
                self.stop_moving_direction(Direction.RIGHT)
            elif event.key == K_LEFT:
                self.stop_moving_direction(Direction.LEFT)
            elif event.key == K_UP:
                self.stop_moving_direction(Direction.UP)
            elif event.key == K_DOWN:
                self.stop_moving_direction(Direction.DOWN)
            elif event.key == K_c:
                self.set_shooting(False)
            elif event.key in (K_LSHIFT, K_RSHIFT):
                self.set_running(False)

    def move_direction(self, direction):
        self.direction = direction

        self.update_velocity()
        self._update_animation()

        self.update_image()

    def stop_moving_direction(self, direction):
        if direction in (Direction.LEFT, Direction.RIGHT):
            self.velocity = (0, self.velocity[1])
        elif direction in (Direction.UP, Direction.DOWN):
            self.velocity = (self.velocity[0], 0)

        # The direction may not make any sense anymore, so recompute it.
        self.recompute_direction()
        self._update_animation()

    def set_shooting(self, shooting):
        if self.shooting == shooting:
            return

        self.shooting = shooting

        if shooting:
            self.shoot_timer.start()
            self.shoot()
        else:
            self.shoot_timer.stop()

        self._update_animation()

    def shoot(self):
        bullet = Bullet(self)
        self.layer.add(bullet)

        bullet.move_beside(self, self.direction)
        bullet.start()
        bullet.set_direction(self.direction)
        bullet.update_velocity()

    def should_adjust_position_with(self, obj, dx, dy):
        return not isinstance(obj, Bullet) or obj.owner_sprite != self

    def set_running(self, running):
        self.running = running

        if running:
            self.speed = self.RUN_SPEED
        else:
            self.speed = self.MOVE_SPEED

        if self.velocity != (0, 0):
            self.update_velocity()

        self._update_animation()

    def stop_running(self):
        self.running = False
        self._update_animation()

    def _update_animation(self):
        if self.velocity == (0, 0):
            if self.shooting and self.frame_state != 'shooting':
                self.frame_state = 'shooting'
            elif not self.shooting and self.frame_state != 'default':
                self.frame_state = 'default'
            else:
                return

            self.anim_timer.stop()
        else:
            if self.running and self.frame_state != 'running':
                self.frame_state = 'running'
            elif self.frame_state != 'walking':
                self.frame_state = 'walking'
            else:
                return

            self.anim_timer.start()

        self.anim_frame = 0
        self.update_image()
