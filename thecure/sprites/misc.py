from thecure import get_engine
from thecure.signals import Signal
from thecure.sprites import Direction, Sprite, Human, WalkingSprite
from thecure.sprites.behaviors import ChaseMixin
from thecure.timer import Timer


class LostBoy(Sprite):
    NAME = "lostboy"
    ANIM_MS = 200
    SPRITESHEET_ROWS = 1
    SPRITESHEET_COLS = 6
    SPRITESHEET_FRAMES = {
        Direction.DOWN: {
            'default': [(0, 0)],
            'fading': [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0)],
        },
    }

    def __init__(self):
        super(LostBoy, self).__init__()
        self.direction = Direction.DOWN

    def fadeout(self):
        self.start_animation('fading')

    def update_image(self):
        if self.frame_state == 'fading' and self.anim_frame == 5:
            self.anim_frame = 0
            self.frame_state = 'default'
            self.dead.emit()
            self.remove()
            return

        super(LostBoy, self).update_image()


class Wife(ChaseMixin, Human, WalkingSprite):
    MOVE_SPEED = 1
    CHASE_SPEED = 1
    WANDER_KEY_NAME = 'walking'
    DEFAULT_HEALTH = 1
    CLEAN_NAME = 'wife'
    INFECTED_NAME = 'infectedwife'
    NAME = INFECTED_NAME
    TRANSITION_MS = 250
    MAX_TRANSITIONS = 6

    def __init__(self):
        super(Wife, self).__init__()

        self.transitioned = Signal()
        self.showed_exclamation = False

    def on_collision(self, dx, dy, obj, self_rect, obj_rect):
        if obj == get_engine().player and not self.showed_exclamation:
            get_engine().ui_manager.close_monologues()
            self.show_exclamation('heart_exclamation',
                                  self._transition_clean)
            self.showed_exclamation = True

    def _transition_clean(self):
        self.transition_count = 0
        self.transition_timer = Timer(ms=self.TRANSITION_MS,
                                      cb=lambda: self._on_transition())

    def _on_transition(self):
        self.transition_count += 1

        if self.name == self.INFECTED_NAME:
            self.name = self.CLEAN_NAME
        else:
            self.name = self.INFECTED_NAME

        if self.transition_count == self.MAX_TRANSITIONS:
            self.name = self.CLEAN_NAME
            self.transition_timer.stop()
            self.transitioned.emit()
