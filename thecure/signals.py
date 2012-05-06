class SignalConnection(object):
    def __init__(self, signal, cb):
        self.signal = signal
        self.cb = cb

    def disconnect(self):
        try:
            self.signal.callbacks.remove(self.cb)
        except ValueError:
            pass


class Signal(object):
    def __init__(self):
        self.callbacks = []

    def connect(self, callback):
        self.callbacks.append(callback)
        return SignalConnection(self, callback)

    def clear(self):
        self.callbacks = []

    def emit(self, *args, **kwargs):
        result = False

        for callback in self.callbacks:
            result = callback(*args, **kwargs) or result

        return result
