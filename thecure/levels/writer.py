try:
    from json import dumps
except ImportError:
    from simplejson import dumps

from thecure.resources import get_level_filename


class LevelWriter(object):
    def __init__(self, name):
        self.name = name

    def write(self, layers):
        files_list = []
        files_map = {}
        layer_list = []
        tile_list = []
        tile_map = {}

        data = {
            'files': files_list,
            'layers': layer_list,
            'tiles': tile_list,
        }

        max_width = 0
        max_height = 0

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
            max_height = max(max_height, len(rows))

            for row, row_data in enumerate(rows):
                row_tiles = []

                col = 0

                num_cols = len(row_data)
                max_width = max(max_width, num_cols)

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

                    for endcol in range(col + 1, len(row_data)):
                        if tile_data == row_data[endcol]:
                            colspan += 1
                        else:
                            break

                    row_tiles.append([tile_id, col, colspan])
                    col += colspan

                if row_tiles:
                    layer_tiles.append([row, row_tiles])

        data['width'] = max_width
        data['height'] = max_height

        fp = open(get_level_filename(self.name), 'w')
        fp.write(dumps(data))
        fp.close()
