import math

from pygame.locals import *

from thecure import get_engine
from thecure.sprites.base import Direction, Sprite, WalkingSprite
from thecure.sprites.behaviors import WanderMixin
from thecure.timer import Timer


class Enemy(WalkingSprite):
    DEFAULT_HEALTH = 10


class InfectedHuman(Enemy):
    MOVE_SPEED = 2
    APPROACH_DISTANCE = 300
    EXCLAMATION_MS = 700

    def __init__(self, *args, **kwargs):
        super(InfectedHuman, self).__init__(*args, **kwargs)

        self.following = False
        self.exclamation = None

    def tick(self):
        super(InfectedHuman, self).tick()

        if self.started:
            # Figure out how close we are to the player.
            player = get_engine().player

            distance_x = abs(player.rect.x - self.rect.x)
            distance_y = abs(player.rect.y - self.rect.y)

            if (self.following or
                (self.frame_state == 'default' and
                 distance_x <= self.APPROACH_DISTANCE and
                 distance_y <= self.APPROACH_DISTANCE and
                 not self.following and
                 not self.exclamation)):

                if not self.following and not self.exclamation:
                    # They haven't noticed the player before, but they do now!
                    self.show_exclamation()

                x_dir = None
                y_dir = None

                if player.rect.x > self.rect.x:
                    x = 1
                    x_dir = Direction.RIGHT
                elif player.rect.x < self.rect.x:
                    x = -1
                    x_dir = Direction.LEFT
                else:
                    x = 0

                if player.rect.y > self.rect.y:
                    y = 1
                    y_dir = Direction.DOWN
                elif player.rect.y < self.rect.y:
                    y = -1
                    y_dir = Direction.UP
                else:
                    y = 0

                if self.following:
                    self.velocity = (x * self.MOVE_SPEED, y * self.MOVE_SPEED)

                if distance_x > distance_y:
                    self.direction = x_dir
                elif distance_y > distance_x:
                    self.direction = y_dir

                self.update_image()

                if self.velocity != (0, 0):
                    self.frame_state = 'walking'
                    self.anim_timer.start()
                else:
                    self.frame_state = 'default'
                    self.anim_timer.stop()

    def show_exclamation(self):
        self.exclamation = Sprite('exclamation')
        self.layer.add(self.exclamation)
        self.exclamation.move_to(
            self.rect.centerx - self.exclamation.rect.width / 2,
            self.rect.y - self.exclamation.rect.height)
        self.exclamation.start()

        Timer(ms=self.EXCLAMATION_MS, cb=self._on_exclamation_done,
              one_shot=True)

    def _on_exclamation_done(self):
        self.exclamation.remove()
        self.exclamation = None
        self.following = True


class InfectedWife(InfectedHuman):
    MOVE_SPEED = 1
    NAME = 'infectedwife'


class Snake(Enemy, WanderMixin):
    NAME = 'snake'
    MOVE_SPEED = 1
    ATTACK_SPEED = 8
    ATTACK_DISTANCE = 400
    POST_ATTACK_MS = 2000
    ATTACK_TICKS_PAD = 10
    SPRITESHEET_ROWS = 4
    SPRITESHEET_COLS = 3
    SPRITESHEET_FRAMES = {
        Direction.DOWN: {
            'default': [(1, 0)],
            'wandering': [(0, 0), (1, 0), (2, 0), (1, 0)],
        },
        Direction.LEFT: {
            'default': [(1, 1)],
            'wandering': [(0, 1), (1, 1), (2, 1), (1, 1)],
        },
        Direction.RIGHT: {
            'default': [(1, 2)],
            'wandering': [(0, 2), (1, 2), (2, 2), (1, 2)],
        },
        Direction.UP: {
            'default': [(1, 3)],
            'wandering': [(0, 3), (1, 3), (2, 3), (1, 3)],
        },
    }

    def __init__(self):
        super(Snake, self).__init__()

        self.frame_state = 'wandering'
        self.attack_start_pos = None
        self.attack_dest_pos = None
        self.attacking = False
        self.can_attack = True

    def start(self):
        super(Snake, self).start()
        self.anim_timer.start()
        self.wander()

    def tick(self):
        if self.started:
            engine = get_engine()
            player = engine.player

            distance_x = abs(player.rect.x - self.rect.x)
            distance_y = abs(player.rect.y - self.rect.y)

            if (not self.attacking and
                self.can_attack and
                distance_x <= self.ATTACK_DISTANCE and
                distance_y <= self.ATTACK_DISTANCE):
                self.stop_wandering()
                self.attacking = True
                self.autoset_velocity = False

                self.attack_start_pos = self.rect.topleft
                self.attack_dest_pos = player.rect.center

                delta_x = self.attack_dest_pos[0] - self.attack_start_pos[0]
                delta_y = self.attack_dest_pos[1] - self.attack_start_pos[1]

                dist = math.sqrt(delta_x * delta_x + delta_y * delta_y)
                self.velocity = ((delta_x * (1.0 / dist) * self.ATTACK_SPEED),
                                 (delta_y * (1.0 / dist) * self.ATTACK_SPEED))

                self.attack_ticks = 1

                if self.velocity[0] == 0:
                    self.max_attack_ticks = int(delta_y / self.velocity[1])
                else:
                    self.max_attack_ticks = int(delta_x / self.velocity[0])

                # Let it go a bit longer than that
                self.max_attack_ticks += self.ATTACK_TICKS_PAD

                self._update_attack_pos()
            elif self.attacking:
                self.attack_ticks += 1
                self._update_attack_pos()

                if self.attack_ticks >= self.max_attack_ticks:
                    self.stop_attacking()
            else:
                # Allow normal moving logic to happen.
                super(Snake, self).tick()

    def stop_attacking(self):
        self.attacking = False
        self.attack_dest_pos = None
        self.can_attack =False
        self.velocity = (0, 0)
        self.autoset_velocity = True
        self.wander()

        Timer(ms=self.POST_ATTACK_MS, cb=self._allow_attacking, one_shot=True)

    def _update_attack_pos(self):
        self.move_to(int(self.attack_start_pos[0] +
                         (self.attack_ticks * self.velocity[0])),
                     int(self.attack_start_pos[1] +
                         (self.attack_ticks * self.velocity[1])),
                     check_collisions=True)
        self.recompute_direction()

    def _allow_attacking(self):
        self.can_attack = True

    def handle_collision(self, obj, rect, dx, dy):
        if self.attacking:
            self.stop_attacking()
