from tile_process import Tile, PlacedTile, pauli2idx
from qiskit.circuit import Parameter
import copy
import numpy as np
from qiskit import QuantumCircuit
from math import ceil
from zx_hopping import double_index, modular_parity_check, double_check, parity_check
import zx_hopping as ZX
import re

def zx_pauli2idx(pauli_string):
    pauli_string = re.findall(r'[A-Z]_\d+', pauli_string)
    gate_type = np.empty(len(pauli_string)//2, dtype = str)
    idx_lst = np.empty(len(pauli_string)//2, dtype = int)
    if len(pauli_string) == 4:
        for n in range(len(pauli_string)//2):
            pauli = pauli_string[n]
            match = re.match(r'([A-Z])_(\d+)', pauli)
            pauli_type, idx = match.groups()
            idx = int(idx)
            gate_type[n] = pauli_type
            idx_lst[n] = idx
        indices = np.argsort(idx_lst)
        gate_type = gate_type[indices]
        idx_lst = idx_lst[indices]

    elif len(pauli_string) == 6:
        for n in range(len(pauli_string)//2):
            pauli = pauli_string[n]
            match = re.match(r'([A-Z])_(\d+)', pauli)
            pauli_type, idx = match.groups()
            idx = int(idx)
            if pauli_type == "Y":
                idx_lst[0] = idx
                gate_type[0] = pauli_type
            elif pauli_type == "X":
                idx_lst[2] = idx
                gate_type[2] = pauli_type
            elif pauli_type == "I":
                idx_lst[1] = idx
                gate_type[1] = pauli_type

    elif len(pauli_string) == 8:
        for n in range(len(pauli_string)//2):
            pauli = pauli_string[n]
            match = re.match(r'([A-Z])_(\d+)', pauli)
            pauli_type, idx = match.groups()
            idx = int(idx)
            gate_type[n] = pauli_type
            idx_lst[n] = idx
    return gate_type, idx_lst

def create_circuit_tile(excitations):
    excitations = copy.deepcopy(excitations)
    tile_lst = []
    for u in range(len(excitations)):
        excitation = excitations[u]
        a,i = excitation
        if len(a) == 1:
            i1 = min([a[0], i[0]])
            i2 = max([a[0], i[0]])
            # single_tile = [[(i2-i1)*2, i2-i1, 0, i1]]
            pauli_lst = [f"Y_{i1}X_{i2}X_{i1}Y_{i2}"]
            if a[0] < i[0]:
                t_lst = [f"t_{u}"]
            else:
                t_lst = [f"-t_{u}"]
            for n in range(1):
                single_tile = Tile((i2-i1) * 2, i2 - i1, 0, i1)
                single_tile.pauli = pauli_lst[n]
                single_tile.t = t_lst[n]
                tile_lst.append(copy.deepcopy(single_tile))
        else:
            p,q = a
            k,m = i
            if set(a) & set(i) != set():
                j = list(set(a) & set(i))
                j = j[0]
                p = list(set(a) ^ set([j]))[0]
                q = list(set(i) ^ set([j]))[0]
                i1 = min([p,q])
                i2 = max([p,q])
                index1 = a.index(j)
                index2 = i.index(j)
                negative = False
                if index1 == index2:
                    negative = True
                pauli_lst = [f"I_{j}Y_{i1}X_{i2}I_{j}X_{i1}Y_{i2}", f"Y_{i1}X_{i2}X_{i1}Y_{i2}"]
                negative_lst = [f"-t_{u}", f"t_{u}"]
                postive_lst = [f"t_{u}", f"-t_{u}"]
                if negative:
                    if p < q:
                        t_lst = postive_lst
                    else:
                        t_lst = negative_lst
                else:
                    if p < q:
                        t_lst = negative_lst
                    else:
                        t_lst = postive_lst
                for n in range(2):
                    if j < i1:
                        tile = Tile((i2-i1)*2+2, i2-j, 0, j)
                    elif j > i2:
                        tile = Tile((i2-i1)*2+2, j-i1, 0, i1)
                    else:
                        tile = Tile((j-1-i1)*2+2+(i2-(j+1))*2, i2-i1, 0, i1)
                    tile.pauli = pauli_lst[n]

                    tile.t = t_lst[n]

                    tile_lst.append(copy.deepcopy(tile))
            else:
                index_lst = [p,q,k,m]
                index_lst.sort()
                i1,i2,i3,i4 = index_lst
                pauli_lst = [f"X_{i1}X_{i2}X_{i3}Y_{i4}X_{i1}X_{i2}Y_{i3}X_{i4}",\
                    f"Y_{i1}Y_{i2}Y_{i3}X_{i4}Y_{i1}Y_{i2}X_{i3}Y_{i4}",
                    f"Y_{i1}X_{i2}X_{i3}X_{i4}Y_{i1}X_{i2}Y_{i3}Y_{i4}",
                    f"X_{i1}Y_{i2}Y_{i3}Y_{i4}X_{i1}Y_{i2}X_{i3}X_{i4}"]
                # t_lst = [f"-t_{u}", f"-t_{u}", f"t_{u}", f"-t_{u}",
                # f"t_{u}",f"-t_{u}",f"t_{u}",f"t_{u}"]
                t_lst = []
                for i in range(4):
                    t_lst.append(f"t_{u}")
                for n in range(4):
                    pauli = pauli_lst[n]
                    
                    pauli = re.sub(r"_\d+", "", pauli)
                    mid = len(pauli) // 2
                    p1 = list(pauli[:mid])
                    p2 = list(pauli[mid:])

                    factor1 = double_index(p, q, k, m, p1)
                    factor2 = double_index(p, q, k, m, p2)

                    t1 = f"t_{u}" if factor1 == 1 else f"-t_{u}"
                    t2 = f"t_{u}" if factor2 == 1 else f"-t_{u}"
                    t = t1 + " " + t2
                    cur_tile = Tile((i2-i1)*2+(i4-i3)*2+2, i4-i1, 0, i1)
                    cur_tile.pauli = pauli_lst[n]
                    cur_tile.t = t
                    tile_lst.append(copy.deepcopy(cur_tile))
    return tile_lst

def tile2circuit(placed_tile_lst, N, seam = -1):
    params = []
    params_dict = {}
    qc = QuantumCircuit(N)
    sort_tile_lst = sorted(placed_tile_lst, key=lambda tile: tile.pos)
    for tile in sort_tile_lst:
        t = tile.t
        pair = t.split(" ")
        t_lst = []
        for t in pair:
            is_negative = t.startswith('-')
            t = t[1:] if is_negative else t
            if t not in params_dict:
                params_dict[t] = Parameter(t)
                params.append(params_dict[t])

            t_lst.append(-1 * params_dict[t] if is_negative else params_dict[t])
        
        pauli = tile.pauli
        gate_type, idx_lst = (zx_pauli2idx(pauli))
        if len(gate_type) == 2:
            i, j = idx_lst
            cur_t = t_lst[0]
            qc = ZX.single_hopping(qc, i, j, N, cur_t, seam)
        elif len(gate_type) == 3:
            cur_t = t_lst[0]
            i, j, k = idx_lst
            qc = ZX.controlled_pauli(qc, i, j, k, N, cur_t, seam)
        elif len(gate_type) == 4:
            i, j, k, m = idx_lst
            gate_type = "".join(gate_type)
            t1, t2 = t_lst
            qc = ZX.double_pauli(qc, i, j, k, m, N, t1, t2, gate_type, seam)
    return qc, params

def single_hopping_width(i, j, seam, N):
    if seam < i or seam >= j:
        width = ceil(np.log2(j - i))
    else:
        w1 = ceil(np.log2(seam - i))
        w2 = ceil(np.log2(j - seam))
        width = np.max([w1, w2])
    return width

def controlled_hopping_width(i, j, k, seam, N):
    
    qc = QuantumCircuit(N)
    
    if j < i:
        if seam == -1:
            upper_half = np.arange((k+i)//2, i-1, -1)
            lower_half = np.arange((k+i)//2 + 1, k + 1)
        else:
            upper_half = np.arange(seam, i-1, -1)
            lower_half = np.arange(seam + 1, k + 1)
        
        upper_half = np.append(upper_half, j)

        upper_half = upper_half.tolist()
        lower_half = lower_half.tolist()

        qc = parity_check(qc, upper_half, target=i)
        qc = parity_check(qc, lower_half, target=k)
        width = qc.depth()
    elif j > i and j < k:
        if seam == -1:
            upper_half = np.arange((k+i)//2, i-1, -1)
            lower_half = np.arange((k+i)//2 + 1, k + 1)
        else:
            upper_half = np.arange(seam, i-1, -1)
            lower_half = np.arange(seam + 1, k + 1)
        
        upper_half = upper_half[upper_half != j]
        lower_half = lower_half[lower_half != j]
    
        qc = modular_parity_check(qc, upper_half, seam)
        qc = modular_parity_check(qc, lower_half, seam)
    else:
        pass
    return 2*(qc.depth() + 1)

def find_tile_width(excitation, seam):
    a, i = excitation
    
    if len(a) == 1:
        i1 = min([a[0], i[0]])
        i2 = max([a[0], i[0]])
        width = single_hopping_width(i1, i2, seam)
    elif len(a) == 2:
        p,q = a
        k,m = i
        if set(a) & set(i) != set():
            j = list(set(a) & set(i))
            j = j[0]
            p,q = list(set(a) ^ set(i))
            i1 = min([p,q])
            i2 = max([p,q])
            pass

def create_zx_circuit_tile(excitations, seam):
    excitations = copy.deepcopy(excitations)
    N = max(x for excitation in excitations for pair in excitation for x in pair)

    tile_lst = []
    for u in range(len(excitations)):
        excitation = excitations[u]
        a,i = excitation
        if len(a) == 1:
            i1 = min([a[0], i[0]])
            i2 = max([a[0], i[0]])
            # single_tile = [[(i2-i1)*2, i2-i1, 0, i1]]
            pauli_lst = [f"Y_{i1}X_{i2}", f"X_{i1}Y_{i2}"]
            t_lst = [f"t_{u}", f"-t_{u}"]
            for n in range(2):
                single_tile = Tile(2*width, i2 - i1, 0, i1)
                single_tile.pauli = pauli_lst[n]
                single_tile.t = t_lst[n]
                tile_lst.append(copy.deepcopy(single_tile))
        else:
            p,q = a
            k,m = i
            if set(a) & set(i) != set():
                j = list(set(a) & set(i))
                j = j[0]
                p,q = list(set(a) ^ set(i))
                i1 = min([p,q])
                i2 = max([p,q])
                pauli_lst = [f"I_{j}Y_{i1}X_{i2}", f"I_{j}X_{i1}Y_{i2}", f"Y_{i1}X_{i2}", f"Y_{i1}X_{i2}"]
                t_lst = [f"-t_{u}", f"t_{u}", f"t_{u}", f"-t_{u}"]
                for n in range(2):
                    if j < i1:
                        tile1 = Tile((i2-i1)*2+2, i2-j, 0, j)
                        tile2 = Tile((i2-i1)*2, i2-i1, 0, i1)
                    elif j > i2:
                        tile1 = Tile((i2-i1)*2+2, j-i1, 0, i1)
                        tile2 = Tile((i2-i1)*2, i2-i1, 0, i1)
                    else:
                        tile1 = Tile((j-1-i1)*2+2+(i2-(j+1))*2, i2-i1, 0, i1)
                        tile2 = Tile((i2-i1)*2, i2-i1, 0, i1)
                    tile1.pauli = pauli_lst[n]
                    tile2.pauli = pauli_lst[n+2]

                    tile1.t = t_lst[n]
                    tile2.t = t_lst[n+2]

                    tile_lst.append(copy.deepcopy(tile1))
                    tile_lst.append(copy.deepcopy(tile2))
            else:
                index_lst = [p,q,k,m]
                index_lst.sort()
                i1,i2,i3,i4 = index_lst
                pauli_lst = [f"X_{i1}X_{i2}X_{i3}Y_{i4}", f"X_{i1}X_{i2}Y_{i3}X_{i4}",\
                    f"Y_{i1}Y_{i2}Y_{i3}X_{i4}", f"X_{i1}Y_{i2}Y_{i3}Y_{i4}",
                    f"Y_{i1}X_{i2}X_{i3}X_{i4}", f"Y_{i1}X_{i2}Y_{i3}Y_{i4}",
                    f"Y_{i1}Y_{i2}X_{i3}Y_{i4}", f"X_{i1}Y_{i2}X_{i3}X_{i4}"]
                raw_pauli = ["XXXY", "XXYX", "YYYX", "XYYY", "YXXX", "YXYY", "YYXY", "XYXX"]
                # t_lst = [f"-t_{u}", f"-t_{u}", f"t_{u}", f"-t_{u}",
                # f"t_{u}",f"-t_{u}",f"t_{u}",f"t_{u}"]
                t_lst = []
                for i in range(8):
                    pauli = raw_pauli[i]
                    factor = double_index(p, q, k, m, pauli)
                    if factor == 1:
                        t_lst.append(f"t_{u}")
                    else:
                        t_lst.append(f"-t_{u}")
                for n in range(8):
                    cur_tile = Tile((i2-i1)*2+(i4-i3)*2+2, i4-i1, 0, i1)
                    cur_tile.pauli = pauli_lst[n]
                    cur_tile.t = t_lst[n]
                    tile_lst.append(copy.deepcopy(cur_tile))
    return tile_lst