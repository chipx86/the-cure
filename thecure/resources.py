import os
import sys

import pygame


DATA_PY = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.normpath(os.path.join(DATA_PY, '..', 'data'))

# Try to find it in the exe.
if not os.path.exists(DATA_DIR):
    DATA_DIR = os.path.normpath(os.path.join(DATA_PY, '..', '..', 'data'))

image_cache = {}
frame_cache = {}


def get_cached_image(name, create_func):
    assert name

    if name not in image_cache:
        image_cache[name] = create_func().convert_alpha()

    return image_cache[name]


def load_image(name):
    def _load_image_file():
        if not name.endswith('.png') and not name.endswith('.jpg'):
            filename = name + '.png'
        else:
            filename = name

        path = os.path.join(DATA_DIR, 'images', *filename.split('/'))

        try:
            return pygame.image.load(path)
        except pygame.error, e:
            print 'Unable to load image %s: %s' % (path, e)
            sys.exit(1)

    return get_cached_image(name, _load_image_file)


def load_spritesheet_frame(name, pos, size):
    spritesheet = load_image('sprites/' + name)

    rect = pygame.Rect(pos, size)
    key = repr(rect)

    if key not in frame_cache:
        frame = pygame.Surface(size).convert_alpha()
        frame.fill((0, 0, 0, 0))
        frame.blit(spritesheet, (0, 0), rect)
        frame_cache[key] = frame

    return frame_cache[key]


def get_font_filename():
    return os.path.join(DATA_DIR, 'fonts', 'DejaVuSans.ttf')
