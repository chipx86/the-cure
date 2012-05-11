import pygame
from pygame.locals import *

from thecure import get_engine
from thecure.signals import Signal
from thecure.sprites.base import Direction, Sprite, WalkingSprite, Human
from thecure.timer import Timer


class Bullet(Sprite):
    NAME = 'bullet'
    MOVE_SPEED = 10
    OFFSET_X = 6
    OFFSET_Y = 12
    DAMAGE_VALUE = 5
    OFFSCREEN_DIST = 100

    def __init__(self, owner_sprite):
        super(Bullet, self).__init__()
        self.owner_sprite = owner_sprite

    def move_by(self, *args, **kwargs):
        super(Bullet, self).move_by(*args, **kwargs)

        camera_rect = get_engine().camera.rect

        if not self.layer:
            return

        screen_size = self.layer.parent.size

        if (self.started and
            (self.rect.x <= max(camera_rect.x - self.OFFSCREEN_DIST, 0) or
             self.rect.y <= max(camera_rect.y - self.OFFSCREEN_DIST, 0) or
             self.rect.right > min(camera_rect.right + self.OFFSCREEN_DIST,
                                   screen_size[0]) or
             self.rect.bottom > min(camera_rect.bottom + self.OFFSCREEN_DIST,
                                    screen_size[1]))):
            # We've hit the edge of the world, or far enough away from the
            # camera, so disappear.
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

            if (obj.health > 0 and obj.damage(self.DAMAGE_VALUE) and
                isinstance(obj, Human)):
                self.owner_sprite.human_kill_count += 1

        return True


class Player(WalkingSprite):
    MAX_LIVES = 3
    MAX_HEALTH = 6

    SHOOT_MS = 500
    FALL_SPEED = 10
    HURT_BLINK_MS = 250

    SPRITESHEET_FRAMES = {
        Direction.DOWN: dict(
            WalkingSprite.SPRITESHEET_FRAMES[Direction.DOWN], **{
                'shooting': [(2, 0)],
                'falling': [(1, 0)],
            }),
        Direction.LEFT: dict(
            WalkingSprite.SPRITESHEET_FRAMES[Direction.LEFT], **{
                'shooting': [(0, 1)],
                'falling': [(1, 1)],
            }),
        Direction.RIGHT: dict(
            WalkingSprite.SPRITESHEET_FRAMES[Direction.RIGHT], **{
                'shooting': [(0, 2)],
                'falling': [(1, 2)],
            }),
        Direction.UP: dict(
            WalkingSprite.SPRITESHEET_FRAMES[Direction.UP], **{
                'shooting': [(2, 3)],
                'falling': [(1, 3)],
            }),
    }

    def __init__(self):
        super(Player, self).__init__('player')

        # Signals
        self.health_changed = Signal()
        self.lives_changed = Signal()

        # State
        self.human_kill_count = 0
        self.shoot_timer = Timer(ms=self.SHOOT_MS,
                                 cb=self.shoot,
                                 start_automatically=False)
        self.reset()

    def update_collision_rects(self):
        self.collision_rects = [
            pygame.Rect(0, self.rect.height / 2,
                        self.rect.width, self.rect.height / 2),
        ]

    def reset(self):
        self.health = self.MAX_HEALTH
        self.lives = self.MAX_LIVES
        self.invulnerable = False
        self.running = False
        self.falling = False
        self.shooting = False
        self.can_run = True
        self.collidable = True
        self.allow_player_control = True

        self.health_changed.emit()
        self.lives_changed.emit()

        self.stop_moving()
        self._update_animation()

    def handle_event(self, event):
        if not self.allow_player_control:
            return

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
            elif event.key == K_F4:
                self.collidable = not self.collidable
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
        if not self.can_run:
            return

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

    def fall(self):
        self.collidable = False
        self.stop_running()
        self.set_direction(Direction.DOWN)
        self.velocity = (0, self.FALL_SPEED)
        self.falling = True
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
            new_state = None

            if self.running and self.frame_state != 'running':
                new_state = 'running'
            elif self.falling:
                new_state = 'falling'
            elif self.frame_state != 'walking':
                new_state = 'walking'
            else:
                return

            if new_state:
                self.start_animation(new_state)

        self.anim_frame = 0
        self.update_image()

    def on_collision(self, dx, dy, obj, self_rect, obj_rect):
        if obj.LETHAL and self.health > 0:
            if not self.invulnerable:
                self.health -= 1
                self.health_changed.emit()

                if self.health == 0:
                    self.on_dead()
                else:
                    self.invulnerable = True
                    self.blink(self.HURT_BLINK_MS, self._on_hurt_blink_done)

            return True

    def _on_hurt_blink_done(self):
        self.invulnerable = False

    def on_dead(self):
        self.lives -= 1
        self.lives_changed.emit()
        self.stop_moving()

        engine = get_engine()

        if self.lives == 0:
            self.die(engine.game_over)
        else:
            self.health = self.MAX_HEALTH
            self.health_changed.emit()
            engine.dead()
