#!/usr/bin/env python

import numpy as np
import matplotlib.pyplot as plt
from astropy.io import ascii
from astrometry.libkd import spherematch_c

def build_cat(cluster,topdir):
    
    cat = ascii.read(topdir+cluster+'_multicolor_nir.cat',
                     format='sextractor')

    f105w = cat['hst_wfc3_ir_f105w_mag_bpz']
    f140w = cat['hst_wfc3_ir_f140w_mag_bpz']
    f160w = cat['hst_wfc3_ir_f160w_mag_bpz']

    ascii.write(cat[0:3],topdir+cluster+'_hff.cat',
                include_names=['number','hst_wfc3_ir_f105w_mag_bpz',
                               'hst_wfc3_ir_f140w_mag_bpz'],
#               dtype=['i5','f1','f1'],
                format='basic')
    
if __name__ == '__main__':

    topdir = '/Users/ioannis/'
    for cat in ['a2744','m0416']:
        build_cat(cat,topdir)
