#!/usr/bin/env python

import numpy as np
import matplotlib.pyplot as plt
from astropy.io import ascii
from astrometry.libkd import spherematch_c

catdir = '/Users/ioannis/'
cat = ascii.read(catdir+'a2744_multicolor_nir.cat')
#cat = ascii.read(catdir+'m0416_multicolor_nir.cat')

# find our high-z candidates



# now make the plot
f105w = cat['HST_WFC3_IR_F105W_MAG_BPZ']
f140w = cat['HST_WFC3_IR_F140W_MAG_BPZ']
f160w = cat['HST_WFC3_IR_F160W_MAG_BPZ']

xmin = -3.0
xmax = 4.0
ymin = -3.0
ymax = 5.0
coeff = [1.0,0.8]
fitmin = (0.8-coeff[1])/coeff[0]
xcolor = np.linspace(fitmin,0.6,20)
ycolor = np.polyval(coeff,xcolor)

plt.clf()
plt.plot(f140w-f160w,f105w-f140w,'bo')
plt.plot(xcolor,ycolor,'r-',[0.6,0.6],
         [np.polyval(coeff,0.6),ymax],'r-',
         [xmin,fitmin],[0.8,0.8],'r-',linewidth=2)

plt.plot(-2.5*np.log10(21.8/35.4),-2.5*np.log10(1.2/21.8),'gs') # JD1A
plt.plot(-2.5*np.log10(24.3/43.8),-2.5*np.log10(2.0/24.3),'gs') # JD1B

plt.axis([xmin,xmax,ymin,ymax])
plt.xlabel('F140W - F160W')
plt.ylabel('F105W - F140W')
plt.savefig('z9_colorcolor.png')
    
