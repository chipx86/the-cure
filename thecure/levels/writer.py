try:
    from json import dumps
except ImportError:
    from simplejson import dumps

from thecure.resources import get_level_filename


class LevelWriter(object):
    def __init__(self, name):
        self.name = name

    def write(self, layers, eventboxes, width, height):
        files_list = []
        files_map = {}
        layer_list = []
        tile_list = []
        tile_map = {}
        eventboxes_map = {}

        for eventbox in eventboxes:
            rect = eventbox['rect']

            eventboxes_map[eventbox['name']] = {
                'rect': [rect.x, rect.y, rect.width, rect.height],
            }

        data = {
            'files': files_list,
            'layers': layer_list,
            'tiles': tile_list,
            'width': width,
            'height': height,
            'eventboxes': eventboxes_map,
        }

        for i, layer in enumerate(layers):
            layer_tiles = []

            layer_data = {
                'name': layer['name'],
                'index': i,
                'is_main': layer['is_main'],
                'tiles': layer_tiles,
            }
            layer_list.append(layer_data)

            rows = layer['tiles']

            for row, row_data in enumerate(rows):
                row_tiles = []

                col = 0

                num_cols = len(row_data)

                prev_tile = None
                prev_tile_data = None

                while col < num_cols:
                    tile_data = row_data[col]

                    if tile_data is None:
                        col += 1
                        continue

                    filename = tile_data['filename']
                    tile_x = tile_data['tile_x']
                    tile_y = tile_data['tile_y']

                    if filename not in files_map:
                        file_id = len(files_list)
                        files_list.append(filename)
                        files_map[filename] = file_id
                    else:
                        file_id = files_map[filename]

                    tile_key = '%s-%s-%s' % (file_id, tile_x, tile_y)

                    if tile_key not in tile_map:
                        tile_id = len(tile_list)
                        tile_list.append([file_id, tile_x, tile_y])
                        tile_map[tile_key] = tile_id
                    else:
                        tile_id = tile_map[tile_key]

                    # Figure out the colspan
                    colspan = 1

                    for endcol in xrange(col + 1, len(row_data)):
                        if tile_data == row_data[endcol]:
                            colspan += 1
                        else:
                            break

                    tile = [tile_id, col, colspan]

                    # See if we can find a repeated pattern from the
                    # previous entry.
                    if (prev_tile and colspan == 1 and
                        not isinstance(prev_tile[0], list) and
                        prev_tile[2] == 1 and
                        prev_tile[1] + 1 == tile[1]):
                        repeat_span = 0
                        start_col = col + colspan

                        for c in xrange(start_col, len(row_data), 2):
                            if (c + 1 < len(row_data) and
                                row_data[c] == prev_tile_data and
                                row_data[c + 1] == tile_data):
                                repeat_span += 1
                            else:
                                break

                        if repeat_span > 0:
                            prev_tile[0] = [prev_tile[0], tile_id]
                            prev_tile[2] = repeat_span
                            col += 2 * (repeat_span - 1)
                            continue

                    row_tiles.append(tile)
                    prev_tile = tile
                    prev_tile_data = tile_data
                    col += colspan

                if row_tiles:
                    layer_tiles.append([row, row_tiles])

        fp = open(get_level_filename(self.name), 'w')
        fp.write(dumps(data))
        fp.close()
