from pygame.locals import *

from thecure import get_engine
from thecure.sprites.base import Direction, Sprite, WalkingSprite
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
