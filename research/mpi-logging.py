#!/usr/bin/env python
"""
srun -N 3 -n 3 python helloworld.py

"""
import sys, time
from mpi4py import MPI
import multiprocessing
ncpu = multiprocessing.cpu_count() // 2   #- avoid hyperthreading

def get_logger(logfile, delimiter=':'):
    import logging
    logger = logging.getLogger()

    hdlr = logging.FileHandler(logfile, mode='w')

    fmtfields = ['%(levelname)s', '%(filename)s', '%(lineno)s',
                 '%(funcName)s', '%(asctime)s', ' %(message)s']
    formatter = logging.Formatter(delimiter.join(fmtfields),
                                  datefmt='%Y-%m-%dT%H:%M:%S')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    logger.setLevel(logging.INFO)

    return logger

comm = MPI.COMM_WORLD
rank, size = comm.rank, comm.size
name = MPI.Get_processor_name()

if rank == 0:
    print('On rank {} started at {}'.format(rank, time.asctime()))

comm.barrier()
logfile = 'rank{}.log'.format(rank)
log = get_logger(logfile)
#log = open(logfile, 'w')
#sys.stdout = log
#sys.stderr = log
    
log.info('On rank {} of {} on {} with {} cores.'.format(rank, size, name, ncpu))#, flush=True)
log.warning('I like cheese.')#, flush=True)
#print('On rank {} of {} on {} with {} cores.'.format(rank, size, name, ncpu))#, flush=True)
#print('I like cheese.')#, flush=True)

#log.close()
#sys.stdout = sys.__stdout__
#sys.stderr = sys.__stderr__

comm.barrier()
if rank == 0:
    print('On rank {} done at {}'.format(rank, time.asctime()))


