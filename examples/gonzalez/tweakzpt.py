#!/usr/bin/python

#Compute the photometric zeropoints for the images.
#Note that numarray only works on older systems. For newer systems this should be replaced with numpy routines.

import sys,os,time,string
from math import *
import numpy
import scipy
from scipy import *
import pyfits
import pyraf
import pyraf.iraf
from pyraf import iraf
from pyraf.iraf import stsdas
import shutil
import numarray
import numarray.mlab
#import SExtractor

def get2mass(imageRA,imageDec,wgetCat,radius,filter):
   print "Querying catalog."
   print radius
   if (os.access(wgetCat, os.F_OK)): os.unlink(wgetCat)
   wgetCom = 'wget -O ' + wgetCat + ' "http://vizier.cfa.harvard.edu/viz-bin/asu-tsv?-oc.form=dec&-c.r='+str(radius)+'&-c.u=arcmin&-c.geom=r&-out.max=9999&-source=II/246&-c.eq=J2000&-c='+str(imageRA)+'+'+str(imageDec)+'"'
   print wgetCom
   if (not os.access(wgetCat, os.F_OK)): os.system(wgetCom)
   f = open(wgetCat, 'rb')
   s = f.read()
   f.close()
   s = s.split('\n')
   #print s
   for j in range(len(s)-1, -1, -1):
      if (s[j] == '' or s[j][0] == '#'): s.pop(j)
   for j in range(3): s.pop(0)
   catRA = []
   catDec = []
   jcatMag = []
   hcatMag = []
   kcatMag = []
   jcatErr = []
   hcatErr = []
   kcatErr = []
   fcol=3
   jflag = [] 
   hflag = []
   kflag = []
   flag = []

   for j in s:
      #print j
      catRA.append(float(j.split('\t')[0]))
      catDec.append(float(j.split('\t')[1]))

      #J Mag
      n=40; m=46
      if(j[n:m]=='      '): j[n:m]='-1.000'
      jcatMag.append(float(j[n:m]))

      #print j[n:m]

      #H Mag
      n=54; m=60
      if(j[n:m]=='      '): hcatMag.append(float(-1.0))
#j[n:m]='-1.000'
      else: hcatMag.append(float(j[n:m]))
      #print j[n:m]

      #K Mag
      n=68; m=74 
      #print j[n:m]
      if(j[n:m]=='      '): kcatMag.append(float(-1.0))
#j[n:m]='-1.000'
      else: kcatMag.append(float(j[n:m]))
      #print j[n:m]

      #J Error
      n=47; m=53 
      #print string.split(j[n:m]),'hij'
      if(string.split(j[n:m])==[]): jcatErr.append(float(-1.0))
      else: jcatErr.append(float(j[n:m]))
      #print j[n:m]

      #H Error
      n=62; m=67 
      #print string.split(j[n:m]),'hih'
      if(string.split(j[n:m])==[]): hcatErr.append(float(-1.0))
      else: hcatErr.append(float(j[n:m]))
      #print j[n:m]

      #Ks Error
      n=75; m=81 
      #print string.split(j[n:m]),'hik'
      if(string.split(j[n:m])==[]): kcatErr.append(float(-1.0))
      else: kcatErr.append(float(j[n:m]))
      #print j[n:m]

      # JOINT QUALITY FLAG REQUIRING GOOD DATA IN ALL BANDS

      # J Quality flag
      q=1
      if(j[82]=="C" or j[82]=="D" or j[82]=="U"): q=0
      if(j[90]!="1"): q=0
      if(j[94]!="0"): q=0
      if(j[98]!="0"): q=0
      if(j[100]!="0"): q=0
      #jflag.append(q)

      # H Quality flag
      #q=1
      if(j[83]=="C" or j[82]=="D" or j[82]=="U"): q=0
      if(j[91]!="1"): q=0
      if(j[95]!="0"): q=0
      if(j[98]!="0"): q=0
      if(j[100]!="0"): q=0
      #hflag.append(q)

      # Ks Quality flag
      #q=1
      if(j[84]=="C" or j[82]=="D" or j[82]=="U"): q=0
      if(j[92]!="1"): q=0
      if(j[96]!="0"): q=0
      if(j[98]!="0"): q=0
      if(j[100]!="0"): q=0
      #print j[84],j[92],j[96],j[98],j[100],q,'boober'
      #kflag.append(q)
      flag.append(q)

   catRA=numpy.array(catRA)
   catDec=numpy.array(catDec)
   jflag=numpy.array(jflag)
   hflag=numpy.array(hflag)
   kflag=numpy.array(kflag)
   jcatMag=numpy.array(jcatMag)
   hcatMag=numpy.array(hcatMag)
   kcatMag=numpy.array(kcatMag)
   jcatErr=numpy.array(jcatErr)
   hcatErr=numpy.array(hcatErr)
   kcatErr=numpy.array(kcatErr)
   for i in range(len(kcatMag)): print jcatMag[i],hcatMag[i],kcatMag[i]
   return catRA[numpy.where(flag==1)],catDec[numpy.where(flag==1)],jcatMag[numpy.where(flag==1)],jcatErr[numpy.where(flag==1)],hcatMag[numpy.where(flag==1)],hcatErr[numpy.where(flag==1)],kcatMag[numpy.where(flag==1)],kcatErr[numpy.where(flag==1)]

