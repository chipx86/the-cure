import pygame

from thecure.effects import ScreenFadeEffect, ScreenFlashEffect
from thecure.levels.base import Level
from thecure.sprites import Direction, Wife, Sprite
from thecure.timer import Timer


class Cliff(Level):
    name = 'cliff'
    start_pos = (256, 1152)

    def setup(self):
        self.killed_wife = False
        self.allow_jump = False
        self.jumped = False

        self.engine.player.can_run = False
        self.engine.player.set_running(False)

        self.wife = Wife()
        self.wife.move_to(*self.eventboxes['infected-wife'].rects[0].topleft)
        self.main_layer.add(self.wife)
        self.wife.dead.connect(self._on_wife_dead)
        self.wife.transitioned.connect(self._on_wife_transitioned)

        self.add_monologue('finding-wife',
                           'This is where I told Laura to meet me. She must '
                           'be here somewhere.')

        self.add_monologue('found-wife', [
            'Laura! NO! No no no, God no.. My wife...',
            "What is she doing? Is she going to kill me?! What do I do?!!",
        ])

    def _on_wife_transitioned(self):
        self.engine.player.allow_player_control = False
        self.engine.ui.show_dialogue(
            actors={
                'player': self.engine.player,
                'wife': self.wife,
            },
            lines=[
                ('wife', 'Honey, you look sick. Are you okay?'),
                ('player', "Laura, I.. I don't understand. You were infected!"),
                ('wife', "Infected? I'm fine, but I've been worrying about "
                         "you all day."),
                ('wife', ["When you left for work you were excited about\n"
                          "some new breakthrough in your cure for the cold."]),
                ('wife', ["Then you called, mumbling to meet me up here."]),
                ('player', "But the lab explosion. The mutation. "
                           "The hallucinations.."),
                ('wife', "You're burning up. I don't think you're remembering "
                         "things clearly."),
                ('player', "It must just be me. I must have the infection.\n"
                           "But I have what I need to cure it."),
            ],
            timeout_ms=5000,
            on_done=self._complete_cure)

    def _on_wife_dead(self):
        self.killed_wife = True

        Timer(ms=1000, cb=self._say_sorry, one_shot=True)

    def _say_sorry(self):
        self.engine.ui.show_monologue([
            "Laura, I'm so sorry. I'm so, so sorry.",
            "I'm a monster. I should just kill myself.",
            "...",
            ".. No, no I can't do that.",
            "Too many other people will suffer if I don't complete this cure."
        ], on_done=self._complete_cure)

    def _complete_cure(self, on_done=None):
        player = self.engine.player
        player.allow_player_control = False
        player.velocity = (0, 0)
        player.stop_running()
        player.set_direction(Direction.SOUTH)
        player.stop()

        ingredients = [
            'vials',
            'mushroom',
            'flower',
            'web',
            'sea-crystal',
        ]

        self._process_ingredient(ingredients, self._on_ingredients_processed)

    def _process_ingredient(self, ingredients, on_done):
        player = self.engine.player

        sprite = Sprite(ingredients[0])
        sprite.move_to(player.rect.left, player.rect.centery)
        self.layer_map['fg'].add(sprite)
        sprite.velocity = (0, 2)
        sprite.collidable = False
        sprite.moved.connect(
            lambda dx, dy: self._on_ingredient_moved(sprite, ingredients[1:],
                                                     on_done))

        Timer(ms=500, one_shot=True, cb=sprite.start)

    def _on_ingredient_moved(self, sprite, ingredients, on_done):
        if sprite.rect.top >= self.engine.player.rect.bottom + 1:
            if sprite.name == 'vials':
                # Change the image to be the "curepot" (*sigh* curepot..)
                sprite.name = 'curepot'
                sprite.layer.remove(sprite)
                self.main_layer.add(sprite)
                sprite.velocity = (0, 0)
                sprite.stop()
            else:
                sprite.remove()

            if ingredients:
                self._process_ingredient(ingredients, on_done)
            else:
                Timer(ms=1500, cb=on_done, one_shot=True)

    def _on_ingredients_processed(self):
        self.engine.player.set_direction(Direction.NORTH)

        if self.killed_wife:
            s = "I'll test it on myself to make sure there aren't any side " \
                "effects..."
        else:
            s = 'Here goes nothing'

        self.engine.ui.show_monologue(s, on_done=self._use_cure)

    def _use_cure(self):
        timer = Timer(ms=1500, cb=self._after_flash, one_shot=True,
                      start_automatically=False)

        self.effect = ScreenFlashEffect(self.layer_map['fg2'],
                                        self.engine.camera.rect)
        self.effect.stopped.connect(timer.start)
        self.effect.start()

    def _after_flash(self):
        self.effect = None
        self.engine.player.set_direction(Direction.SOUTH)

        if self.killed_wife:
            lines = [
                'I...\n...',

                'I was infected. I remember now. It was only me.\n'
                'The infection was never even airborne.',
            ]

            lines += [
                'Oh God! I killed Laura! She was safe and fine and I '
                'KILLED her!',
                "I truly am a monster. There's nothing left to do but jump.",
            ]
        else:
            lines = "I can think clearly now. I remember everything.\n" \
                    "I've been hallucinating."

        self.engine.ui.show_monologue(lines, on_done=self._after_cure)

    def _after_cure(self):
        if self.killed_wife:
            self.engine.player.allow_player_control = True
            self.engine.player.start()
            self.allow_jump = True
            self.connect_eventbox_enter('jump-off-cliff',
                                        self._begin_jump_off_cliff, True)
        else:
            Timer(ms=5000, cb=self._finale, one_shot=True)

    def _begin_jump_off_cliff(self):
        player = self.engine.player
        self.engine.ui.show_monologue(
            'If only I had made different choices...')
        player.allow_player_control = False
        player.velocity = (0, 0)
        player.set_direction(Direction.EAST)
        player.update_velocity()
        player.moved.connect(lambda dx, dy: self._on_player_move())
        self.pending_jump = False

    def _on_player_move(self):
        player = self.engine.player
        jump_spot = self.eventboxes['jump-spot'].rects[0]

        if self.jumped and player.rect.y >= self.size[1]:
            player.velocity = (0, 0)
            player.stop()
        elif not self.jumped and player.rect.x == jump_spot.x:
            self.main_layer.remove(player)
            self.layer_map['fg'].add(player)
            player.fall()
            self.jumped = True
            Timer(ms=5000, cb=self._finale, one_shot=True)
        elif not self.pending_jump and player.rect.right >= jump_spot.x:
            player.stop_moving()
            self.pending_jump = True
            Timer(700, player.update_velocity, one_shot=True)

    def _finale(self):
        self.effect = ScreenFadeEffect(self.layer_map['fg2'],
                                       self.engine.camera.rect)
        self.effect.start()

        player = self.engine.player
        player.stop_moving()

        kill_count = player.human_kill_count

        if self.killed_wife:
            kill_count -= 1

            if kill_count == 1:
                s = ['Your wife is dead, by your own hand. And by the way, you',
                     'killed one other harmless victim. You monster.']
            elif kill_count > 1:
                s = ['Your wife is dead, by your own hand. And by the way, you',
                     'killed %s other harmless victims. You monster.' % \
                     kill_count]
            else:
                s = ['Your wife is dead, by your own hand. You monster.']

            s += ['Maybe you should have done things differently.']
        else:
            if kill_count == 0:
                s = ["Your wife is safe, the town is safe, and you didn't "
                     "kill anybody. Good job!",
                     "Reality is only what you perceive it to be. How do you "
                     "know what's even real?",
                     "Kids, don't do drugs."]
            else:
                if kill_count == 1:
                    s = ['Your wife is safe, but in your infected state, you '
                         'killed an innocent person.']
                elif kill_count > 1:
                    s = ['Your wife is safe, but in your infected state, you '
                         'killed %s innocent people.' % kill_count]

                s += [
                     'You were later sentenced to prison for manslaughter. '
                     'Shortly after, your wife left you.',
                     'If only you had made different choices.',
                ]

        widget = self.engine.ui.show_textbox(s)
        widget.closed.connect(self.engine._setup_game)
