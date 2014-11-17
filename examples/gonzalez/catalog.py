#!/usr/bin/python

#Make Catalogs for NEWFIRM Survey                           

import sys,os,time,string
from math import *
#from scipy import *
#import scipy
#import scipy.optimize
import numpy
# import pyfits.NP_pyfits as pyfits
import pyfits
import pyraf
import pyraf.iraf
from pyraf import iraf
from pyraf.iraf import stsdas
#import SExtractor

def runsex(img,sexdir,detect_minarea,detect_thresh,analysis_thresh,zpt,gain,saturation,fwhm):
    weightimage=img.split(".fits")[0]+".weight.fits"
    flagimage=img.split(".fits")[0]+".flag.fits"
    weight=pyfits.open(weightimage)
    wdat=weight[0].data
    print len(wdat),len(wdat[0])
    #print numpy.max(wdat)
    #print numpy.compress(wdat>0.,wdat,axis=None)
    midweight=numpy.median(wdat[numpy.where(wdat>0)])
    #midweight=numpy.median(numpy.compress(wdat>0.,wdat,axis=None),axis=None)
    print midweight
    wdat2=numpy.where(wdat<midweight/4.,1001.,0.)
    wdat2=numpy.array(wdat2,dtype=numpy.int)
    print 'goober'
    #wdat2=wdat2.astype(numpy.int)
    weight[0].data=wdat2
    if(os.access(flagimage,0.)): os.remove(flagimage)
    weight.writeto(flagimage)
    
    #catname=img.split("rm_")[0].split(".fits")[0]+str(".cat")
    #gain=8.0   #NOT CORRECT -- should be 8.0*NCOMBINE, but NCOMBINE not currently in header...
    imcat=img.split(".fits")[0]+".cat"
    regname=img.split(".fits")[0]+".reg"
    flagregname=img.split(".fits")[0]+".flag.reg"
    if(os.access(imcat,0)): os.remove(imcat)
    sparam="newfirm_sex.param"
    if(os.access(sparam,0)): os.remove(sparam)
    file_par=open(sparam,"w")
    #Establish parameters for output file\n
    #!!!!!MUST GET THIS LIST TO CORRECT LENGTH!!!
    outline="\
	NUMBER\n\
	ALPHA_J2000\n\
	DELTA_J2000\n\
        X_IMAGE\n\
        Y_IMAGE\n\
        XWIN_IMAGE\n\
        YWIN_IMAGE\n\
	FLAGS\n\
        IMAFLAGS_ISO\n\
        NIMAFLAGS_ISO\n\
	FWHM_IMAGE\n\
	FWHM_WORLD\n\
	KRON_RADIUS\n\
        FLUX_RADIUS(1)\n\
        FLUX_RADIUS(2)\n\
        FLUX_RADIUS(3)\n\
	MAG_ISO\n\
	MAG_ISOCOR\n\
	MAG_AUTO\n\
	MAG_PETRO\n\
	MAG_BEST\n\
	MAGERR_ISO\n\
	MAGERR_ISOCOR\n\
	MAGERR_AUTO\n\
	MAGERR_PETRO\n\
	MAGERR_BEST\n\
  	MAG_APER(1)\n\
  	MAG_APER(2)\n\
  	MAG_APER(3)\n\
  	MAG_APER(4)\n\
  	MAG_APER(5)\n\
  	MAG_APER(6)\n\
  	MAG_APER(7)\n\
  	MAG_APER(8)\n\
  	MAG_APER(9)\n\
  	MAG_APER(10)\n\
  	MAG_APER(11)\n\
  	MAG_APER(12)\n\
  	MAG_APER(13)\n\
	MAGERR_APER(1)\n\
	MAGERR_APER(2)\n\
	MAGERR_APER(3)\n\
	MAGERR_APER(4)\n\
	MAGERR_APER(5)\n\
	MAGERR_APER(6)\n\
	MAGERR_APER(7)\n\
	MAGERR_APER(8)\n\
	MAGERR_APER(9)\n\
	MAGERR_APER(10)\n\
	MAGERR_APER(11)\n\
	MAGERR_APER(12)\n\
	MAGERR_APER(13)\n\
	FLUX_AUTO\n\
	FLUXERR_AUTO\n\
	BACKGROUND\n\
	THRESHOLD\n\
	FLUX_MAX\n\
	ISOAREA_IMAGE\n\
	X2_IMAGE\n\
	Y2_IMAGE\n\
	XY_IMAGE\n\
	X2_WORLD\n\
	Y2_WORLD\n\
	XY_WORLD\n\
	CXX_IMAGE\n\
	CYY_IMAGE\n\
	CXY_IMAGE\n\
	CXX_WORLD\n\
	CYY_WORLD\n\
	CXY_WORLD\n\
	ERRCXX_IMAGE\n\
	ERRCYY_IMAGE\n\
	ERRCXY_IMAGE\n\
	ERRCXX_WORLD\n\
	ERRCYY_WORLD\n\
	ERRCXY_WORLD\n\
	A_WORLD\n\
	B_WORLD\n\
	ERRA_WORLD\n\
	ERRB_WORLD\n\
	THETA_WORLD\n\
	THETA_J2000\n\
	ERRTHETA_WORLD\n\
	ERRTHETA_J2000\n\
	ELONGATION\n\
	ELLIPTICITY\n\
        CLASS_STAR\n"
    file_par.write(outline)
    file_par.close()
    #Should later specify convolution filter to match data!!!!
    #Photometric apertures (argues for fixed plate scale of 0.4"/pixel
    # 1,1.5,2,2.5,3,4,5,6,7,8,9,10,20 arcsec
    # 2.5,3.75,5,6.25,7.5,10,12.5,15.0,17.5,20,22.5,25.0,50.0 pixels
    weightthresh=0.001
    #AG!!! MUST PUT IN A WEIGHT THRESHOLD THAT IS A FRACTION OF THE MAX WEIGHT
    #flags="-c "+sexdir+"/config/default.sex -FILTER_NAME "+sexdir+"/config/default.conv -PARAMETERS_NAME \
    convfilter="default.conv"
    pixfwhm=fwhm/0.4
    if(pixfwhm<=2.25): convfilter="gauss_2.0_5x5.conv"
    elif(pixfwhm<=2.75): convfilter="gauss_2.5_5x5.conv"
    elif(pixfwhm<=3.5): convfilter="gauss_3.0_7x7.conv"
    elif(pixfwhm<=4.5): convfilter="gauss_4.0_7x7.conv"
    else: convfilter="gauss_5.0_9x9.conv"
    flags="-c "+sexdir+"/config/default.sex -FILTER_NAME "+sexdir+"/config/"+str(convfilter)+" -PARAMETERS_NAME \
newfirm_sex.param -DETECT_MINAREA "+str(detect_minarea)+" -DETECT_THRESH "+str(detect_thresh)+" -ANALYSIS_THRESH "+\
str(analysis_thresh)+" -STARNNW_NAME "+sexdir+"/config/default.nnw -FILTER Y -DEBLEND_MINCONT .001 -DEBLEND_NTHRESH 64 \
-CHECKIMAGE_TYPE NONE -SEEING_FWHM "+str(fwhm)+" -VERBOSE_TYPE QUIET   -CATALOG_NAME "+imcat+" -BACK_TYPE AUTO   -BACK_VALUE 0. -BACK_SIZE 64 -BACK_FILTERSIZE 3 -BACKPHOTO_TYPE LOCAL -BACKPHOTO_THICK 24  -CATALOG_TYPE ASCII_HEAD \
-PHOT_APERTURES  2.5,3.75,5,6.25,7.5,10,12.5,15.0,17.5,20,22.5,25.0,50.0 -SATUR_LEVEL "+str(saturation)+" -WEIGHT_TYPE MAP_WEIGHT -WEIGHT_IMAGE "+weightimage+" -WEIGHT_THRESH "+str(weightthresh)+" -GAIN "+str(gain)+ \
" -PIXEL_SCALE 0.40 -PHOT_FLUXFRAC 0.5,0.8,0.9 -MAG_ZEROPOINT "+str(zpt)+" -FLAG_TYPE OR -FLAG_IMAGE "+str(flagimage)
    #print flags
