#!/usr/bin/env python
#Script to read data cards and turn them either into a table that can be copied to Excel/OpenOffice
#1;2cor print out in latex format.

import shutil
import subprocess
import os
import sys
import glob
from multiprocessing import Pool
from ROOT import *
import math
from readYields import getYield, getScanYieldDict
######################GLOBAL VARIABLES PUT IN OPTIONS############
ignoreEmptySignal = True


def getYieldDict(cardFnames, region, sig = "", lep = "lep"):
    yields = {}
    for cardFname in cardFnames:
        binname = os.path.basename(cardFname)
        binname = binname.replace('.merge.root','')
        tfile = TFile(cardFname,"READ")
        if 'Scan' in sig:
            yields[binname] = getScanYieldDict(tfile, sig ,region, lep)
            
        else:
            tfile.cd(region)
            dirList = gDirectory.GetListOfKeys()
            sourceYield = {}

            for k1 in dirList:
                h1 = k1.ReadObj().GetName()
                (yd, yerr)  = getYield(tfile, h1, region, (lep,'sele'))
                if 'dummy' in sig:
                    sourceYield[h1] = (0.3, 0)
                else:
                    sourceYield[h1] = (yd, yerr)
                yields[binname] = sourceYield
    return yields


def getPredDict(cardFnames, lep = 'lep'):
    yields = {}
    for cardFname in cardFnames:
        binname = os.path.basename(cardFname)
        binname = binname.replace('.merge.root','')
        tfile = TFile(cardFname,"READ")
        h1 = "background"
 
        (ySR_MB, ySR_MBerr) = getYield(tfile, h1, "SR_MB", (lep,'sele'))

        (yCR_MB, yCR_MBerr) = getYield(tfile, h1, "CR_MB", ('lep','sele'))

        (yCR_SB, yCR_SBerr) = getYield(tfile, h1, "CR_SB", ('lep','sele'))
        (ySR_SB, ySR_SBerr) = getYield(tfile, h1, "SR_SB", ('lep','sele'))
        (Rcs_SB, Rcs_SBerr) = getYield(tfile, h1, "Rcs_SB", ('lep','sele'))
        (kappa, kappaerr) = getYield(tfile, h1, "Kappa", ('lep','sele'))
        
#        print  binname, "CR_SB", (yCR_SB, yCR_SBerr), "SR_SB", (ySR_SB, ySR_SBerr),"RCS_SB",(Rcs_SB, Rcs_SBerr), "Kappa", (kappa, kappaerr)

        predSR_MB = yCR_MB * Rcs_SB * kappa
        if  yCR_MB > 0.01  and kappa > 0.01 and Rcs_SB > 0.01:
            predSR_MBerr = predSR_MB * math.sqrt( (yCR_MBerr/yCR_MB)**2 + (kappaerr/kappa)**2 + (Rcs_SBerr/Rcs_SB)**2)
        else: predSR_MBerr =  1.0 * predSR_MB
        if predSR_MB < 0.001 :
            predSR_MB = 0.01
            predSR_MBerr = 0.01
            #        print  binname, predSR_MB, ySR_MB, yCR_MB, Rcs_SB, kappa
        sourceYield = {}
        sourceYield['data'] = getYield(tfile, 'data', "SR_MB", (lep,'sele'))
        sourceYield['RcsPred'] = (predSR_MB, predSR_MBerr)

        yields[binname] = sourceYield

    return yields

def getSystDict(cardFnames, region, sig = "", lep = "lep", uncert = "default"):
    yields = {}
    for cardFname in cardFnames:
        binname = os.path.basename(cardFname)
        binname = binname.replace('.merge.root','')
        tfile = TFile(cardFname,"READ")
        if 'Scan' in sig:
            sampleDict = getScanYieldDict(tfile, sig ,region, lep)

            if type(uncert) == float:
                sampleDict.update({key: ( uncert, 0)  for key in sampleDict.keys() } )
            
            yields[binname] = sampleDict


        else:
            tfile.cd(region)
            dirList = gDirectory.GetListOfKeys()
            sourceYield = {}

            for k1 in dirList:
                h1 = k1.ReadObj().GetName()
                (yd, yerr)  = getYield(tfile, h1, region, (lep,'sele'))
                if type(uncert) == float:
                    sourceYield[h1] = (uncert , 0)

                yields[binname] = sourceYield
    return yields


def printBinnedTable(yieldsList, yieldsSig, printSource, name):
    benchmark = (1200, 300)
    precision = 2
    if 'Rcs' in name:
        precision = 4
    f = open(name + '.tex','w')
    f.write('\\begin{table}[ht] \n ')
    binNames = sorted(yieldsList[0].keys())
    singleSourceNames = []
    regions = []
    region = ['MB', 'SB', '$\kappa$']
    for i,yields in enumerate(yieldsList):
        if 'Rcs' in name:
