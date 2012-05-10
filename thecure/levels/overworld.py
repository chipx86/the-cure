import pygame

from thecure.eventbox import EventBox
from thecure.levels.base import Level
from thecure.sprites import Direction, InfectedHuman, Sprite, LostBoy


class Overworld(Level):
    name = 'overworld'
    start_pos = (3968, 6400)

    def setup(self):
        self.has_items = {}

        self.add_item('vials',
                      'Found the equipment I need. Time to leave town and '
                      'get the rest.')
        self.add_item('mushroom',
                      'This looks like the right kind of mushroom. Lucky '
                      'nothing ate it...')
        self.add_item('sea-crystal',
                      'Shiny... I must be careful not to drop this.')
        self.add_item('web',
                      'This thing is gigantic. I\'m not sticking around to '
                      'see what made this.')
        self.add_item('flower',
                      'These aren\'t usually in bloom this time of year.\n'
                      'Another month and we\'d be screwed.')
        #self.add_item('sulfur',
        #              'Hot hot hot! I better scoop this up carefully.')

        # Town
        self.add_monologue('exit-lab',
                           '*cough* *cough* I can\'t believe I made it out '
                           'of there alive!')

        # Forest
        self.add_monologue('find-flower',
                           'This forest has a special kind of flower '
                           'that could help, if I can find it.')
        self.add_monologue('campsite',
                           'A campsite? So close to town? That\'s hardly '
                           'camping, guys.')
        self.add_monologue('turned-around',
                           "I think I'm starting to get turned around "
                           "out here.")
        self.add_monologue('see-flower',
                           "Oh! I see the flower!")
        self.add_monologue('people-everywhere',
                           "Geeze, people everywhere. Must have "
                           "ran panicking into the woods.")

        # Grove
        self.lost_boy = LostBoy()
        self.lost_boy.move_to(*self.eventboxes['lostboy'].rects[0].topleft)
        self.layer_map['fg'].add(self.lost_boy)

        self.connect_eventbox_enter('lostboy-fadeout', self._on_lostboy_enter)

    def add_item(self, name, text):
        self.has_items[name] = False

        item = Sprite(name)
        item.move_to(*self.eventboxes[name].rects[0].topleft)
        self.layer_map['bg2'].add(item)

        self.connect_eventbox_enter(
            name,
            lambda: self._on_item_entered(name, text, item),
            True)

    def _on_item_entered(self, name, text, item):
        self.engine.ui_manager.show_monologue(text)
        self.has_items[name] = True
        item.remove()

    def _on_lostboy_enter(self):
        self.lost_boy.fadeout()
