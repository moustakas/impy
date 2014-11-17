#!/bin/tcsh
# Some notes re wget:
#  nv - no verbose (output is cleaner for some reason)
#   m - mirror the repository
#  nH - leave off the host directory
#  np - "no parent" directories
#   N - grab the latest version of a file using the timestamp
#   o - dump the output to a log file
#   b - put the job in the background

setenv CLASHARCHIVEDIR /moustakas-archive/clash-archive/
setenv CLASHMIRRORLOG `date "+%Y-%m-%d-%H%M"`'.log'
pushd $CLASHARCHIVEDIR

wget -nv -m -nH -np -N -b -o $CLASHARCHIVEDIR$CLASHMIRRORLOG \
-I '/pub/clash/outgoing/abell_*/,/pub/clash/outgoing/abell_2261/,/pub/clash/outgoing/macs*/,/pub/clash/outgoing/macs1311/,/pub/clash/outgoing/rxj*/,/pub/clash/outgoing/clj1226/,/pub/clash/outgoing/ms2137/,/pub/clash/outgoing/spitzer/,/pub/clash/outgoing/PSFs/,/pub/clash/outgoing/kelson/,/pub/clash/outgoing/color_images/'\
-X '/pub/clash/outgoing/*/SZE_Data/,/pub/clash/outgoing/*/SN/,/pub/clash/outgoing/*/weak_lensing/,/pub/clash/outgoing/*/lens_model/,/pub/clash/outgoing/*/LBT/,\
/pub/clash/outgoing/*/SZE/,/pub/clash/outgoing/*/Lens_Models/,/pub/clash/outgoing/*/VLT/,/pub/clash/outgoing/*/supernova_candidates/,\
/pub/clash/outgoing/*/HST/PhotoZ/drex_image_pipeline/,\
/pub/clash/outgoing/*/HST/catalogs/aplus_pipeline/,\
/pub/clash/outgoing/*/HST/catalogs/aplus_image_pipeline/,\
/pub/clash/outgoing/*/HST/color_images/aplus_image_pipeline/,\
/pub/clash/outgoing/*/HST/galapagos-arjen/,\
/pub/clash/outgoing/*/HST/galaxy_subtracted_images/yoli/,\
/pub/clash/outgoing/*/HST/galaxy_subtracted_images/yoli_subt/,\
/pub/clash/outgoing/*/HST/images/aplus_pipeline/,\
/pub/clash/outgoing/*/HST/images/aplus_image_pipeline/,\
/pub/clash/outgoing/*/HST/images/mosaicdrizzle_image_pipeline/acspar1/,\
/pub/clash/outgoing/*/HST/images/mosaicdrizzle_image_pipeline/acspar2/,\
/pub/clash/outgoing/*/HST/images/mosaicdrizzle_image_pipeline/scale_native/,\
/pub/clash/outgoing/*/HST/images/mosaicdrizzle_image_pipeline/weak_lensing/,\
/pub/clash/outgoing/*/HST/images/mosaicdrizzle_image_pipeline/wfc3par1/,\
/pub/clash/outgoing/*/HST/images/mosaicdrizzle_image_pipeline/wfc3par2' \
-R '*mk_cf_directories,*very_red_objects.pptx,*vi_edit_commands.txt,*CLASHschedule.png,*diskusage.txt' --cut-dirs=3 --ftp-user=ioannis --ftp-password=javert01 "ftp://archive.stsci.edu/pub/clash/outgoing/"

# wget -nv -m -nH -np -N -b --cut-dirs=3 --ftp-user=ioannis --ftp-password=javert01 "ftp://archive.stsci.edu/pub/clash/outgoing/rxj2129/HST/images/mosaicdrizzle_image_pipeline/scale_65mas/clnpix_cosmetic"
# wget -nv -m -nH -np -N --cut-dirs=3 --ftp-user=ioannis --ftp-password=javert01 "ftp://archive.stsci.edu/pub/clash/outgoing/macs2129/HST/images/mosaicdrizzle_image_pipeline/scale_65mas/clnpix_cosmetic"
# wget -nv -m -nH -np -N --cut-dirs=3 --ftp-user=ioannis --ftp-password=javert01 "ftp://archive.stsci.edu/pub/clash/outgoing/rxj2248/HST/images/mosaicdrizzle_image_pipeline/scale_65mas/clnpix_cosmetic"



