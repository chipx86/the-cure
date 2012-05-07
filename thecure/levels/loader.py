import sys

try:
    from json import loads
except ImportError:
    from simplejson import loads

from thecure.resources import get_level_filename


class LevelLoader(object):
    def __init__(self, name):
        self.name = name

        self._load_file(get_level_filename(name))

    def get_width(self):
        assert self.data
        assert 'width' in self.data
        return self.data['width']

    def get_height(self):
        assert self.data
        assert 'height' in self.data
        return self.data['height']

    def iter_layers(self):
        assert self.data
        assert 'layers' in self.data

        for layer_data in self.data['layers']:
            yield layer_data

    def iter_eventboxes(self):
        assert self.data

        for name, eventbox in self.data.get('eventboxes', {}).iteritems():
            yield name, eventbox

    def iter_tiles(self, layer_name):
        assert self.data
        assert 'files' in self.data
        assert 'layers' in self.data
        assert 'tiles' in self.data

        rows = []

        for layer_data in self.data['layers']:
            if layer_data['name'] == layer_name:
                rows = layer_data['tiles']
                break

        if not rows:
            return

        files = self.data['files']
        tile_types = self.data['tiles']

        for row_num, tiles in rows:
            for tile_id, start_col, colspan in tiles:
                for i in range(colspan):
                    tile_type = tile_types[tile_id]

                    yield {
                        'row': row_num,
                        'col': start_col + i,
                        'tile_file': files[tile_type[0]],
                        'tile_x': tile_type[1],
                        'tile_y': tile_type[2],
                    }

    def _load_file(self, filename):
        try:
            fp = open(filename, 'r')
        except IOError, e:
            sys.stderr.write('Failed to load level file %s: %s\n' %
                             (filename, e))
            sys.exit(1)

        try:
            self.data = loads(fp.read())
        except Exception, e:
            sys.stderr.write('Failed to deserialize level file %s: %s\n' %
                             (filename, e))
            sys.exit(1)

        fp.close()
