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

        self.running = False

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
            elif event.key in (K_LSHIFT, K_RSHIFT):
                self.set_running(False)

    def move_direction(self, direction):
        self.direction = direction

        self._update_velocity()
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

    def set_running(self, running):
        self.running = running

        if self.velocity != (0, 0):
            self._update_velocity()

        self._update_animation()

    def stop_running(self):
        self.running = False
        self._update_animation()

    def _update_velocity(self):
        x, y = {
            Direction.LEFT: (-1, None),
            Direction.RIGHT: (1, None),
            Direction.UP: (None, -1),
            Direction.DOWN: (None, 1),
        }[self.direction]

        if self.running:
            speed = self.RUN_SPEED
        else:
            speed = self.MOVE_SPEED

        if x:
            x *= speed
        else:
            x = self.velocity[0]

        if y:
            y *= speed
        else:
            y = self.velocity[1]

        self.velocity = (x, y)

    def _update_animation(self):
        if self.velocity == (0, 0):
            if self.frame_state != 'default':
                self.anim_timer.stop()
                self.frame_state = 'default'
                self.anim_frame = 0
                self.update_image()
        else:
            if self.running and self.frame_state != 'running':
                self.frame_state = 'running'
            elif self.frame_state != 'walking':
                self.frame_state = 'walking'
            else:
                return

            self.anim_frame = 0
            self.anim_timer.start()
            self.update_image()
