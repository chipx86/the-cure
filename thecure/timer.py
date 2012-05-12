from thecure import get_engine


class Timer(object):
    def __init__(self, ms, cb, one_shot=False, start_automatically=True):
        self.engine = get_engine()
        assert self.engine

        self.ms = ms
        self.cb = cb
        self.tick_count_count = 0
        self.started = False
        self.one_shot = one_shot
        self.tick_cnx = None
        self.start_automatically = True

        if ms > 0 and start_automatically:
            self.start()

    def start(self):
        if not self.started:
            self.tick_count = 0
            self.tick_cnx = self.engine.tick.connect(self.on_tick)
            self.started = True

    def reset(self):
        self.tick_count = 0

        if self.ms > 0 and self.start_automatically:
            self.start()

    def stop(self):
        if self.started:
            self.tick_cnx.disconnect()
            self.tick_cnx = None
            self.started = False

    def on_tick(self):
        self.tick_count += 1.0 / self.engine.FPS * 1000

        if self.tick_count >= self.ms:
            self.tick_count = 0
            self.cb()

            if self.one_shot:
                self.stop()
