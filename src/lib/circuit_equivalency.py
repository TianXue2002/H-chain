import re

from plotting import *
from readings import *
from tile_process import *
# from double_packing import *
from JW_circuit import *
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter

def pauli2circuit(qc, pauli):
    pauli_string = re.findall(r'[A-Z]_\d+', pauli)
    if len(pauli_string) == 2:
        hopping_type = "single"
    elif len(pauli_string) == 3:
        hopping_type = "control"
    elif len(pauli_string) == 4:
        hopping_type = "double"
    else:
        raise ValueError("Invalid hopping type of a pauli string")
    
    

def tile2circuit(placed_tile_lst, N):
    params = []
    params_dict = {}
    qc = QuantumCircuit(N)
    sort_tile_lst = sorted(placed_tile_lst, key=lambda tile: tile.pos)
    for tile in sort_tile_lst:
        t = tile.t
        is_negative = t.startswith('-')
        t = t[1:] if is_negative else t

        if t not in params_dict:
            params_dict[t] = Parameter(t)
            params.append(params_dict[t])

        cur_t = -1 * params_dict[t] if is_negative else params_dict[t]
        
        pauli = tile.pauli
        gate_type, idx_lst = (pauli2idx(pauli))
        if len(gate_type) == 2:
            qc = single_pauli(qc, idx_lst, N, cur_t, gate_type)
        elif len(gate_type) == 3:
            qc = controlled_pauli(qc, idx_lst, N, cur_t, gate_type)
        elif len(gate_type) == 4:
            qc = double_pauli(qc, idx_lst, N, cur_t, gate_type)
    return qc, params
