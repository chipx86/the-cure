import random

import pygame

from thecure.levels.base import Level
from thecure.sprites import Direction, InfectedHuman, Sprite, LostBoy, Snake, \
                            Slime, Tile
from thecure.timer import Timer


class Overworld(Level):
    name = 'overworld'
    start_pos = (3968, 6400)

    MOB_SPAWN_REGIONS = [
        # Forest
        {
            'rect': pygame.Rect(0, 0, 48, 38),
            'mobs': [Slime, Snake],
            'min': 10,
            'max': 15,
        },
        # Grove area
        {
            'rect': pygame.Rect(7, 42, 46, 33),
            'mobs': [Slime],
            'min': 10,
            'max': 20,
        },
        # Behind lab
        {
            'rect': pygame.Rect(15, 75, 24, 30),
            'mobs': [Slime],
            'min': 10,
            'max': 20,
        },
        # Swamp
        {
            'rect': pygame.Rect(0, 113, 57, 43),
            'mobs': [Snake],
            'min': 20,
            'max': 30,
        },
        # Dirt area near ocean
        {
            'rect': pygame.Rect(92, 104, 36, 40),
            'mobs': [Slime],
            'min': 15,
            'max': 30,
        },
        # Desert
        {
            'rect': pygame.Rect(126, 98, 23, 29),
            'mobs': [Snake],
            'min': 10,
            'max': 20,
        },
        # South-East of mountain
        {
            'rect': pygame.Rect(124, 38, 25, 45),
            'mobs': [Slime],
            'min': 10,
            'max': 20,
        },
        # South of mountain
        {
            'rect': pygame.Rect(70, 43, 47, 19),
            'mobs': [Slime],
            'min': 20,
            'max': 30,
        },
        # Mountain
        {
            'rect': pygame.Rect(69, 2, 62, 32),
            'mobs': [Slime], # XXX
            'min': 20,
            'max': 30,
        },
    ]

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

        self.connect_eventbox_enter('lostboy-fadeout', self._on_lostboy_enter,
                                    only_once=True)

        # Mountain
        self.connect_eventbox_enter('to-cliff', self._on_to_cliff)

        # Spawn the mobs
        for region in self.MOB_SPAWN_REGIONS:
            mob_count = random.randint(region['min'], region['max'])
            rect = region['rect']
            mob_classes = region['mobs']

            for i in xrange(mob_count):
                while 1:
                    x = random.randint(rect.left, rect.right)
                    y = random.randint(rect.top, rect.bottom)

                    if self._allowed_spawn_bitmap[y][x]:
                        break

                mob_cls = random.choice(mob_classes)
                mob = mob_cls()
                mob.direction = Direction.random()
                mob.update_image()
                mob.move_to(x * Tile.WIDTH, y * Tile.HEIGHT)
                self.main_layer.add(mob)
                self._allowed_spawn_bitmap[y][x] = 0

    def add_item(self, name, text):
        self.has_items[name] = False

        item = Sprite(name)
        item.move_to(*self.eventboxes[name].rects[0].topleft)
        self.layer_map['items'].add(item)

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
        self.lost_boy.dead.connect(self._on_lostboy_gone)

    def _on_lostboy_gone(self):
        Timer(ms=1000, one_shot=True, cb=lambda:
            self.engine.ui_manager.show_monologue(
                ['That was weird.',
                 'I swear I heard music playing.']))

    def _on_to_cliff(self):
        player = self.engine.player

        if all(self.has_items.values()):
            player.allow_player_control = False
            player.velocity = (0, player.velocity[1])
            player.set_direction(Direction.UP)
            Timer(ms=1000, one_shot=True,
                  cb=lambda: self.engine.switch_level(1))
        else:
            self.engine.ui_manager.show_monologue(
                "I'm still missing some of the ingredients.")

            player.set_direction(Direction.DOWN)
            player.stop_moving()
            player.move_by(0, 10)
