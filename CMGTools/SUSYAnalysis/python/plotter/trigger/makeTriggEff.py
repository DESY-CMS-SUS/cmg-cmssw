#!/usr/bin/python

import sys

from math import *
from array import array
from ROOT import *

from triggTools import *

# global storages
_canvStore = []
_histStore = {}
_hEffStore = {}

_fitrStore = []

_colorList = [2,4,8,9,7,3,6] + range(10,50)

def getHistsFromTree(tree, var = 'MET', refTrig = '', cuts = '', testTrig = '', maxEntries = -1, lumi = -1):

    # maximum number of entries to process
    if maxEntries == -1:
        maxEntries = tree.GetEntries()

    # histogram name prefix
    histPrefix = 'h' + var + '_'

    # plot option
    plotOpt = 'e1'

    # histogram list
    histList = []

    # prepend HLT name
    testTrig = ['HLT_'+name.replace('HLT_','') for name in testTrig]

    # names
    if 'HLT' in refTrig:
        refName = refTrig.replace('HLT_','')
    elif refTrig != '':
        refName = refTrig#'PreSel'
        refTrig = ''
    else:
        refName = 'PreSel'

    ## name replacement
    refName = renameTrig(refName)

    # for OR and AND test triggers
    if '||' in refTrig:
        tnames = refTrig.replace('HLT_','').split('||')
        refTrigName = tnames[0]
        refTrig = '(' + 'HLT_'+tnames[0].replace('HLT_','')

        for name in tnames[1:]:
            refTrigName += '||' + name
            refTrig += '||' + 'HLT_'+name.replace('HLT_','')
        refTrig += ')'

        print refTrigName
        print refTrig
    else:
        refTrigName = refTrig.replace('HLT_','')

    refTrigName = renameTrig(refTrigName)

