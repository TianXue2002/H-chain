import numpy as np
import sys
from qiskit import QuantumCircuit
import qiskit.quantum_info as qi
from IPython.display import display
from qiskit import transpile
import matplotlib.pyplot as plt
import re
from sympy.combinatorics import Permutation
from JW_circuit import *


def create_double_ladder_cnot(qc,i,j,k,m,t,N):
    for a in range(i,j):
        qc.cx(a, a+1)
    
    qc.cx(j, k)
    
    for b in range(k, m):
        qc.cx(b, b+1)
    
    qc.rz(t, m)
    
    for b in range(m, k,-1):
        qc.cx(b-1, b)

    qc.cx(j, k)

    for a in range(j,i,-1):
        qc.cx(a-1, a)

def pauli2idx(pauli_string):
    pauli_string = re.findall(r'[A-Z]_\d+', pauli_string)
    gate_type = np.empty(len(pauli_string), dtype = str)
    idx_lst = np.empty(len(pauli_string), dtype = int)
    if len(pauli_string) == 2:
        for n in range(len(pauli_string)):
            pauli = pauli_string[n]
            match = re.match(r'([A-Z])_(\d+)', pauli)
            pauli_type, idx = match.groups()
            idx = int(idx)
            gate_type[n] = pauli_type
            idx_lst[n] = idx
        indices = np.argsort(idx_lst)
        gate_type = gate_type[indices]
        idx_lst = idx_lst[indices]

    elif len(pauli_string) == 3:
        for n in range(len(pauli_string)):
            pauli = pauli_string[n]
            match = re.match(r'([A-Z])_(\d+)', pauli)
            pauli_type, idx = match.groups()
            idx = int(idx)
            if pauli_type == "X":
                idx_lst[0] = idx
                gate_type[0] = pauli_type
            elif pauli_type == "Y":
                idx_lst[2] = idx
                gate_type[2] = pauli_type
            elif pauli_type == "I":
                idx_lst[1] = idx
                gate_type[1] = pauli_type
        
        include = [0, 2]           # elements to sort
        # Sort only the selected indices
        order = np.argsort(idx_lst[include])
        gate_type[include] = gate_type[include][order]
        idx_lst[include] = idx_lst[include][order]

    elif len(pauli_string) == 4:
        for n in range(len(pauli_string)):
            pauli = pauli_string[n]
            match = re.match(r'([A-Z])_(\d+)', pauli)
            pauli_type, idx = match.groups()
            idx = int(idx)
            gate_type[n] = pauli_type
            idx_lst[n] = idx
        indices = np.argsort(idx_lst)
        gate_type = gate_type[indices]
        idx_lst = idx_lst[indices]
    return gate_type, idx_lst


def pauli_overhead(qc, gate_type, idx_lst, overhead_type = "head"):

    for i in range(len(gate_type)):
        pauli_type = gate_type[i]
        idx = idx_lst[i]
        if pauli_type == "X":
            qc.h(idx)
        elif pauli_type == "Y":
            if overhead_type == "head":
                qc.sdg(idx)
                qc.h(idx)
            elif overhead_type == "end":
                qc.h(idx)
                qc.s(idx)
            else:
                raise ValueError("invalid overhead type")
    return qc

def create_ladder_cnot(qc, i, j, N):
    for a in range(i,j):
        qc.cx(a, a+1)
    return None

def create_inverse_ladder_cnot(qc, i, j, N):
    for a in range(j,i,-1):
        qc.cx(a-1, a)
    return None   

def inter_control_pauli(qc, idx_lst ,N,t, gate_type):

    i,j,k = idx_lst

    pauli_overhead(qc, gate_type, idx_lst)
    
    create_ladder_cnot(qc, i, j-1, N)
    qc.cx(j-1, j+1)
    create_ladder_cnot(qc, j+1, k, N)
    qc.rz(-t/2, k)

    create_inverse_ladder_cnot(qc, j+1, k, N)
    qc.cx(j-1, j+1)
    create_inverse_ladder_cnot(qc, i, j-1, N)
    
    pauli_overhead(qc, gate_type, idx_lst, overhead_type="end")
    return qc


def upper_control_pauli(qc, idx_lst ,N,t, gate_type):
    
    i,j,k = idx_lst

    pauli_overhead(qc, gate_type, idx_lst)
    # Component 1
    qc.cx(j, i)
    create_ladder_cnot(qc, i, k, N)
    qc.rz(-t/2, k)
    create_inverse_ladder_cnot(qc, i, k, N)
    qc.cx(j, i)
    
    pauli_overhead(qc, gate_type, idx_lst, overhead_type="end")

    return qc


def lower_control_pauli(qc, idx_lst ,N,t, gate_type):

    i,j,k = idx_lst

    pauli_overhead(qc, gate_type, idx_lst)
    
    create_ladder_cnot(qc, i, k, N)
    qc.cx(k, j)
    qc.rz(t/2, j)
    qc.cx(k, j)
    create_inverse_ladder_cnot(qc, i, k, N)
    
    pauli_overhead(qc, gate_type, idx_lst, overhead_type="end")

    return qc

def controlled_pauli(qc, idx_lst ,N,t, pauli_string):
    if len(idx_lst) != 3:
        raise ValueError("invalid index for controlled pauli")
    i,j,k = idx_lst
    if j < i:
        return upper_control_pauli(qc, idx_lst, N, t, pauli_string)
    elif j > i and j < k:
        return inter_control_pauli(qc, idx_lst, N, t, pauli_string)
    elif j > k:
        return lower_control_pauli(qc, idx_lst, N, t, pauli_string)
    else:
        raise ValueError("Invalid index")
    
def double_pauli(qc, idx_lst, N, t, gate_sets):
    index = idx_lst
    i,j,k,m = idx_lst

    for a in range(4):
        cur_index = index[a]
        if gate_sets[a] == "X":
            qc.h(cur_index)
        else:
            qc.sdg(cur_index)
            qc.h(cur_index)
    
    create_double_ladder_cnot(qc, i, j, k, m, t, N)
    
    for a in range(4):
        cur_index = index[a]
        if gate_sets[a] == "X":
            qc.h(cur_index)
        else:
            qc.h(cur_index)
            qc.s(cur_index)
    return qc

def single_pauli(qc, idx_lst, N, t, gate_sets):
    i,j = idx_lst

    qc = pauli_overhead(qc, gate_sets, idx_lst)

    create_ladder_cnot(qc, i, j, N)
    qc.rz(t, j)
    create_inverse_ladder_cnot(qc, i, j, N)

    qc = pauli_overhead(qc, gate_sets, idx_lst, overhead_type="end")
    return qc

def double_index(i, j, k, m, pauli):
    factor = 1
    sign_lst = ["+", "+", "-", "-"]
    index = np.argsort([i,j,k,m])
    perm = Permutation(index)
    factor = -1 if perm.is_even else 1
    sign_lst = [sign_lst[idx] for idx in index]
    for n in range(4):
        cur_sign = sign_lst[n]
        cur_pauli = pauli[n]
        # sigma_z Q^+ = -Q^+
        if n % 2 == 0 and cur_sign == "+":
            factor *= -1
        if cur_pauli == "Y":
            if cur_sign == "+":
                factor *= -1j
            else:
                factor *= 1j
            
    factor = factor / 1j
    if factor.imag != 0:
        raise ValueError("factor must be a real number")
    factor = factor.real
    return factor