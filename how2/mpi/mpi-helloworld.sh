#! /bin/bash -l

#salloc -N 2 -C cpu -A desi -L cfs -t 00:10:00 --qos interactive --image=dstndstn/cutouts:dvsro
#srun -N 2 -n 2 shifter ./mpi-helloworld.sh > mpi-helloworld.log 2>&1 &

time python mpi-helloworld.py 