#    refName = refTrigName
#    print 'New', refTrigName, refTrig
#    exit(0)

    rname = histPrefix + refName

    cname = var + '_' + refName
    ctitle = 'Plots for reference:' + refName

    if cuts != '':
        ctitle += ' cut: ' + cuts

    if refTrig != '':
        #cuts += ' && HLT_' + refTrig.replace('HLT_','')
        cuts += ' && ' + refTrig
        htitle = refTrig.replace('HLT_','')#'Ref: ' + refTrig
    else:
        htitle = 'Preselection'

    print 'Going to draw', ctitle

    # make canvas
    canv = TCanvas(cname,ctitle,800,800)

    # make hist
    nbins = 50

    varBinSize = False

    if 'MET' in var:
        hRef = TH1F(rname,htitle,nbins,0,1000)
        varBinSize = True
        hRef = TH1F(rname,htitle,len(met_bins)-1,array('f',met_bins))
    elif 'HT' in var:
        varBinSize = True
        hRef = TH1F(rname,htitle,len(ht_bins)-1,array('f',ht_bins))
        #hRef = TH1F(rname,htitle,nbins,0,3000)
    elif 'LT' in var:
        hRef = TH1F(rname,htitle,nbins,0,1000)
        varBinSize = True
        hRef = TH1F(rname,htitle,len(lt_bins)-1,array('f',lt_bins))
    elif 'pt' in var:
        varBinSize = True
        hRef = TH1F(rname,htitle,len(pt_bins)-1,array('f',pt_bins))
        #hRef = TH1F(rname,htitle,nbins,0,200)
    elif 'eta' in var:
        #print eta_bins; exit(0)
        #hRef = TH1F(rname,htitle,nbins,-2.5,2.5)
        hRef = TH1F(rname,htitle,len(eta_bins)-1,array('f',eta_bins))
    else:
        hRef = TH1F(rname,htitle,nbins,0,1000)

    ## lumi scaling
    if lumi == 0:
        # don't do lumi scaling on MC
        doLumi = False
        CMS_lumi.lumi_13TeV = "MC"
        CMS_lumi.extraText = "Simulation"
        hRef.GetYaxis().SetTitle('MC counts')
    elif lumi > 0:
        # make lumi label for data
        doLumi = False
        CMS_lumi.lumi_13TeV = str(lumi) + " pb^{-1}"
        CMS_lumi.extraText = "Preliminary"
        hRef.GetYaxis().SetTitle('Events')
    elif lumi < 0:
        # do lumi scaling for MC
        doLumi = True
        lumi = abs(lumi)
        CMS_lumi.lumi_13TeV = str(lumi) + " fb^{-1}"
        CMS_lumi.extraText = "Simulation"
        hRef.GetYaxis().SetTitle('Events')

    # make reference plot
    if not doLumi:
        #hRef.Sumw2(False)
        tree.Draw(var + '>>' + hRef.GetName(),cuts,plotOpt, maxEntries)
        print '# Drawing', hRef.GetName(), 'with cuts', cuts
    else:
        hRef.Sumw2()

        wt = 1000*lumi/float(maxEntries)
        print '# Weight for %2.2f lumi and maxEntries %10.f is %f' %(lumi, maxEntries,wt)
        weight = str(wt) + ' * Xsec'
        if cuts != '': wcuts = weight + '*(' + cuts + ')'
        else: wcuts = weight
        print '# Drawing', hRef.GetName(), 'with cuts', wcuts

        tree.Draw(var + '>>' + hRef.GetName(),wcuts,plotOpt, maxEntries)
        hRef.SetMaximum(hRef.GetMaximum() * 2)

    ## do overflow
    doOverflow = False#True

    if doOverflow:
        n = hRef.GetNbinsX()
        print hRef.GetBinContent(n+1),hRef.GetBinContent(n)
        hRef.SetBinContent(n,hRef.GetBinContent(n+1)+hRef.GetBinContent(n))
        hRef.SetBinError(n,hypot(hRef.GetBinError(n+1),hRef.GetBinError(n)))
        hRef.SetBinContent(n+1,0)
        hRef.SetBinError(n+1,0)
        hRef.Sumw2(False)

    print '# Found', hRef.Integral(), 'events'

    hRef.SetLineColor(1)
    # axis set up
    hRef.SetStats(0)

    label = varToLabel(var)
    if 'eta' not in label:
        label += ' [GeV]'

    hRef.GetXaxis().SetTitle(label)
    hRef.GetYaxis().SetTitleOffset(1.2)
    canv.SetLogy()

    gPad.Update()

    _histStore[hRef.GetName()] = hRef
    histList.append(hRef)

    # loop over test triggers:
    for ind, trig in enumerate(testTrig):

        # for OR and AND test triggers
        if '||' in trig:
            tnames = trig.replace('HLT_','').split('||')
            trigName = tnames[0]
            trig = '(' + 'HLT_'+tnames[0].replace('HLT_','')

            for name in tnames[1:]:
                trigName += '||' + name
                trig += '||' + 'HLT_'+name.replace('HLT_','')
            trig += ')'

            print trigName
            print trig
        else:
            trigName = trig.replace('HLT_','')

        trigName = renameTrig(trigName)

        hname = 'h' + var + '_' + trigName

        hTest = hRef.Clone(hname)
        hTest.SetTitle(trigName)

        hTest.SetLineColor(_colorList[ind])

        # cuts

        if cuts != '':
            tcuts = cuts + ' && ' + trig
        else:
            tcuts = trig

        print '# Drawing', hTest.GetName(), 'with cuts', tcuts

        # lumi scale
        if not doLumi:
            tree.Draw(var + '>>' + hTest.GetName(),tcuts,plotOpt+'same', maxEntries)
            #hTest.Sumw2(False)
        else:
            #hTest.Sumw2()
            if tcuts != '': wtcuts = weight + '*(' + tcuts + ')'
            else: wtcuts = weight
            tree.Draw(var + '>>' + hTest.GetName(),wtcuts,plotOpt+'same', maxEntries)

        if doOverflow:
            n = hTest.GetNbinsX()
            hTest.SetBinContent(n,hTest.GetBinContent(n+1)+hTest.GetBinContent(n))
            hTest.SetBinError(n,hypot(hTest.GetBinError(n+1),hTest.GetBinError(n)))
            hTest.SetBinContent(n+1,0)
            hTest.SetBinError(n+1,0)
            hTest.Sumw2(False)

        print '# Found', hTest.Integral(), 'events'

        gPad.Update()

        _histStore[hTest.GetName()] = hTest
        histList.append(hTest)

    # if var bin sizes
    if varBinSize and False: # leave it off for now (strange errors)

        # add /bin in Y axis label
        hRef.GetYaxis().SetTitle(hRef.GetYaxis().GetTitle() + '/bin')

        for hist in histList:
            for bin in range(1,hist.GetNbinsX()+1):
                binC = hist.GetBinContent(bin)
                binE = hist.GetBinError(bin)
                binW = hist.GetBinWidth(bin)

                binV = binC/binW
                binE = binE/binW
                #print binC, binW, binV

                hist.SetBinContent(bin, binV)
                #hist.SetBinError(bin, binE)

        hist.Sumw2(False)

    #hRef.SetTitle(ctitle)

    # legend
    leg = canv.BuildLegend()
    leg.SetFillColor(0)
    #leg.SetHeader(ctitle.replace('&&','\n'));

    # plot CMS info
    CMS_lumi.CMS_lumi(canv, 4, iPos)

    gPad.Update()
    _canvStore.append(canv)

    return histList

