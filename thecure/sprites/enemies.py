from pygame.locals import *

from thecure import get_engine
from thecure.signals import Signal
from thecure.sprites.base import Direction, Sprite, WalkingSprite


class Enemy(WalkingSprite):
    DEFAULT_HEALTH = 10


class InfectedHuman(Enemy):
    MOVE_SPEED = 2

    def tick(self):
        super(InfectedHuman, self).tick()

        if self.started:
            # Figure out how close we are to the player.
            player = get_engine().player

            if player.rect.x > self.rect.x:
                x = 1
            elif player.rect.x < self.rect.x:
                x = -1
            else:
                x = 0

            if player.rect.y > self.rect.y:
                y = 1
            elif player.rect.y < self.rect.y:
                y = -1
            else:
                y = 0

            self.velocity = (x * self.MOVE_SPEED, y * self.MOVE_SPEED)

            if self.velocity != (0, 0):
                self.frame_state = 'walking'
                self.anim_timer.start()
                self.recompute_direction()
            else:
                self.frame_state = 'default'
                self.anim_timer.stop()
