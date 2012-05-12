import math
import random

import pygame

from thecure import get_engine
from thecure.sprites import Direction, Sprite
from thecure.timer import Timer


class WanderMixin(object):
    MOVE_INTERVAL_MS = 1000
    PAUSE_CHANCE = 0.1
    CHANGE_DIR_CHANCE = 0.3
    WANDER_KEY_NAME = 'wandering'
    WANDER_DISTANCE = 64 * 8

    def __init__(self, *args, **kwargs):
        super(WanderMixin, self).__init__(*args, **kwargs)
        self.auto_wander = True
        self._wander_timer = None

    def start(self):
        super(WanderMixin, self).start()

        if self.auto_wander:
            self.wander()

    def stop(self):
        super(WanderMixin, self).stop()
        self.stop_wandering()

    def wander(self):
        self.set_home_pos()

        self._generate_direction()

        self._pause_wander = False
        self._wander_timer = Timer(ms=self.MOVE_INTERVAL_MS,
                                   cb=self._on_wander_tick)

    def stop_wandering(self):
        if self._wander_timer:
            self._wander_timer.stop()
            self._wander_timer = None

    def set_home_pos(self):
        self.home_pos = self.rect.center

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

        dist_x = self.home_pos[0] - self.rect.centerx
        dist_y = self.home_pos[1] - self.rect.centery

        turning_back = False

        if abs(dist_x) >= self.WANDER_DISTANCE / 2:
            self.velocity = (-self.velocity[0], self.velocity[1])
            turning_back = True

        if abs(dist_y) >= self.WANDER_DISTANCE / 2:
            self.velocity = (self.velocity[0], -self.velocity[1])
            turning_back = True

        if turning_back:
            self.recompute_direction()
        else:
            if random.random() <= self.CHANGE_DIR_CHANCE:
                self._generate_direction()

            if random.random() <= self.PAUSE_CHANCE:
                self._pause_wander = True
                self.stop_moving()
            elif self.frame_state != self.WANDER_KEY_NAME:
                self.start_animation(self.WANDER_KEY_NAME)



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

            if (not self.attacking and
                self.can_attack and
                self._can_see_player()):
                self.stop_wandering()
                self.attacking = True
                self.autoset_velocity = False

                self.attack_start_pos = self.rect.topleft
                self.attack_dest_pos = player.rect.center

                self.velocity, self.max_attack_ticks = self._get_attack_data()

                # Let it go a bit longer than that
                self.max_attack_ticks += self.ATTACK_TICKS_PAD
                self.attack_ticks = 1

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

    def _can_see_player(self):
        player = get_engine().player

        distance_x = abs(player.rect.x - self.rect.x)
        distance_y = abs(player.rect.y - self.rect.y)

        if (distance_x <= self.ATTACK_DISTANCE and
            distance_y <= self.ATTACK_DISTANCE):
            # See if there's anything in the way. We'll simulate an attack.

            start_pos = self.rect.topleft
            velocity, max_attack_ticks = self._get_attack_data()

            for i in xrange(1, max_attack_ticks - 1):
                pos = self._get_attack_position(start_pos, velocity, i)
                rect = pygame.Rect(pos, self.rect.size)

                for sprite in self.layer.iterate_in_rect(rect):
                    if sprite != self and sprite != player:
                        return False

            return True

        return False

    def _update_attack_pos(self):
        self.move_to(*self._get_attack_position(self.attack_start_pos,
                                                self.velocity,
                                                self.attack_ticks),
                     check_collisions=True)
        self.recompute_direction()

    def _get_attack_data(self):
        player = get_engine().player
        delta_x = player.rect.center[0] - self.rect.topleft[0]
        delta_y = player.rect.center[1] - self.rect.topleft[1]
        dist = math.sqrt(delta_x * delta_x + delta_y * delta_y)

        if dist == 0:
            return (0, 0), 0

        velocity = ((delta_x * (1.0 / dist) * self.ATTACK_SPEED),
                    (delta_y * (1.0 / dist) * self.ATTACK_SPEED))

        if velocity[0] == 0:
            max_attack_ticks = int(delta_y / velocity[1])
        else:
            max_attack_ticks = int(delta_x / velocity[0])

        return velocity, max_attack_ticks

    def _get_attack_position(self, start_pos, velocity, cur_tick):
        return (int(start_pos[0] + (cur_tick * velocity[0])),
                int(start_pos[1] + (cur_tick * velocity[1])))

    def _allow_attacking(self):
        self.can_attack = True

    def handle_collision(self, *args, **kwargs):
        if self.attacking:
            self.stop_attacking()

        return super(AttackLineMixin, self).handle_collision(*args, **kwargs)


class ChaseMixin(object):
    APPROACH_DISTANCE = 250
    CHASE_SPEED = 3
    STOP_FOLLOWING_DISTANCE = 1000
    SHOW_EXCLAMATION = True
    EXCLAMATION_MS = 700
    FOLLOWING_KEY_NAME = "walking"

    def __init__(self, *args, **kwargs):
        super(ChaseMixin, self).__init__(*args, **kwargs)

        self.following = False
        self.exclamation = None

    def stop(self):
        super(ChaseMixin, self).stop()
        self.stop_following()

    def tick(self):
        super(ChaseMixin, self).tick()

        if self.started:
            # Figure out how close we are to the player.
            player = get_engine().player

            distance_x = abs(player.rect.x - self.rect.x)
            distance_y = abs(player.rect.y - self.rect.y)

            if (self.following and
                (distance_x >= self.STOP_FOLLOWING_DISTANCE or
                 distance_y >= self.STOP_FOLLOWING_DISTANCE)):
                self.stop_following()
            if (self.following or
                (distance_x <= self.APPROACH_DISTANCE and
                 distance_y <= self.APPROACH_DISTANCE and
                 not self.following and
                 (not self.SHOW_EXCLAMATION or not self.exclamation))):

                if not self.following and not self.exclamation:
                    if self.SHOW_EXCLAMATION:
                        # They haven't noticed the player before, but they
                        # do now!
                        self.show_exclamation(on_done=self.start_following)
                        return
                    else:
                        self.start_following()

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

                self.velocity = (x * self.CHASE_SPEED, y * self.CHASE_SPEED)

                if distance_x > distance_y:
                    self.direction = x_dir
                elif distance_y > distance_x:
                    self.direction = y_dir

                self.update_image()

        super(ChaseMixin, self).tick()

    def start_following(self):
        self.following = True
        self.stop_wandering()
        self.velocity = (0, 0)
        self.start_animation(self.FOLLOWING_KEY_NAME)

    def stop_following(self):
        self.following = False
        self.stop_moving()
        self.wander()

    def wander(self):
        pass

    def stop_wandering(self):
        pass

    def show_exclamation(self, exclamation_type='exclamation', on_done=None):
        self.stop_wandering()
        self.stop_moving()

        self.exclamation = Sprite(exclamation_type)
        self.layer.add(self.exclamation)
        self.exclamation.move_to(
            self.rect.centerx - self.exclamation.rect.width / 2,
            self.rect.y - self.exclamation.rect.height)
        self.exclamation.start()

        Timer(ms=self.EXCLAMATION_MS,
              cb=lambda: self._on_exclamation_done(on_done),
              one_shot=True)

    def _on_exclamation_done(self, on_done):
        if self.exclamation:
            self.exclamation.remove()
            self.exclamation = None

        if on_done:
            on_done()
