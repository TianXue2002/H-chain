import matplotlib.pyplot as plt
from tile_process import *
from joblib import Parallel, delayed
import threading
import subprocess


def packing_with_c(tiles, c_directory, ifreordered = True):
    print("Current Directory:", os.path.abspath("./lib/tile_packing.exe"))


    if ifreordered:
        print("sorted")
        sorted(tiles, key=lambda x: sum(w * h for w, h, _, _ in x), reverse=True)
    filename = "C:/Users/24835/Desktop/homework/uiuc/Covey/chem/H-chain/test_tiles.txt"
    export_tiles_to_file(tiles, filename)
    subprocess.run([c_directory, "output.txt"])
    filename = 'C:/Users/24835/Desktop/homework/uiuc/Covey/chem/H-chain/placed_tiles.txt'
    bounding_width, placed_tiles = read_placed_tiles(filename)
    return bounding_width, placed_tiles


def count_single_CNOT(i,j,N):
    count = []
    for i in range(i,j):
        count.append([(i,i+1), 4])
    return count

def count_double_CNOT(i,j,k,m,N):
    index_lst = [i,j,k,m]
    index_lst.sort()
    i,j,k,m = index_lst
    count = []
    for a in range(i,j):
        count.append([(a,a+1), 16])
    count.append([(j, k), 16])
    for b in range(k,m):
        count.append([(b, b+1), 16])
    return count

def count_controlled_CNOT(i,j,k,N):
    index_lst = [i,k]
    index_lst.sort()
    i,k = index_lst
    count = []
    if j < i:
        count.append([(j, i), 4])
        for a in range(i, k):
            count.append([(a, a+1), 8])
    elif j>k:
        count.append([(k,j), 4])
        for a in range(i, k):
            count.append([(a, a+1), 8])
    else:
        for a in range(i,j-1):
            count.append([(i, i+1), 8])
        count.append([(j-1, j+1), 4])
        for b in range(j-1, j+1):
            count.append([(b, b+1), 4])
        for b in range(j+1, k):
            count.append([(b, b+1), 8])
    return count

def count_gate(excitation, N):
    a, i = excitation
    if len(a) == 1:
        if a == i:
            print("single evolution")
        else:
            # print("single hopping")
            return count_single_CNOT(a[0],i[0],N)
        
    if len(a) == 2:
        a.sort()
        i.sort()
        p,q = a
        k,m = i
        if set(a) & set(i) != set():
            # print("controlled hopping")
            j = list(set(a) & set(i))
            j = j[0]
            p,q = list(set(a) ^ set(i))
            return count_controlled_CNOT(p, j, q, N)
        else:
            # print("double hopping")
            return count_double_CNOT(p,q,k,m,N)
            # print("excitation", p,q,k,m)
            # print(cur_count)
    return None

def plot_CNOT_dist(excitations):
    count = 0
    for n in range(len(excitations)):
        excitation = excitations[n]
        a, i = excitation
        if len(a) == 1:
            if a == i:
                print("single evolution")
            else:
                # print("single hopping")
                i1 = min([a[0], i[0]])
                i2 = max([a[0], i[0]])
                for _ in range(4):
                    plt.plot([count, count], [i1+0.5, i2+0.5], "r")
                    count += 1
        if len(a) == 2:
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
                    for _ in range(4):
                        plt.plot([count, count], [j+0.5, i1+0.5], "b")
                        plt.plot([count, count], [i1+0.5, i2+0.5], "r")
                        count = count + 1
                elif j > i2:
                    for _ in range(4):
                        plt.plot([count, count], [j+0.5, i2+0.5], "b")
                        plt.plot([count, count], [i1+0.5, i2+0.5], "r")
                        count = count + 1
                else:
                    for _ in range(4):
                        plt.plot([count, count], [i1+0.5, j-0.5], "r")
                        plt.plot([count, count], [j-0.5, j+1.5], "b")
                        plt.plot([count, count], [j+1.5, i2+0.5], "r")
                        count = count + 1
                for _ in range(4):
                    plt.plot([count, count], [i1+0.5,i2+0.5],"r")
                    count = count+1
            else:
                # print("double hopping")
                index_lst = [p,q,k,m]
                index_lst.sort()
                i1,i2,i3,i4 = index_lst
                for _ in range(16):
                    plt.plot([count,count],[i1+0.5,i2+0.5],'r')
                    plt.plot([count,count],[i2+0.5,i3+0.5],'b')
                    plt.plot([count,count],[i3+0.5,i4+0.5],'r')
                    count +=1
                # print("excitation", p,q,k,m)
                # print(cur_count)


