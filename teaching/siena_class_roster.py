import requests 
#import BeautifulSoup
from bs4 import BeautifulSoup
import HTMLParser
from HTMLParser import HTMLParser
import sys
import os

# Open the file.
r = open(sys.argv[1])

if os.path.exists('./Siena Class Roster_files'):
    os.rename('Siena Class Roster_files','Siena_Class_Roster_files')

# Try to parse the webpage by looking for the tables.
soup = BeautifulSoup(r)

print "\documentclass{article}"
print "\usepackage{graphicx}"
print "\usepackage{subfig}"

print "\hoffset=-1.50in"
print "\setlength{\\textwidth}{7.5in}"
print "\setlength{\\textheight}{9in}"
print "\setlength{\\voffset}{0pt}"
print "\setlength{\\topmargin}{0pt}"
print "\setlength{\headheight}{0pt}"
print "\setlength{\headsep}{0pt}"


h2s = soup.find_all('h2')
caption = 'Default'
for h in h2s:
    if h.string.find('Class Roster For')>=0:
        caption = h.string

tables = soup.find_all('table')

icount = 0
closed_figure = False
for table in tables:
    
    if table['class'][0]=='datadisplaytable':
       
        rows = table.findAll('tr')
        
        image = None
        name = None
        for row in rows:
            cols = row.findAll('td')
        
            for col in cols:
                
                img = col.findAll('img')
                
                a = col.findAll('p')
                if len(img)>0 and img[0]['src'].find('jpg')>=0:
                    image = img[0]['src']
                    image = image.replace(' ','_')
                if len(a)>0 and a[0]['class']==['leftaligntext']:
                    name = a[0].string


                if name is not None and image is not None:
                    if icount%25==0:
                        print "\\begin{document}"
                        print "\\begin{figure}"
                        print "\centering"
                        closed_figure = False

                    if os.stat(image).st_size < 200:
                        image = './file_not_found.jpg'

                    if icount%5==4:
                        print "\subfloat[%s]{\includegraphics[width=0.19\\textwidth]{%s}}\\\\" % (name,image)
                    else:
                        print "\subfloat[%s]{\includegraphics[width=0.19\\textwidth]{%s}}\\hfill" % (name,image)

                    image = None
                    name = None

                    if icount%25==24:
                        print "\caption{%s}" % (caption)
                        print "\end{figure}"
                        closed_figure = True

                    icount += 1
                    

if not closed_figure:
    print "\caption{%s}" % (caption)
    print "\end{figure}"
print "\end{document}"

