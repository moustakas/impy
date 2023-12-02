#!/usr/bin/env python

from mpi4py import MPI
comm = MPI.COMM_WORLD
print(f'Yo! I am on rank {comm.rank}/{comm.size}')
