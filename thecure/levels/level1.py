import pygame

from thecure.eventbox import EventBox
from thecure.levels.base import Level
from thecure.sprites import Direction, InfectedHuman


class Level1(Level):
    name = 'level1'
    start_pos = (900, 6200)

    infected_humans = [
        ('boy1', (1536, 5696), Direction.DOWN),
        ('girl1', (1536, 5824), Direction.UP),
        ('girl1', (1280, 4800), Direction.DOWN),
        ('boy1', (1216, 4608), Direction.RIGHT),
        ('boy1', (1152, 3904), Direction.LEFT),
        ('girl1', (1216, 3136), Direction.DOWN),
        ('girl1', (512, 2240), Direction.DOWN),
        ('boy1', (1408, 2048), Direction.DOWN),
        ('girl1', (1280, 1152), Direction.LEFT),
        ('girl1', (384, 384), Direction.RIGHT),
        ('boy1', (448, 576), Direction.UP),
        ('girl1', (960, 128), Direction.LEFT),
        ('girl1', (832, 128), Direction.DOWN),
        ('boy1', (896, 192), Direction.DOWN),
        ('boy1', (1600, 576), Direction.DOWN),
        ('girl1', (320, 1344), Direction.DOWN),
        ('girl1', (1152, 2624), Direction.DOWN),
        ('girl1', (512, 4672), Direction.RIGHT),
    ]

    def setup(self):
        self.has_vials = False

        self.eventboxes['vials'].object_entered.connect(self._on_vials_entered)
        self.eventboxes['exit-level'].object_entered.connect(
            self._on_exit_entered)

        self.add_monologue('back-to-lab',
            'I wish I could just go back to the safety of my lab, but...')

        self.add_monologue('kids',
            'Even the kids are infected. What have I done...')

        self.add_monologue('gone-to-hell',
            "It's all gone to hell. All of it. This town is done for. It's "
            "all my fault.")

        self.add_monologue('looking-for-vials',
            'The vials I ordered should be in this shipment somewhere.')

        self.add_monologue('my-house',
            'They set us up with a nice house. My wife spent months picking '
            'out just the right furniture and plants. I hope she\'s safe.',
            5000)

        self.add_monologue('why-not-zombies',
            'I\'ve always wondered why the movies never use the word "zombie."')

        self.add_monologue('horde',
            'Oh god. Now that\s a zombie horde...')

        for sprite_name, pos, direction in self.infected_humans:
            human = InfectedHuman(sprite_name)
            self.main_layer.add(human)
            human.move_to(*pos)
            human.set_direction(direction)

    def _on_vials_entered(self, obj):
        self.engine.ui_manager.show_monologue(
            'Found the vials. Time to leave town.')
        self.has_vials = True
        self.eventboxes['vials'].disconnect()
        del self.eventboxes['vials']

    def _on_exit_entered(self, obj):
        if not self.has_vials:
            self.engine.ui_manager.show_monologue(
                "I can't leave until I find my shipment of vials.")
            obj.set_direction(Direction.DOWN)
            obj.velocity = (0, 0)
            obj.move_by(0, 4)
            obj.set_running(False)