def plotEff(histList, var = 'HT', doFit = False):


    ## histList: [hReference, hTest1, hTest2,...]

    # hist prefix
    histPrefix = 'h' + var + '_'

    # reference hist should be first
    hRef = histList[0]
    hRefEff = hRef.Clone(hRef.GetName()+'Eff')
    # set reference eff to 1
    hRefEff.Divide(hRef)

    hRefEff.GetYaxis().SetTitle("Efficiency")

    if not doFit:
        cname = hRef.GetName().replace('h'+var,var) + '_Eff_'
    else:
        cname = hRef.GetName().replace('h'+var,var) + '_EffFit'

    ctitle = 'Eff for reference:' + hRefEff.GetName()

    ## make canvas
    canv = TCanvas(cname,ctitle,800,800)
    #canv.UseGL()
    #canv.SetSupportGL(True)
    ## style

    ## legend
    leg = getLegend('fit2')

    # set reference eff to 1
    for bin in range(1,hRefEff.GetNbinsX()+1):
        hRefEff.SetBinContent(bin,1)
        hRefEff.SetBinError(bin,0)

    hRefEff.Draw()
    #leg.AddEntry(0,'Reference: ' + hRefEff.GetName(),'')
    pureName = hRef.GetName().replace('h'+var+'_','')
    leg.SetHeader('Reference: ' + cleanName(pureName))
    #leg.AddEntry(hRefEff,hRefEff.GetTitle(),'lp')

    # axis set up
    hRefEff.SetStats(0)
    #hRef.GetXaxis().SetTitle(var)
    hRefEff.GetYaxis().SetRangeUser(0.01,1.5)
    canv.SetTicks(1,0)
    #canv.SetLogy()

    '''
    if len(histList) == 2:
        # add normalized hist shape
        hRef.SetFillColorAlpha(hRef.GetLineColor(),0.35)
        hRef.DrawNormalized("same")
        leg.AddEntry(hRef,varToLabel(var)+' distribution','f')
    '''

    plotOpt = 'same'

    gPad.Update()

    # loop over test
    #for ind,hname in enumerate(nameList):
    for ind,hist in enumerate(histList[1:]):

        #hist = _histStore[hname]
        hname = hist.GetName()

        # filter out hists
        #if histPrefix not in hname: continue
        #if 'Ref' in hname: continue

        htitle = hname.replace(histPrefix,'')
        hname = hname.replace('h','hEff')

        print 'Drawing', hname, 'from', hRef.GetName()

        ## Divide
        hEff = hist.Clone(hname)
        hEff.Divide(hRef)

        ## TEfficiency
        tEff = TEfficiency(hist,hRef)
        tEff.SetName(hname);#+';'+var+';Efficiency')
        tEff.SetTitle(htitle)

        # style
        if len(histList) == 2: # for one single curve
            tEff.SetLineColor(1)#kBlue)
            tEff.SetMarkerColor(1)#kBlue)
        else:
            tEff.SetLineColor(hist.GetLineColor())
            tEff.SetMarkerColor(hist.GetLineColor())

        tEff.SetFillColor(0)
        tEff.SetMarkerStyle(20)

        tEff.Draw(plotOpt)
        leg.AddEntry(tEff,tEff.GetTitle(),'lpe')

        if len(histList) == 2:

            # transparent color for hist and axis
            hCol = kBlue #hist.GetLineColor()
            hAlpha = 0.35

            # add normalized hist shape
            hist.SetFillColorAlpha(hCol,hAlpha)
            hist.SetLineColorAlpha(hCol,hAlpha)
            hist.DrawNormalized("samehist")
            hist.Scale()

            leg.AddEntry(hist,varToLabel(var)+' distribution','f')

            # extra axis
            #scale = 1.5*hist.GetEntries()#/hist.GetMaximum()#*1.1/1.5
            scale = hist.GetEntries()#/hist.GetMaximum()#*1.1/1.5
            #scale = 1.5

            raxis = TGaxis(gPad.GetUxmax(),gPad.GetUymin(),gPad.GetUxmax(), gPad.GetUymax()/1.5,0.01,scale,505,"+L")
            raxis.SetLineColor(hCol)
            raxis.SetLabelColor(hCol)
            raxis.SetTitleColor(hCol)
            raxis.SetTitle("Events")
            raxis.Draw()
            SetOwnership(raxis, 0)

        if 'same' not in plotOpt: plotOpt += 'same'

        gPad.Update()

        #SetOwnership(tEff,0)

        if doFit and hEff.GetEntries() > 0 and 'eta' not in var:
            ## Fitting turn on curve
            print 'Fitting...'

            xmin = hEff.GetXaxis().GetXmin()
            xmax = hEff.GetXaxis().GetXmax()

            fturn = TF1("turnon",turnon_func,xmin,xmax,3)
            fturn.SetParNames('halfpoint','width','plateau')
            fturn.SetParLimits(0,0,10000)
            fturn.SetParLimits(1,0.1,10000)
            fturn.SetParLimits(2,0,1)

            fturn.SetLineColor(hEff.GetLineColor())

            ## get painted graph and fit with turn-on
            #print tEff
            gEff = tEff.GetPaintedGraph()
            #print gEff
            #gEff = hEff

            ## get estimate of parameters
            expPlateau = min(hEff.GetMaximum(),0.99)
            expHalfP = max(hEff.GetBinCenter(hEff.FindFirstBinAbove(0.5)),0)
            expWidth = TMath.Sqrt(expHalfP)

            #fturn.SetParameters(300,100,1)
            fturn.SetParameters(expHalfP,expWidth,expPlateau)

            ## do fit
            fitr = gEff.Fit(fturn,'S Q EX0')#EX0

            SetOwnership(gEff,0)

            halfpoint = fitr.Value(0)
            width = fitr.Value(1)
            plateau = fitr.Value(2)

            print 'Expected values: halfpoint = %5.2f, width = %5.2f, plateau = %5.2f' % (expHalfP, expWidth, expPlateau)
            print 'Fit result: halfpoint = %5.2f, width = %5.2f, plateau = %5.2f' % (halfpoint, width, plateau)

            # get 0.99% of plateau
            xpl = 0
            for x in range(int(xmin),int(xmax)):
                tpl = fturn(x)
                if tpl > 0.98*plateau:
                    xpl = x
                    break

            plattxt = '#varepsilon =  %2.1f#pm%2.1f%%' % (plateau*100, fitr.Error(2)*100)
            if xpl > 0:
                plattxt += ' at %s = %3.0f GeV' % (varToLabel(var),xpl)

            leg.AddEntry(0,"Plateau:","")
            leg.AddEntry(fturn,plattxt,"l")

            gPad.Update()

            # get stat box
            #stats = gEff.GetListOfFunctions().FindObject("stats")
            #stats.SetLineColor(gEff.GetLineColor())

            _fitrStore.append((hname,halfpoint, width, plateau))

        _hEffStore[hname] = tEff

    # remove refEff
    #gPad.GetListOfPrimitives().Remove(hRef)

    # legend
    #leg = canv.BuildLegend()
    #leg.SetFillColor(0)
    leg.Draw()
    SetOwnership( leg, 0 )

    #leg.GetListOfPrimitives().Remove(hRefEff)

    ## CMS lumi
    CMS_lumi.CMS_lumi(canv, 4, iPos)

    gPad.Update()

    _hEffStore[hRefEff.GetName] = hRefEff
    _canvStore.append(canv)

    return 1

