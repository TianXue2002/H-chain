from qiskit import QuantumCircuit
import numpy as np
from toolkit import *
from sympy.combinatorics import Permutation


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
        print(pauli)
        print(i, j, k, m)
        print(factor.imag)
        raise ValueError("factor must be a real number")
    factor = factor.real
    return factor

def single_hopping(qc: QuantumCircuit,
                   i: int,
                   j: int,
                   N: int,
                   t: float,
                   seam = -1):
    # prehead
    i1 = min([i, j])
    i2 = max([i, j])
    qc.h(i)
    qc.h(j)
    if seam == -1 or seam < i1 or seam >= i2:
        upper_half = list(range(i1, (i1+i2)//2 + 1))
        lower_half = list(range((i1+i2)//2 + 1, i2 + 1))
    else:
        upper_half = list(range(i1, seam + 1))
        lower_half = list(range(seam + 1, i2 + 1))

    qc = parity_check(qc, upper_half, target=i1)
    qc = parity_check(qc, lower_half, target=i2)

    qc.rz(np.pi/2, i)
    qc.h(i)
    qc.rz(np.pi/2, j)

    qc.cx(i, j)
    qc.rx(-t/2, i)
    qc.rz(t/2, j)
    qc.cx(i, j)

    qc.h(i)
    qc.rz(-np.pi/2, i)
    qc.rz(-np.pi/2, j)

    qc = parity_check_inverse(qc, upper_half, target=i1)
    qc = parity_check_inverse(qc, lower_half, target=i2)
    
    qc.h(i)
    qc.h(j)

    return qc


def double_check(qc,
                 i: int,
                 j: int,
                 k: int,
                 m: int,
                 seam):
    if_target = False
    if seam < i or seam >= m or seam == j:
        upper_half = list(range(i, j + 1))
        lower_half = list(range(k + 1, m+1))
        target_up = j
    elif seam == k:
        upper_half = list(range(i, j + 1)) + [k]
        lower_half = list(range(k + 1, m+1))
        qc = parity_check(qc, upper_half, target=k)
        qc = parity_check(qc, lower_half, target=m)
        return qc
    else:
        if seam < k:
            if j < seam:
                upper_half = list(range(i, j + 1))
                # lower_half = list(range(seam + 1, k)) + list(range(k + 1, m + 1))
                lower_half = list(range(k + 1, m + 1))
                target_up = j
            else:
                upper_half = list(range(i, seam+1))
                lower_half = list(range(seam + 1, j+1)) + list(range(k + 1, m + 1))
                target_up = seam
        else:
            upper_half = list(range(i, j+1)) + list(range(k + 1, seam + 1))
            lower_half = list(range(seam + 1, m + 1))
            target_up = seam
        if_target = True
    # print(upper_half, lower_half)
    qc = parity_check(qc, upper_half, target=target_up)
    qc = parity_check(qc, lower_half, target=m)
    qc.cx(target_up, k)

    # if if_target:
    #     if len(upper_half) != 0:
    #         qc.cx(upper_half[-1], k)
    #     if len(lower_half) != 0:
    #         qc.cx(lower_half[-1], m)

def double_check_inv(qc,
                 i: int,
                 j: int,
                 k: int,
                 m: int,
                 seam):
    if_target = False
    if seam < i or seam >= m or seam == j:
        upper_half = list(range(i, j + 1))
        lower_half = list(range(k + 1, m+1))
        target_up = j
    elif seam == k:
        upper_half = list(range(i, j + 1)) + [k]
        lower_half = list(range(k + 1, m+1))
        qc = parity_check_inverse(qc, upper_half, target=k)
        qc = parity_check_inverse(qc, lower_half, target=m)
        return qc
    else:
        if seam < k:
            if j < seam:
                upper_half = list(range(i, j + 1))
                # lower_half = list(range(seam + 1, k)) + list(range(k + 1, m + 1))
                lower_half = list(range(k + 1, m + 1))
                target_up = j
            else:
                upper_half = list(range(i, seam+1))
                lower_half = list(range(seam + 1, j+1)) + list(range(k + 1, m + 1))
                target_up = seam
        else:
            upper_half = list(range(i, j+1)) + list(range(k + 1, seam + 1))
            lower_half = list(range(seam + 1, m + 1))
            target_up = seam

    # if if_target:
    #     if len(upper_half) != 0:
    #         qc.cx(upper_half[-1], k)
    #     if len(lower_half) != 0:
    #         qc.cx(lower_half[-1], m)
    qc.cx(target_up, k)
    qc = parity_check_inverse(qc, upper_half, target=target_up)
    qc = parity_check_inverse(qc, lower_half, target=m)

    

def double_hopping1(qc: QuantumCircuit, 
                    i: int,
                    j: int,
                    k: int,
                    m: int,
                    N: int,
                    t1: int,
                    t2: int,
                    seam = -1):
    """
    XXXY -t and XXYX -t
    """

    index = [i,j,k,m]
    index.sort()
    i,j,k,m = index

    qc.h(i)
    qc.h(j)
    qc.h(k)
    qc.h(m)

    double_check(qc, i, j, k, m, seam)
    
    qc.rz(np.pi/2, k)
    qc.rz(np.pi/2, m)

    qc.h(m)
    qc.cx(k, m)
    qc.rx(t2, k)
    qc.rz(t1, m)
    qc.cx(k, m)
    qc.h(m)

    qc.rz(-np.pi/2, k)
    qc.rz(-np.pi/2, m)

    double_check_inv(qc, i, j, k, m, seam)

    qc.h(i)
    qc.h(j)
    qc.h(k)
    qc.h(m)
    return qc

def double_hopping2(qc: QuantumCircuit, 
                    i: int,
                    j: int,
                    k: int,
                    m: int,
                    N: int,
                    t1: int,
                    t2: int,
                    seam = -1):
    """
    YYYX t and YYXY t
    """

    index = [i,j,k,m]
    index.sort()
    i,j,k,m = index

    qc.rx(np.pi/2, i)
    qc.rx(np.pi/2, j)
    qc.h(k)
    qc.h(m)

    double_check(qc, i, j, k, m, seam)
    
    qc.rz(np.pi/2, k)
    qc.rz(np.pi/2, m)
    qc.h(k)

    qc.cx(k, m)
    qc.rx(t2, k)
    qc.rz(t1, m)
    qc.cx(k, m)

    qc.h(k)
    qc.rz(-np.pi/2, k)
    qc.rz(-np.pi/2, m) 

    double_check_inv(qc, i, j, k, m, seam)

    qc.rx(-np.pi/2, i)
    qc.rx(-np.pi/2, j)
    qc.h(k)
    qc.h(m)
    return qc

def double_hopping3(qc: QuantumCircuit, 
                    i: int,
                    j: int,
                    k: int,
                    m: int,
                    N: int,
                    t1: int,
                    t2: int,
                    seam = -1):
    """
    YXXX t and YXYY -t
    """

    index = [i,j,k,m]
    index.sort()
    i,j,k,m = index

    qc.rx(np.pi/2, i)
    qc.h(j)
    qc.h(k)
    qc.h(m)

    double_check(qc, i, j, k, m, seam)
    
    qc.rz(np.pi/2, k)
    qc.rz(np.pi/2, m)

    qc.cx(k, m)
    qc.rx(t2, k)
    qc.rz(t1, m)
    qc.cx(k, m)

    qc.rz(-np.pi/2, k)
    qc.rz(-np.pi/2, m) 

    double_check_inv(qc, i, j, k, m, seam)

    qc.rx(-np.pi/2, i)
    qc.h(j)
    qc.h(k)
    qc.h(m)
    return qc

def double_hopping4(qc: QuantumCircuit, 
                    i: int,
                    j: int,
                    k: int,
                    m: int,
                    N: int,
                    t1: int,
                    t2: int,
                    seam = -1):
    """
    XYYY -t and XYXX t
    """

    index = [i,j,k,m]
    index.sort()
    i,j,k,m = index

    qc.h(i)
    qc.rx(np.pi/2, j)
    qc.h(k)
    qc.h(m)

    double_check(qc, i, j, k, m, seam)
    
    qc.rz(np.pi/2, k)
    qc.rz(np.pi/2, m)

    qc.cx(k, m)
    qc.rx(t1, k)
    qc.rz(t2, m)
    qc.cx(k, m)

    qc.rz(-np.pi/2, k)
    qc.rz(-np.pi/2, m) 

    double_check_inv(qc, i, j, k, m, seam)

    qc.h(i)
    qc.rx(-np.pi/2, j)
    qc.h(k)
    qc.h(m)
    return qc


def double_pauli(qc, i, j, k, m, N, t1, t2, pauli, seam):
    idx_lst = [i,j,k,m]
    idx_lst.sort()
    i,j,k,m = idx_lst
    if pauli == "XXXY":
        qc = double_hopping1(qc, i, j, k, m, N, t1, t2, seam=seam)
    elif pauli == "YYYX":
        qc = double_hopping2(qc, i, j, k, m, N, t1, t2, seam=seam)
    elif pauli == "YXXX":
        qc = double_hopping3(qc, i, j, k, m, N, t1, t2, seam=seam)
    elif pauli == "XYYY":
        qc = double_hopping4(qc, i, j, k, m, N, t1, t2, seam=seam)
    return qc

def mid_controlled_pauli(qc: QuantumCircuit,
                   i: int,
                   j: int,
                   k:int,
                   N: int,
                   t: float,
                   seam = -1):
    i1 = min([i, k])
    i2 = max([i, k])
    qc.h(i)
    qc.h(k)

    if seam == -1 or seam < i1 or seam >= i2:
        upper_half = list(range(i1, (i1+i2)//2 + 1))
        lower_half = list(range((i1+i2)//2 + 1, i2 + 1))
    else:
        upper_half = list(range(i1, seam + 1))
        lower_half = list(range(seam+1, i2 + 1))

    upper_half = np.array(upper_half)
    lower_half = np.array(lower_half)

    upper_half = upper_half[upper_half != j]
    lower_half = lower_half[lower_half != j]

    upper_half = upper_half.tolist()
    lower_half = lower_half.tolist()
    
    qc = parity_check(qc, upper_half, target=i)
    qc = parity_check(qc, lower_half, target=k)

    qc.rz(np.pi/2, i)
    qc.h(i)
    qc.rz(np.pi/2, k)

    qc.cx(i, k)
    qc.rx(-t/2, i)
    qc.rz(t/2, k)
    qc.cx(i, k)

    qc.h(i)
    qc.rz(-np.pi/2, i)
    qc.rz(-np.pi/2, k)

    qc = parity_check_inverse(qc, upper_half, target=i)
    qc = parity_check_inverse(qc, lower_half, target=k)
    
    qc.h(i)
    qc.h(k)

    return qc

def upper_controlled_pauli(qc: QuantumCircuit,
                   i: int,
                   j: int,
                   k:int,
                   N: int,
                   t: float,
                   seam = -1):
    
    qc.h(i)
    qc.h(k)
    if seam == -1 or seam < j or seam >= k:
        upper_half = np.arange((k+i)//2, i-1, -1)
        lower_half = np.arange((k+i)//2 + 1, k + 1)
    elif seam < i and seam >= j:
        upper_half = np.array([j, i])
        lower_half = np.arange(i + 1, k + 1)
    elif seam >= i and seam < k:
        upper_half = list(range(i, seam + 1)) + [j]
        lower_half = list(range(seam + 1, k + 1))
    
    upper_half = upper_half.tolist()
    lower_half = lower_half.tolist()

    qc = parity_check(qc, upper_half, target=i)
    qc = parity_check(qc, lower_half, target=k)

    qc.rz(np.pi/2, i)
    qc.h(i)
    qc.rz(np.pi/2, k)

    qc.cx(i, k)
    qc.rx(-t/2, i)
    qc.rz(t/2, k)
    qc.cx(i, k)

    qc.h(i)
    qc.rz(-np.pi/2, i)
    qc.rz(-np.pi/2, k)

    qc = parity_check_inverse(qc, upper_half, target=i)
    qc = parity_check_inverse(qc, lower_half, target=k)
    
    qc.h(i)
    qc.h(k)

    return qc

def lower_controlled_pauli(qc: QuantumCircuit,
                   i: int,
                   j: int,
                   k:int,
                   N: int,
                   t: float,
                   seam = -1):
    i1 = min([i, k])
    i2 = max([i, k])
    qc.h(i)
    qc.h(k)

    if seam == -1 or seam < i or seam >= j:
        upper_half = list(range(i1, (i1+i2)//2 + 1))
        lower_half = list(range((i1+i2)//2 + 1, i2 + 1)) +[j]
    else:
        if seam >= i and seam < k:
            upper_half = list(range(i, seam + 1))
            lower_half = list(range(seam + 1, k + 1)) + [j]
        elif seam >= k and seam < j:
            upper_half = list(range(i, k))
            lower_half = [k, j]

    qc = parity_check(qc, upper_half, target=i)
    qc = parity_check(qc, lower_half, target=k)

    qc.rz(np.pi/2, i)
    qc.h(i)
    qc.rz(np.pi/2, k)

    qc.cx(i, k)
    qc.rx(-t/2, i)
    qc.rz(t/2, k)
    qc.cx(i, k)

    qc.h(i)
    qc.rz(-np.pi/2, i)
    qc.rz(-np.pi/2, k)

    qc = parity_check_inverse(qc, upper_half, target=i)
    qc = parity_check_inverse(qc, lower_half, target=k)
    
    qc.h(i)
    qc.h(k)

    return qc

def controlled_pauli(qc:QuantumCircuit,
                       i:int,
                       j:int,
                       k:int,
                       N:int,
                       t:float,
                       seam = -1):
    if j < i:
        qc = upper_controlled_pauli(qc, i, j, k, N, t, seam=seam)
    elif j > i and j < k:
        qc = mid_controlled_pauli(qc, i, j, k, N, t, seam=seam)
    elif j > k:
        qc = lower_controlled_pauli(qc, i, j, k, N, t, seam=seam)
    else:
        raise ValueError("Invalid index for controlled hopping")
    return qc