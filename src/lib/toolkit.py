from qiskit import QuantumCircuit
import numpy as np
from typing import List

def modular_parity_check(qc: QuantumCircuit,
                         check_lst: List[int],
                         seam: int,
                         target = None):
    if len(check_lst) >= 2:
        if check_lst[0] < check_lst[-1]:
            inverse = False
        elif check_lst[0] > check_lst[-1]:
            inverse = True
        else:
            raise ValueError("Cannot have the same two numbers in the parity check matrix")
   
    upper_half= []
    lower_half = []
    for check in check_lst:
        if check <= seam:
            upper_half.append(check)
        else:
            lower_half.append(check)
    if len(upper_half) != 0:
        qc = parity_check(qc, upper_half, target=upper_half[-1])
    if len(lower_half) != 0:
        qc = parity_check(qc, lower_half, target=lower_half[-1])
    
    if len(upper_half) != 0 and len(lower_half) != 0:
        if not inverse:
            qc.cx(upper_half[-1], lower_half[-1])
        else:
            qc.cx(lower_half[-1], upper_half[-1])
    return qc

def modular_parity_check_inverse(qc: QuantumCircuit,
                         check_lst: List[int],
                         seam: int,
                         target = None):
    if len(check_lst) >= 2:
        if check_lst[0] < check_lst[-1]:
            inverse = False
        elif check_lst[0] > check_lst[-1]:
            inverse = True
        else:
            raise ValueError("Cannot have the same two numbers in the parity check matrix")
    
    upper_half= []
    lower_half = []
    for check in check_lst:
        if check <= seam:
            upper_half.append(check)
        else:
            lower_half.append(check)

    if len(upper_half) != 0 and len(lower_half) != 0:
        if not inverse:
            qc.cx(upper_half[-1], lower_half[-1])
        else:
            qc.cx(lower_half[-1], upper_half[-1])

    if len(upper_half) != 0:
        qc = parity_check_inverse(qc, upper_half, target=upper_half[-1])
    if len(lower_half) != 0:
        qc = parity_check_inverse(qc, lower_half, target=lower_half[-1])
    
    return qc

def parity_check(qc: QuantumCircuit,
                 check_lst: List[int],
                 target = None):
    if target == None:
        target = check_lst[-1]

    if len(check_lst) == 0 or len(check_lst) == 1:
        return qc
    elif len(check_lst) == 2:
        if target == None:
            target = check_lst[-1]
        if target not in check_lst:
            raise ValueError("Target not in the check_lst")
        target_index = check_lst.index(target)
        control = check_lst[int(1-target_index)]
        qc.cx(control, target)
        return qc
    else:
        cut_pos = check_lst.index(target)
        upper = False
        lower = False
        if target == check_lst[0]:
            cut_pos = len(check_lst)//2 - 1
            lower = True
        elif target == check_lst[-1]:
            cut_pos = len(check_lst)//2 - 1
            upper = True
        upper_half = check_lst[:cut_pos + 1]
        lower_half = check_lst[cut_pos + 1:]

        if upper:
            upper_target = upper_half[-1]
            lower_target = lower_half[-1]
        elif lower:
            upper_target = upper_half[0]
            lower_target = lower_half[0]
        else:
            upper_target = upper_half[-1]
            lower_target = lower_half[0]

        qc = parity_check(qc, upper_half, target=upper_target)
        qc = parity_check(qc, lower_half, target=lower_target)
        if upper:
            qc.cx(upper_target, lower_target)
        elif lower:
            qc.cx(lower_target, upper_target)
        else:
            qc.cx(lower_target, upper_target)
        return qc
    
def parity_check_inverse(qc: QuantumCircuit,
                 check_lst: List[int],
                 target = None):
    if target == None:
        target = check_lst[-1]

    if len(check_lst) == 0 or len(check_lst) == 1:
        return qc
    elif len(check_lst) == 2:
        if target == None:
            target = check_lst[-1]
        if target not in check_lst:
            raise ValueError("Target not in the check_lst")
        target_index = check_lst.index(target)
        control = check_lst[int(1-target_index)]
        qc.cx(control, target)
        return qc
    else:
        cut_pos = check_lst.index(target)
        upper = False
        lower = False
        if target == check_lst[0]:
            cut_pos = len(check_lst)//2 - 1
            lower = True
        elif target == check_lst[-1]:
            cut_pos = len(check_lst)//2 - 1
            upper = True
        upper_half = check_lst[:cut_pos + 1]
        lower_half = check_lst[cut_pos + 1:]

        if upper:
            upper_target = upper_half[-1]
            lower_target = lower_half[-1]
        elif lower:
            upper_target = upper_half[0]
            lower_target = lower_half[0]
        else:
            upper_target = upper_half[-1]
            lower_target = lower_half[0]

        if upper:
            qc.cx(upper_target, lower_target)
        elif lower:
            qc.cx(lower_target, upper_target)
        else:
            qc.cx(lower_target, upper_target)

        qc = parity_check_inverse(qc, upper_half, target=upper_target)
        qc = parity_check_inverse(qc, lower_half, target=lower_target)
        
        return qc