def makeEffPlots(tree, lumi = -1, maxEntries = -1, doFit = False, varList = [], refTrig = '', testTrig = [], cuts = ''):

    # lumi dir
    if lumi == 0:
        # unscaled MC counts
        lumiDir = 'MC/LumiMC/'
    elif lumi < 0:
        # scaled MC
        lumiDir = 'MC/Lumi'+str(-lumi).replace('.','p')+'fb/'
    elif lumi > 0:
        # data
        lumiDir = 'Data/Lumi'+str(lumi).replace('.','p')+'pb/'

    # make suffix from testTrigNames
    suffix = 'test'
    for trig in testTrig:
        suffix +=  '_' + trig.replace('||','OR')

    # final output dir:
    lumiDir = 'plots/1d/' + lumiDir

    print 80*'#'
    print '## Going to save plots to', lumiDir

    for var in varList:

        histList = getHistsFromTree(tree,var,refTrig, cuts, testTrig, maxEntries, lumi)
        plotEff(histList, var, doFit)
        saveCanvases(_canvStore, lumiDir,suffix, _batchMode)

        # empty stores for further use
        del _canvStore[:]
        _histStore.clear()
        _hEffStore.clear()
        del _fitrStore[:]

    return 1

if __name__ == "__main__":

    ## remove '-b' option
    _batchMode = False

    if '-b' in sys.argv:
        sys.argv.remove('-b')
        _batchMode = True

    if len(sys.argv) > 1:
        fileName = sys.argv[1]
        print '#fileName is', fileName
    else:
        print '#No file names given'
        exit(0)

    tfile  = TFile(fileName, "READ")

    if not tfile:
        print "Couldn't open the file"
        exit(0)

    ## Get tree from file
    # for friend trees
    tree = tfile.Get('sf/t')
    # for cmg trees
    #tree = tfile.Get('tree')

    nentries = tree.GetEntries()
    print 'Entries in tree:', nentries

    ## SETTINGS
    # max entries to process
    maxEntries = -1#100000
    # do efficiency fit
    doFit = True
    # luminosity: 0 takes MC counts, >0 is data, <0 is for MC scaling
    lumi = 0


    ###################
    ###################
    # DATA
    ###################
    ###################

    basecuts = 'METfilters && '
    #basecuts = ''

    doFit = True

    if 'SingleEl' in fileName:
        ## Electrons
        #lumi = 40.03 # SingleEl RunB
        lumi = 42 # SingleEl RunB

        refTrig = 'IsoEle32'
        testTrig = ['EleHT350MET70']

        varList = ['HT']
        #cuts = basecuts + 'Selected == 1 && nEl >= 1 && Lep_pt > 25 && METNoHF  > 200'
        cuts = basecuts + 'Selected == 1 && nEl >= 1 && Lep_pt > 25 && MET  > 200'
        #makeEffPlots(tree, lumi, maxEntries, doFit, varList, refTrig, testTrig, cuts)

        varList = ['MET']
        cuts = basecuts + 'Selected == 1 && nEl >= 1 && Lep_pt > 25 && HT  > 500'
        #makeEffPlots(tree, lumi, maxEntries, doFit, varList, refTrig, testTrig, cuts)

        varList = ['METNoHF']
        cuts = basecuts + 'Selected == 1 && nEl >= 1 && Lep_pt > 25 && HT  > 500'
        #makeEffPlots(tree, lumi, maxEntries, doFit, varList, refTrig, testTrig, cuts)

        refTrig = 'IsoEle32'
        testTrig = ['Ele105']

        varList = ['Lep_eta']
        cuts = basecuts + 'Selected == 1 && nEl >= 1 && Lep_pt > 130'
        #cuts = basecuts + 'nEl >= 1 && Lep_pt > 5'
        makeEffPlots(tree, lumi, maxEntries, doFit, varList, refTrig, testTrig, cuts)

    elif 'SingleMu' in fileName:
        ## Muons
        #lumi = 40.0 # SingleMu RunB
        lumi = 42 # SingleMu RunB

        refTrig = 'IsoMu27'
        testTrig = ['MuHT350MET70']

        varList = ['HT']
        #cuts = basecuts + 'Selected == 1 && nMu >= 1 && Lep_pt > 25 && MET  > 200'
        cuts = basecuts + 'Selected == 1 && nMu >= 1 && Lep_pt > 25 && METNoHF  > 200'
        makeEffPlots(tree, lumi, maxEntries, doFit, varList, refTrig, testTrig, cuts)

        varList = ['MET']
        cuts = basecuts + 'Selected == 1 && nMu >= 1 && Lep_pt > 25 && HT  > 500'
        makeEffPlots(tree, lumi, maxEntries, doFit, varList, refTrig, testTrig, cuts)

        varList = ['METNoHF']
        cuts = basecuts + 'Selected == 1 && nMu >= 1 && Lep_pt > 25 && HT  > 500'
        makeEffPlots(tree, lumi, maxEntries, doFit, varList, refTrig, testTrig, cuts)

        varList = ['MET']
        cuts = basecuts + 'Selected == 1 && nMu >= 1 && Lep_pt > 25 && HT  > 500'
        makeEffPlots(tree, lumi, maxEntries, doFit, varList, refTrig, testTrig, cuts)

        testTrig = ['Mu50']
        varList = ['Lep_pt']
        cuts = basecuts + 'Selected == 1 && nMu >= 1 && Lep_pt > 25'
        makeEffPlots(tree, lumi, maxEntries, doFit, varList, refTrig, testTrig, cuts)

    elif 'SingleLep' in fileName:
        ## Ele + Mu
        lumi = 42.0 # SingleEl/Mu RunB

        basecuts += ' (PD_SingleMu + PD_SingleEl == 1) &&'

        refTrig = 'HLT_IsoMu27||HLT_IsoEle32'
        testTrig = ['MuHT350MET70||EleHT350MET70']

        varList = ['HT']
        cuts = basecuts + 'Selected == 1 && nLep == 1  && Lep_pt > 25 && MET  > 200 && HT > 180'
        makeEffPlots(tree, lumi, maxEntries, doFit, varList, refTrig, testTrig, cuts)

        varList = ['MET']
        cuts = basecuts + 'Selected == 1 && nLep >= 1 && Lep_pt > 25 && HT  > 500'
        makeEffPlots(tree, lumi, maxEntries, doFit, varList, refTrig, testTrig, cuts)

    elif 'JetHT' in fileName:

        # Jet + HT triggers
        if 'dcsonly' in fileName:
            lumi = 50
        elif 'Lep' in fileName:
            lumi = 42.
        elif 'golden40pb' in fileName:
            lumi = 40
        elif 'golden42pb' in fileName:
            lumi = 42.0
        else:
            lumi = 42.0

        '''
        ## LT
        varList = ['LTNoHF']
        refTrig = 'JetHT'
        #refTrig = 'HLT_HT800'

        testTrig = ['Mu50||MuHT350MET70||Ele105||EleHT350MET70']
        cuts = basecuts + 'Selected == 1 && nLep == 1 && nVeto == 0 && Lep_pt > 25 && HT > 400'
        #makeEffPlots(tree, lumi, maxEntries, doFit, varList, refTrig, testTrig, cuts)

        cuts = basecuts + 'Selected == 1 && nMu >= 1 && Lep_pt > 25 && HT > 500'
        testTrig = ['Mu50||MuHT350MET70']
        #makeEffPlots(tree, lumi, maxEntries, doFit, varList, refTrig, testTrig, cuts)

        cuts = basecuts + 'Selected == 1 && nEl >= 1 && Lep_pt > 25 && HT > 500 && abs(Lep_eta) < 1.5'
        testTrig = ['Ele105||EleHT350MET70']
        makeEffPlots(tree, lumi, maxEntries, doFit, varList, refTrig, testTrig, cuts)

        varList = ['LT']

        cuts = basecuts + 'Selected == 1 && nMu >= 1 && Lep_pt > 25 && HT > 500'
        testTrig = ['Mu50||MuHT350MET70']
        #makeEffPlots(tree, lumi, maxEntries, doFit, varList, refTrig, testTrig, cuts)

        cuts = basecuts + 'Selected == 1 && nEl >= 1 && Lep_pt > 25 && HT > 500'
        testTrig = ['Ele105||EleHT350MET70']
        #makeEffPlots(tree, lumi, maxEntries, doFit, varList, refTrig, testTrig, cuts)

        '''

        #### LEPTON LEG
        '''
        #refTrig = 'JetHT_EE'#HLT_HT800'#||HLT_HT350MET100'
        refTrig = 'JetHT'#HLT_HT800'

        ## Lep PT
        varList = ['Lep_pt']

        testTrig = ['Ele105']
        cuts = basecuts + 'Selected == 1 && nEl == 1 && Lep_pt > 50'# && abs(Lep_eta) < 1.5'
        makeEffPlots(tree, lumi, maxEntries, doFit, varList, refTrig, testTrig, cuts)

        testTrig = ['Mu50']
        cuts = basecuts + 'Selected == 1 && nMu >= 1 && Lep_pt > 5'
        makeEffPlots(tree, lumi, maxEntries, doFit, varList, refTrig, testTrig, cuts)

        ## Lep ETA
        varList = ['Lep_eta']

        testTrig = ['Ele105']
        cuts = basecuts + 'Selected == 1 && nEl == 1 && Lep_pt > 120'
        makeEffPlots(tree, lumi, maxEntries, doFit, varList, refTrig, testTrig, cuts)

        testTrig = ['Mu50']
        cuts = basecuts + 'Selected == 1 && nMu >= 1 && Lep_pt > 60'
        makeEffPlots(tree, lumi, maxEntries, doFit, varList, refTrig, testTrig, cuts)
        '''

        ## Ele105 tests
        testTrig = ['Ele105']


        ## EB -- barrel
        refTrig = 'JetHT'

        varList = ['Lep_pt']; cuts = basecuts + 'Selected == 1 && nEl == 1 && Lep_pt > 50'
        makeEffPlots(tree, lumi, maxEntries, doFit, varList, refTrig, testTrig, cuts)
        varList = ['Lep_eta']; cuts = basecuts + 'Selected == 1 && nEl == 1 && Lep_pt > 120'
        makeEffPlots(tree, lumi, maxEntries, doFit, varList, refTrig, testTrig, cuts)

        '''
        ## EB -- barrel
        refTrig = 'JetHT_EB'

        varList = ['Lep_pt']; cuts = basecuts + 'Selected == 1 && nEl == 1 && Lep_pt > 50 && abs(Lep_eta) < 1.5'
        makeEffPlots(tree, lumi, maxEntries, doFit, varList, refTrig, testTrig, cuts)
        varList = ['Lep_eta']; cuts = basecuts + 'Selected == 1 && nEl == 1 && Lep_pt > 120 && abs(Lep_eta) < 1.5'
        makeEffPlots(tree, lumi, maxEntries, doFit, varList, refTrig, testTrig, cuts)

        ## EB -- barrel
        refTrig = 'JetHT_EE'

        varList = ['Lep_pt']; cuts = basecuts + 'Selected == 1 && nEl == 1 && Lep_pt > 50 && abs(Lep_eta) > 1.5'
        makeEffPlots(tree, lumi, maxEntries, doFit, varList, refTrig, testTrig, cuts)
        varList = ['Lep_eta']; cuts = basecuts + 'Selected == 1 && nEl == 1 && Lep_pt > 120 && abs(Lep_eta) > 1.5'
        makeEffPlots(tree, lumi, maxEntries, doFit, varList, refTrig, testTrig, cuts)

        ## HoverE < 0.05
        refTrig = 'JetHT_HoE'#HLT_HT800'

        varList = ['Lep_pt']; cuts = basecuts + 'Selected == 1 && nEl == 1 && Lep_pt > 50 && Lep_hOverE < 0.05'# && abs(Lep_eta) < 1.5'
        makeEffPlots(tree, lumi, maxEntries, doFit, varList, refTrig, testTrig, cuts)
        varList = ['Lep_eta']; cuts = basecuts + 'Selected == 1 && nEl == 1 && Lep_pt > 120 && Lep_hOverE < 0.05'
        makeEffPlots(tree, lumi, maxEntries, doFit, varList, refTrig, testTrig, cuts)

        ## EB: HoverE < 0.05
        refTrig = 'JetHT_EB_HoE'

        varList = ['Lep_pt']; cuts = basecuts + 'Selected == 1 && nEl == 1 && Lep_pt > 50  && abs(Lep_eta) < 1.5 && Lep_hOverE < 0.05'
        makeEffPlots(tree, lumi, maxEntries, doFit, varList, refTrig, testTrig, cuts)
        varList = ['Lep_eta']; cuts = basecuts + 'Selected == 1 && nEl == 1 && Lep_pt > 120  && abs(Lep_eta) < 1.5 && Lep_hOverE < 0.05'
        makeEffPlots(tree, lumi, maxEntries, doFit, varList, refTrig, testTrig, cuts)

        ## EE: HoverE < 0.05
        refTrig = 'JetHT_EE_HoE'

        varList = ['Lep_pt']; cuts = basecuts + 'Selected == 1 && nEl == 1 && Lep_pt > 50  && abs(Lep_eta) > 1.5 && Lep_hOverE < 0.05'
        makeEffPlots(tree, lumi, maxEntries, doFit, varList, refTrig, testTrig, cuts)
        varList = ['Lep_eta']; cuts = basecuts + 'Selected == 1 && nEl == 1 && Lep_pt > 120  && abs(Lep_eta) > 1.5 && Lep_hOverE < 0.05'
        makeEffPlots(tree, lumi, maxEntries, doFit, varList, refTrig, testTrig, cuts)
        '''
        '''
        ## more triggers
        varList = ['Lep_pt']

        refTrig = 'JetHT'
        testTrig = ['EleHT350MET70','Ele105']
        #testTrig = ['EleHT350MET70||Ele105']

        cuts = basecuts + 'Selected == 1 && nEl >= 1 && Lep_pt > 5 && MET > 150 && HT > 400'
        makeEffPlots(tree, lumi, maxEntries, doFit, varList, refTrig, testTrig, cuts)

        ## muons
        testTrig = ['MuHT350MET70','Mu50']
        cuts = basecuts + 'Selected == 1 && nMu >= 1 && Lep_pt > 5 && MET > 150 && HT > 400'
        makeEffPlots(tree, lumi, maxEntries, doFit, varList, refTrig, testTrig, cuts)

        refTrig = 'HLT_HT350MET100'

        testTrig = ['EleHT350MET70','Ele105']
        cuts = basecuts + 'Selected == 1 && nEl >= 1 && Lep_pt'# > 5 && MET > 200 && HT > 500'
        makeEffPlots(tree, lumi, maxEntries, doFit, varList, refTrig, testTrig, cuts)

        testTrig = ['MuHT350MET70']
        cuts = basecuts + 'Selected == 1 && nMu >= 1 && Lep_pt > 5 && MET > 200 && HT > 500'
        makeEffPlots(tree, lumi, maxEntries, doFit, varList, refTrig, testTrig, cuts)
        '''

    elif 'HTMHT' in fileName:

        # Jet + HT triggers
        lumi = 40.0

        refTrig = 'HT350MET100'
        varList = ['Lep_pt']

        testTrig = ['EleHT350MET70','Ele105']
        cuts = basecuts + 'Selected == 1 && nEl >= 1 && Lep_pt > 5 && MET > 200'
        makeEffPlots(tree, lumi, maxEntries, doFit, varList, refTrig, testTrig, cuts)

        testTrig = ['MuHT350MET70','Mu50']
        cuts = basecuts + 'Selected == 1 && nMu >= 1 && Lep_pt > 5 && MET > 200'
        #makeEffPlots(tree, lumi, maxEntries, doFit, varList, refTrig, testTrig, cuts)

    ###################
    ###################
    # MC
    ###################
    ###################

    elif 'WJets' in fileName:

        basecuts = ''

        lumi = 0

        '''
        refTrig = ''#HT350MET120'
        varList = ['Lep_pt']

        testTrig = ['EleHT400MET70']
        #testTrig = ['EleHT400MET70','Ele105']
        cuts = basecuts + 'Selected == 1 && nEl >= 1 && Lep_pt > 5 && HT > 500 && MET > 200'
        makeEffPlots(tree, lumi, maxEntries, doFit, varList, refTrig, testTrig, cuts)

        ## LT
        varList = ['LTNoHF']
        refTrig = 'JetHT'
        #refTrig = 'HLT_HT800'

        testTrig = ['Mu50||MuHT350MET70||Ele105||EleHT350MET70']
        cuts = basecuts + 'Selected == 1 && nLep == 1 && nVeto == 0 && Lep_pt > 25 && HT > 400'
        #makeEffPlots(tree, lumi, maxEntries, doFit, varList, refTrig, testTrig, cuts)

        cuts = basecuts + 'Selected == 1 && nMu >= 1 && Lep_pt > 25 && HT > 500'
        testTrig = ['Mu50||MuHT350MET70']
        #makeEffPlots(tree, lumi, maxEntries, doFit, varList, refTrig, testTrig, cuts)

        cuts = basecuts + 'Selected == 1 && nEl >= 1 && Lep_pt > 25 && HT > 500 && abs(Lep_eta) < 1.5'
        testTrig = ['Ele105||EleHT350MET70']
        makeEffPlots(tree, lumi, maxEntries, doFit, varList, refTrig, testTrig, cuts)

        varList = ['LT']

        cuts = basecuts + 'Selected == 1 && nMu >= 1 && Lep_pt > 25 && HT > 500'
        testTrig = ['Mu50||MuHT350MET70']
        #makeEffPlots(tree, lumi, maxEntries, doFit, varList, refTrig, testTrig, cuts)

        cuts = basecuts + 'Selected == 1 && nEl >= 1 && Lep_pt > 25 && HT > 500'
        testTrig = ['Ele105||EleHT350MET70']
        #makeEffPlots(tree, lumi, maxEntries, doFit, varList, refTrig, testTrig, cuts)

        '''

        #### LEPTON LEG
        refTrig = 'WJets'#HLT_HT800'#||HLT_HT350MET100'
        varList = ['Lep_eta']

        testTrig = ['Ele105']
        #cuts = basecuts + 'Selected == 1 && nEl == 1 && Lep_pt > 50 && abs(Lep_eta) < 0.8'
        cuts = basecuts + 'Selected == 1 && nEl == 1 && Lep_pt > 120'
        makeEffPlots(tree, lumi, maxEntries, doFit, varList, refTrig, testTrig, cuts)

        testTrig = ['Mu50']
        cuts = basecuts + 'Selected == 1 && nMu >= 1 && Lep_pt > 60'
        makeEffPlots(tree, lumi, maxEntries, doFit, varList, refTrig, testTrig, cuts)

        varList = ['Lep_pt']

        testTrig = ['Ele105']
        cuts = basecuts + 'Selected == 1 && nEl == 1 && Lep_pt > 5'
        makeEffPlots(tree, lumi, maxEntries, doFit, varList, refTrig, testTrig, cuts)

        testTrig = ['Mu50']
        cuts = basecuts + 'Selected == 1 && nMu >= 1 && Lep_pt > 50'
        makeEffPlots(tree, lumi, maxEntries, doFit, varList, refTrig, testTrig, cuts)

        refTrig = 'JetHT'
        testTrig = ['EleHT350MET70','Ele105']
        #testTrig = ['EleHT350MET70||Ele105']

        cuts = basecuts + 'Selected == 1 && nEl >= 1 && Lep_pt > 5 && MET > 150 && HT > 400'
        #makeEffPlots(tree, lumi, maxEntries, doFit, varList, refTrig, testTrig, cuts)


    elif 'QCD' in fileName:

        basecuts = ''#ngenLep > 0'

        lumi = -42

        #### LEPTON LEG
        refTrig = 'QCD'#HLT_HT800'#||HLT_HT350MET100'
        varList = ['Lep_eta']

        testTrig = ['Ele105']
        #cuts = basecuts + 'Selected == 1 && nEl == 1 && Lep_pt > 50 && abs(Lep_eta) < 0.8'
        cuts = basecuts + 'Selected == 1 && nEl == 1 && Lep_pt > 120'
        makeEffPlots(tree, lumi, maxEntries, doFit, varList, refTrig, testTrig, cuts)

        testTrig = ['EleHT400MET70']
        cuts = basecuts + 'Selected == 1 && nEl == 1 && Lep_pt > 25  && HT > 500 && MET > 200'
        makeEffPlots(tree, lumi, maxEntries, doFit, varList, refTrig, testTrig, cuts)

        testTrig = ['Mu50']
        cuts = basecuts + 'Selected == 1 && nMu >= 1 && Lep_pt > 60'
        makeEffPlots(tree, lumi, maxEntries, doFit, varList, refTrig, testTrig, cuts)

        varList = ['Lep_pt']

        testTrig = ['Ele105']
        cuts = basecuts + 'Selected == 1 && nEl == 1 && Lep_pt > 5'
        makeEffPlots(tree, lumi, maxEntries, doFit, varList, refTrig, testTrig, cuts)

        testTrig = ['EleHT400MET70']
        cuts = basecuts + 'Selected == 1 && nEl == 1 && Lep_pt > 5  && HT > 500 && MET > 200'
        makeEffPlots(tree, lumi, maxEntries, doFit, varList, refTrig, testTrig, cuts)

        testTrig = ['Mu50']
        cuts = basecuts + 'Selected == 1 && nMu >= 1 && Lep_pt > 50'
        makeEffPlots(tree, lumi, maxEntries, doFit, varList, refTrig, testTrig, cuts)

        refTrig = 'JetHT'
        testTrig = ['EleHT350MET70','Ele105']
        #testTrig = ['EleHT350MET70||Ele105']

        cuts = basecuts + 'Selected == 1 && nEl >= 1 && Lep_pt > 5 && MET > 150 && HT > 400'
        #makeEffPlots(tree, lumi, maxEntries, doFit, varList, refTrig, testTrig, cuts)

    else:
        print 'Nothing to draw for this file!'

    tfile.Close()
    #outfile.Close()
