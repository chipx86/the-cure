import json
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

from thecure.levels import get_levels
from thecure.levels.loader import LevelLoader
from thecure.levels.writer import LevelWriter
from thecure.resources import get_image_filename, get_level_filename
from thecure.sprites import Tile


# We can't reuse the cache in resources, since we need GdkPixbufs.
_tilesheet_cache = {}
_tile_cache = {}


def _load_tilesheet(name):
    if name not in _tilesheet_cache:
        _tilesheet_cache[name] = gtk.gdk.pixbuf_new_from_file(
            get_image_filename('sprites/tiles/' + name))

    return _tilesheet_cache[name]


def _load_tile(name, x, y):
    key = '%s-%s-%s' % (name, x, y)

    if key not in _tile_cache:
        pixbuf = _load_tilesheet(name)

        _tile_cache[key] = pixbuf.subpixbuf(int(x * Tile.WIDTH),
                                            int(y * Tile.HEIGHT),
                                            Tile.WIDTH,
                                            Tile.HEIGHT)

    return _tile_cache[key]


class LevelGrid(gtk.DrawingArea):
    # XXX Hard-coding these is fragile.
    LAYERS = ['bg', 'main', 'fg']

    def __init__(self, tile_list):
        super(LevelGrid, self).__init__()

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
        self.current_layer = len(self.LAYERS) - 1

        for layer_name in self.LAYERS:
            self.tiles[layer_name] = [
                [None] * loader.get_width()
                for i in range(loader.get_height())
            ]

            for tile_data in self.loader.iter_tiles(layer_name):
                tilesheet = _load_tilesheet(tile_data['tile_file'])
                row = tile_data['row']
                col = tile_data['col']

                self.tiles[layer_name][row][col] = {
                    'filename': tile_data['tile_file'],
                    'tile_x': tile_data['tile_x'],
                    'tile_y': tile_data['tile_y'],
                }

        self._reload_layers()
        self.loaded = True

    def write(self, writer):
        writer.write([
            {
                'name': layer_name,
                'is_main': layer_name == 'main',
                'tiles': self.tiles[layer_name]
            }
            for layer_name in self.LAYERS
        ])

    def set_show_active_layer_only(self, show_only):
        self.show_active_layer_only = show_only
        self._reload_layers()

    def _clear(self):
        width = self.loader.get_width() * Tile.WIDTH
        height = self.loader.get_height() * Tile.HEIGHT

        self.image = gtk.gdk.Pixmap(self.window, width, height)
        self.image.draw_rectangle(self.bg_gc, True, 0, 0, width, height)

    def _load_layer(self, layer_name):
        layer_tiles = self.tiles[layer_name]

        for row, row_data in enumerate(self.tiles[layer_name]):
            for col, col_data in enumerate(row_data):
                if col_data is None:
                    continue

                tilesheet = _load_tilesheet(col_data['filename'])

                self.image.draw_pixbuf(self.gc,
                                       tilesheet,
                                       int(col_data['tile_x'] * Tile.WIDTH),
                                       int(col_data['tile_y'] * Tile.HEIGHT),
                                       col * Tile.WIDTH,
                                       row * Tile.HEIGHT,
                                       Tile.WIDTH,
                                       Tile.HEIGHT)

    def set_current_layer(self, index):
        if index != self.current_layer:
            self.current_layer = index

            if self.loaded:
                self._reload_layers()

    def _reload_layers(self):
        self._clear()

        for i in range(self.current_layer + 1):
            if not self.show_active_layer_only or self.current_layer == i:
                self._load_layer(self.LAYERS[i])

        self.queue_draw()

    def _on_expose_event(self, level_grid, e):
        if self.image:
            self.window.draw_drawable(self.gc, self.image, e.area.x, e.area.y,
                                      e.area.x, e.area.y, e.area.width,
                                      e.area.height)

            if self.cursor_area:
                self.window.draw_rectangle(self.cursor_gc, False,
                                           *self.cursor_area)

    def _place_tile(self, e):
        tile_area = self._get_tile_area(e)
        tile_x = tile_area[0] / Tile.WIDTH
        tile_y = tile_area[1] / Tile.HEIGHT
        selected_tile = self.tile_list.selected_tile

        tiles = self.tiles[self.LAYERS[self.current_layer]]

        if selected_tile:
            pixbuf = selected_tile['pixbuf']
            self.image.draw_pixbuf(self.gc,
                                   pixbuf,
                                   0,
                                   0,
                                   *tile_area)

            tiles[tile_y][tile_x] = {
                'filename': selected_tile['filename'],
                'tile_x': selected_tile['x'],
                'tile_y': selected_tile['y'],
            }
        else:
            self.image.draw_rectangle(self.bg_gc, True, *tile_area)
            tiles[tile_y][tile_x] = None

        self.queue_draw_area(*tile_area)

    def _on_button_press(self, w, e):
        self._place_tile(e)
        self.drawing = True

    def _on_button_release(self, w, e):
        self.drawing = False

    def _on_motion_notify(self, w, e):
        if self.drawing:
            self._place_tile(e)
            return

        old_cursor_area = self.cursor_area
        self.cursor_area = self._get_tile_area(e)

        if self.cursor_area != old_cursor_area:
            if old_cursor_area:
                self.queue_draw_area(old_cursor_area[0],
                                     old_cursor_area[1],
                                     old_cursor_area[2] + 1,
                                     old_cursor_area[3] + 1)

            self.queue_draw_area(self.cursor_area[0],
                                 self.cursor_area[1],
                                 self.cursor_area[2] + 1,
                                 self.cursor_area[3] + 1)

    def _get_tile_area(self, e):
        return (int(e.x / Tile.WIDTH) * Tile.WIDTH,
                int(e.y / Tile.HEIGHT) * Tile.HEIGHT,
                Tile.WIDTH,
                Tile.HEIGHT)


