import pygame

from thecure.eventbox import EventBox
from thecure.levels.base import Level
from thecure.sprites import Direction, InfectedHuman, Sprite


class Level2(Level):
    name = 'level2'
    start_pos = (960, 140)
    #start_pos = (280, 400)
    #start_pos = (2144, 2456)

    def setup(self):
        self.got_mushroom = False

        self.mushroom = Sprite('mushroom')
        self.layer_map['bg2'].add(self.mushroom)
        self.mushroom.move_to(*self.eventboxes['mushroom'].rects[0].topleft)

        self.eventboxes['mushroom'].object_entered.connect(
            self._on_mushroom_entered)

        self.eventboxes['exit'].object_entered.connect(
            self._on_exit_entered)

        girl = InfectedHuman('girl1')
        self.main_layer.add(girl)
        girl.move_to(192, 2048)
        girl.set_direction(Direction.DOWN)

        girl = InfectedHuman('girl1')
        self.main_layer.add(girl)
        girl.move_to(448, 2048)
        girl.set_direction(Direction.LEFT)

        girl = InfectedHuman('girl1')
        self.main_layer.add(girl)
        girl.move_to(2880, 2240)
        girl.set_direction(Direction.LEFT)

        girl = InfectedHuman('girl1')
        self.main_layer.add(girl)
        girl.move_to(2688, 2304)
        girl.set_direction(Direction.UP)

        girl = InfectedHuman('girl1')
        self.main_layer.add(girl)
        girl.move_to(2880, 1408)
        girl.set_direction(Direction.UP)

        girl = InfectedHuman('girl1')
        self.main_layer.add(girl)
        girl.move_to(2880, 256)
        girl.set_direction(Direction.DOWN)

        girl = InfectedHuman('girl1')
        self.main_layer.add(girl)
        girl.move_to(832, 1216)
        girl.set_direction(Direction.UP)

        girl = InfectedHuman('girl1')
        self.main_layer.add(girl)
        girl.move_to(320, 768)
        girl.set_direction(Direction.RIGHT)

        girl = InfectedHuman('girl1')
        self.main_layer.add(girl)
        girl.move_to(1280, 1216)
        girl.set_direction(Direction.UP)

        girl = InfectedHuman('girl1')
        self.main_layer.add(girl)
        girl.move_to(320, 64)
        girl.set_direction(Direction.DOWN)

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

    def _on_mushroom_entered(self, obj):
        if obj == self.engine.player:
            self.got_mushroom = True
            self.mushroom.remove()
            self.engine.ui_manager.show_monologue(
                'Got the mushroom. I should be able to finish this cure now.')

            self.eventboxes['mushroom'].disconnect()
            del self.eventboxes['mushroom']

    def _on_exit_entered(self, obj):
        if obj == self.engine.player:
            if not self.got_mushroom:
                self.engine.ui_manager.show_monologue(
                    'I still need to find that mushroom.')
                obj.set_direction(Direction.DOWN)
                obj.velocity = (0, 0)
                obj.move_by(0, 4)
                obj.set_running(False)
