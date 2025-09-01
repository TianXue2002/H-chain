import matplotlib.pyplot as plt
import numpy as np
from plotting import *
from readings import *
from tile_process import *
import os
import zx_tile_process as ZX

PARENT_PATH = "C:/Users/24835/Desktop/homework/uiuc/Covey/chem"
C_PATH = PARENT_PATH + "/H-chain/src/lib/double_packing.exe"

def export_separation(filename, separation_value, if_double):
    with open(filename, 'w') as f:
        f.write(str(separation_value) + '\n')
        if if_double:
            f.write(str(1) + '\n')
        else:
            f.write(str(0) + '\n')

def first_pack(excitations, separation, seam_lst, if_zx = False):
    if not if_zx:
        tiles = create_circuit_tile(excitations)
    else:
        tiles = ZX.create_circuit_tile(excitations)
    print(f"first input has {len(tiles)} tiles")
    # random.shuffle(tiles)
    # tiles = create_circuit_tile(excitations)
    tile_dir = PARENT_PATH + "/H-chain/src/double_packing/tiles"
    filename = tile_dir + "/inter_intra_tiles.txt"
    # np.random.shuffle(tiles)
    tiles = sorted(tiles, key=lambda tile: tile.h, reverse=True)
    export_inter_intra(tiles, filename, seam_lst)
    c_directory = C_PATH
    separation_file = tile_dir + "/separation.txt"
    export_separation(separation_file, separation, False)
    bounding_width, placed_tiles_lst = packing_with_c(tiles,c_directory)
    filename = tile_dir + '/result_tiles.txt'
    bounding_width, placed_tiles = read_placed_tiles(filename)
    print(f"first output has {len(placed_tiles)} tiles")
    return bounding_width, placed_tiles

def double_pack_with_c(excitations, separation, seam_lst, if_double = False, 
                       file_name = "./tiles/second_input_tiles.txt", if_zx = True):
    
    tile_dir = PARENT_PATH + "/H-chain/src/double_packing/tiles"

    bounding_width, placed_tiles_lst = first_pack(excitations, separation, seam_lst, if_zx=if_zx)
    if if_double:
        return bounding_width, placed_tiles_lst
    def reexport_tiles(placed_tiles):
        new_tiles = []
        for placed_tile in placed_tiles:
            cur_tile = Tile(placed_tile.w, placed_tile.h, placed_tile.dx, placed_tile.dy)
            cur_tile.pauli = placed_tile.pauli
            cur_tile.t = placed_tile.t
            new_tiles.append(cur_tile)
            
        return new_tiles
    
    def sort_key(tile):
        criteria = (tile.pos, tile.h, tile.dy)
        return criteria

    ordered_placed_tiles = sorted(placed_tiles_lst, key=sort_key)
    filename = tile_dir + "/second_input_tiles.txt"

    new_tiles = reexport_tiles(ordered_placed_tiles)
    export_inter_intra(new_tiles, filename, seam_lst)
    
    print(f"second output has {len(new_tiles)} tiles")
    separation_file = tile_dir + "/separation.txt"
    export_separation(separation_file, separation, True)
    second_packing_c = C_PATH
    second_bounding_width, second_placed_tiles_lst = packing_with_c(new_tiles,second_packing_c)
    filename = tile_dir + '/second_result_tiles.txt'
    bounding_width, placed_tiles_lst = read_placed_tiles(filename)
    print(f"second output has {len(placed_tiles_lst)} tiles")
    return bounding_width, placed_tiles_lst