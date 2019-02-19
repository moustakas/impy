#! /bin/bash

#SBATCH -A cosmo
#SBATCH -L SCRATCH
#SBATCH -p debug
#SBATCH -n 3
#SBATCH -t 00:01:00
#SBATCH -C haswell

srun -A cosmo -C haswell -t 00:01:00 --qos interactive -n 3 python helloworld.py
