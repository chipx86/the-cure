from pygame.locals import *

from thecure.signals import Signal
from thecure.sprites.base import Direction, Sprite


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
                self.move_direction(Direction.RIGHT)
            elif event.key == K_LEFT:
                self.move_direction(Direction.LEFT)
            elif event.key == K_UP:
                self.move_direction(Direction.UP)
            elif event.key == K_DOWN:
                self.move_direction(Direction.DOWN)
        elif event.type == KEYUP:
            if event.key == K_RIGHT:
                self.stop_moving_direction(Direction.RIGHT)
            elif event.key == K_LEFT:
                self.stop_moving_direction(Direction.LEFT)
            elif event.key == K_UP:
                self.stop_moving_direction(Direction.UP)
            elif event.key == K_DOWN:
                self.stop_moving_direction(Direction.DOWN)

    def move_direction(self, direction):
        self.direction = direction

        x, y = {
            Direction.LEFT: (-1, None),
            Direction.RIGHT: (1, None),
            Direction.UP: (None, -1),
            Direction.DOWN: (None, 1),
        }[direction]

        if x:
            x *= self.MOVE_SPEED
        else:
            x = self.velocity[0]

        if y:
            y *= self.MOVE_SPEED
        else:
            y = self.velocity[1]

        self.velocity = (x, y)

        if not self.anim_timer.started:
            self.anim_timer.start()
            self.frame_state = 'walking'

        self.update_image()

    def stop_moving_direction(self, direction):
        if direction in (Direction.LEFT, Direction.RIGHT):
            self.velocity = (0, self.velocity[1])
        elif direction in (Direction.UP, Direction.DOWN):
            self.velocity = (self.velocity[0], 0)

        # The direction may not make any sense anymore, so recompute it.
        self.recompute_direction()

        if self.velocity == (0, 0):
            self.anim_timer.stop()
            self.frame_state = 'default'
            self.anim_frame = 0
            self.update_image()

    def recompute_direction(self):
        if self.velocity[1] > 0:
            self.direction = Direction.DOWN
        elif self.velocity[1] < 0:
            self.direction = Direction.UP
        elif self.velocity[0] > 0:
            self.direction = Direction.RIGHT
        elif self.velocity[0] < 0:
            self.direction = Direction.LEFT
