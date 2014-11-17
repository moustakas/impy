#!/usr/bin/python

#Align individual NEWFIRM images using SCAMP 

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

def quicksex(lresimg,sexdir,detect_minarea,detect_thresh,analysis_thresh,flagimage):
    lres_cat=lresimg.split(".fits")[0]+".cat"
    if(os.access(lres_cat,0)): os.remove(lres_cat)
    sparam="newfirm_sex.param"
    if(os.access(sparam,0)): os.remove(sparam)
    file_par=open(sparam,"w")
    #outline="NUMBER\n X_IMAGE\n Y_IMAGE\n MAG_AUTO\n"
    #Establish parameters for output file\n
    outline="\
	NUMBER\n\
  	FLUX_APER(1)\n\
	FLUXERR_APER(1)\n\
	FLUX_AUTO\n\
	FLUXERR_AUTO\n\
	XWIN_IMAGE\n\
	YWIN_IMAGE\n\
	AWIN_IMAGE\n\
	ERRAWIN_IMAGE\n\
	BWIN_IMAGE\n\
	ERRBWIN_IMAGE\n\
	THETAWIN_IMAGE\n\
	ERRTHETAWIN_IMAGE\n\
	FLAGS\n\
	IMAFLAGS_ISO(1)\n\
	FLUX_RADIUS\n"
	
    file_par.write(outline)
    file_par.close()
    flags="-c "+sexdir+"/config/default.sex -FILTER_NAME "+sexdir+"/config/default.conv -PARAMETERS_NAME \
          newfirm_sex.param -DETECT_MINAREA "+str(detect_minarea)+" -DETECT_THRESH "+str(detect_thresh)+" -ANALYSIS_THRESH "+\
          str(analysis_thresh)+" -STARNNW_NAME "+sexdir+"/config/default.nnw -DEBLEND_MINCONT .005 \
           -CHECKIMAGE_TYPE NONE  -VERBOSE_TYPE QUIET  -CATALOG_NAME "+lres_cat+" -BACKPHOTO_TYPE GLOBAL -CATALOG_TYPE FITS_LDAC -PHOT_APERTURES 15.5 -SATUR_LEVEL 10000. -FLAG_IMAGE "+flagimage+" -GAIN 8"

    os.system(sexdir+"/bin/sex "+lresimg+" "+flags)

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
#photkey=sys.argv[2]

#Remove scamp directory if it exists
#Note: currently only does so if directory is empty; should change
#if(os.access("scamp",1)): os.rmdir("scamp")
if(os.access("scamp",1)): shutil.rmtree("scamp")
os.mkdir("scamp")
f=open(list,"r")
namelist=[]
skynamelist=[]
masknamelist=[]
outmasknamelist=[]

#Create list of filenames and copy images into scamp directory
for line in f.readlines():
   name=string.split(line)[0]
   name=name.split("rm_")[1]
   print name
   namelist.append(name)
   skynamelist.append("rm_"+name)
   masknamelist.append("mask_"+name)
   outmasknamelist.append("rm_"+name.split(".fits")[0]+".weight.fits")
f.close()

for i in range(len(skynamelist)):
   #os.system("cp mergedSkySubtracted/"+skynamelist[i]+" scamp/")
   os.system("cp remerged/"+skynamelist[i]+" scamp/")
   #Note that the masks must be inverted so that 1 -> 0 and 0-> 1
   #Also right now must add additional masking where science image is zero due to edge masking
   #For new version with multi-value flags, this will have to change again
   #stsdas.toolbox.imgtools.imcalc("mergedTotalMasks/"+masknamelist[i],"scamp/"+skynamelist[i].split(".fits")[0]+".weight.fits",equals="-1.*(im1-1)",pixtype="int")
   if(os.access("scamp/junk.fits",1)): os.remove("scamp/junk.fits")
   #os.system("cp mergedSkySubtracted/"+skynamelist[i]+" scamp/junk.fits")
   os.system("cp remerged/"+masknamelist[i]+" scamp/")

   #Want a weight map where values are 1 if good and 0 if bad
   #Take the mask in the remerged directory and set it to 0/1.

   w=pyfits.open("remerged/"+masknamelist[i])
   for k in range(1,5):
     w[k].data=numpy.where(numpy.logical_or(w[k].data==0,w[k].data==4),1,0)
     w[k].data=w[k].data.astype("UInt8")
   w.verify('silentfix')
   print "scamp/"+outmasknamelist[i]
   w.writeto("scamp/"+outmasknamelist[i])
   w.close()

#Enter scamp directory
#os.chdir("scamp/")