#-CHECKIMAGE_TYPE SEGMENTATION -SEEING_FWHM "+str(fwhm)+" -VERBOSE_TYPE QUIET   -CATALOG_NAME "+imcat+" -BACK_TYPE AUTO   -BACK_VALUE 0. -BACK_SIZE 64 -BACK_FILTERSIZE 1 -BACKPHOTO_TYPE LOCAL -BACKPHOTO_THICK 32  -CATALOG_TYPE ASCII_HEAD \
    print sexdir+"/bin/sex "+img+" "+flags
    os.system(sexdir+"/bin/sex "+img+" "+flags)

    file_cat=open(imcat,"r")
    file_reg=open(regname,"w")
    file_flagreg=open(flagregname,"w")
    file_reg.write("# Region file format: DS9 version 4.0\n")
    file_reg.write("global color=green font=\"helvetica 10 normal\" select=1 highlite=1 edit=1 move=1 delete=1 include=1 fixed=0 source\n")
    file_reg.write("fk5\n")
    file_flagreg.write("# Region file format: DS9 version 4.0\n")
    file_flagreg.write("global color=red font=\"helvetica 10 normal\" select=1 highlite=1 edit=1 move=1 delete=1 include=1 fixed=0 source\n")
    file_flagreg.write("fk5\n")

    for line in file_cat.readlines(): 
      if(len(line)>0):
        data=string.split(line)
        if(data[0][0]!="#"):
           if(float(data[57])>0): badvalue=float(data[9])/float(data[57])
           else: badvalue=-999.
	   outline="point("+str(data[1])+","+str(data[2])+") #point=circle\n" #   text={"+str(badvalue)+"}\n"
           if(float(data[8])<1000 and badvalue>-999): 
		file_reg.write(outline)
	   else:
           	#badvalue=float(data[9])/float(data[56])
		if(badvalue<0.5 and badvalue>-999):
		   file_reg.write(outline)
                else: file_flagreg.write(outline)
    file_reg.close()
    file_flagreg.close()
    file_cat.close()


#
########################################
# Main Program			       #
########################################

#Run this from the upper level directory
#Goal is to generate a final catalog for each image, using the header information for ZPT generated by zpt.py

start=time.time()
print 'Started at: ',start

# -- 1. Read input parameters
# Format for list should be the mergedSkySubtracted names
print "Reading command line arguments."
imagelist=sys.argv[1]

# -- 2. Set up fixed parameters for catalog
sexdir="/astro/depot/sextractor"
detect_minarea=10
detect_thresh=1.
analysis_thresh=1.

# -- 3. Loop over images and perform photometry with sextractor
list = open(imagelist, 'rb')
for line in list.readlines():
  data=string.split(line)
  image=data[0]
  #put a line here to gunzip image
  w=pyfits.open(image)
  print image
  zpt=w[0].header['ZPTMED']
  gain=w[0].header['GAIN']
  fwhm=w[0].header['FWHM']
  saturation=w[0].header['SATURATE']
      
  runsex(image,sexdir,detect_minarea,detect_thresh,analysis_thresh,zpt,gain,saturation,fwhm)
