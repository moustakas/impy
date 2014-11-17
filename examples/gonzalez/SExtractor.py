#!/usr/bin/python


#NOTE: I have discovered that there is a package cosmograil that includes more advanced
#sextractor functionality. This package includes a file sextractor.py, so I changed
#the name of this one to SExtractor.py

## 5/23/2007 -- In previous versions execution of sextractor was achieved via two call,
## with the first being to sexinit and the second to runsex. I have removed the first in
## favor of requiring the user to either have a .sex file containing the full path to the
##.param,.nnw, and .conv files being used, or to specify these with the flags option.

#Example Run From FLAMINGOS SURVEY
#######################
# run sextractor
#######################
#print "Running SExtractor on original image ("+sciname+")"
#flags= " -c FLAMINGOS.sex -CATALOG_NAME "+outcat+" -MAG_ZEROPOINT "\
#    +str(imzpt)+" -GAIN "+str(gain)+" -WEIGHT_IMAGE "+str(weightname)\
#    +","+str(weightname)+" -PIXEL_SCALE .158 -PHOT_APERTURES "\
#    " 6.329,9.494,12.658,15.823,18.987,25.316,31.646,37.975,44.304,50.633,59.962,63.291,126.582"
# sextractor.runsex(sciname+","+sciname,flags)



import os

###########################################################
# Create sextractor segmentation image if it does not exist
###########################################################

def runsex(image,flags):
    sexcmd="sex "+image+" "+flags
    os.system(sexcmd)


