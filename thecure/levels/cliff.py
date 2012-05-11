from thecure.levels.base import Level
from thecure.sprites import Direction, InfectedWife, Sprite
from thecure.timer import Timer


class Cliff(Level):
    name = 'cliff'
    start_pos = (256, 1152)

    def setup(self):
        self.killed_wife = False
        self.allow_jump = False
        self.jumped = False

        self.engine.player.can_run = False

        self.wife = InfectedWife()
        self.wife.move_to(*self.eventboxes['infected-wife'].rects[0].topleft)
        self.main_layer.add(self.wife)
        self.wife.dead.connect(self._on_wife_dead)

        self.add_monologue('finding-wife',
                           'This is where I told Laura to meet me. She must '
                           'be here somewhere.')

        self.add_monologue('found-wife', [
            'NO! No no no, God no.. My wife...',
            "What is she doing? Is she going to kill me?! What do I do?!!",
        ])

    def _on_wife_dead(self):
        self.killed_wife = True

        self.engine.ui_manager.show_monologue([
            "Laura, I'm so sorry. I'm so, so sorry.",
            "I'm a monster. I should just kill myself.",
            "...",
            ".. No, no I can't do that.",
            "Too many other people will suffer if I don't complete this cure."
        ], on_done=self._complete_cure)

    def _complete_cure(self):
        player = self.engine.player
        player.allow_player_control = False
        player.velocity = (0, 0)
        player.stop_running()
        player.set_direction(Direction.DOWN)
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
        self.engine.player.set_direction(Direction.UP)
        self.engine.ui_manager.show_monologue(
            "I'll test it on myself to make sure there aren't any side "
            "effects...",
            on_done=self._use_cure)

    def _use_cure(self):
        # TODO: Some sort of visual effect.
        self.engine.player.set_direction(Direction.DOWN)
        lines = [
            'I...\n...',

            'I was infected. I remember now. It was only me.\n'
            'The infection was never even airborne.',
        ]

        if self.killed_wife:
            lines += [
                'Oh God! I killed Laura! She was safe and fine and I '
                'KILLED her!',
                "I truly am a monster. There's nothing left to do but jump.",
            ]

        self.engine.ui_manager.show_monologue(lines, on_done=self._after_cure)

    def _after_cure(self):
        self.engine.player.allow_player_control = True
        self.engine.player.start()
        self.allow_jump = True
        self.connect_eventbox_enter('jump-off-cliff',
                                    self._begin_jump_off_cliff, True)

    def _begin_jump_off_cliff(self):
        player = self.engine.player
        self.engine.ui_manager.show_monologue(
            'If only I had made different choices...')
        player.allow_player_control = False
        player.velocity = (0, 0)
        player.set_direction(Direction.RIGHT)
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
            Timer(ms=5000, cb=self._on_splat, one_shot=True)
        elif not self.pending_jump and player.rect.right >= jump_spot.x:
            player.stop_moving()
            self.pending_jump = True
            Timer(700, player.update_velocity, one_shot=True)

    def _on_splat(self):
        player = self.engine.player
        player.stop_moving()

        kill_count = player.human_kill_count - 1

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

        widget = self.engine.ui_manager.show_textbox(s)
        widget.closed.connect(self.engine._setup_game)