def mean(values):
    """Return the arithmetic average of the values."""
    print len(values)
    return sum(values) / float(len(values))


def sort(seq, compare=cmp):
    """Sort seq (mutating it) and return it.  compare is the 2nd arg to .sort.
    Ex: sort([3, 1, 2]) ==> [1, 2, 3]; reverse(sort([3, 1, 2])) ==> [3, 2, 1]
    sort([-3, 1, 2], comparer(abs)) ==> [1, 2, -3]"""
    if isinstance(seq, str):
        seq = ''.join(sort(list(seq), compare))
    elif compare == cmp:
        seq.sort()
    else:
        seq.sort(compare)
    return seq

def median(values):
    """Return the middle value, when the values are sorted.
    If there are an odd number of elements, try to average the middle two.
    If they can't be averaged (e.g. they are strings), choose one at random.
    Ex: median([10, 100, 11]) ==> 11; median([1, 2, 3, 4]) ==> 2.5"""
    n = len(values)
    values = sort(values[:])
    if n % 2 == 1:
        return values[n/2]
    else:
        middle2 = values[(n/2)-1:(n/2)+1]
        try:
            return mean(middle2)
        except TypeError:
            return random.choice(middle2)



def itmed(arr,thresh):
   arr=numarray.array(arr)
   arr2=arr
   m=numarray.mlab.median(arr)
   lold=0
   l=len(arr)
   while(l!=lold):
      arr2=numarray.compress(abs(arr-m)<thresh,arr)
      m=numarray.mlab.median(arr2)
      lold=l
      l=len(arr2)
   print numarray.mlab.median(arr), numarray.mlab.median(arr2),len(arr2),len(arr)
   return numarray.mlab.median(arr2)



def itmean(arr,darr,thresh):
   arr=numarray.array(arr)
   darr=numarray.array(darr)
   print len(arr),len(darr)
   arr=numarray.compress(darr>0.,arr)
   darr=numarray.compress(darr>0.,darr)
   arr2=arr
   darr2=darr
   m=numarray.sum(arr/darr)/numarray.sum(1./darr)
   lold=0
   l=len(arr)
   while(l!=lold):
      arr2=numarray.compress(abs(arr-m)<thresh,arr)
      darr2=numarray.compress(abs(arr-m)<thresh,darr)
      m=numarray.sum(arr2/darr2)/numarray.sum(1./darr2)
      lold=l
      l=len(arr2)
   print numarray.sum(arr/darr)/numarray.sum(1./darr), numarray.sum(arr2/darr2)/numarray.sum(1./darr2),len(arr2),len(arr)
   return numarray.sum(arr2/darr2)/numarray.sum(1./darr2)


def imgets(img,field):
   iraf.flprcache()
   iraf.flprcache()
   iraf.imgets(img,field)
   return iraf.imgets.value


