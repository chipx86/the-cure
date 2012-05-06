import pygame
from pygame.locals import *


from thecure.engine import TheCureEngine


def main():
    pygame.init()

    version = pygame.__version__.split('.')

    if int(version[0]) <= 1 and int(version[1]) < 9:
        print 'This game requires pygame 1.9 or higher.'
        return

    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption('The Cure')

    engine = TheCureEngine(screen)
    engine.run()

    pygame.quit()
