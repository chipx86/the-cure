import pygame


class SpriteQuadTree(object):
    def __init__(self, rect, depth=6, parent=None):
        depth -= 1

        self.rect = rect
        self.sprites = []
        self.parent = parent
        self.depth = depth
        self.cx = self.rect.centerx
        self.cy = self.rect.centery
        self._moved_cnxs = {}
        self._next_stamp = 1

        if depth == 0:
            self.nw_tree = None
            self.ne_tree = None
            self.sw_tree = None
            self.se_tree = None
        else:
            quad_size = (rect.width / 2, rect.height / 2)

            self.nw_tree = SpriteQuadTree(
                pygame.Rect(rect.x, rect.y, *quad_size),
                depth, self)
            self.ne_tree = SpriteQuadTree(
                pygame.Rect(self.cx, rect.y, *quad_size),
                depth, self)
            self.sw_tree = SpriteQuadTree(
                pygame.Rect(rect.x, self.cy, *quad_size),
                depth, self)
            self.se_tree = SpriteQuadTree(
                pygame.Rect(self.cx, self.cy, *quad_size),
                depth, self)

    def add(self, sprite):
        if not self.parent and sprite.can_move:
            self._moved_cnxs[sprite] = sprite.moved.connect(
                lambda dx, dy: self._recompute_sprite(sprite))

        # If this is a leaf node or the sprite is overlapping all quadrants,
        # store it in this QuadTree's list of sprites. If it's in fewer
        # quadrants, go through and add to each that it touches.
        if self.depth == 0:
            trees = list(self._get_trees(sprite.rect))
            assert len(trees) > 0

            if len(trees) < 4:
                for tree in trees:
                    tree.add(sprite)

                return

        assert sprite not in self.sprites
        self.sprites.append(sprite)
        sprite.quad_trees.add(self)

    def remove(self, sprite):
        if self.parent:
            self.parent.remove(sprite)
            return

        assert sprite.quad_trees

        for tree in sprite.quad_trees:
            tree.sprites.remove(sprite)

        sprite.quad_trees.clear()

        if sprite.can_move:
            cnx = self._moved_cnxs.pop(sprite)
            cnx.disconnect()

    def get_sprites(self, rect=None, stamp=None):
        if stamp is None:
            stamp = self._next_stamp
            self._next_stamp += 1

        for sprite in self.sprites:
            if (getattr(sprite, '_quadtree_stamp', None) != stamp and
                (rect is None or rect.colliderect(sprite.rect))):
                sprite._quadtree_stamp = stamp
                yield sprite

        for tree in self._get_trees(rect):
            for sprite in tree.get_sprites(rect, stamp):
                yield sprite

    def __iter__(self):
        return self.get_sprites()

    def _get_trees(self, rect):
        if self.depth > 0:
            if not rect or (rect.left <= self.cx and rect.top <= self.cy):
                yield self.nw_tree

            if not rect or (rect.right >= self.cx and rect.top <= self.cy):
                yield self.ne_tree

            if not rect or (rect.left <= self.cx and rect.bottom >= self.cy):
                yield self.sw_tree

            if not rect or (rect.right >= self.cx and rect.bottom >= self.cy):
                yield self.se_tree

    def _get_leaf_trees(self, rect):
        trees = list(self._get_trees(rect))

        if not trees or len(trees) == 4:
            yield self
        else:
            for tree in trees:
                for leaf in tree._get_leaf_trees(rect):
                    yield leaf

    def _recompute_sprite(self, sprite):
        assert sprite.quad_trees

        if sprite.quad_trees != set(self._get_leaf_trees(sprite.rect)):
            self.remove(sprite)
            self.add(sprite)


class Layer(object):
    def __init__(self, name, index, parent):
        self.name = name
        self.index = index
        self.parent = parent
        self.quad_tree = SpriteQuadTree(pygame.Rect(0, 0, *self.parent.size))
        self.tick_sprites = []

    def add(self, *objs):
        for obj in objs:
            obj.layer = self
            self.update_sprite(obj)

            if obj.use_quadtrees:
                self.quad_tree.add(obj)

            obj.on_added(self)

    def remove(self, *objs):
        for obj in objs:
            self.update_sprite(obj, True)

            if obj.use_quadtrees:
                self.quad_tree.remove(obj)

            obj.on_removed(self)

    def update_sprite(self, sprite, force_remove=False):
        assert sprite.layer == self

        sprite.update_image()

        if sprite.NEED_TICKS:
            if sprite.visible and not force_remove:
                self.tick_sprites.append(sprite)
            else:
                try:
                    self.tick_sprites.remove(sprite)
                except ValueError:
                    # It may be gone now.
                    pass

    def __iter__(self):
        return iter(self.quad_tree)

    def iterate_in_rect(self, rect):
        return self.quad_tree.get_sprites(rect)

    def tick(self):
        for sprite in self.tick_sprites:
            sprite.tick()

    def start(self):
        for sprite in self.quad_tree:
            sprite.start()

    def stop(self):
        for sprite in self.quad_tree:
            sprite.stop()
