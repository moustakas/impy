"""
Assign DESI spectral templates to the Durham BGS mock catalog.

"""

from __future__ import division, print_function

import os
import pdb

import h5py
import numpy as np

from speclite import filters

from desispec.io.util import write_bintable
from desisim.io import read_basis_templates, empty_metatable
from desisim.templates import BGS

def main():

    seed = 123
    ngal = 100
    npergal = 50

    # Read the mock catalog.
    cat = h5py.File('galaxy_catalogue_0.hdf5')

    gr = cat['Data']['g_r'][:ngal]
    mag = cat['Data']['app_mag'][:ngal]
    z = cat['Data']['z_obs'][:ngal]
    zmin, zmax = np.min(z), np.max(z)

    # Read the basis templates and initialize the output metadata table.
    baseflux, basewave, basemeta = read_basis_templates('BGS')
    meta = empty_metatable(objtype='BGS', nmodel=ngal)

    bgs = BGS(minwave=3000, maxwave=11000.0)

    for igal in range(ngal):
        flux, wave, meta = bgs.make_templates(npergal, zrange=(zmin, zmax),
                                              nocolorcuts=True)

        pdb.set_trace()

if __name__ == '__main__':
    main()