#            singleSourceNames.append(sorted( x for x in yields[binNames[0]].keys() if (('EWK' in x) or ('TT' in x)) ))
            singleSourceNames.append(sorted( x for x in yields[binNames[0]].keys() if (x in printSource)))

        else:
            singleSourceNames.append(sorted( x for x in yields[binNames[0]].keys() if not('EWK' in x) ))
    SourceNames = singleSourceNames
    singleSourceNames = sum(singleSourceNames, [])

    nSource = len(singleSourceNames) 
    nCol = nSource + 3
    f.write('\\tiny \n')
    f.write('\\begin{tabular}{|' + (nCol *'%(align)s | ') % dict(align = 'c') + '} \n')

    f.write('\\hline \n')
    f.write('$L_T$ & $H_T$ & nB & ' +  ' %s ' % ' & '.join(map(str, singleSourceNames)) + ' \\\ \n')
    f.write(' $[$ GeV $]$  &   $[$GeV$]$ &  '  + (nSource *'%(tab)s  ') % dict(tab = '&') + ' \\\ \\hline \n')
    #write out all the counts
    for i,bin in enumerate(binNames):
        (LT, HT, B ) = bin.split("_")[0:3]        
        (LT0, HT0, B0 ) = ("","","") 
        if i > 0 :
            (LT0, HT0, B0 ) = binNames[i-1].split("_")[0:3]
        if LT != LT0:
            f.write(('\\cline{1-%s} ' + LT + ' & ' + HT + ' & ' + B) % (nCol))
        if LT == LT0 and HT != HT0:
            f.write(('\\cline{2-%s}  & ' + HT + ' & ' + B) % (nCol))
        elif LT == LT0 and HT == HT0:
            f.write('  &  & ' + B)
        for sources, yields in zip(SourceNames, yieldsList):
            for source in sources:
                print source, yields[bin][source]
                if type(source) == str:
                    f.write((' & %.'+str(precision)+'f $\pm$ %.'+str(precision)+'f') % yields[bin][source])                

                elif type(source) == tuple:
                    f.write((' & %.'+str(precision)+'f $\pm$ %.'+str(precision)+'f') % yieldsSig[bin][source])
        print '--'
        f.write(' \\\ \n')

    f.write('\\hline \n')
    f.write('\\end{tabular} \n')
    f.write('\\end{table} \n')   
    return


def printDataCardsFromMC(mc, sig, mcSys, sigSys, signal, lep):
    
   # print sigSys.keys()
    signalPoint =  {'m1': ('mGlu',signal[0]) , 'm2': ('mLSP',signal[1]) }
    signalName = ('%s_%s') % signalPoint['m1'] + ('_%s_%s') % signalPoint['m2']
    dataCardDir = 'datacards_' + signalName
    try:
        os.stat(inDirSig + '/' + dataCardDir)
    except:
        os.mkdir(inDirSig + '/' + dataCardDir)

    
    binNames = sorted(mc.keys())
    for binName in binNames:
        sigp = {signalName: sig[binName][signal]}
        singleBkgNames = sorted([ x for x in mc[binName].keys() if not('EWK' in x or 'background' in x or 'data' in x)])
        myyields = mc[binName]
        myyields.update(sigp)
        print myyields

        singleSourceNames = sorted([ x for x in myyields.keys() if not('EWK' in x or 'background' in x or 'data' in x)])

        allSys = {}

        #make sure we get all systematics together
        for syst in mcSys.keys():
            allSys.update( { syst : { p: 1 + mcSys[syst][binName][p][0]  for p in singleBkgNames } })
            if syst in sigSys:
                allSys[syst].update( { signalName: 1 + sigSys[syst][binName][signal][0] }  )
            elif not syst in sigSys:
                allSys[syst].update( { signalName: '-' } ) 

        for syst in sigSys.keys():
            allSys.update( { syst : { signalName: 1 + sigSys[syst][binName][signal][0] } } )
            if syst in mcSys:
                allSys[syst].update( { p: 1 + mcSys[syst][binName][p][0]  for p in singleBkgNames } )
            else:
                allSys[syst].update({ p : '-'  for p in singleSourceNames if p in singleBkgNames } )
        
        
            


        iproc = { key: i for (i,key) in enumerate(reversed(singleSourceNames))}
        #print 'print ' + binName +'_.card.txt'

        if ignoreEmptySignal and myyields[signalName][0] > 0.01:
            datacard = open(inDirSig + '/' + dataCardDir + '/' + binName +'_'+lep+'.card.txt', 'w'); 
            datacard.write("## Datacard for cut file %s (signal %s)\n"%(binName,signalName))
            
            #datacard.write("shapes *        * ../common/%s.input.root x_$PROCESS x_$PROCESS_$SYSTEMATIC\n" % binName)
            datacard.write('##----------------------------------\n')
            datacard.write('bin         %s\n' % binName)
            datacard.write('observation %s\n' % myyields['data'][0])
            datacard.write('##----------------------------------\n')
            klen = len(singleSourceNames)
            kpatt = " %%%ds "  % klen
            fpatt = " %%%d.%df " % (klen,3)
            datacard.write('##----------------------------------\n')
            datacard.write('bin             '+(" ".join([kpatt % binName     for p in singleSourceNames]))+"\n")
            datacard.write('process         '+(" ".join([kpatt % p           for p in singleSourceNames]))+"\n")
            datacard.write('process         '+(" ".join([kpatt % iproc[p]    for p in singleSourceNames]))+"\n")
            datacard.write('rate            '+(" ".join([fpatt % myyields[p][0] for p in singleSourceNames]))+"\n")
            datacard.write('##----------------------------------\n')
            
            for syst in allSys:
                name = syst
                if 'uBin' in name:
                    name = name.replace('uBin', binName)
                if 'uLep' in name:
                    name = name.replace('uLep', lep) 
                datacard.write(('%-12s lnN' % name) + " ".join([kpatt % numToBar(allSys[syst][p])  for p in singleSourceNames]) +"\n")             

            datacard.close()
        
    return