def time_gate_with_C(excitations, N, epsilon, ifsorted = True, ratio=4):
    time = np.zeros(N)
    legend_handles = [
        mpatches.Patch(color='blue', label='inter-module gate time'),
        mpatches.Patch(color='red', label='intra-module gate time'),
    ]
    tiles = create_circuit_tile(excitations)

    # Initialize time
    tiles = create_circuit_tile(excitations)
    if ifsorted:
        print("sorted")
        tiles = sorted(tiles, key=lambda x: sum(w * h for w, h, _, _ in x), reverse=True)
    bounding_width, _ = packing_with_c(tiles)
    initial_time = bounding_width * 25
    time[0] = initial_time
    for seam in range(1,N):
        tiles = create_circuit_tile(excitations)
        inter_tile, intra_tile = split_grid(tiles, [seam])
        inter_tile = expand_tiles(inter_tile, ratio)
        tiles = inter_tile + intra_tile
        if sorted:
            tiles = sorted(tiles, key=lambda x: sum(w * h for w, h, _, _ in x), reverse=True)
        bounding_width, _ = packing_with_c(tiles)
        time[seam] = bounding_width * 25
    for i in range(N):
        plt.fill_betweenx([0, time[0]], i-0.5, i+0.5 , color = "red")
        if i != 0:
            plt.fill_betweenx([time[0], time[i]], i-0.5, i+0.5, color = "blue")

    plt.plot(time)
    plt.legend(handles=legend_handles)
    plt.xlabel("Position of the seam")
    plt.ylabel("Time (µs)")
    plt.title(f"epsilon = {epsilon}")



def time_gate(excitations, N):
    time = np.zeros(N)
    legend_handles = [
        mpatches.Patch(color='blue', label='inter-module gate time'),
        mpatches.Patch(color='red', label='intra-module gate time'),
    ]
    ratio = 4
    tiles = create_circuit_tile(excitations)

    # Function to process each seam in parallel
    def process_seam(seam, tiles, ratio, intra_module_gate):
        thread_id = threading.get_ident()  # Get the current thread ID
        print(f"Processing seam {seam} on thread {thread_id}")

        if seam == 0:
            initial_time = intra_module_gate * 25
            post_time = initial_time
            max_time = initial_time
            color_segments = [(0, initial_time, 'red')]
        else:
            inter_tiles, intra_tiles = split_grid(tiles, [seam])
            initial_packer = TilePacker(tiles)

            # Adjust inter_tiles
            for i in range(len(inter_tiles)):
                inter_tiles[i][0] = inter_tiles[i][0].copy()
                inter_tiles[i][0][0] += 2 * (ratio - 1)

            post_tiles = inter_tiles + intra_tiles
            post_packer = TilePacker(post_tiles)

            initial_gates, _, _, _ = initial_packer.pack_tiles()
            post_gates, _, _, _ = post_packer.pack_tiles()

            initial_time = initial_gates * 25
            post_time = post_gates * 25
            max_time = max(initial_time, post_time)

            color_segments = [
                (0, initial_time, 'red'),
                (initial_time, max_time, 'blue')
            ]
        print(f"END Processing seam {seam} on thread {thread_id}")
        return seam, max_time, color_segments

    # Initialize intra-module gate time for seam 0
    intra_packer = TilePacker(tiles)
    intra_module_gate, _, _, _ = intra_packer.pack_tiles()

    # Parallel processing for all seams
    results = Parallel(n_jobs=-1, backend='threading')(
        delayed(process_seam)(seam, tiles, ratio, intra_module_gate) for seam in range(N)
    )

    # Collect results
    for seam, max_time, color_segments in results:
        time[seam] = max_time
        for start, end, color in color_segments:
            plt.fill_betweenx([start, end], seam - 1 / 2, seam + 1 / 2, color=color)

    plt.plot(time)
    plt.legend(handles=legend_handles)
    plt.xlabel("Position of the seam")
    plt.ylabel("Time (µs)")