#Strip the WAT header information and modify the CTYPE header information
print "stripping headers"
for i in range(len(namelist)):
   for j in range(4):
     print "scamp/"+skynamelist[i]+"["+str(j+1)+"]"
     pyraf.iraf.images.imutil.hedit("scamp/"+skynamelist[i]+"["+str(j+1)+"]",fields="WAT1*",add="no",delete="yes",show="yes",update="yes",verify="no",addonly="no")
     print "scamp/"+skynamelist[i]+"["+str(j+1)+"]"+" WAT2"
     pyraf.iraf.images.imutil.hedit("scamp/"+skynamelist[i]+"["+str(j+1)+"]",fields="WAT2*",add="no",delete="yes",show="yes",update="yes",verify="no",addonly="no")
     pyraf.iraf.images.imutil.hedit("scamp/"+skynamelist[i]+"["+str(j+1)+"]",fields="CTYPE1",add="yes",addonly="no",delete="no",show="yes",update="yes",value="RA---TAN",verify="no")
     pyraf.iraf.images.imutil.hedit("scamp/"+skynamelist[i]+"["+str(j+1)+"]",fields="CTYPE2",add="yes",addonly="no",delete="no",show="yes",update="yes",value="DEC--TAN",verify="no")
     pyraf.iraf.images.imutil.hedit("scamp/"+outmasknamelist[i]+"["+str(j+1)+"]",fields="WAT1*",add="no",delete="yes",show="yes",update="yes",verify="no",addonly="no")
     pyraf.iraf.images.imutil.hedit("scamp/"+outmasknamelist[i]+"["+str(j+1)+"]",fields="WAT2*",add="no",delete="yes",show="yes",update="yes",verify="no")
     pyraf.iraf.images.imutil.hedit("scamp/"+outmasknamelist[i]+"["+str(j+1)+"]",fields="CTYPE1",add="yes",addonly="no",delete="no",show="yes",update="yes",value="RA---TAN",verify="no")
     pyraf.iraf.images.imutil.hedit("scamp/"+outmasknamelist[i]+"["+str(j+1)+"]",fields="CTYPE2",add="yes",addonly="no",delete="no",show="yes",update="yes",value="DEC--TAN",verify="no")


#Enter scamp directory
os.chdir("scamp/")
#Run Source Extractor
print "Running SExtractor..."
sexdir="/astro/depot/sextractor/"
detect_minarea=5
detect_thresh=3
analysis_thresh=1.5
for i in range(len(skynamelist)):
    #quicksex(skynamelist[i],sexdir,detect_minarea,detect_thresh,analysis_thresh,outmasknamelist[i])
    quicksex(skynamelist[i],sexdir,detect_minarea,detect_thresh,analysis_thresh,masknamelist[i])


#Run scamp
print "Running scamp..."
os.system("scamp -dd > default.scamp")
f=open("scamp.inlist","w")
for i in range(len(skynamelist)):
    f.write(skynamelist[i].split(".fits")[0]+".cat"+"\n")
f.close()

directory=os.path.abspath('')
os.system('cp /astro/data/manatee1/NEWFIRM-NDWFS/code/scamp-1.4.6/xsl/scamp.xsl .')
print "scamp -c default.scamp -ASTREF_CATALOG 2MASS -SAVE_REFCATALOG Y -MERGEDOUTCAT_TYPE ASCII_HEAD -MOSAIC_TYPE SAME_CRVAL -DISTORT_DEGREES 5 -VERBOSE_TYPE FULL -AHEADER_GLOBAL /astro/data/manatee1/NEWFIRM-NDWFS/code/calibration/newfirm.good.ahead -FWHM_THRESHOLDS 2,100.0 -FGROUP_RADIUS 0.3 -POSITION_MAXERR 10.0  -PIXSCALE_MAXERR 1.1 -POSANGLE_MAXERR 2 -FLAGS_MASK 0x00fc -WEIGHTFLAGS_MASK 0x00ff -IMAFLAGS_MASK 0x00ff -XSL_URL file://"+directory+"/scamp.xsl @scamp.inlist"
os.system("scamp -c default.scamp -ASTREF_CATALOG 2MASS -SAVE_REFCATALOG Y -MERGEDOUTCAT_TYPE ASCII_HEAD -MOSAIC_TYPE SAME_CRVAL -DISTORT_DEGREES 5 -VERBOSE_TYPE FULL -AHEADER_GLOBAL /astro/data/manatee1/NEWFIRM-NDWFS/code/calibration/newfirm.good.ahead -FWHM_THRESHOLDS 2,100.0 -FGROUP_RADIUS 0.3 -POSITION_MAXERR 10.0  -PIXSCALE_MAXERR 1.1 -POSANGLE_MAXERR 2 -FLAGS_MASK 0x00fc -WEIGHTFLAGS_MASK 0x00ff -IMAFLAGS_MASK 0x00ff -XSL_URL file://"+directory+"/scamp.xsl @scamp.inlist")


end=time.time()

print 'Total elapsed time: ',end-start

