from thecure.signals import Signal


class EventBox(object):
    def __init__(self, level):
        self.level = level
        self.rects = []
        self._moved_cnxs = []
        level.register_for_events(self)
        self.entered_objects = set()

        # Signals
        self.event_fired = Signal()
        self.object_moved = Signal()
        self.object_entered = Signal()
        self.object_exited = Signal()

    def disconnect(self):
        self.level.unregister_for_events(self)

        for cnx in self._moved_cnxs:
            cnx.disconnect()

        self._moved_cnxs = []

    def watch_object_moves(self, obj):
        self._moved_cnxs.append(
            obj.moved.connect(lambda dx, dy: self.handle_object_move(obj)))

    def handle_event(self, event):
        return self.event_fired.emit(event)

    def handle_object_move(self, obj):
        if obj.layer.parent != self.level:
            return

        obj_rects = obj.get_absolute_collision_rects()

        for obj_rect in obj_rects:
            if obj_rect.collidelist(self.rects) != -1:
                if obj not in self.entered_objects:
                    self.entered_objects.add(obj)
                    self.object_entered.emit(obj)

                self.object_moved.emit(obj)
            elif obj in self.entered_objects:
                self.entered_objects.remove(obj)
                self.object_exited.emit(obj)
