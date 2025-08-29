#########################
# Notebook to run LASVQE after setting up a mean field object
#########################

# PySCF imports
from pyscf import gto, scf, lib

from lasvqe.get_geom import get_geom,sph2cart
from lasvqe.las_vqe import LASVQE

import numpy as np
import argparse


def get_geom_many_h(dist=0.0, angles=[-0.3031323952381563, -0.1964410468213601], n_dimers=2, uniform=False, clusterOnly=False):
    disp = np.array(sph2cart(angles[0], angles[1]))
    xyzs = []
    for i in range(n_dimers):
        mid = np.array([0.12291127, 0.992417664, 0.0]) * (i + i // 2) * (1.461078387 + dist * 0.5)
        if uniform:
            mid = np.array([0.12291127, 0.992417664, 0.0]) * i * (1.461078387 + dist * 0.5)
        if clusterOnly:
            mid = np.array([0.12291127, 0.992417664, 0.0]) * (i + i // 2 * dist) * (1.461078387)
        mid[0] += 0.5
        h3 = mid - disp
        h4 = mid + disp

        # Format as XYZ string for each dimer
        xyz = """H {} {} {};
        H {} {} {};
        """.format(h3[0], h3[1], h3[2], h4[0], h4[1], h4[2])
        xyzs.append(xyz)
    
    # Combine all the dimers into one XYZ string
    xyz = xyzs[0]
    for i in range(1, n_dimers):
        xyz += xyzs[i]
    if clusterOnly:
        print(f"Only change the cluster seperation by {1+dist} times")
    return xyz


# Define molecule: (H2)_2

parser = argparse.ArgumentParser(description="Process two input parameters.")
parser.add_argument('--epsilon', type=float, required=True, help="epsilon")
parser.add_argument('--dist', type=float, required=True, help="distance")

args = parser.parse_args()
dist = args.dist
epsilon = args.epsilon

print(f"distance is {dist}")
#There are a couple of ways to increase the size
#One is to increase the basis set, but keep the number of atoms the same
#This is a more accurate description of the same chemical system
#From small to large:
basis_sets = ["sto-3g","6-31g","cc-pvdz","cc-pvtz","cc-pvqz"]

#The other way is to increase the number of dimers, which increases the
#number of atoms
uniform = True
if uniform:
    print("uniform H-chain")
xyz = get_geom_many_h(dist=dist,n_dimers=6, clusterOnly=True)
print(xyz)
mol = gto.M (atom = xyz, basis = 'sto-3g', output='h4_sto3g_{}.log'.format(dist),
    symmetry=False, verbose=lib.logger.DEBUG)

# Do RHF
mf = scf.RHF(mol).run()
print("HF energy: ", mf.e_tot)
# epsilon = 0
#Here, you define the fragmentation
#Frag atom list is based on the atom index

#As an example, for n_dimers=4, we could do

#2 fragments of 4 atoms each
# frag_atom_list = ((0,1,2,3),(4,5,6,7))

#or 4 fragments of 2 atoms each
frag_atom_list = ((0,1),(2,3),(4,5),(6,7),(8,9),(10,11))

# You can of course use other numbers of dimers to generate, say, 3 fragments of 2 atoms each
# or 2 fragments of 3 atoms each, etc, etc
#f_orbs is the number of orbitals in each fragment sum(f_orbs) should be = mol.nbas
#       Each H has the same number of basis functions
#       If you use a larger basis set (6-31g), you'll want to make sure f_orbs is increased
#f_elec is the number of electrons in each fragment sum(f_elec) should be = mol.nelec
#       Each H has the same number of electrons
#spin_sub is the spin state of each fragment. We can do singlets (1,1,...,1) for each for now

# Create LASVQE object
# lasvqe = LASVQE(mf, f_orbs=(2, 2, 2, 2), f_elec=(2, 2, 2, 2), f_atom_list=frag_atom_list, spin_sub=(1, 1, 1, 1), selected=True, epsilon=0.01)
lasvqe = LASVQE(mf, f_orbs=(2,2,2,2,2,2), f_elec=(2,2,2,2,2,2), f_atom_list=frag_atom_list, spin_sub=(1,1,1,1,1,1), selected=True, epsilon=epsilon)
path = f"/u/tianxue2/chem/data_base/H_12_cluster/data_e={epsilon}"
lasvqe.path = path
# Run LAS-VQE calculation
lasvqe.distance = dist
num_parameters = lasvqe.run(if_VQE=False)

print("number of parameters: ", num_parameters)
myhf = mol.RHF().run()