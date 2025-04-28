import matplotlib.pyplot as plt
import numpy as np
import qiskit.qpy as qpy
import pickle
import json
import matplotlib.patches as mpatches
from numba import njit
from numba.typed import List
import matplotlib.patches as patches
import threading
import subprocess
import os
import copy



def to_numba_typed_list(jagged_list):
    """Convert a Python list of lists of lists (jagged array) to a Numba-typed list."""
    numba_list = List()
    for sublist in jagged_list:
        typed_sublist = List()
        for inner_list in sublist:
            typed_sublist.append(List(inner_list))
        numba_list.append(typed_sublist)
    return numba_list

def create_excitation(uop, all_g, epsilon):
    excitations = []
    a_index = uop.a_idxs
    i_index = uop.i_idxs
    for [gradient, i] in all_g:
        gradient = abs(gradient)
        if gradient > epsilon:
            cur_a = a_index[i].copy()
            cur_i = i_index[i].copy()
            cur_excitation = [cur_a, cur_i]
            excitations.append(cur_excitation)
    return excitations

def orbital_reordering(excitations, f_orbs):
    fragment = np.array(f_orbs)
    fragment = 2*fragment
    n = f_orbs[0]
    N = 2*sum(f_orbs)
    for i in range(1,np.size(fragment)):
        fragment[i] += fragment[i-1]
    for excitation in excitations:
        for pair in excitation:
            for i in range(len(pair)):
                if pair[i]<sum(f_orbs):
                    pair[i] = (pair[i]//n)*2*n + pair[i] % n
                else:
                    pair[i] = ((pair[i]-sum(f_orbs))//n)*2*n + pair[i] % n + n
    return excitations

def create_circuit_tile(excitations):
    tile_lst = []
    for excitation in excitations:
        a,i = excitation
        if len(a) == 1:
            i1 = min([a[0], i[0]])
            i2 = max([a[0], i[0]])
            single_tile = [[(i2-i1)*2, i2-i1, 0, i1]]
            for _ in range(2):
                tile_lst.append(copy.deepcopy(single_tile))
        else:
            a.sort()
            i.sort()
            p,q = a
            k,m = i
            if set(a) & set(i) != set():
                j = list(set(a) & set(i))
                j = j[0]
                p,q = list(set(a) ^ set(i))
                i1 = min([p,q])
                i2 = max([p,q])
                if j < i1:
                    tile1 = [[(i2-i1)*2+2, i2-j, 0, j]]
                    tile2 = [[(i2-i1)*2, i2-i1, 0, i1]]
                elif j > i2:
                    tile1 = [[(i2-i1)*2+2, j-i1, 0, i1]]
                    tile2 = [[(i2-i1)*2, i2-i1, 0, i1]]
                else:
                    tile1 = [[(j-1-i1)*2+2+(i2-(j+1))*2, i2-i1, 0, i1]]
                    tile2 = [[(i2-i1)*2, i2-i1, 0, i1]]
                for _ in range(2):
                        tile_lst.append(copy.deepcopy(tile1))
                for _ in range(2):
                    tile_lst.append(copy.deepcopy(tile2))
            else:
                index_lst = [p,q,k,m]
                index_lst.sort()
                i1,i2,i3,i4 = index_lst
                cur_tile = [[(i2-i1)*2+(i4-i3)*2+2, i4-i1, 0, i1]]
                for _ in range(8):
                    tile_lst.append(copy.deepcopy(cur_tile))
    return tile_lst

def split_grid(tile_lst, seam_lst, twoCut = False):
    if twoCut:
        inter_tile = [[],[]]
        intra_tile = [[],[],[]]
        for tile in tile_lst:
            w,h,x,y = tile[0]
            put = False
            for i in range(len(seam_lst)):
                seam = seam_lst[i]
                if y < seam and y+h >= seam:
                    inter_tile[i].append(copy.deepcopy(tile))
                    put = True
            if not put:
                if y+h < seam_lst[0]:
                    intra_tile[0].append(copy.deepcopy(tile))
                elif y>=seam_lst[1]:
                    intra_tile[-1].append(copy.deepcopy(tile))
                else:
                    intra_tile[1].append(copy.deepcopy(tile))
    else:
        inter_tile = []
        intra_tile = []
        for tile in tile_lst:
            w,h,x,y = tile[0]
            put = False
            for seam in seam_lst:
                if y < seam and y+h >= seam:
                    inter_tile.append(tile.copy())
                    put = True
            if not put:
                intra_tile.append(tile.copy())
    return inter_tile, intra_tile


def expand_tiles(inter_tiles, ratio):
    for i in range(len(inter_tiles)):
        inter_tiles[i][0] = inter_tiles[i][0].copy()
        inter_tiles[i][0][0] += 2 * (ratio - 1)
    return inter_tiles



def process_tiles(tiles, ratio, seam_lst, ifsorted = False):
    inter_tiles_lst, intra_tiles_lst = split_grid(tiles, seam_lst,twoCut=True)
    for inter_tiles in inter_tiles_lst:
        for i in range(len(inter_tiles)):
            inter_tiles[i][0] = inter_tiles[i][0].copy()
            inter_tiles[i][0][0] += int(2 * (ratio - 1))

    post_tiles = []
    intra_tiles_up = sorted(intra_tiles_lst[2], key = lambda tile: tile[0][3])
    intra_tiles_mid = sorted(intra_tiles_lst[1], key = lambda tile: ((tile[0][3]+tile[0][1])*tile[0][3]), reverse=True)
    intra_tiles_down = sorted(intra_tiles_lst[0], key = lambda tile: (tile[0][3]+tile[0][1], tile[0][-1]))

    post_tiles = intra_tiles_up + intra_tiles_mid + intra_tiles_down

    inter_tiles_down = sorted(inter_tiles_lst[0], key = lambda tile: (tile[0][1]+tile[0][3], tile[0][1]), reverse=True)
    inter_tiles_up = sorted(inter_tiles_lst[1], key = lambda tile: (tile[0][1],tile[0][0]))
    if len(post_tiles) < len(inter_tiles_down) + len(inter_tiles_up):
        print("hi")
        post_tiles = inter_tiles_up + inter_tiles_down + post_tiles
    else:
        post_tiles = post_tiles + inter_tiles_down + inter_tiles_up    
    print(sum(tile[0][0] for tile in post_tiles))
    print(sum(tile[0][0] for tile in inter_tiles_up) + sum(tile[0][0] for tile in inter_tiles_down))
    if ifsorted:
        post_tiles = sorted(post_tiles, key=lambda x: sum(w * h for w, h, _, _ in x), reverse=True)
    return post_tiles

def tile_expanding(k, ratio_lst, tiles, seam_lst, initial_time, twocut = False):

    thread_id = threading.get_ident()  # Get the current thread ID
    print(f"Running job {k} on thread {thread_id}")
    ratio = int(ratio_lst[k])

    if not twocut:
        inter_tiles, intra_tiles = split_grid(tiles, seam_lst)
        
        for i in range(len(inter_tiles)):
            inter_tiles[i][0] = inter_tiles[i][0].copy()
            inter_tiles[i][0][0] += 2 * (ratio - 1)

        post_tiles = inter_tiles + intra_tiles
        post_packer = TilePacker(post_tiles)
    else:
        post_tiles = process_tiles(tiles, ratio, seam_lst)
        post_packer = TilePacker(post_tiles, twoCut=True)
    post_gates, _, _, post_grid = post_packer.pack_tiles()
    post_time = post_gates * 25
    print(f"END job {k} on thread {thread_id}")
    return initial_time, post_time

def export_tiles_to_file(tiles, filename):
    with open(filename, "w") as f:
        for tile in tiles:
            # Write the number of parts for this tile
            f.write(f"{len(tile)}\n")
            for part in tile:
                # Write each part's details: w h dx dy
                f.write(f"{part[0]} {part[1]} {part[2]} {part[3]}\n")
    print(f"Tiles successfully exported to {filename}")

def export_inter_intra(tiles, filename, seam_lst):
    with open(filename, "w") as f:
        for tile in tiles:
            # Write the number of parts for this tile
            f.write(f"{len(tile)}\n")
            for part in tile:
                w,h,x,y = tile[0]
                for i in range(len(seam_lst)):
                    seam = seam_lst[i]
                    if y < seam and y+h >= seam:
                        f.write(f"interTile {part[0]} {part[1]} {part[2]} {part[3]}\n")
                        inter = True
                if not inter:
                    f.write(f"intraTile {part[0]} {part[1]} {part[2]} {part[3]}\n")
                # Write each part's details: w h dx dy
                f.write(f"{part[0]} {part[1]} {part[2]} {part[3]}\n")
    print(f"Tiles successfully exported to {filename}")

def read_placed_tiles(filename):
    placed_tiles = []
    bounding_width = 0

    try:
        with open(filename, 'r') as file:
            # Read the bounding width
            first_line = file.readline().strip()
            if first_line.startswith("Bounding Width:"):
                bounding_width = int(first_line.split(":")[1].strip())
            else:
                print("Error: Invalid bounding width format.")
                return []

            # Read the placed tiles data
            for line in file:
                line = line.strip()
                if line:
                    data = list(map(int, line.split()))
                    x_position = data[0]
                    parts = []
                    # Each tile part consists of 4 values: width, height, offsetX, offsetY
                    for i in range(1, len(data), 4):
                        width = data[i]
                        height = data[i + 1]
                        offsetX = data[i + 2]
                        offsetY = data[i + 3]
                        parts.append((width, height, offsetX, offsetY))
                    placed_tiles.append((x_position, parts))

        print(f"Bounding width: {bounding_width}")

    except Exception as e:
        print(f"Error reading the file: {e}")

    return bounding_width, placed_tiles

class TilePacker:
    def __init__(self, *args):
        # Sort tiles by area once during initialization
        if len(args) <= 2:
            print("Construct based on unplaced tiles")
            if len(args) == 2:
                tiles = args[0]
                twoCut = args[1]
            else:
                tiles = args[0]
                twoCut = False
            self.tiles = tiles
            if not twoCut:
                self.tiles = sorted(tiles, key=lambda x: sum(w * h for w, h, _, _ in x), reverse=True)
            self.placed_tiles = []
            self.bounding_width = 0
            self.bounding_height = max(dy + h for tile in tiles for _, h, _, dy in tile)
        elif len(args) == 3:
            print("Construct based on placed tiles")
            placed_tiles = args[0]
            bounding_width = args[1]
            bounding_height = args[2]
            self.placed_tiles = placed_tiles
            self.bounding_width = bounding_width
            self.bounding_height = bounding_height
        
    def fits(self, x, tile, grid):
        """Check if a composite tile fits horizontally at position x."""
        for w, h, dx, dy in tile:
            # Check if it fits within the grid width
            if x + dx + w > grid.shape[1]:
                return False
            # Check if space is occupied in the grid (optimized check)
            if np.any(grid[dy:dy + h, x + dx:x + dx + w] == 1):
                return False
        return True

    def place_tile(self, tile, grid):
        """Find the best position to place a composite tile horizontally."""
        for x in range(grid.shape[1]):
            if self.fits(x, tile, grid):
                # Place the tile in the grid
                for w, h, dx, dy in tile:
                    grid[dy:dy + h, x + dx:x + dx + w] = 1
                return x  # Return x position where the tile is placed
        return -1  # Return -1 if the tile cannot be placed

    def pack_tiles(self):
        """Pack the tiles into a grid and return the bounding box dimensions."""
        max_width = sum(max(w + dx for w, _, dx, _ in tile) for tile in self.tiles)
        grid = np.zeros((self.bounding_height, max_width), dtype=int)
        count = 0

        # Precompute positions where each tile could fit
        fit_positions_cache = {}

        for tile in self.tiles:
            x_position = self.place_tile(tile, grid)
            if x_position == -1:
                print("Error: Tile doesn't fit, increase grid size.")
                break
            # Add the tile to placed tiles
            self.placed_tiles.append((x_position, tile))
            # Update bounding width
            self.bounding_width = max(self.bounding_width, x_position + max(dx + w for w, _, dx, _ in tile))

        return self.bounding_width, self.bounding_height, self.placed_tiles, grid

    def draw_packing(self, grid, seam_lst, epsilon, intra_color="tomato", inter_color="cyan", edge=False):
        """
        Draws the placement of tiles with color, boundaries, and sets the plot limits 
        to the min_x and max_x of the placed tiles.

        Args:
            grid: The grid containing the tile placement.
            seam_lst: List of seam positions.
            epsilon: Parameter for the plot title.
            intra_color: Color for intra-region tiles.
            inter_color: Color for inter-region tiles.
            edge: Whether to draw tile boundaries.
        """
        fig, ax = plt.subplots(figsize=(12, 8))
        ax.set_aspect('auto')

        # Initialize variables to track the min_x and max_x of placed tiles
        min_x = float('inf')
        max_x = float('-inf')

        # Draw each tile
        for idx, (tile_x, tile) in enumerate(self.placed_tiles):
            for w, h, dx, dy in tile:
                tile_left = tile_x + dx
                tile_right = tile_left + w

                # Update min_x and max_x based on tile positions
                min_x = min(min_x, tile_left)
                max_x = max(max_x, tile_right)

                # Draw tiles with boundaries
                if edge:
                    rect = patches.Rectangle((tile_left, dy), w, h, facecolor=intra_color, edgecolor="black", linewidth=1)
                else:
                    rect = patches.Rectangle((tile_left, dy), w, h, facecolor=intra_color)

                # Change color for inter-region tiles
                for seam in seam_lst:
                    if dy < seam and dy + h >= seam:
                        if edge:
                            rect = patches.Rectangle((tile_left, dy), w, h, facecolor=inter_color, edgecolor="black", linewidth=1)
                        else:
                            rect = patches.Rectangle((tile_left, dy), w, h, facecolor=inter_color)
                
                ax.add_patch(rect)

        # Set the plot limits based on the min_x and max_x of placed tiles
        margin_x = (max_x - min_x) * 0.05  # Add 5% margin to the width
        margin_y = self.bounding_height * 0.05  # Add 5% margin to the height

        ax.set_xlim(min_x, max_x)
        ax.set_ylim(0, self.bounding_height)

        # Hide axis ticks
        ax.set_xticks([])
        ax.set_yticks([])

        # Draw seams
        for seam in seam_lst:
            plt.axhline(seam - 0.5, color="purple", linewidth=2)

        plt.title(f"circuit depth = {self.bounding_width}, epsilon = {epsilon}")
        plt.show()