def numToBar(num):
    r = num
    if type(num) == float and abs(num - 1.0) < 0.001:
        r = '-'
    return r


# MAIN
if __name__ == "__main__":
    if len(sys.argv) > 2:
        cardDirectory = sys.argv[1]
        cardDirectorySig = sys.argv[2]
    else:
        print "Will stop, give input Dir"
        quit()

    cardDirectory = os.path.abspath(cardDirectory)
    cardDirName = os.path.basename(cardDirectory)

    print 'Using cards from', cardDirName
    inDir = cardDirectory
    cardFnames = glob.glob(inDir+'/*/*68*.root')
    cardFnames9 = glob.glob(inDir+'/*/*9i*.root')
    inDirSig = cardDirectorySig
    cardFnamesSig = glob.glob(inDirSig+'/*/*.root')


    sigYields = getYieldDict(cardFnamesSig,"SR_MB", "T1tttt_Scan", "lep")
    mcYields = getYieldDict(cardFnames,"SR_MB","","lep")


    printBinnedTable((mcYields,), sigYields, [],'SR_table')
    dictRcs_MB = getYieldDict(cardFnames,"Rcs_MB","","lep")
    dictRcs_SB = getYieldDict(cardFnames,"Rcs_SB","","lep")
    dictKappa = getYieldDict(cardFnames,"Kappa","","lep")
    tableList = ['EWK','TT','WJets','TTV']
    for name in tableList:
        printBinnedTable((dictRcs_MB, dictRcs_SB, dictKappa), sigYields, [name],'Rcs_table_'+name)


    sigYields9 = getYieldDict(cardFnamesSig,"SR_MB", "T1tttt_Scan", "lep")
    mcYields9 = getYieldDict(cardFnames9,"SR_MB","","lep")
    printBinnedTable((mcYields9,), sigYields9, [],'SR_table_9')
    dictRcs_MB9 = getYieldDict(cardFnames9,"Rcs_MB","","lep")
    dictRcs_SB9 = getYieldDict(cardFnames9,"Rcs_SB","","lep")
    dictKappa9 = getYieldDict(cardFnames9,"Kappa","","lep")
    tableList = ['EWK','TT','WJets','TTV']
    for name in tableList:
        printBinnedTable((dictRcs_MB9, dictRcs_SB9, dictKappa9), sigYields, [name],'Rcs_table_9_'+name)


#    printBinnedTable(getYieldDict(cardFnames,"Rcs_MB","","lep") , getYieldDict(cardFnamesSig,"Rcs_MB", "T1tttt_Scan", "lep"), 'RCS_MB_table')
#    printBinnedTable(getYieldDict(cardFnames,"Rcs_SB","","lep") , getYieldDict(cardFnamesSig,"Rcs_SB", "T1tttt_Scan", "lep"), 'Rcs_SB_table')

#    for lep in ('ele','mu'):
#        sig = getYieldDict(cardFnamesSig,"SR_MB", "T1tttt_Scan", lep)
 #       mc = getYieldDict(cardFnames,"SR_MB","", lep)
#        pred = getPredDict(cardFnames, lep)        
#        mcSys = {"Flat_uBin_Lep": getSystDict(cardFnames,"SR_MB","dummy", lep, 0.3),
#                 "FlatLumi_Bin_Lep": getSystDict(cardFnames,"SR_MB","dummy", lep, 0.1) }
        
#        sigSys  = { "Xsec_Bin_Lep": getSystDict(cardFnamesSig,"SR_MB", "T1tttt_Scan_Xsec_syst",lep),
#                    "FlatSig_Bin_Lep": getSystDict(cardFnamesSig,"SR_MB", "T1tttt_Scan_Xsec_syst",lep, 0.2),
#                    "FlatLumi_Bin_Lep": getSystDict(cardFnamesSig,"SR_MB", "T1tttt_Scan_Xsec_syst",lep, 0.1) }
        
#        printDataCardsFromMC(pred, sig, {},{},(1200,300), lep)
        
#    pred = getPredDict(cardFnames, 'lep')
#    printBinnedTable(pred, sigYields, 'PredTable')
    #loop stuff needs fixing
    #for sig in sigYields['LT1_HT0_NB1_NJ68_SR'].keys():
    #    print "processing datacards for ", sig
    #    printDataCardsFromMC(mcYields, sigYields, sig)
