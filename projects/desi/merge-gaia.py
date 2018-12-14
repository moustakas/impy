#!/usr/bin/env python

import os
import fitsio
import numpy as np
from glob import glob

topdir = '/Users/ioannis/work/desi/mocks/mws/galaxia/alpha'           
#topdir = '/global/projecta/projectdirs/desi/mocks/mws/galaxia/alpha'           
gaiafiles = glob(topdir+'/v0.0.5/healpix/8/?/*/gaia_mock_allsky_galaxia_desi-8-*.fits')
mockfiles = [gg.replace('gaia_', '') for gg in gaiafiles]

for gg, mm in zip( gaiafiles, mockfiles ):
    mock = fitsio.read(mm, lower=True)
    gaia = fitsio.read(gg, lower=True)
    
    outdtype = mock.dtype.descr
    for col in gaia.dtype.names:
        outdtype = outdtype + [(col, gaia[col].dtype.str)]

    out = np.empty(mock.shape, dtype=outdtype)
    for col in mock.dtype.names:
        out[col] = mock[col]
    for col in gaia.dtype.names:
        out[col] = gaia[col]
        
    #out = np.hstack( (mock, gaia) ) # invalid type promotion???

    outfile = mm.replace('v0.0.5', 'v0.0.6')
    os.makedirs(os.path.dirname(outfile), exist_ok=True)

    print('Writing {}'.format(outfile))
    fitsio.write(outfile, out, clobber=True)
