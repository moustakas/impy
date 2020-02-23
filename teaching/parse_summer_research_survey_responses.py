#!/usr/bin/env python

import os, pdb
import argparse
import numpy.ma as ma
from astropy.io import ascii

def maketex(year):
    dat = ascii.read('{}-summer-research-survey-responses.tsv'.format(year), format='tab')
    head = dat.colnames

    ncols = len(head)
    nrows = len(dat)
    #indx = [10,11,15,16,21,19,20,12,9,13]

    outfilename = '{}-summer-research-survey-responses'.format(year)
    outfile = open('{}.tex'.format(outfilename), 'w')
    outfile.write(r'\documentclass[12pt,preprint]{aastex}'+'\n')
    outfile.write(r'\usepackage{mdwlist}'+'\n')
    outfile.write(r'\usepackage[parfill]{parskip}'+'\n')
    outfile.write(r'\pagestyle{plain}'+'\n')
    outfile.write(r'\begin{document}'+'\n')

    # loop on each student    
    #for ii in range(26,30):
    for ii in range(nrows):
        ans = dat[:][ii]
        print(ii+1, ans[2])
        #print(ans[2], ans[9], ans[10])

        outfile.write(r'{\large {\bf '+ans[2]+r'}}\\'+'\n')

        outfile.write(r'Email: {}\\'.format(ans[5])+'\n')
        outfile.write(r'Cell: {}\\'.format(ans[6])+'\n')
        outfile.write(r'Class: {}\\'.format(ans[3])+'\n')
        outfile.write(r'Anticipated Graduation Date: {}\\'.format(ans[4])+'\n')

        outfile.write(r'Major(s): {}\\'.format(ans[7].replace('&', '\&'))+'\n')
        if ma.is_masked(ans[8]):
            outfile.write(r'Minor(s): None\\'+'\n')
        else:
            outfile.write(r'Minor(s): {}\\'.format(ans[8])+'\n')
        outfile.write(r'Overall GPA: {:.5}\\'.format(str(ans[9]))+'\n')
        outfile.write(r'Major GPA: {:.5}\\'.format(str(ans[10]))+'\n')
        outfile.write('\n ')
        outfile.write(r'\vspace*{1mm}'+'\n')
        for jj in range(11, 20):
            #print(ii, jj, ans[jj])
            outfile.write(r'{\bf '+head[jj]+r'}\\'+'\n')
            if ma.is_masked(ans[jj]):
                outfile.write(r'\vspace*{3mm}'+'\n')
            else:
                #outfile.write(ans[jj]+'\n')
                outfile.write(ans[jj].replace('&', '\&')+'\n')
            #   for jj in range(len(indx)):
    #       outfile.write(r'{\bf '+head[indx[jj]]+r'}\\'+'\n')
    #       if (ans[indx[jj]]==None): outfile.write(r'\vspace*{3mm}'+'\n')
    #       else: outfile.write(ans[indx[jj]].replace('&',',')+'\n')

            outfile.write('\n')
            outfile.write(r'\vspace*{3mm}'+'\n')
        outfile.write(r'\clearpage'+'\n')

    outfile.write(r'\end{document}'+'\n')
    outfile.close()

    return outfilename

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-y', '--year', default=2020, type=int, help='Year to parse.')
    args = parser.parse_args()

    outfile = maketex(args.year)
    os.system('pdflatex {}'.format(outfile))
    for suffix in ('.aux', '.log'):
        os.remove('{}{}'.format(outfile, suffix))
        
    

    

