import os
import sys

try:
    import pygtk
    pygtk.require('2.0')
    import gtk

    gtk.init_check()
except:
    sys.stderr.write('PyGTK 2.0 is needed for the level editor.\n')
    sys.exit(1)

import pango
import pygame

from thecure.levels import get_levels
from thecure.levels.loader import LevelLoader
from thecure.levels.writer import LevelWriter
from thecure.resources import get_image_filename, get_tilesets_path
from thecure.sprites import Tile


# XXX Hard-coding these is fragile.
LAYERS = ['bg', 'bg2', 'main', 'fg', 'fg2', 'events']
LAYER_NAMES = [
    'Background Layer',
    'Background Detail Layer',
    'Main Layer',
    'Foreground Layer',
    'Foreground Detail Layer',
    'Events',
]
DEFAULT_LAYER = LAYERS.index('main')

# We can't reuse the cache in resources, since we need GdkPixbufs.
_tilesheet_cache = {}
_tile_cache = {}


def _load_tilesheet(name, zoom_level=1.0):
    key = '%s-%s' % (name, zoom_level)

    if key not in _tilesheet_cache:
        pixbuf = gtk.gdk.pixbuf_new_from_file(
            get_image_filename('sprites/tiles/' + name))

        if zoom_level != 1.0:
            pixbuf = pixbuf.scale_simple(int(pixbuf.get_width() * zoom_level),
                                         int(pixbuf.get_height() * zoom_level),
                                         gtk.gdk.INTERP_HYPER)

        _tilesheet_cache[key] = pixbuf

    return _tilesheet_cache[key]


def _load_tile(name, x, y, zoom_level=1.0):
    key = '%s-%s-%s-%s' % (name, x, y, zoom_level)

    if key not in _tile_cache:
        pixbuf = _load_tilesheet(name, zoom_level)

        width = int(Tile.WIDTH * zoom_level)
        height = int(Tile.HEIGHT * zoom_level)

        _tile_cache[key] = pixbuf.subpixbuf(int(x * width),
                                            int(y * height),
                                            width,
                                            height)

    return _tile_cache[key]


