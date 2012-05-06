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
    def __init__(self, tile_list):
        super(LevelGrid, self).__init__()

        self.tile_list = tile_list

        self.add_events(gtk.gdk.POINTER_MOTION_MASK |
                        gtk.gdk.BUTTON_PRESS_MASK |
                        gtk.gdk.BUTTON_RELEASE_MASK)

        self.gc = None
        self.image = None
        self.cursor_area = None

        self.connect('expose-event', self._on_expose_event)
        self.connect('button-press-event', self._on_button_press)
        self.connect('button-release-event', self._on_button_release)
        self.connect('motion-notify-event', self._on_motion_notify)

    def load(self, loader):
        self.realize()

        style = self.get_style()
        self.gc = style.fg_gc[gtk.STATE_NORMAL]
        self.bg_gc = self.style.bg_gc[gtk.STATE_NORMAL]
        self.cursor_gc = self.style.bg_gc[gtk.STATE_SELECTED]

        self.image = gtk.gdk.Pixmap(self.window,
                                    loader.get_width() * Tile.WIDTH,
                                    loader.get_height() * Tile.HEIGHT)

        for tile_data in loader.iter_tiles('bg'):
            tilesheet = _load_tilesheet(tile_data['tile_file'])

            self.image.draw_pixbuf(self.gc,
                                   tilesheet,
                                   tile_data['tile_x'] * Tile.WIDTH,
                                   tile_data['tile_y'] * Tile.HEIGHT,
                                   tile_data['col'] * Tile.WIDTH,
                                   tile_data['row'] * Tile.HEIGHT,
                                   Tile.WIDTH,
                                   Tile.HEIGHT)

    def _on_expose_event(self, level_grid, e):
        if self.image:
            self.window.draw_drawable(self.gc, self.image, e.area.x, e.area.y,
                                      e.area.x, e.area.y, e.area.width,
                                      e.area.height)

            if self.cursor_area:
                self.window.draw_rectangle(self.cursor_gc, False,
                                           *self.cursor_area)

    def _on_button_press(self, w, e):
        tile_area = self._get_tile_area(e)
        selected_tile = self.tile_list.selected_tile

        if selected_tile:
            pixbuf = selected_tile['pixbuf']
            self.image.draw_pixbuf(self.gc,
                                   pixbuf,
                                   0,
                                   0,
                                   *tile_area)
        else:
            self.image.draw_rectangle(self.bg_gc, True, *tile_area)

        self.queue_draw_area(*tile_area)

    def _on_button_release(self, w, e):
        pass

    def _on_motion_notify(self, w, e):
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

        self.set_filename('ground_1.png')

    def set_filename(self, filename):
        pixbuf = _load_tilesheet(filename)
        assert pixbuf

        tiles_x = pixbuf.get_width() / Tile.WIDTH
        tiles_y = pixbuf.get_height() / Tile.HEIGHT

        self.resize(0, 0)

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
            for x in range(tiles_x):
                tile_pixbuf = _load_tile(filename, x, y)

                if not tile_pixbuf:
                    continue

                image = gtk.image_new_from_pixbuf(tile_pixbuf)
                image.show()

                button = self._add_button(y + 1, x, {
                    'filename': filename,
                    'x': x,
                    'y': y,
                    'tilesheet': pixbuf,
                    'pixbuf': tile_pixbuf,
                })
                button.add(image)

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
        hpaned.pack2(self.sidebar)

        # Level selector
        self.level_combo = gtk.combo_box_new_text()
        self.level_combo.show()
        self.sidebar.pack_start(self.level_combo, False, False, 0)

        for level in get_levels():
            self.level_combo.append_text(level.name)

        self.level_combo.connect('changed', lambda w: self.load_level())

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

    def load_level(self):
        loader = LevelLoader(self.level_combo.get_active_text())

        self.level_grid.load(loader)


def main():
    editor = LevelEditor()
    editor.show()
    gtk.main()