def quicksex(img,sexdir,detect_minarea,detect_thresh,analysis_thresh,weightimage):
    imcat=img.split(".fits")[0]+".cat"
    if(os.access(imcat,0)): os.remove(imcat)
    sparam="newfirm_sex.param"
    if(os.access(sparam,0)): os.remove(sparam)
    file_par=open(sparam,"w")
    #outline="NUMBER\n X_IMAGE\n Y_IMAGE\n MAG_AUTO\n"
    #Establish parameters for output file\n
    outline="\
	NUMBER\n\
	ALPHA_J2000\n\
	DELTA_J2000\n\
  	MAG_APER(1)\n\
	MAGERR_APER(1)\n\
	MAG_AUTO\n\
	MAGERR_AUTO\n\
	FLAGS\n\
	FLUX_RADIUS\n\
        XWIN_IMAGE\n\
        YWIN_IMAGE\n"
	
    file_par.write(outline)
    file_par.close()
    flags="-c "+sexdir+"/config/default.sex -FILTER_NAME "+sexdir+"/config/default.conv -PARAMETERS_NAME \
          newfirm_sex.param -DETECT_MINAREA "+str(detect_minarea)+" -DETECT_THRESH "+str(detect_thresh)+" -ANALYSIS_THRESH "+\
          str(analysis_thresh)+" -STARNNW_NAME "+sexdir+"/config/default.nnw -DEBLEND_MINCONT .005 \
           -CHECKIMAGE_TYPE NONE  -VERBOSE_TYPE QUIET  -CATALOG_NAME "+imcat+" -CATALOG_TYPE ASCII -PHOT_APERTURES 25.0 -WEIGHT_TYPE MAP_WEIGHT -WEIGHT_IMAGE "+weightimage+" -SATUR_LEVEL 100000. -GAIN 1 -BACK_TYPE AUTO   -BACK_VALUE 0. -BACK_SIZE 64 -BACK_FILTERSIZE 3 -BACKPHOTO_TYPE LOCAL -BACKPHOTO_THICK 24 "
           #-CHECKIMAGE_TYPE NONE  -VERBOSE_TYPE QUIET  -CATALOG_NAME "+imcat+" -BACKPHOTO_TYPE GLOBAL -CATALOG_TYPE ASCII -PHOT_APERTURES 25.0 -SATUR_LEVEL 10000. -WEIGHT_TYPE MAP_WEIGHT -WEIGHT_IMAGE "+weightimage+" -GAIN 8"

    os.system(sexdir+"/bin/sex "+img+" "+flags)

    m=[]
    dm=[]
    ra=[]
    dec=[]
    flag=[]
    ma=[]
    dma=[]
    size=[]
    x=[]
    y=[]

    obs = open(imcat, 'rb')
    for line in obs.readlines():
      data=string.split(line)
      #FLUX_RADIUS less than 2" * 2.5 pixels per arcsec = 5.0 pix
      if(float(data[8])<(2.*2.5)):
         ra.append(float(data[1]))
         dec.append(float(data[2]))
         m.append(float(data[3]))
         dm.append(float(data[4]))
         ma.append(float(data[5]))
         dma.append(float(data[6]))
         flag.append(float(data[7]))
         size.append(float(data[8]))
         x.append(float(data[9]))
         y.append(float(data[10]))
    obs.close()
    return ra,dec,m,dm,ma,dma,flag,size,x,y

def getheaderinfo(image):
    data=pyfits.open(image)
    #return  data[0].header['CRVAL1'],data[0].header['CRVAL2'],data[0].header['FILTER'],str(2.*float(data[0].header['NAXIS1'])*float(data[0].header['CD1_1']))
    #return  data[0].header['CRVAL1'],data[0].header['CRVAL2'],'J',str(2.*abs(float(data[0].header['NAXIS1'])*float(data[0].header['CD1_1']))*60.)
    return  data[0].header['CRVAL1'],data[0].header['CRVAL2'],data[0].header['FILTER'],str(2.*abs(float(data[0].header['NAXIS1'])*float(data[0].header['CD1_1']))*60.),data[0].header['ZPT']
def getoldzpt(image):
    data=pyfits.open(image)
    return data[0].header['ZPT']

def residuals (p,mag1,dmag1,mag2,dmag2,color2,dcolor2):
  zpt=p[0]
  a=p[1]
  rerr=(dmag1**2+dmag2**2+dcolor2**2)**0.5  #fix later
  resid=(mag1-(zpt+mag2-a*color2)/rerr)**2
  
def zptleastsquare(residuals, freeparams,args):
  return scipy.optimize.leastsq(residuals,freeparams,args=args,ftol=1.e-13,xtol=1.e-13,ful_output=1,epsfcn=1.e-1)
  
