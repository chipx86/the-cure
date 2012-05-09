import sys

try:
    from json import loads
except ImportError:
    from simplejson import loads

from thecure.resources import get_level_filename


class LevelLoader(object):
    def __init__(self, name):
        self.name = name
        self.data = None

        self._load_file(get_level_filename(name))

    def get_width(self):
        assert self.data is not None
        return self.data.get('width', 1)

    def get_height(self):
        assert self.data is not None
        return self.data.get('height', 1)

    def iter_layers(self):
        assert self.data is not None

        for layer_data in self.data.get('layers', []):
            yield layer_data

    def iter_eventboxes(self):
        assert self.data is not None

        for name, eventbox in self.data.get('eventboxes', {}).iteritems():
            yield name, eventbox

    def iter_tiles(self, layer_name):
        assert self.data is not None

        if 'tiles' not in self.data:
            return

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
            for tile_ids, start_col, colspan in tiles:
                if isinstance(tile_ids, list):
                    print row_num, start_col, tile_ids, colspan
                    repeat_count = colspan
                    colspan = 1
                else:
                    tile_ids = [tile_ids]
                    repeat_count = 1

                for i in xrange(repeat_count):
                    for tile_id in tile_ids:
                        for j in xrange(colspan):
                            tile_type = tile_types[tile_id]

                            yield {
                                'row': row_num,
                                'col': start_col + j,
                                'tile_file': files[tile_type[0]],
                                'tile_x': tile_type[1],
                                'tile_y': tile_type[2],
                            }

                        start_col += colspan

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
