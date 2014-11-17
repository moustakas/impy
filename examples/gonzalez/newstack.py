#!/usr/bin/python

#Stack the individual NEWFIRM images using SWARP after running newalign.py

import sys,os,time,string
import numpy
import pyfits
import pyraf
import pyraf.iraf
from pyraf.iraf import stsdas
import shutil
import SExtractor


def imgets(img,field):
   iraf.flprcache()
   iraf.flprcache()
   iraf.imgets(img,field)
   return iraf.imgets.value


########################################
# Main Program			       #
########################################

#Run this from the upper level directory
#Should auto grab list of files from mergedSkySubtracted directory
#Should then cut off mergedskySubtracted from prefix

start=time.time()
print 'Started at: ',start

# -- 1. Read input parameters
# Format for list should be the mergedSkySubtracted names
list=sys.argv[1]
output=str(sys.argv[2]).split(".fits")[0]
photcal=int(sys.argv[3])

keywords="EXPTIME,DETECTOR,FILTER,"


#Run swarp
#Have to split things here based upon image name...gets slightly more tricky.
#NO -- only have to split into photcal and non-photcal images. Beyond this
#everything should automatically segregate.
#...but then there won't be a sensible propagation of the name either....not clear that manual is the way to go here...but may have to rename fields at the end...???
#Setting it to a final pixel scale of 0.40"/pixel rather than letting is float around 0.3953 in the interests of consistent photometry between frames
print "Running swarp..."
os.system("/astro/data/manatee1/NEWFIRM-NDWFS/code/SWARP/bin/swarp -dd > default.swarp")
if(photcal==0):
  print "/astro/data/manatee1/NEWFIRM-NDWFS/code/SWARP/bin/swarp  -COPY_KEYWORDS "+keywords+" -WEIGHT_TYPE MAP_WEIGHT -WEIGHT_THRESH 0.01 -COMBINE_TYPE SIGWEIGHTED -COMBINE_SIGMA 3 -SUBTRACT_BACK N -NTHREADS 0 -GAIN_DEFAULT 8. -PIXELSCALE_TYPE MANUAL -PIXEL_SCALE 0.4 -IMAGEOUT_NAME "+str(output)+".fits -WEIGHTOUT_NAME "+str(output)+".weight.fits @"+list
  #os.system("/astro/data/manatee1/NEWFIRM-NDWFS/code/SWARP/bin/swarp  -COPY_KEYWORDS "+keywords+" -WEIGHT_TYPE MAP_WEIGHT -WEIGHT_THRESH 0.01 -COMBINE_TYPE SIGWEIGHTED -COMBINE_SIGMA 3 -SUBTRACT_BACK N -NTHREADS 0 -GAIN_DEFAULT 8. -PIXELSCALE_TYPE MANUAL -PIXEL_SCALE 0.4 -IMAGEOUT_NAME "+str(output)+".fits -WEIGHTOUT_NAME "+str(output)+".weight.fits @"+list)
  os.system("/astro/data/manatee1/NEWFIRM-NDWFS/code/SWARP/bin/swarp  -COPY_KEYWORDS "+keywords+" -WEIGHT_TYPE MAP_WEIGHT -WEIGHT_THRESH 0.01 -COMBINE_TYPE SIGWEIGHTED -COMBINE_SIGMA 3 -SUBTRACT_BACK N -NTHREADS 1 -GAIN_DEFAULT 8. -PIXELSCALE_TYPE MANUAL -PIXEL_SCALE 0.4 -IMAGEOUT_NAME "+str(output)+".fits -WEIGHTOUT_NAME "+str(output)+".weight.fits @"+list)
elif(photcal==1): 
  print "/astro/data/manatee1/NEWFIRM-NDWFS/code/SWARP/bin/swarp  -COPY_KEYWORDS "+keywords+" -WEIGHT_TYPE MAP_WEIGHT -WEIGHT_THRESH 0.01 -COMBINE_TYPE AVERAGE -COMBINE_SIGMA 3 -SUBTRACT_BACK N -NTHREADS 0 -GAIN_DEFAULT 8. -PIXELSCALE_TYPE MANUAL -PIXEL_SCALE 0.4 -IMAGEOUT_NAME "+str(output)+".fits -WEIGHTOUT_NAME "+str(output)+".weight.fits @"+list
  os.system("/astro/data/manatee1/NEWFIRM-NDWFS/code/SWARP/bin/swarp  -COPY_KEYWORDS "+keywords+" -WEIGHT_TYPE MAP_WEIGHT -WEIGHT_THRESH 0.01 -COMBINE_TYPE AVERAGE -COMBINE_SIGMA 3 -SUBTRACT_BACK N -NTHREADS 0 -GAIN_DEFAULT 8. -PIXELSCALE_TYPE MANUAL -PIXEL_SCALE 0.4 -IMAGEOUT_NAME "+str(output)+".fits -WEIGHTOUT_NAME "+str(output)+".weight.fits @"+list)


end=time.time()

print 'Total elapsed time: ',end-start

