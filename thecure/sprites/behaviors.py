import math
import random

from thecure import get_engine
from thecure.sprites import Direction, Sprite
from thecure.timer import Timer


class WanderMixin(object):
    MOVE_INTERVAL_MS = 1000
    PAUSE_CHANCE = 0.1
    CHANGE_DIR_CHANCE = 0.3
    WANDER_KEY_NAME = 'wandering'

    def start(self):
        super(WanderMixin, self).start()

        self.wander()

    def wander(self):
        self.frame_state = self.WANDER_KEY_NAME
        self.anim_timer.start()

        self._generate_direction()

        self._pause_wander = False
        self._wander_timer = Timer(ms=self.MOVE_INTERVAL_MS,
                                   cb=self._on_wander_tick)

    def stop_wandering(self):
        self._wander_timer.stop()
        self._wander_timer = None

    def _generate_direction(self):
        self.velocity = (0, 0)

        # Do this twice, so we can maybe get different X, Y velocities.
        self.set_direction(random.randint(0, 3))
        self.update_velocity()

        self.set_direction(random.randint(0, 3))
        self.update_velocity()

    def _on_wander_tick(self):
        if self._pause_wander:
            self._pause_wander = False
            return

        if random.random() <= self.CHANGE_DIR_CHANCE:
            self._generate_direction()

        if random.random() <= self.PAUSE_CHANCE:
            self._pause_wander = True
            self.velocity = (0, 0)


class AttackLineMixin(object):
    ATTACK_SPEED = 8
    ATTACK_DISTANCE = 400
    POST_ATTACK_MS = 2000
    ATTACK_TICKS_PAD = 10

    def __init__(self):
        super(AttackLineMixin, self).__init__()

        self.attack_start_pos = None
        self.attack_dest_pos = None
        self.attacking = False
        self.can_attack = True

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
                super(AttackLineMixin, self).tick()

    def stop_attacking(self):
        self.attacking = False
        self.attack_dest_pos = None
        self.can_attack = False
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

    def handle_collision(self, *args, **kwargs):
        if self.attacking:
            self.stop_attacking()

        return super(AttackLineMixin, self).handle_collision(*args, **kwargs)


class ChaseMixin(object):
    APPROACH_DISTANCE = 300
    SHOW_EXCLAMATION = True
    EXCLAMATION_MS = 700

    def __init__(self, *args, **kwargs):
        super(ChaseMixin, self).__init__(*args, **kwargs)

        self.following = False
        self.exclamation = None

    def tick(self):
        super(ChaseMixin, self).tick()

        if self.started:
            # Figure out how close we are to the player.
            player = get_engine().player

            distance_x = abs(player.rect.x - self.rect.x)
            distance_y = abs(player.rect.y - self.rect.y)

            if (self.following or
                (distance_x <= self.APPROACH_DISTANCE and
                 distance_y <= self.APPROACH_DISTANCE and
                 not self.following and
                 (not self.SHOW_EXCLAMATION or not self.exclamation))):

                if not self.following and not self.exclamation:
                    if self.SHOW_EXCLAMATION:
                        # They haven't noticed the player before, but they
                        # do now!
                        self.show_exclamation()
                    else:
                        self.following = True

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
        self.stop_wandering()
        self.stop()

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
        self.start()
