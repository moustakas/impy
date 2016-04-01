#!/usr/bin/env python

"""Build a parent catalog.
"""

from __future__ import print_function, division

import os, sys
from time import time
import numpy as np
from astropy.table import Table, Row

from desitarget.internal import sharedmem
from desitarget import io

columns = [
    'BRICKID', 'BRICKNAME', 'OBJID', 'TYPE',
    'RA', 'RA_IVAR', 'DEC', 'DEC_IVAR',
    'DECAM_FLUX', 'DECAM_MW_TRANSMISSION',
    'DECAM_FRACFLUX', 'DECAM_FLUX_IVAR', 'DECAM_NOBS',
    'DECAM_ANYMASK', 'DECAM_DEPTH', 'DECAM_GALDEPTH',
    'WISE_FLUX', 'WISE_MW_TRANSMISSION',
    'WISE_FLUX_IVAR',
    'SHAPEDEV_R', 'SHAPEEXP_R',
    ]

def isBLUE(gflux, rflux, zflux, primary=None):
    """Target Definition of LRG. Returning a boolean array.

    Args:
        rflux, zflux, w1flux : array_like
            The flux in nano-maggies of r, z, and w1 band.
        primary: array_like or None
            If given, the BRICK_PRIMARY column of the catalogue.

    Returns:
        mask : array_like. True if and only the object is an LRG
            target.

    """
    #----- Luminous Red Galaxies
    if primary is None:
        primary = np.ones_like(rflux, dtype='?')

    elg = primary.copy()
    elg &= zflux < rflux * 10**(0.4/2.5)
    elg &= rflux < gflux * 10**(0.4/2.5)
    elg &= rflux > 10**((22.5-18.5)/2.5)
    elg &= rflux < 10**((22.5-22.0)/2.5)
    #- clip to avoid warnings from negative numbers raised to fractional powers
    #rflux = rflux.clip(0)
    #zflux = zflux.clip(0)

    #import pdb ; pdb.set_trace()

    return elg

def _is_row(table):
    '''Return True/False if this is a row of a table instead of a full table
    
    supports numpy.ndarray, astropy.io.fits.FITS_rec, and astropy.table.Table
    '''
    import astropy.io.fits.fitsrec
    import astropy.table.row
    if isinstance(table, (astropy.io.fits.fitsrec.FITS_record, astropy.table.row.Row)) or \
        np.isscalar(table):
        return True
    else:
        return False
    
def unextinct_fluxes(objects):
    """
    Calculate unextincted DECam and WISE fluxes
    
    Args:
        objects: array or Table with columns DECAM_FLUX, DECAM_MW_TRANSMISSION,
            WISE_FLUX, and WISE_MW_TRANSMISSION
            
    Returns:
        array or Table with columns GFLUX, RFLUX, ZFLUX, W1FLUX, W2FLUX, WFLUX
        
    Output type is Table if input is Table, otherwise numpy structured array
    """
    dtype = [('GFLUX', 'f4'), ('RFLUX', 'f4'), ('ZFLUX', 'f4'),
             ('W1FLUX','f4'), ('W2FLUX','f4'), ('WFLUX', 'f4')]
    if _is_row(objects):
        result = np.zeros(1, dtype=dtype)[0]
    else:
        result = np.zeros(len(objects), dtype=dtype)

    dered_decam_flux = objects['DECAM_FLUX'] / objects['DECAM_MW_TRANSMISSION']
    result['GFLUX'] = dered_decam_flux[..., 1]
    result['RFLUX'] = dered_decam_flux[..., 2]
    result['ZFLUX'] = dered_decam_flux[..., 4]

    dered_wise_flux = objects['WISE_FLUX'] / objects['WISE_MW_TRANSMISSION']
    result['W1FLUX'] = dered_wise_flux[..., 0]
    result['W2FLUX'] = dered_wise_flux[..., 1]
    result['WFLUX']  = 0.75* result['W1FLUX'] + 0.25*result['W2FLUX']

    if isinstance(objects, Table):
        return Table(result)
    else:
        return result

