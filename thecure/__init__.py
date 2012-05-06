_engine = None


def set_engine(engine):
    global _engine
    _engine = engine


def get_engine():
    return _engine
