#!/usr/bin/env python
# srun -A cosmo -C haswell -t 00:01:00 --qos interactive -n 3 python helloworld.py

import subprocess
from mpi4py import MPI
from contextlib import redirect_stdout, redirect_stderr

comm = MPI.COMM_WORLD

cmd = 'python helloworld-print.py'

with open('helloworld-{}.log'.format(comm.rank), 'w') as log:
    with redirect_stdout(log), redirect_stderr(log):
        print('Yo! I am on rank {}/{}'.format(comm.rank, comm.size))
        err = subprocess.call(cmd.split(), stdout=log, stderr=log)
