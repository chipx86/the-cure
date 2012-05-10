import random

from thecure.timer import Timer


class WanderMixin(object):
    MOVE_INTERVAL_MS = 1000
    PAUSE_CHANCE = 0.1
    CHANGE_DIR_CHANCE = 0.3

    def wander(self):
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