class LevelGrid(gtk.DrawingArea):
    PLACE_TILE_ACTION = 'place-tile'
    ADD_EVENTBOX_ACTION = 'add-eventbox'
    REMOVE_EVENTBOX_ACTION = 'remove-eventbox'

    def __init__(self, editor, tile_list):
        super(LevelGrid, self).__init__()

        self.editor = editor
        self.tile_list = tile_list

        self.add_events(gtk.gdk.POINTER_MOTION_MASK |
                        gtk.gdk.BUTTON_PRESS_MASK |
                        gtk.gdk.BUTTON_RELEASE_MASK)

        self.gc = None
        self.image = None
        self.cursor_area = None
        self.current_layer = None
        self.loaded = False
        self.drawing = False
        self.tiles = {}
        self.show_active_layer_only = False
        self.width = 0
        self.height = 0
        self.undo_list = []
        self.redo_list = []
        self.undo_record_count = 0
        self.recorded_undos = []
        self.action = None
        self.eventboxes = []

        self.zoom_level = 0.5
        self.tile_width = int(Tile.WIDTH * self.zoom_level)
        self.tile_height = int(Tile.HEIGHT * self.zoom_level)

        self.connect('expose-event', self._on_expose_event)
        self.connect('button-press-event', self._on_button_press)
        self.connect('button-release-event', self._on_button_release)
        self.connect('motion-notify-event', self._on_motion_notify)

    def load(self, loader):
        self.realize()

        style = self.get_style()
        self.loader = loader
        self.gc = style.fg_gc[gtk.STATE_NORMAL]
        self.bg_gc = self.style.bg_gc[gtk.STATE_NORMAL]
        self.cursor_gc = self.style.bg_gc[gtk.STATE_SELECTED]
        self.eventbox_gc = self.style.bg_gc[gtk.STATE_SELECTED]
        self.current_layer = len(LAYERS) - 1
        self.width = loader.get_width()
        self.height = loader.get_height()
        self.eventboxes = []

        self.undo_list = []

        for layer_name in LAYERS:
            self.tiles[layer_name] = [
                [None] * self.width
                for i in range(self.height)
            ]

            for tile_data in self.loader.iter_tiles(layer_name):
                row = tile_data['row']
                col = tile_data['col']

                self.tiles[layer_name][row][col] = {
                    'filename': tile_data['tile_file'],
                    'tile_x': tile_data['tile_x'],
                    'tile_y': tile_data['tile_y'],
                }

        for name, eventbox_data in self.loader.iter_eventboxes():
            rect = eventbox_data['rect']

            self.eventboxes.append({
                'name': name,
                'rect': pygame.Rect(rect),
            })

        self._recompute_size()
        self.loaded = True

    def write(self, writer):
        writer.write(
            [
                {
                    'name': layer_name,
                    'is_main': layer_name == 'main',
                    'tiles': self.tiles[layer_name]
                }
                for layer_name in LAYERS
            ],
            self.eventboxes,
            self.width,
            self.height)

    def set_zoom_level(self, zoom_level):
        self.zoom_level = zoom_level
        self.tile_width = int(Tile.WIDTH * self.zoom_level)
        self.tile_height = int(Tile.HEIGHT * self.zoom_level)
        self._recompute_size()

    def _recompute_size(self):
        self.set_size_request(self.width * self.tile_width,
                              self.height * self.tile_height)
        self._reload_layers()

    def set_width(self, width):
        if width == self.width:
            return

        for layer_name, rows in self.tiles.iteritems():
            for cols in rows:
                if self.width > width:
                    del cols[width:]
                elif self.width < width:
                    cols.extend([None] * (width - self.width))

        self.width = width
        self._recompute_size()

    def set_height(self, height):
        if height == self.height:
            return

        for layer_name, rows in self.tiles.iteritems():
            if self.height > height:
                del rows[height:]
            elif self.height < height:
                for i in range(self.height, height):
                    rows.append([None] * self.width)

        self.height = height
        self._recompute_size()

    def set_action(self, action):
        self.action = action

    def set_show_active_layer_only(self, show_only):
        self.show_active_layer_only = show_only
        self._reload_layers()

    def begin_record(self):
        if self.undo_record_count == 0:
            self.recorded_undos = []
            self.redo_list = []

        self.undo_record_count += 1

    def end_record(self):
        if self.undo_record_count > 0:
            self.undo_record_count -= 1

        if self.undo_record_count == 0:
            self.undo_list.append(self.recorded_undos)
            self.recorded_undos = []

    def record(self, x, y):
        self.recorded_undos.append({
            'x': x,
            'y': y,
            'layer': self.current_layer,
            'tile': self.tiles[LAYERS[self.current_layer]][y][x]
        })

    def undo(self):
        if self.undo_list:
            undos = self.undo_list.pop()
            self.redo_list.append(self._apply_undos_redos(undos))

    def redo(self):
        if self.redo_list:
            redos = self.redo_list.pop()
            self.undo_list.append(self._apply_undos_redos(redos))

    def _apply_undos_redos(self, items):
        revert_list = []

        for item in reversed(items):
            revert_list.append(item)
            self._place_tile(item['x'], item['y'], item['tile'],
                             item['layer'], record=False)

        return revert_list

    def _clear(self):
        width = self.width * self.tile_width
        height = self.height * self.tile_height

        self.image = gtk.gdk.Pixmap(self.window, width, height)
        self.image.draw_rectangle(self.bg_gc, True, 0, 0, width, height)

    def _load_layer(self, layer_name):
        for row, row_data in enumerate(self.tiles[layer_name]):
            for col, col_data in enumerate(row_data):
                if col_data is None:
                    continue

                tilesheet = _load_tilesheet(col_data['filename'],
                                            self.zoom_level)

                self.image.draw_pixbuf(self.gc,
                                       tilesheet,
                                       int(col_data['tile_x'] * self.tile_width),
                                       int(col_data['tile_y'] * self.tile_height),
                                       col * self.tile_width,
                                       row * self.tile_height,
                                       self.tile_width,
                                       self.tile_height)

    def set_current_layer(self, index):
        if index != self.current_layer:
            self.current_layer = index

            if self.loaded:
                self._reload_layers()

    def _reload_layers(self):
        self._clear()

        for i in range(self.current_layer + 1):
            if not self.show_active_layer_only or self.current_layer == i:
                self._load_layer(LAYERS[i])

        self.queue_draw()

    def _tiles_rect_to_pixels(self, rect):
        return pygame.Rect(rect.x * self.tile_width,
                           rect.y * self.tile_height,
                           rect.width * self.tile_width,
                           rect.height * self.tile_height)

    def _on_expose_event(self, level_grid, e):
        if self.image:
            self.window.draw_drawable(self.gc, self.image, e.area.x, e.area.y,
                                      e.area.x, e.area.y, e.area.width,
                                      e.area.height)

            if self.cursor_area:
                self.window.draw_rectangle(self.cursor_gc, False,
                                           *self.cursor_area)

            if self.current_layer >= LAYERS.index('events'):
                for eventbox in self.eventboxes:
                    rect = eventbox['rect']

                    if rect.width <= 0 or rect.height <= 0:
                        continue

                    pixels_rect = self._tiles_rect_to_pixels(rect)

                    self.window.draw_rectangle(self.eventbox_gc, True,
                                               *pixels_rect)
                    layout = self.create_pango_layout(eventbox['name'])
                    layout.set_width(pixels_rect.width * pango.SCALE)
                    layout.set_ellipsize(pango.ELLIPSIZE_END)
                    layout.set_alignment(pango.ALIGN_CENTER)

                    size = layout.get_pixel_size()
                    self.window.draw_layout(
                        self.gc,
                        pixels_rect.x,
                        pixels_rect.y + (pixels_rect.height - size[1]) / 2,
                        layout)

    def _place_tile_from_event(self, e):
        tile_area = self._get_tile_area(e)

        if not self._is_tile_area_valid(self.cursor_area):
            return

        self._place_tile(tile_area[0] / self.tile_width,
                         tile_area[1] / self.tile_height,
                         self.tile_list.selected_tile)

    def _redraw_tiles(self, x, y):
        tile_area = (x * self.tile_width, y * self.tile_height,
                     self.tile_width, self.tile_height)
        self.image.draw_rectangle(self.bg_gc, True, *tile_area)

        for layer_name in LAYERS:
            layer_tile = self.tiles[layer_name][y][x]

            if layer_tile:
                self._draw_tile(layer_tile, tile_area)

    def _draw_tile(self, tile, tile_area):
        pixbuf = _load_tile(tile['filename'],
                            tile['tile_x'],
                            tile['tile_y'],
                            self.zoom_level)
        self.image.draw_pixbuf(self.gc,
                               pixbuf,
                               0,
                               0,
                               *tile_area)

    def _place_tile(self, tile_x, tile_y, tile, layer=None, record=True):
        layer = layer or self.current_layer
        tiles = self.tiles[LAYERS[layer]]
        tile_area = (tile_x * self.tile_width, tile_y * self.tile_height,
                     self.tile_width, self.tile_height)

        if record:
            self.record(tile_x, tile_y)

        if tile:
            if tiles[tile_y][tile_x]:
                # Due to transparency, if the sprite on this layer changes,
                # we'll need to redraw what's below it.
                tiles[tile_y][tile_x] = None
                self._redraw_tiles(tile_x, tile_y)

            self._draw_tile(tile, tile_area)

            tiles[tile_y][tile_x] = tile
        else:
            self.image.draw_rectangle(self.bg_gc, True, *tile_area)
            tiles[tile_y][tile_x] = None

            if not self.show_active_layer_only:
                self._redraw_tiles(tile_x, tile_y)

        self.queue_draw_area(*tile_area)

    def _fill(self, e):
        def can_place_at(x, y):
            return (0 <= x < self.width and
                    0 <= y < self.height and
                    tiles[y][x] == start_tile)

        area = self._get_tile_area(e)

        if not self._is_tile_area_valid(area):
            return

        x = area[0] / self.tile_width
        y = area[1] / self.tile_height

        tiles = self.tiles[LAYERS[self.current_layer]]
        tile = self.tile_list.selected_tile
        start_tile = tiles[y][x]

        self.begin_record()

        queue = [(x, y)]

        for x, y in queue:
            if can_place_at(x, y):
                west = x
                east = x

                while can_place_at(west - 1, y):
                    west -= 1

                while can_place_at(east + 1, y):
                    east += 1

                for c in range(west, east + 1):
                    self._place_tile(c, y, tile)

                    for dy in (-1, 1):
                        new_y = y + dy

                        if can_place_at(c, new_y):
                            queue.append((c, new_y))

        self.end_record()

    def _on_button_press(self, w, e):
        if self.action == self.PLACE_TILE_ACTION:
            if e.state & gtk.gdk.SHIFT_MASK:
                self._fill(e)
            else:
                self.begin_record()
                self._place_tile_from_event(e)
                self.drawing = True
        elif self.action == self.ADD_EVENTBOX_ACTION:
            rect = pygame.Rect(self._get_tile_area(e, False))

            for eventbox in self.eventboxes:
                if eventbox['rect'].contains(rect):
                    dialog = gtk.Dialog('Rename Event Box',
                                        self.editor.get_parent(),
                                        gtk.DIALOG_MODAL |
                                        gtk.DIALOG_DESTROY_WITH_PARENT,
                                        (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                                         gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
                    dialog.set_default_response(gtk.RESPONSE_ACCEPT)

                    entry = gtk.Entry()
                    entry.show()
                    dialog.vbox.pack_start(entry, False, False, 0)
                    entry.set_text(eventbox['name'])
                    entry.set_activates_default(True)

                    response = dialog.run()
                    eventbox['name'] = entry.get_text()
                    dialog.destroy()

                    self.queue_draw_area(
                        *self._tiles_rect_to_pixels(eventbox['rect']))
                    return

            self.begin_record()
            self.drawing = True
            self._cur_eventbox_rect = rect

            self.eventboxes.append({
                'rect': self._cur_eventbox_rect,
                'name': 'eventbox%s,%s' % self._cur_eventbox_rect.topleft,
            })
        elif self.action == self.REMOVE_EVENTBOX_ACTION:
            rect = pygame.Rect(self._get_tile_area(e, False))

            for eventbox in self.eventboxes:
                if eventbox['rect'].contains(rect):
                    self.queue_draw_area(
                        *self._tiles_rect_to_pixels(eventbox['rect']))
                    self.eventboxes.remove(eventbox)
                    break

    def _on_button_release(self, w, e):
        if self.drawing:
            self.drawing = False
            self.end_record()

            if self.action == self.ADD_EVENTBOX_ACTION:
                if (self._cur_eventbox_rect.width <= 0 or
                    self._cur_eventbox_rect.height <= 0):
                    self.eventboxes.pop()

                self._cur_eventbox_rect = None

    def _on_motion_notify(self, w, e):
        old_cursor_area = self.cursor_area
        cursor_tiles_area = self._get_tile_area(e, False)
        self.cursor_area = self._tiles_rect_to_pixels(cursor_tiles_area)

        self.editor.tile_coord_label.set_text(
            '%s, %s' % (cursor_tiles_area[0], cursor_tiles_area[1]))
        self.editor.pixels_coord_label.set_text(
            '%s, %s' % (int(self.cursor_area[0] / self.zoom_level),
                        int(self.cursor_area[1] / self.zoom_level)))

        if not self._is_tile_area_valid(self.cursor_area):
            self.cursor_area = None

        if self.cursor_area != old_cursor_area:
            if old_cursor_area:
                self.queue_draw_area(old_cursor_area[0],
                                     old_cursor_area[1],
                                     old_cursor_area[2] + 1,
                                     old_cursor_area[3] + 1)

            if self.cursor_area:
                self.queue_draw_area(self.cursor_area[0],
                                     self.cursor_area[1],
                                     self.cursor_area[2] + 1,
                                     self.cursor_area[3] + 1)

        if self.action == self.PLACE_TILE_ACTION:
            if self.drawing:
                self._place_tile_from_event(e)
                return
        elif self.action == self.ADD_EVENTBOX_ACTION:
            if not self.drawing:
                return

            self.queue_draw_area(
                *self._tiles_rect_to_pixels(self._cur_eventbox_rect))

            self._cur_eventbox_rect.width = \
                cursor_tiles_area[0] + cursor_tiles_area[2] - \
                self._cur_eventbox_rect.x

            self._cur_eventbox_rect.height = \
                cursor_tiles_area[1] + cursor_tiles_area[3] - \
                self._cur_eventbox_rect.y

            self.queue_draw_area(
                *self._tiles_rect_to_pixels(self._cur_eventbox_rect))

    def _is_tile_area_valid(self, area):
        return (area is not None and
                0 <= area[0] < self.width * self.tile_width and
                0 <= area[1] < self.height * self.tile_height)

    def _get_tile_area(self, e, in_pixels=True):
        rect = pygame.Rect(e.x / self.tile_width,
                           e.y / self.tile_height,
                           1, 1)

        if in_pixels:
            rect = self._tiles_rect_to_pixels(rect)

        return rect


class TileList(gtk.VBox):
    def __init__(self):
        super(TileList, self).__init__(False, 0)

        self._group = None
        self.selected_button = None
        self.selected_tile = None
        self.shift_x = False
        self.shift_y = False
        self.zoom_level = 0.5
        self.tile_width = int(Tile.WIDTH * self.zoom_level)
        self.tile_height = int(Tile.HEIGHT * self.zoom_level)

        self.toolbox = gtk.HBox(False, 0)
        self.toolbox.show()
        self.pack_start(self.toolbox, False, False, 0)

        # Erase button
        button = self._create_button()
        self.toolbox.pack_start(button, False, False, 0)
        self.selected_button = button
        button.set_active(True)
        self._group = button

        image = gtk.image_new_from_stock(gtk.STOCK_REMOVE, gtk.ICON_SIZE_BUTTON)
        image.show()
        button.add(image)

        # Tiles window
        swin = gtk.ScrolledWindow()
        swin.show()
        self.pack_start(swin, True, True, 0)
        swin.set_shadow_type(gtk.SHADOW_IN)
        swin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        vbox = gtk.VBox(False, 0)
        vbox.show()
        swin.add_with_viewport(vbox)

        hbox = gtk.HBox(False, 0)
        hbox.show()
        vbox.pack_start(hbox, False, False, 0)

        self.table = gtk.Table()
        self.table.show()
        hbox.pack_start(self.table, False, False, 0)
        self.table.set_row_spacings(0)
        self.table.set_col_spacings(0)

    def set_filename(self, filename):
        self.filename = filename
        self.pixbuf = _load_tilesheet(filename, self.zoom_level)
        assert self.pixbuf

        self._reload_tiles()

    def _reload_tiles(self):
        tiles_x = self.pixbuf.get_width() / self.tile_width
        tiles_y = self.pixbuf.get_height() / self.tile_height

        self.table.foreach(lambda w: w.destroy())

        for y in range(tiles_y):
            attach_y = y

            if self.shift_y:
                if y == tiles_y - 1:
                    break

                y += 0.5

            for x in range(tiles_x):
                attach_x = x

                if self.shift_x:
                    if x == tiles_x - 1:
                        break

                    x += 0.5

                tile_pixbuf = _load_tile(self.filename, x, y, self.zoom_level)

                if not tile_pixbuf:
                    continue

                image = gtk.image_new_from_pixbuf(tile_pixbuf)
                image.show()

                button = self._add_button(attach_y, attach_x, {
                    'filename': self.filename,
                    'tile_x': x,
                    'tile_y': y,
                })
                button.add(image)

    def set_shift_x(self, shift):
        self.shift_x = shift
        self._reload_tiles()

    def set_shift_y(self, shift):
        self.shift_y = shift
        self._reload_tiles()

    def _create_button(self, tile_data=None):
        button = gtk.RadioButton(self._group)
        button.show()
        button.set_border_width(0)
        button.set_mode(False)
        button.connect('toggled', lambda w: self._on_clicked(w, tile_data))

        return button

    def _add_button(self, row, col, tile_data=None):
        button = self._create_button(tile_data)
        self.table.attach(button, col, col + 1, row, row + 1)
        return button

    def _on_clicked(self, w, tile_data):
        if not w.get_active():
            return

        self.selected_button = w
        self.selected_tile = tile_data


class SpritePane(gtk.VBox):
    def __init__(self, editor):
        super(SpritePane, self).__init__(False, 0)

        self.editor = editor

        # Spritesheet selector
        self.spritesheet_combo = gtk.combo_box_new_text()
        self.spritesheet_combo.show()
        self.pack_start(self.spritesheet_combo, False, False, 0)

        for path in sorted(os.listdir(get_tilesets_path())):
            self.spritesheet_combo.append_text(path)

        self.spritesheet_combo.connect(
            'changed',
            lambda w: self.tile_list.set_filename(w.get_active_text()))

        # Shifts
        hbox = gtk.HBox(False, 12)
        hbox.show()
        self.pack_start(hbox, False, False, 0)

        self.tile_shift_x = gtk.CheckButton("Shift X")
        self.tile_shift_x.show()
        hbox.pack_start(self.tile_shift_x, False, False, 0)
        self.tile_shift_x.connect('toggled', self._on_shift_x_toggled)

        self.tile_shift_y = gtk.CheckButton("Shift Y")
        self.tile_shift_y.show()
        hbox.pack_start(self.tile_shift_y, False, False, 0)
        self.tile_shift_y.connect('toggled', self._on_shift_y_toggled)

        # Tile list
        self.tile_list = TileList()
        self.tile_list.show()
        self.pack_start(self.tile_list, True, True, 0)

        self.spritesheet_combo.set_active(0)

    def set_active(self):
        self.editor.level_grid.set_action(LevelGrid.PLACE_TILE_ACTION)

    def _on_shift_x_toggled(self, w):
        self.tile_list.set_shift_x(w.get_active())

    def _on_shift_y_toggled(self, w):
        self.tile_list.set_shift_y(w.get_active())


class EventBoxPane(gtk.VBox):
    def __init__(self, editor):
        super(EventBoxPane, self).__init__(False, 0)

        self.editor = editor

        hbox = gtk.HBox(False, 0)
        hbox.show()
        self.pack_start(hbox, False, False, 0)

        self.add_button = gtk.RadioButton(None, 'Add')
        self.add_button.show()
        hbox.pack_start(self.add_button, False, False, 0)
        self.add_button.set_mode(False)
        self.add_button.connect('toggled', self._update_button_state)
        group = self.add_button

        self.remove_button = gtk.RadioButton(group, 'Remove')
        self.remove_button.show()
        hbox.pack_start(self.remove_button, False, False, 0)
        self.remove_button.set_mode(False)
        self.remove_button.connect('toggled', self._update_button_state)

    def set_active(self):
        self._update_button_state()

    def _update_button_state(self, *args, **kwargs):
        if self.add_button.get_active():
            self.editor.level_grid.set_action(LevelGrid.ADD_EVENTBOX_ACTION)
        elif self.remove_button.get_active():
            self.editor.level_grid.set_action(LevelGrid.REMOVE_EVENTBOX_ACTION)


class LevelEditor(gtk.Window):
    def __init__(self):
        super(LevelEditor, self).__init__(gtk.WINDOW_TOPLEVEL)

        self.zoom_level = 0.5

        self.set_title('The Cure - Level Editor')
        self.set_border_width(0)
        self.set_resizable(True)
        self.set_size_request(1024, 768)
        self.connect('delete_event', gtk.main_quit)
        self.connect('key-press-event', self._on_key_press)

        hpaned = gtk.HPaned()
        hpaned.show()
        self.add(hpaned)
        hpaned.set_position(self.get_size_request()[0] - 300)

        # Sidebar
        self.sidebar = gtk.VBox(False, 6)
        self.sidebar.show()
        self.sidebar.set_border_width(6)
        hpaned.pack2(self.sidebar)

        # Level selector
        hbox = gtk.HBox(False, 6)
        hbox.show()
        self.sidebar.pack_start(hbox, False, False, 0)

        self.level_combo = gtk.combo_box_new_text()
        self.level_combo.show()
        hbox.pack_start(self.level_combo, True, True, 0)

        save_button = gtk.Button("Save")
        save_button.show()
        hbox.pack_start(save_button, False, False, 0)
        save_button.connect('clicked', lambda w: self.save())

        for level in get_levels():
            self.level_combo.append_text(level.name)

        self.level_combo.connect('changed', lambda w: self.load_level())

        # Level Size
        hbox = gtk.HBox(False, 6)
        hbox.show()
        self.sidebar.pack_start(hbox, False, False, 0)

        label = gtk.Label("Size:")
        label.show()
        hbox.pack_start(label, False, False, 0)

        self.width_entry = gtk.Entry()
        self.width_entry.show()
        hbox.pack_start(self.width_entry, False, False, 0)
        self.width_entry.set_width_chars(4)
        self.width_entry.connect('focus-out-event', self._on_width_focus_out)

        label = gtk.Label("x")
        label.show()
        hbox.pack_start(label, False, False, 0)

        self.height_entry = gtk.Entry()
        self.height_entry.show()
        hbox.pack_start(self.height_entry, False, False, 0)
        self.height_entry.set_width_chars(4)
        self.height_entry.connect('focus-out-event', self._on_height_focus_out)

        # Layer selector
        self.layer_combo = gtk.combo_box_new_text()
        self.layer_combo.show()
        self.sidebar.pack_start(self.layer_combo, False, False, 0)

        for name in LAYER_NAMES:
            self.layer_combo.append_text(name)

        self.layer_combo.connect('changed', lambda w: self._on_layer_changed())

        show_only = gtk.CheckButton('Show only this layer')
        show_only.show()
        self.sidebar.pack_start(show_only, False, False, 0)
        show_only.connect('toggled', self._on_show_active_layer_only_toggled)

        # Sprite pane
        self.sprite_pane = SpritePane(self)
        #self.sprite_pane.show()
        self.sidebar.pack_start(self.sprite_pane, True, True, 0)

        # Event box pane
        self.eventbox_pane = EventBoxPane(self)
        self.eventbox_pane.show()
        self.sidebar.pack_start(self.eventbox_pane, True, True, 0)

        # Coordinates status
        hbox = gtk.HBox(False, 0)
        hbox.show()
        self.sidebar.pack_start(hbox, False, False, 0)

        label = gtk.Label("Tile: ")
        label.show()
        hbox.pack_start(label, False, False, 0)

        self.tile_coord_label = gtk.Label()
        self.tile_coord_label.show()
        hbox.pack_start(self.tile_coord_label, False, False, 0)

        label = gtk.Label("; Pixels: ")
        label.show()
        hbox.pack_start(label, False, False, 0)

        self.pixels_coord_label = gtk.Label()
        self.pixels_coord_label.show()
        hbox.pack_start(self.pixels_coord_label, False, False, 0)

        # Level grid
        swin = gtk.ScrolledWindow()
        swin.show()
        hpaned.pack1(swin)
        swin.set_shadow_type(gtk.SHADOW_IN)
        swin.set_policy(gtk.POLICY_ALWAYS, gtk.POLICY_ALWAYS)

        self.level_grid = LevelGrid(self, self.sprite_pane.tile_list)
        self.level_grid.show()
        swin.add_with_viewport(self.level_grid)

        self.level_combo.set_active(0)
        self.layer_combo.set_active(DEFAULT_LAYER)

    def set_zoom_level(self, zoom_level):
        if zoom_level < 0.125 or zoom_level > 1.0:
            return

        self.zoom_level = zoom_level
        self.level_grid.set_zoom_level(self.zoom_level)

    def load_level(self):
        loader = LevelLoader(self.level_combo.get_active_text())
        self.level_grid.load(loader)
        self.width_entry.set_text(str(self.level_grid.width))
        self.height_entry.set_text(str(self.level_grid.height))

    def save(self):
        writer = LevelWriter(self.level_combo.get_active_text())
        self.level_grid.write(writer)

    def _on_key_press(self, w, e):
        if e.state & gtk.gdk.CONTROL_MASK:
            if e.keyval == ord('z'):
                self.level_grid.undo()
                return True
            elif e.keyval == ord('r'):
                self.level_grid.redo()
                return True
        elif e.keyval == ord('-'):
            self.set_zoom_level(self.zoom_level / 2)
        elif e.keyval == ord('+'):
            self.set_zoom_level(self.zoom_level * 2)

    def _on_layer_changed(self):
        current_layer = self.layer_combo.get_active()
        self.level_grid.set_current_layer(current_layer)

        if LAYERS[current_layer] == 'events':
            self.sprite_pane.hide()
            self.eventbox_pane.show()
            self.eventbox_pane.set_active()
        else:
            self.eventbox_pane.hide()
            self.sprite_pane.show()
            self.sprite_pane.set_active()

    def _on_show_active_layer_only_toggled(self, w):
        self.level_grid.set_show_active_layer_only(w.get_active())

    def _on_width_focus_out(self, w, e):
        try:
            width = int(self.width_entry.get_text())
        except ValueError:
            self.width_entry.set_text(self.level_grid.width)

        self.level_grid.set_width(width)

    def _on_height_focus_out(self, w, e):
        try:
            height = int(self.height_entry.get_text())
        except ValueError:
            self.height_entry.set_text(self.level_grid.height)

        self.level_grid.set_height(height)


def main():
    editor = LevelEditor()
    editor.show()
    gtk.main()
