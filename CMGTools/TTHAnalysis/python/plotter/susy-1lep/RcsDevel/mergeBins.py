#!/usr/bin/env python
#import re, sys, os, os.path
#from searchBins import *
import glob, os, sys
from ROOT import *

from optparse import OptionParser
parser = OptionParser()

parser.usage = '%prog pattern [options]'
parser.description="""
Merge search bins from yield files
"""

# extra options for tty
parser.add_option("-v","--verbose",  dest="verbose",  default=0,  type="int",    help="Verbosity level (0 = quiet, 1 = verbose, 2+ = more)")

(options,args) = parser.parse_args()

def matchSB(bname):
    # Matching main band (MB) bins to side band (SB)

    name = bname+'_'

    if 'NJ68' in name:
        # match for NJ68
        name = name.replace('NJ68','NJ45f6')
        name = name.replace('NB2_','NB2i_')
        name = name.replace('NB3i','NB2i')
    elif 'NJ9' in name:
        # match for NJ9i
        name = name.replace('NJ9i','NJ45f9')
        name = name.replace('NB2_','NB2i_')
        name = name.replace('NB3i_','NB2i_')

    name = name[:-1]

    if options.verbose > 0:
        if name!= bname:
            print 'Replaced %s with %s' %(bname,name)
        else:
            print 'No replace: %s with %s' %(bname,name)

    return name #to remove the trailing _

def findMatchBins(binname):

    # have to supply SR binname:
    # LTx_HTx_NBx_NJx_SR

    ## Need 5 yields for RCS
    # * SB SR: sele
    # * SB CR: sele & anti
    # * CR: sele & anti
    ## QCD:

    ## Prediction
    # SR = (CR-CRqcd) * SB_SR/(SB_CR-SB_CRqcd) * kappa

    # find bin names
    if '.' in binname:
        binname = binname[:binname.find('.')]
    purebname = binname[:binname.find('_NJ')]
    
    SR_MBname = binname
    CR_MBname = binname.replace('_SR','_CR')

    #print 'replace', purebname, 'to', matchSB(purebname)

    if 'NJ68' in binname:
        njSB = 'NJ45f6'
    elif 'NJ9i' in binname:
        njSB = 'NJ45f9'
    SBname = matchSB(binname)# + '_NJ45'
    SBname = SBname[:SBname.find('_NJ')] + '_' + njSB
    SR_SBname = SBname + '_SR'
    CR_SBname = SBname + '_CR'

    ## collect files
    if options.verbose > 1:
        print 'Found these bins matching to', binname
        print 'SR of MB:', SR_MBname
        print 'CR of MB:', CR_MBname
        print 'SR of SB:', SR_SBname
        print 'CR of SB:', CR_SBname

    return (SR_MBname, CR_MBname, SR_SBname, CR_SBname)

def getBinName(name, pattern = "NJ68"):

    binname = os.path.basename(name)
    binname = binname.replace('.yields.root','')
    #if '.' in binname: binname = binname[:binname.find('.')]
    #binname = binname[:binname.find('_'+pattern)]

    return binname

def writeBins(ofname, srcdir, binnames):

    # ofname is output fname
    # binnames is source fnames: SR_MBname, CR_MBname, SR_SBname, CR_SBname

    if len(binnames) != 4: print 'Not 4 source names given!'; return 0

    if options.verbose > 1:
        print ofname, srcdir, binnames
        #return 0

    ofile = TFile(ofname,"RECREATE")

    #SR_SBdirname = 'SR_SB'; CR_SBdirname = 'CR_SB'
    #SR_MBdirname = 'SR_MB'; CR_MBdirname = 'CR_MB'

    dirnames = ['SR_MB','CR_MB','SR_SB','CR_SB']

    for idx,dname in enumerate(dirnames):

        ofile.mkdir(dname)

        srcfname = srcdir+binnames[idx]+'.yields.root'
        if not os.path.exists(srcfname):
            print 'Could not find src file', srcfname
            continue

        tfile = TFile(srcfname,"READ")

        for key in tfile.GetListOfKeys():

            obj = key.ReadObj()
            ofile.cd(dname)
            obj.Write()

        tfile.Close()

    ofile.Close()
    return 1

def mergeBins(fileList, pattern = 'NJ68', outdir = None):

    # filter out MB_SR files
    srList = [fname for fname in fileList if pattern in fname]
    srList = [fname for fname in srList if 'SR' in fname]

    if len(srList) == 0:
        print "No files found matching pattern", pattern , "+ SR"
        exit(0)

    # create outdir
    if outdir == None: outdir = os.path.dirname(srList[0]) + "/merged/"
    if not os.path.exists(outdir): os.system("mkdir -p "+outdir)

    srcdir = os.path.dirname(srList[0])+'/'

    # Loop over files
    for fname in srList:

        binname = getBinName(fname, pattern)
        matchbins = findMatchBins(binname)

        if options.verbose > 0:
            print 'File bin name is', binname
            print 'Matching bins are:', matchbins

        ofname = outdir+'/'+binname+'.merge.root'

        writeBins(ofname, srcdir, matchbins)

    return 1


if __name__ == "__main__":

    # Read options and args -- already done above
    if len(args) > 0:
        pattern = args[0]
        print '# pattern is', pattern
    else:
        print "No pattern given!"
        print parser.usage
        exit(0)

    # find files matching pattern
    fileList = glob.glob(pattern+"*.root")

    mergeBins(fileList)
    mergeBins(fileList,'NJ9i')

    print 'Finished'
