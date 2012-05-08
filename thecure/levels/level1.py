import pygame

from thecure.eventbox import EventBox
from thecure.levels.base import Level
from thecure.sprites import Direction, InfectedHuman


class Level1(Level):
    name = 'level1'
    start_pos = (900, 6200)

    def setup(self):
        boy = InfectedHuman('boy1')
        self.main_layer.add(boy)
        boy.move_to(1536, 5696)
        boy.set_direction(Direction.DOWN)

        girl = InfectedHuman('girl1')
        self.main_layer.add(girl)
        girl.move_to(1536, 5824)
        girl.set_direction(Direction.UP)

        girl = InfectedHuman('girl1')
        self.main_layer.add(girl)
        girl.move_to(1280, 4800)
        girl.set_direction(Direction.DOWN)

        girl = InfectedHuman('girl1')
        self.main_layer.add(girl)
        girl.move_to(1216, 4608)
        girl.set_direction(Direction.RIGHT)

        girl = InfectedHuman('girl1')
        self.main_layer.add(girl)
        girl.move_to(1152, 3904)
        girl.set_direction(Direction.RIGHT)

        girl = InfectedHuman('girl1')
        self.main_layer.add(girl)
        girl.move_to(1216, 3136)
        girl.set_direction(Direction.RIGHT)

        girl = InfectedHuman('girl1')
        self.main_layer.add(girl)
        girl.move_to(512, 2240)
        girl.set_direction(Direction.DOWN)

        girl = InfectedHuman('girl1')
        self.main_layer.add(girl)
        girl.move_to(1408, 2048)
        girl.set_direction(Direction.DOWN)

        girl = InfectedHuman('girl1')
        self.main_layer.add(girl)
        girl.move_to(1280, 1152)
        girl.set_direction(Direction.DOWN)

        girl = InfectedHuman('girl1')
        self.main_layer.add(girl)
        girl.move_to(384, 384)
        girl.set_direction(Direction.RIGHT)

        girl = InfectedHuman('girl1')
        self.main_layer.add(girl)
        girl.move_to(448, 576)
        girl.set_direction(Direction.UP)

        girl = InfectedHuman('girl1')
        self.main_layer.add(girl)
        girl.move_to(960, 128)
        girl.set_direction(Direction.DOWN)

        girl = InfectedHuman('girl1')
        self.main_layer.add(girl)
        girl.move_to(832, 128)
        girl.set_direction(Direction.DOWN)

        girl = InfectedHuman('girl1')
        self.main_layer.add(girl)
        girl.move_to(896, 192)
        girl.set_direction(Direction.DOWN)

        girl = InfectedHuman('girl1')
        self.main_layer.add(girl)
        girl.move_to(1600, 576)
        girl.set_direction(Direction.DOWN)

        girl = InfectedHuman('girl1')
        self.main_layer.add(girl)
        girl.move_to(320, 1344)
        girl.set_direction(Direction.RIGHT)

        girl = InfectedHuman('girl1')
        self.main_layer.add(girl)
        girl.move_to(1152, 2624)
        girl.set_direction(Direction.UP)

        girl = InfectedHuman('girl1')
        self.main_layer.add(girl)
        girl.move_to(512, 4672)
        girl.set_direction(Direction.RIGHT)

        self.add_monologue('back-to-lab',
            'I wish I could just go back to the safety of my lab, but...')

        self.add_monologue('kids',
            'Even the kids are infected. What have I done...')

        self.add_monologue('gone-to-hell',
            "It's all gone to hell. All of it. This town is done for. It's "
            "all my fault.")

        self.add_monologue('looking-for-vials',
            'The vials I ordered should be in this shipment somewhere.')

        self.add_monologue('vials',
            'Found the vials. Time to leave town.')

        self.add_monologue('my-house',
            'They set us up with a nice house. My wife spent months picking '
            'out just the right furniture and plants. I hope she\'s safe.',
            5000)

        self.add_monologue('why-not-zombies',
            'I\'ve always wondered why the movies never use the word "zombie."')

        self.add_monologue('horde',
            'Oh god. Now that\s a zombie horde...')
