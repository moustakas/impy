"""
Generate archetypes from the DESI ELG basis spectra.

"""

from __future__ import division, print_function

import os
import sys
import numpy as np
import argparse

import pdb

from astropy.io import fits
from astropy.table import Table

from SetCoverPy.mathutils import quick_amplitude

from desispec.log import get_logger, DEBUG
from desispec.io.util import write_bintable, makepath
from desisim.io import read_basis_templates

def main(args):

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     description='ELG archetypes')
    parser.add_argument('-o', '--objtype', type=str,  default='ELG', help='ELG', metavar='')

    # Set up the logger.
    if args.verbose:
        log = get_logger(DEBUG)
    else:
        log = get_logger()
        
    objtype = args.objtype.upper()
    log.debug('Using OBJTYPE {}'.format(objtype))

    baseflux, basewave, basemeta = read_basis_templates(objtype=objtype)



    pdb.set_trace()
