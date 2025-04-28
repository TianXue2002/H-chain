import matplotlib.pyplot as plt
import numpy as np
import qiskit.qpy as qpy
import pickle
import json
import matplotlib.patches as mpatches
from numba import njit
from numba.typed import List

import pickle

def read_excitation(distance, read_epsilon, epsilon, prehead):
    uop, all_g = read_uop(distance, read_epsilon, prehead)
    excitations = create_excitation(uop, all_g, epsilon)
    return excitations

def read_data_distance(distance, epsilon, prehead):
    with open(prehead+f"data_e={epsilon}/ansatz_distance={distance}.qpy", "rb") as file:
        ansatz = qpy.load(file)

    with open(prehead+f"data_e={epsilon}/hamiltonian_distance={distance}.pkl", 'rb') as file:
        hamiltonian = pickle.load(file)


    with open(prehead+f"data_e={epsilon}/excitations_distance={distance}.json", "rb") as file:
        excitations = json.load(file)

    with open(prehead+f"data_e={epsilon}/initial_distance={distance}.qpy", "rb") as file:
        initial_state = qpy.load(file)

    with open(prehead+f"data_e={epsilon}/initial_distance={distance}.qpy", "rb") as file:
        initial_state = qpy.load(file)
    ansatz = ansatz[0]
    initial_state = initial_state[0]
    hamiltonian = hamiltonian
    return ansatz, excitations,initial_state,hamiltonian

def read_uop(distance, epsilon, prehead):

    class DummyMRH:
        def __init__(self, *args, **kwargs):
            pass

# Custom unpickler to handle missing modules gracefully
    class CustomUnpickler(pickle.Unpickler):
        def find_class(self, module, name):
            if module == "mrh":
                print(f"Substituting missing class: {name} with DummyMRH")
                return DummyMRH
            try:
                return super().find_class(module, name)
            except ModuleNotFoundError:
                print(f"Missing module: {module}, substituting with DummyMRH")
                return DummyMRH
    with open(prehead+f"data_e={epsilon}/uop_distance={distance}.json", "rb") as file:
            uop =  CustomUnpickler(file).load()
    with open(prehead+f"data_e={epsilon}/all_g_distance={distance}.json", "rb") as file:
        all_g = json.load(file)
    return uop, all_g

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