def plot_uop(uop, all_g, epsilon_min, seam_lst, epsilon_lst, f_orbs, total = True, ifinter = True, ifintra = True):
    e_min = np.log10(epsilon_min)//1
    print(e_min)
    nbins = len(epsilon_lst) - 1
    intra_double = np.zeros(nbins)
    inter_double = np.zeros(nbins)
    intra_control = np.zeros(nbins)
    inter_control = np.zeros(nbins)
    intra_single = np.zeros(nbins)
    inter_single = np.zeros(nbins)
    a_index = uop.a_idxs
    i_index = uop.i_idxs
    for epsilon_index in range(len(epsilon_lst) - 1):
        epsilon_min = epsilon_lst[epsilon_index+1]
        if total:
            epsilon_max = np.inf
        else:
            epsilon_max = epsilon_lst[epsilon_index]
        for [gradient, i] in all_g:
            gradient = abs(gradient)
            if gradient > epsilon_min and gradient < epsilon_max:
                cur_index = epsilon_index
                cur_a = a_index[i].copy()
                cur_i = i_index[i].copy()
                cur_excitation = [[cur_a, cur_i]]
                cur_excitation = orbital_reordering(cur_excitation,f_orbs)
                cur_a, cur_i = cur_excitation[0]
                # print(cur_a, cur_i)
                if len(cur_a) == 1:
                    if cur_a == cur_i:
                        print("single evolution")
                    else:
                        # print("single hopping")
                        i1 = min([cur_a[0], cur_i[0]])
                        i2 = max([cur_a[0], cur_i[0]])
                        if (i1 < seam_lst[0] and i2>=seam_lst[0]) or (i1 < seam_lst[1] and i2>=seam_lst[1]):
                            inter_single[cur_index] += 1
                        else:
                            intra_single[cur_index] += 1
                if len(cur_a) == 2:
                    cur_a.sort()
                    cur_i.sort()
                    p,q = cur_a
                    k,m = cur_i
                    if set(cur_a) & set(cur_i) != set():
                        j = list(set(cur_a) & set(cur_i))
                        j = j[0]
                        p,q = list(set(cur_a) ^ set(cur_i))
                        i1 = min([p,q,j])
                        i2 = max([p,q,j])
                        if (i1 < seam_lst[0] and i2>=seam_lst[0]) or (i1 < seam_lst[1] and i2>=seam_lst[1]):
                            inter_control[cur_index] += 1
                        else:
                            intra_control[cur_index] += 1
                    else:
                        index_lst = [p,q,k,m]
                        index_lst.sort()
                        i1,i2,i3,i4 = index_lst
                        if (i1 < seam_lst[0] and i4>=seam_lst[0]) or (i1 < seam_lst[1] and i4>=seam_lst[1]):
                            inter_double[cur_index] += 1
                        else:
                            intra_double[cur_index] += 1
    colors = ["red", "blue", "yellow", "green", "pink", "cyan"]
    for i in range(nbins):
        start = 0
        if ifinter:
            # Plot inter hopping
            plt.fill_betweenx([start, start+inter_double[i]], np.log10(epsilon_lst[i]),np.log10(epsilon_lst[i+1]), color=colors[0])
            start += inter_double[i]
            
            plt.fill_betweenx([start, start+inter_control[i]], np.log10(epsilon_lst[i]),np.log10(epsilon_lst[i+1]), color=colors[1])
            start += inter_control[i]

            plt.fill_betweenx([start, start+inter_single[i]], np.log10(epsilon_lst[i]),np.log10(epsilon_lst[i+1]), color=colors[2])
        if ifintra:
            # Intra hopping
            plt.fill_betweenx([start, start+intra_double[i]], np.log10(epsilon_lst[i]),np.log10(epsilon_lst[i+1]), color=colors[3])
            start += intra_double[i]

            plt.fill_betweenx([start, start+intra_control[i]], np.log10(epsilon_lst[i]),np.log10(epsilon_lst[i+1]), color=colors[4])
            start += intra_control[i]
            if intra_single[i]!=0:
                plt.fill_betweenx([start, start+intra_single[i]], np.log10(epsilon_lst[i]),np.log10(epsilon_lst[i+1]), color=colors[5])
                start += intra_single[i]

    if not ifintra:
        legend_handles = [
        mpatches.Patch(color=colors[0], label='inter double'),
        mpatches.Patch(color=colors[1], label='inter control'),
        mpatches.Patch(color=colors[2], label='inter single'),
    ]
    elif not ifinter:
        legend_handles = [
        mpatches.Patch(color=colors[3], label='intra double'),
        mpatches.Patch(color=colors[4], label='intra control'),
        mpatches.Patch(color=colors[5], label='intra single'),
    ]
    else:
        legend_handles = [
            mpatches.Patch(color=colors[0], label='inter double'),
            mpatches.Patch(color=colors[1], label='inter control'),
            mpatches.Patch(color=colors[2], label='inter single'),
            mpatches.Patch(color=colors[3], label='intra double'),
            mpatches.Patch(color=colors[4], label='intra control'),
            mpatches.Patch(color=colors[5], label='intra single'),
        ]
    if total:
        if not ifintra:
            plt.title(r"total number of inter-module excitations above $\epsilon$")
        elif not ifinter:
            plt.title(r"total number of intra-module excitations above $\epsilon$")
        else:
            plt.title(r"total number of excitations above $\epsilon$")
    else:
        if not ifintra:
            plt.title(r"inter-module excitations around $\epsilon$")
        elif not ifinter:
            plt.title(r"intra-module excitations around $\epsilon$")
        else:
            plt.title(r"excitations around $\epsilon$")

    return inter_single, intra_single, inter_control, intra_control, inter_double, intra_double

    