class TileList(gtk.Table):
    MAX_COLS = 10

    def __init__(self):
        super(TileList, self).__init__(columns=self.MAX_COLS)

        self.set_row_spacings(0)
        self.set_col_spacings(0)

        self._group = None
        self.selected_button = None
        self.selected_tile = None
        self.shift_x = False
        self.shift_y = False

        self.set_filename('ground_1.png')

    def set_filename(self, filename):
        self.filename = filename
        self.pixbuf = _load_tilesheet(filename)
        assert self.pixbuf

        self._reload_tiles()

    def _reload_tiles(self):
        tiles_x = self.pixbuf.get_width() / Tile.WIDTH
        tiles_y = self.pixbuf.get_height() / Tile.HEIGHT

        self.foreach(lambda w: w.destroy())

        # Add the "erase" one
        button = self._add_button(0, 0)
        self.selected_button = button
        button.set_active(True)
        self._group = button

        image = gtk.image_new_from_stock(gtk.STOCK_REMOVE, gtk.ICON_SIZE_BUTTON)
        image.show()
        button.add(image)
        image.set_size_request(Tile.WIDTH, Tile.HEIGHT)

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

                tile_pixbuf = _load_tile(self.filename, x, y)

                if not tile_pixbuf:
                    continue

                image = gtk.image_new_from_pixbuf(tile_pixbuf)
                image.show()

                button = self._add_button(attach_y + 1, attach_x, {
                    'filename': self.filename,
                    'x': x,
                    'y': y,
                    'tilesheet': self.pixbuf,
                    'pixbuf': tile_pixbuf,
                })
                button.add(image)

    def set_shift_x(self, shift):
        self.shift_x = shift
        self._reload_tiles()

    def set_shift_y(self, shift):
        self.shift_y = shift
        self._reload_tiles()

    def _add_button(self, row, col, tile_data=None):
        button = gtk.RadioButton(self._group)
        button.show()
        self.attach(button, col, col + 1, row, row + 1)
        button.set_border_width(0)
        button.set_mode(False)
        button.connect('toggled', lambda w: self._on_clicked(w, tile_data))

        return button

    def _on_clicked(self, w, tile_data):
        if not w.get_active():
            return

        self.selected_button = w
        self.selected_tile = tile_data


class LevelEditor(gtk.Window):
    def __init__(self):
        super(LevelEditor, self).__init__(gtk.WINDOW_TOPLEVEL)
        self.set_title('The Cure - Level Editor')
        self.set_border_width(0)
        self.set_resizable(True)
        self.set_size_request(1024, 768)
        self.connect('delete_event', gtk.main_quit)

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

        # Layer selector
        self.layer_combo = gtk.combo_box_new_text()
        self.layer_combo.show()
        self.sidebar.pack_start(self.layer_combo, False, False, 0)
        self.layer_combo.append_text('Background Layer')
        self.layer_combo.append_text('Main Layer')
        self.layer_combo.append_text('Foreground Layer')
        self.layer_combo.connect('changed', lambda w: self._on_layer_changed())

        show_only = gtk.CheckButton('Show only this layer')
        show_only.show()
        self.sidebar.pack_start(show_only, False, False, 0)
        show_only.connect('toggled', self._on_show_active_layer_only_toggled)

        # Shifts
        hbox = gtk.HBox(False, 12)
        hbox.show()
        self.sidebar.pack_start(hbox, False, False, 0)

        self.tile_shift_x = gtk.CheckButton("Shift X")
        self.tile_shift_x.show()
        hbox.pack_start(self.tile_shift_x, False, False, 0)
        self.tile_shift_x.connect('toggled', self._on_shift_x_toggled)

        self.tile_shift_y = gtk.CheckButton("Shift Y")
        self.tile_shift_y.show()
        hbox.pack_start(self.tile_shift_y, False, False, 0)
        self.tile_shift_y.connect('toggled', self._on_shift_y_toggled)

        # Sprites list
        swin = gtk.ScrolledWindow()
        swin.show()
        self.sidebar.pack_start(swin, True, True, 0)
        swin.set_shadow_type(gtk.SHADOW_IN)
        swin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        vbox = gtk.VBox(False, 0)
        vbox.show()
        swin.add_with_viewport(vbox)

        hbox = gtk.HBox(False, 0)
        hbox.show()
        vbox.pack_start(hbox, False, False, 0)

        self.tile_list = TileList()
        self.tile_list.show()
        hbox.pack_start(self.tile_list, False, False, 0)

        # Level grid
        self.level_grid = LevelGrid(self.tile_list)
        self.level_grid.show()
        hpaned.pack1(self.level_grid)

        self.level_combo.set_active(0)
        self.layer_combo.set_active(1)

    def load_level(self):
        loader = LevelLoader(self.level_combo.get_active_text())

        self.level_grid.load(loader)

    def save(self):
        writer = LevelWriter(self.level_combo.get_active_text())
        self.level_grid.write(writer)

    def _on_layer_changed(self):
        current_layer = self.layer_combo.get_active()
        self.level_grid.set_current_layer(current_layer)

    def _on_shift_x_toggled(self, w):
        self.tile_list.set_shift_x(w.get_active())

    def _on_shift_y_toggled(self, w):
        self.tile_list.set_shift_y(w.get_active())

    def _on_show_active_layer_only_toggled(self, w):
        self.level_grid.set_show_active_layer_only(w.get_active())


def main():
    editor = LevelEditor()
    editor.show()
    gtk.main()
