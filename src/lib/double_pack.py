import matplotlib.pyplot as plt
import numpy as np
from plotting import *
from readings import *
from tile_process import *
import os

def read_packing_results(filename):
    result = []
    bounding_width = None  # Initialize bounding width variable

    with open(filename, 'r') as file:
        lines = file.readlines()
        
        for line in lines:
            line = line.strip()
            
            # Check if the line contains the bounding width
            if line.startswith("Bounding Width:"):
                bounding_width = int(line.split(":")[1].strip())
                continue  # Skip this line, as we've already processed the bounding width

            # Skip bounding height line
            if line.startswith("Bounding Height:"):
                continue

            # Check if the line contains tile data
            if line.startswith("Preplaced") or line.startswith("Placed"):
                parts = line.split()

                # Extract Position_x and the tile parts
                position_x = int(parts[1])  # Position_x comes after "Preplaced" or "Placed"
                tile_parts = []

                i = 2
                while i < len(parts):
                    w = int(parts[i])
                    h = int(parts[i + 1])
                    dx = int(parts[i + 2])
                    dy = int(parts[i + 3])
                    tile_parts.append((w, h, dx, dy))
                    i += 4

                result.append([position_x, tile_parts])

    return bounding_width, result

def export_separation(filename, separation_value, if_double):
    with open(filename, 'w') as f:
        f.write(str(separation_value) + '\n')
        if if_double:
            f.write(str(1) + '\n')
        else:
            f.write(str(0) + '\n')

def first_pack(excitations, separation, seam_lst):
    tiles = create_circuit_tile(excitations)
    print(f"first input has {len(tiles)} tiles")
    # random.shuffle(tiles)
    # tiles = create_circuit_tile(excitations)
    filename = "./tiles/inter_intra_tiles.txt"
    # np.random.shuffle(tiles)
    tiles = sorted(tiles, key=lambda tile: tile[0][1], reverse=True)
    export_inter_intra(tiles, filename, seam_lst)
    c_directory = "../lib/double_packing.exe"
    separation_file = "./tiles/separation.txt"
    export_separation(separation_file, separation, False)
    bounding_width, placed_tiles_lst = packing_with_c(tiles,c_directory)
    filename = './tiles/result_tiles.txt'
    bounding_width, placed_tiles = read_packing_results(filename)
    print(f"first output has {len(placed_tiles)} tiles")
    return bounding_width, placed_tiles

def double_pack_with_c(excitations, separation, seam_lst, if_double = False):
    bounding_width, placed_tiles_lst = first_pack(excitations, separation, seam_lst)
    if if_double:
        return bounding_width, placed_tiles_lst
    def reexport_tiles(placed_tiles):
        new_tiles = []
        for placed_tile in placed_tiles:
            new_tiles.append(placed_tile[1])
        return new_tiles
    
    def sort_key(tile):
        criteria = (tile[0], tile[1][0][1], tile[1][0][3])
        return criteria

    ordered_placed_tiles = sorted(placed_tiles_lst, key=sort_key)
    filename = "./tiles/second_input_tiles.txt"

    new_tiles = reexport_tiles(ordered_placed_tiles)
    export_inter_intra(new_tiles, filename, seam_lst)
    
    print(f"second output has {len(new_tiles)} tiles")
    separation_file = "./tiles/separation.txt"
    export_separation(separation_file, separation, True)
    second_packing_c = "../lib/double_packing.exe"
    second_bounding_width, second_placed_tiles_lst = packing_with_c(new_tiles,second_packing_c)
    filename = './tiles/second_result_tiles.txt'
    bounding_width, placed_tiles_lst = read_packing_results(filename)
    print(f"second output has {len(placed_tiles_lst)} tiles")
    return bounding_width, placed_tiles_lst