from pygame.locals import *

from thecure import get_engine
from thecure.sprites.base import Direction, WalkingSprite


class Enemy(WalkingSprite):
    DEFAULT_HEALTH = 10


class InfectedHuman(Enemy):
    MOVE_SPEED = 2
    APPROACH_DISTANCE = 400

    def tick(self):
        super(InfectedHuman, self).tick()

        if self.started:
            # Figure out how close we are to the player.
            player = get_engine().player

            distance_x = abs(player.rect.x - self.rect.x)
            distance_y = abs(player.rect.y - self.rect.y)

            if (self.frame_state == 'walking' or
                (distance_x <= self.APPROACH_DISTANCE and
                 distance_y <= self.APPROACH_DISTANCE)):
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

                self.velocity = (x * self.MOVE_SPEED, y * self.MOVE_SPEED)

                if self.velocity != (0, 0):
                    self.frame_state = 'walking'
                    self.anim_timer.start()

                    if distance_x > distance_y:
                        self.set_direction(x_dir)
                    elif distance_y > distance_x:
                        self.set_direction(y_dir)
                else:
                    self.frame_state = 'default'
                    self.anim_timer.stop()