#
########################################
# Main Program			       #
########################################

#This program should read the JHK zeropoints from the headers, and then use the joint photometry to cull outliers and recompute the zeropoints (color terms?).
#

start=time.time()
print 'Started at: ',start

# -- 1. Read input parameters
# Format for list should be the mergedSkySubtracted names
root=sys.argv[1]
filter=sys.argv[2]
image=root+"."+filter+".fits"
jimage=root+".J.fits"
himage=root+".H.fits"
ksimage=root+".Ks.fits"
minmag=float(sys.argv[3])
#image=root+"."+filter+".fits"
#MAX_MAG=float(sys.argv[3])

# -- 2. Read RA,DEC,FILTER, and image size from header
#put line here to gunzip image
ra,dec,filter,radius,jzpt=getheaderinfo(image)
hzpt=getheaderinfo(jimage)
hzpt=getheaderinfo(himage)
kzpt=getheaderinfo(ksimage)

print filter

# -- 3. Download the 2mass catalog for the appropriate region

# at some point restrict minimu and maximum magnitudes here so that
# I don't waste time sorting stuff out of range
junkcat=image.split(".fits")[0]+".2mass.cat"
catRA,catDec,jcatMag,jcatErr,hcatMag,hcatErr,kcatMag,kcatErr= get2mass(ra,dec,junkcat,radius,filter)
print "Retrieved 2MASS data...\n"
catRA=numpy.array(catRA)
catDec=numpy.array(catDec)
jcatMag=numpy.array(jcatMag)
jcatErr=numpy.array(jcatErr)
hcatMag=numpy.array(hcatMag)
hcatErr=numpy.array(hcatErr)
kcatMag=numpy.array(kcatMag)
kcatErr=numpy.array(kcatErr)


# -- 4. Perform photometry with sextractor
weightimage=image.split(".fits")[0]+".weight.fits"
print weightimage
sexdir="/astro/depot/sextractor"
detect_minarea=25
detect_thresh=3
analysis_thresh=2

print "Performing SExtractor photometry...\n"
obsRA,obsDec,obsMag,obsErr,obsMagAuto,obsErrAuto,obsflag,obssize,obsx,obsy = quicksex(image,sexdir,detect_minarea,detect_thresh,analysis_thresh,weightimage)
imcat=image.split(".fits")[0]+".cat"

print len(obsRA),'lenobsra'

# -- 5. Cross-match 2mass and sextractor catalogs

SEARCH_RADIUS=2./3600. 	#2 arcsec converted to degrees

tmp=zip(catRA,catDec,jcatMag,jcatErr,hcatMag,hcatErr,kcatMag,kcatErr)
tmp.sort()
catRA,catDec,jcatMag,jcatErr,hcatMag,hcatErr,kcatMag,kcatErr=zip(*tmp)

tmp=zip(obsRA,obsDec,obsMag,obsErr,obsMagAuto,obsErrAuto,obsflag,obssize,obsx,obsy)
tmp.sort()
obsRA,obsDec,obsMag,obsErr,obsMagAuto,obsErrAuto,obsflag,obssize,obsx,obsy=zip(*tmp)

#in current setup allows double matches. should fix later.
#should also push objects out of lists once they are matched
x1=[]
y1=[]
ra1=[]
dec1=[]
mag1=[]
dmag1=[]
dmaga1=[]
maga1=[]
flag1=[]
size1=[]
ra2=[]
dec2=[]
mag2=[]
dmag2=[]
s=[]
color2=[]
dcolor2=[]

#for i in range(len(catRA)): print catRA[i],catDec[i], 'cat', i
#for i in range(len(obsRA)): print obsRA[i],obsDec[i], 'obs', i, SEARCH_RADIUS
if(filter=='J'): 
	catMag=jcatMag
	catErr=jcatErr
elif(filter=='H'):
	catMag=hcatMag
	catErr=hcatErr
elif(filter=='Ks'):
	catMag=kcatMag
	catErr=kcatErr
#print numpy.array(jcatMag)
#print numpy.array(jcatMag) - numpy.array(kcatMag)
jk=numpy.array(jcatMag)-numpy.array(kcatMag)
jkerr=(numpy.array(jcatErr)**2+numpy.array(kcatErr)**2)**0.5		
#wrong, as errors should be added as flux errors...fix later when have more time