# test code
## wget -nv -m -nH -np -N -I \
## '/pub/clash/outgoing/abell_1423/' \
## -X '/pub/clash/outgoing/*/HST/PhotoZ/drex_image_pipeline/,\
## /pub/clash/outgoing/*/HST/catalogs/aplus_pipeline/,\
## /pub/clash/outgoing/*/HST/catalogs/aplus_image_pipeline/,\
## /pub/clash/outgoing/*/HST/catalogs/archival_data/,\
## /pub/clash/outgoing/*/HST/color_images/aplus_image_pipeline/,\
## /pub/clash/outgoing/*/HST/galaxy_subtracted_images/yoli/,\
## /pub/clash/outgoing/*/HST/galaxy_subtracted_images/yoli_subt/,\
## /pub/clash/outgoing/*/HST/images/aplus_pipeline/,\
## /pub/clash/outgoing/*/HST/images/aplus_image_pipeline/,\
## /pub/clash/outgoing/*/HST/images/archival_data/,\
## /pub/clash/outgoing/*/HST/images/mosaicdrizzle_image_pipeline/acspar1/,\
## /pub/clash/outgoing/*/HST/images/mosaicdrizzle_image_pipeline/acspar2/,\
## /pub/clash/outgoing/*/HST/images/mosaicdrizzle_image_pipeline/scale_native/,\
## /pub/clash/outgoing/*/HST/images/mosaicdrizzle_image_pipeline/weak_lensing/,\
## /pub/clash/outgoing/*/HST/images/mosaicdrizzle_image_pipeline/wfc3par1/,\
## /pub/clash/outgoing/*/HST/images/mosaicdrizzle_image_pipeline/wfc3par2' \
## -R '*very_red_objects.pptx,*vi_edit_commands.txt,*CLASHschedule.png,*diskusage.txt' --cut-dirs=3 --ftp-user=ioannis --ftp-password=javert01 "ftp://archive.stsci.edu/pub/clash/outgoing/"
## 
## wget -nv -m -nH -np -N -I /pub/clash/outgoing/abell_1423/,/pub/clash/outgoing/abell_1423/Subaru/ --cut-dirs=3 --ftp-user=ioannis --ftp-password=javert01 "ftp://archive.stsci.edu/pub/clash/outgoing/"


# wget -nv -m -nH -np -N -b -o $CLASHARCHIVEDIR$CLASHMIRRORLOG --exclude-directories='/*/*/*/sn,/*/*/*/*/*/*/*/acspar1,/*/*/*/*/*/*/*/acspar2,/*/*/*/*/*/*/*/wfc3par1,/*/*/*/*/*/*/*/wfc3par2,/*/*/*/*/*/*/*/weak_lensing,/*/*/*/*/*/*/aplus_image_pipeline' --cut-dirs=3 --ftp-user=ioannis --ftp-password=javert01 "ftp://archive.stsci.edu/pub/clash/outgoing/"

# wget -nv -m -nH -np -N -b -o $CLASHARCHIVEDIR$CLASHMIRRORLOG --exclude-directories='/*/*/*/*/Subaru,/*/*/*/sn' --cut-dirs=3 --ftp-user=ioannis --ftp-password=javert01 "ftp://archive.stsci.edu/pub/clash/outgoing/"
# find . -name "old" -print | xargs rm -rf {}
popd
# grep saved $CLASHARCHIVEDIR$CLASHMIRRORLOG | grep -v .listing > /tmp/savedclash.log
# mail -s $CLASHARCHIVEDIR$CLASHMIRRORLOG jmoustakas@siena.edu < /tmp/savedclash.log
# \rm /tmp/savedclash.log
