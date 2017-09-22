#!/usr/bin/env python

"""Plots for talks I'm giving at the the June 2017 DESI Collaboration Meeting.

"""
import os
import argparse
import numpy as np

import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
import seaborn as sns

from desitarget.mock.sample import SampleGMM

sns.set(style='ticks', font_scale=1.4, palette='Set2')
#sns.set(style='white', font_scale=1.3, palette='Set2')
setcolors = sns.color_palette()

def elg_colorbox(ax):
    """Draw the ELG selection box."""
    rmaglim = 23.4
    grlim = ax.get_ylim()
    coeff0, coeff1 = (1.15, -0.15), (-1.2, 1.6)
    rzmin, rzpivot = 0.3, (coeff1[1] - coeff0[1]) / (coeff0[0] - coeff1[0])
    verts = [(rzmin, grlim[0]),
             (rzmin, np.polyval(coeff0, rzmin)),
             (rzpivot, np.polyval(coeff1, rzpivot)),
             ((grlim[0] - 0.1 - coeff1[1]) / coeff1[0], grlim[0] - 0.1)
            ]
    ax.add_patch(Polygon(verts, fill=False, ls='--', color='k', lw=3))
    return rmaglim


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('--gmm', action='store_true')
    args = parser.parse_args()

    talkpath = os.path.join(os.getenv('IM_RESEARCH_DIR'), 'talks', 'desi', '17jun_desi')

    seed = 999
    rand = np.random.RandomState(seed)

    # --------------------------------------------------
    if args.gmm:

        nobj = 500

        GMM = SampleGMM(random_state=rand)
        mags = GMM.sample('ELG', nobj) # [g, r, z, w1, w2, w3, w4]

        fig, ax = plt.subplots(figsize=(8, 5))
        ax.scatter(mags['r'] - mags['z'], mags['g'] - mags['r'])
        ax.set_xlim(-0.2, 2)
        ax.set_ylim(-0.4, 1.5)
        ax.set_xlabel(r'$r - z$')
        ax.set_ylabel(r'$g - r$')
        ax.grid()
        ax.text(0.9, 0.92, 'GMM-sampled ELG colors', ha='right', va='center',
                transform=ax.transAxes, fontsize=18)
        elg_colorbox(ax)
        fig.subplots_adjust(bottom=0.15, top=0.92, left=0.15)
        fig.savefig(os.path.join(talkpath, 'elg-gmm-example.png'))


if __name__ == '__main__':
    main()