def apply_cuts(objects):
    """Apply the cuts we want."""

    #zfaint = 22.0
    #keep = np.where((np.sum((objects['DECAM_NOBS'][:,[1,2,4]]>=3)*1,axis=1)==3)*
    #                (np.sum((objects['DECAM_ANYMASK'][:,[1,2,4]]>0)*1,axis=1)==0)*
    #                (objects['DECAM_FLUX'][:,4]<(10**(-0.4*(zfaint-22.5)))))[0]

    if isinstance(objects, (str, unicode)):
        from desitarget import io
        objects = io.read_tractor(objects)
    
    #- ensure uppercase column names if astropy Table
    if isinstance(objects, (Table, Row)):
        for col in objects.columns.itervalues():
            if not col.name.isupper():
                col.name = col.name.upper()

    #- undo Milky Way extinction
    flux = unextinct_fluxes(objects)
    gflux = flux['GFLUX']
    rflux = flux['RFLUX']
    zflux = flux['ZFLUX']
    w1flux = flux['W1FLUX']
    wflux = flux['WFLUX']
    
    #- DR1 has targets off the edge of the brick; trim to just this brick
    try:
        primary = objects['BRICK_PRIMARY']
    except (KeyError, ValueError):
        if _is_row(objects):
            primary = True
        else:
            primary = np.ones_like(objects, dtype=bool)
        
    blue = isBLUE(primary=primary, gflux=gflux, zflux=zflux, rflux=rflux)

    #keep = np.where((blue==1))[0]
    #keep = np.where((blue==1)*
    #                (np.sum((objects['DECAM_ANYMASK'][:,[1,2,4]]>0)*1,axis=1)==0))[0]
    keep = np.where((blue==1)*
                    (np.sum((objects['DECAM_ANYMASK'][:,[1,2,4]]>0)*1,axis=1)==0)*
                    (np.sum((objects['DECAM_FLUX'][:,[1,2,4]]>0)*1,axis=1)==3))[0]
    
    return keep

def select_targets(infiles, numproc=4, verbose=False):
    """
    Process input files in parallel to select targets
    
    Args:
        infiles: list of input filenames (tractor or sweep files),
            OR a single filename
        
    Optional:
        numproc: number of parallel processes to use
        verbose: if True, print progress messages
        
    Returns:
        targets numpy structured array: the subset of input targets which
            pass the cuts, including extra columns for DESI_TARGET,
            BGS_TARGET, and MWS_TARGET target selection bitmasks. 
            
    Notes:
        if numproc==1, use serial code instead of parallel
    """
    #- Convert single file to list of files
    if isinstance(infiles, (str, unicode)):
        infiles = [infiles,]

    #- Sanity check that files exist before going further
    for filename in infiles:
        if not os.path.exists(filename):
            raise ValueError("{} doesn't exist".format(filename))
    
    #- function to run on every brick/sweep file
    def _select_targets_file(filename):
        '''Returns targets in filename that pass the cuts'''
        from desitarget import io
        objects = io.read_tractor(filename, columns=columns)
        keep = apply_cuts(objects)
        
        return io.fix_tractor_dr1_dtype(objects[keep])

    # Counter for number of bricks processed;
    # a numpy scalar allows updating nbrick in python 2
    # c.f https://www.python.org/dev/peps/pep-3104/
    nbrick = np.zeros((), dtype='i8')

    t0 = time()
    def _update_status(result):
        ''' wrapper function for the critical reduction operation,
            that occurs on the main parallel process '''
        if verbose and nbrick%50 == 0 and nbrick>0:
            rate = nbrick / (time() - t0)
            print('{} files; {:.1f} files/sec'.format(nbrick, rate))

        nbrick[...] += 1    # this is an in-place modification
        return result

    #- Parallel process input files
    if numproc > 1:
        pool = sharedmem.MapReduce(np=numproc)
        with pool:
            targets = pool.map(_select_targets_file, infiles, reduce=_update_status)
    else:
        targets = list()
        for x in infiles:
            targets.append(_update_status(_select_targets_file(x)))

    print(len(targets))

    #import pdb ; pdb.set_trace()
    #targets1 = np.concatenate(targets)
    return targets

def main():

    # Build a catalog of all the grz, 3-pass sources.
    tracdir = '/project/projectdirs/cosmo/data/legacysurvey/dr2/tractor'
    outfile = 'lensedecals-parent.fits'
    
    ramin = 210
    ramax = 240 # 250
    rarange = np.arange(ramin, ramax+1, 1).astype(str)
    infiles = [io.list_tractorfiles(os.path.join(tracdir, this)) for this in rarange]
    infiles = np.concatenate(infiles).flatten()

    #infiles = io.list_tractorfiles(tracdir)

    print('Found {} tractor catalogs.'.format(len(infiles)))
    cat = select_targets(infiles, verbose=True)#, numproc=1)
    print('Selected {} objects.'.format(len(cat)))
    io.write_targets(outfile, cat)
    
if __name__ == "__main__":
    main()