for i in range(len(catRA)):
   #print catRA[i],catDec[i]
   for j in range(len(obsRA)):
      #print i,j
      if((obsRA[j]-catRA[i])>SEARCH_RADIUS): break
      if(abs((obsRA[j]-catRA[i])*cos(catDec[i]*pi/180.))<SEARCH_RADIUS and abs(obsDec[j]-catDec[i])<SEARCH_RADIUS):
      #else:
	 #print obsRA[j],catRA[i],catDec[i],obsDec[j],SEARCH_RADIUS, 'lima',i,j
	 dr=( (obsDec[j]-catDec[i])**2+ ((obsRA[j]-catRA[i])*cos(catDec[i]*pi/180.))**2)**0.5
         if(dr<SEARCH_RADIUS):
               #print i,j,dr,SEARCH_RADIUS, 'echo'
 	       #print dr*3600.,"arcsec",i,j
	       ra1.append(obsRA[j])
	       dec1.append(obsDec[j])
	       mag1.append(obsMag[j])
	       dmag1.append(obsErr[j])
	       maga1.append(obsMagAuto[j])
	       dmaga1.append(obsErrAuto[j])
	       flag1.append(obsflag[j])
	       size1.append(obssize[j])
	       x1.append(obsx[j])
	       y1.append(obsy[j])
	       ra2.append(catRA[i])
	       dec2.append(catDec[i])
	       mag2.append(catMag[i])
	       dmag2.append(catErr[i])
	       color2.append(jk[i])
	       dcolor2.append(jkerr[i])
	       s.append(dr*3600.)
               break
	
print len(ra1)


	   
   #print ra1[j],dec1[j],ra2[j],dec2[j],mag1[j],mag2[j],dmag1[j],dmag2[j],flag1[j],size1[j],s[j]*3600.

#6.new Compute the zeropoint and color term via a linear least squares fit
p=[20.,0.]
args=mag1,dmag1,mag2,dmag2,color2,dcolor2
plsq=zptleastsquare(residuals,p,args)
print plsq, 'AAAAA'
#perhaps sigma-clip  5-sigma outliers and then repeat??

# -- 6. Compute zeropoint based upon difference within a restricted magnitude
# range
#ETA: 30 minutes
#minmag=12.5
if(filter=="Ks"): thresh=0.4
else: thresh=0.25

if(filter=="Ks"): maxmag=14.25
elif(filter=="H"): maxmag=15.75
else: maxmag=16
#else: maxmag=20
print maxmag,'maxmag'

deltamag=[]
error=[]
file_out=open(image.split(".fits")[0]+".zpt.outdata","w")
for i in range(len(ra1)):
    #print minmag,maxmag,mag1[i],mag2[i],flag1[i]
    if(mag2[i]>minmag and mag2[i]< maxmag and flag1[i]==0):
       deltamag.append(mag2[i]-mag1[i])
       error.append(dmag2[i])
       #file_out.write(str(mag2[i]-mag1[i])+" "+str(dmag2[i])+" "+str(mag1[i])+" "+str(mag2[i])+" "+str(ra1[i])+" "+str(dec1[i])+" "+str(size1[i])+"\n")
       file_out.write(str(mag2[i]-mag1[i])+" "+str(dmag2[i])+" "+str(mag1[i])+" "+str(mag2[i])+" "+str(ra1[i])+" "+str(dec1[i])+" "+str(size1[i])+" "+str(x1[i])+" "+str(y1[i])+"\n")
file_out.close()
   
#print len(deltamag),'lendeltamag' 
if(len(deltamag)>0):
  print median(deltamag),mean(deltamag)

  zpt= itmean(deltamag,error,0.4)
  zptmedian=median(deltamag)
  print zpt,'itmean'
else:
  zpt=0
  zptmedian=0


# -- 7. Print output to screen and file, and write zeropoint information to image header.
w=pyfits.open(image,mode="update")
w[0].header.update('ZPT',zpt, 'Photometric Zeropoint')
w[0].header.update('ZPTMED',zptmedian, 'Photometric Zeropoint')
w[0].header.update('ZPTNSTAR',len(deltamag), 'No. Stars used in ZPT')
w.flush()
w.close()

