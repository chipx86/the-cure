from thecure.sprites import Direction, Sprite


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
        self.frame_state = 'fading'
        self.anim_timer.start()

    def update_image(self):
        if self.frame_state == 'fading' and self.anim_frame == 5:
            self.anim_frame = 0
            self.frame_state = 'default'
            self.remove()
            return

        super(LostBoy, self).update_image()
