import matplotlib.pyplot as plt
import numpy as np
from plotting import *
from readings import *
from tile_process import *
import os

def find_inter_module_tiles(tiles_lst, seam_lst):
    inter_tiles = []
    intra_tiles = []
    for cur_tile in tiles_lst:
        inter = False
        w,h,x,y = cur_tile[0]
        for i in range(len(seam_lst)):
            seam = seam_lst[i]
            if y < seam and y+h >= seam:
                inter_tiles.append(cur_tile)
                inter = True
        if not inter:
            intra_tiles.append(cur_tile)
    return inter_tiles, intra_tiles

def move_inter_tiles(placed_tiles, seperation, seam_lst):
    moved_tiles = []
    pre_x = np.zeros(len(seam_lst), dtype=int)
    for placed_tile in placed_tiles:
        cur_x, tile = placed_tile
        w,h,dx,dy = tile[0]
        inter = False
        print(tile)
        for i in range(len(seam_lst)):
            seam = seam_lst[i]
            if inter and dy < seam and dy + h >= seam:
                cur_x2 = pre_x[i] + w + seperation
                cur_x = max(cur_x, cur_x2)
                pre_x[0] = cur_x
                pre_x[1] = cur_x
                # print("cross", tile, cur_x, pre_x)
            if dy < seam and dy + h >= seam and not inter:
                if cur_x != 0:
                    cur_x = pre_x[i] + w + seperation
                    inter = True
                pre_x[i] = cur_x
        moved_tiles.append((cur_x, tile))
        if inter:
            print(cur_x)
            print(pre_x)
            print(i)
            print("====")
    return moved_tiles

def expand_inter_tiles(inter_tiles, expand_size):
    expanded_tiles = copy.deepcopy(inter_tiles)
    for inter_tile in expanded_tiles:
        inter_tile[0][0] += expand_size
    return expanded_tiles

def expand_inter_tiles(inter_tiles, expand_size):
    expanded_tiles = copy.deepcopy(inter_tiles)
    for i in range(len(expanded_tiles)):
        inter_tile = expanded_tiles[i]
        cur_inter_tile = [[inter_tile[0][0], inter_tile[0][1], inter_tile[0][2], inter_tile[0][3]]]
        cur_inter_tile[0][0] += expand_size
        expanded_tiles[i] = cur_inter_tile
    return expanded_tiles

def shrink_placed_tiles(placed_tiles, shrink_size):
    shrinked_tiles = []
    for placed_tile in placed_tiles:
        x, tile = placed_tile
        new_tile = list(copy.deepcopy(tile[0]))
        new_tile[0] -= shrink_size
        new_tile = tuple(new_tile)
        shrinked_tiles.append((x, [new_tile]))
    return shrinked_tiles

def export_placed_tiles(placed_tiles, output_file):
    # Determine the bounding width (maximum x-coordinate of the placed tiles plus their width)
    bounding_width = max(placed_x + w for placed_x, [(w, h, dx, dy)] in placed_tiles)

    with open(output_file, 'w') as f:
        # Write the bounding width to the file
        f.write(f"Bounding Width: {bounding_width}\n")

        # Write the placed tiles and their single part
        for placed_x, [(w, h, dx, dy)] in placed_tiles:
            f.write(f"{placed_x} {w} {h} {dx} {dy}\n")

    print(f"Placed tiles exported to: {output_file}")

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

def preplace_pack_with_c(excitations, separation, seam_lst):
    
    tiles = create_circuit_tile(excitations)
    # Find all inter/intra tiles
    inter_tiles, intra_tiles = find_inter_module_tiles(tiles, seam_lst)
    # Sort and pack inter_tiles
    inter_tiles = sorted(inter_tiles, key=lambda x: sum(h for w, h, _, _ in x), reverse=True)
    inter_tiles = expand_inter_tiles(inter_tiles, separation)
    c_directory = "../lib/tile_packing.exe"
    bounding_width, placed_tiles_lst = packing_with_c(inter_tiles,c_directory)
    # Seperate all inter_tiles by first expanding them by seperations and them shrink them to the original size
    moved_placed_tiles = shrink_placed_tiles(placed_tiles_lst, separation)
    print(moved_placed_tiles)
    filename = "../../moved_place_tiles.txt"
    export_placed_tiles(moved_placed_tiles, filename)
    # Export all intra(free) tiles
    filename = "../../test_tiles.txt"
    intra_tiles = sorted(intra_tiles, key=lambda x: sum(h for w, h, _, _ in x), reverse=False)
    # tiles = create_circuit_tile(excitations)
    export_tiles_to_file(intra_tiles, filename)
    # preplaced packing
    c_directory = "../lib/preplaced_tile_packing.exe"
    bounding_width, placed_tiles_lst = packing_with_c(intra_tiles,c_directory)
    
    result = '../../all_tiles.txt'
    bounding_width, placed_tiles_lst = read_packing_results(result)
    return bounding_width, placed_tiles_lst
