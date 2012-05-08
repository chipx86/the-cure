import pygame

from thecure.eventbox import EventBox
from thecure.levels.base import Level
from thecure.sprites import Direction, InfectedHuman, Sprite


class Level2(Level):
    name = 'level2'
    start_pos = (2144, 2456)

    infected_humans = [
        ('girl1', (192, 2048), Direction.DOWN),
        ('girl1', (448, 2048), Direction.LEFT),
        ('girl1', (2880, 2240), Direction.LEFT),
        ('girl1', (2688, 2304), Direction.UP),
        ('girl1', (2880, 1408), Direction.UP),
        ('girl1', (2880, 256), Direction.DOWN),
        ('girl1', (832, 1216), Direction.UP),
        ('girl1', (320, 768), Direction.RIGHT),
        ('girl1', (1280, 1216), Direction.UP),
        ('girl1', (320, 64), Direction.DOWN),
    ]

    def setup(self):
        self.got_mushroom = False

        self.mushroom = Sprite('mushroom')
        self.layer_map['bg2'].add(self.mushroom)
        self.mushroom.move_to(*self.eventboxes['mushroom'].rects[0].topleft)

        self.eventboxes['mushroom'].object_entered.connect(
            self._on_mushroom_entered)

        self.eventboxes['exit'].object_entered.connect(self._on_exit_entered)

        self.add_monologue('find-mushroom',
                           'This forest has a special kind of mushroom '
                           'that could help with a cure, if I can find it.')

        self.add_monologue('campsite',
                           'A campsite? So close to town? Should have gone '
                           'further, guys.')

        self.add_monologue('turned-around',
                           "I think I'm starting to get turned around "
                           "out here.")

        self.add_monologue('people-everywhere',
                           "Geeze, people everywhere. Must have "
                           "ran panicking into the woods.")

        self.add_monologue('see-mushroom',
                           "Oh! I see the mushroom!")

        for sprite_name, pos, direction in self.infected_humans:
            human = InfectedHuman(sprite_name)
            self.main_layer.add(human)
            human.move_to(*pos)
            human.set_direction(direction)

    def _on_mushroom_entered(self, obj):
        self.got_mushroom = True
        self.mushroom.remove()
        self.engine.ui_manager.show_monologue(
            'Got the mushroom. I should be able to finish this cure now.')

        self.eventboxes['mushroom'].disconnect()
        del self.eventboxes['mushroom']

    def _on_exit_entered(self, obj):
        if not self.got_mushroom:
            self.engine.ui_manager.show_monologue(
                'I still need to find that mushroom.')
            obj.set_direction(Direction.DOWN)
            obj.velocity = (0, 0)
            obj.move_by(0, 4)
            obj.set_running(False)
