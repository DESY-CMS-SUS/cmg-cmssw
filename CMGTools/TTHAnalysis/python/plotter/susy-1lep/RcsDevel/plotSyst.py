import sys,os

#from makeYieldPlots import *
import makeYieldPlots as yp

yp._batchMode = False
yp._alpha = 0.75

if __name__ == "__main__":

    #yp.CMS_lumi.lumi_13TeV = str(2.1) + " fb^{-1}"
    yp.CMS_lumi.lumi_13TeV = "MC"
    yp.CMS_lumi.extraText = "Simulation"

    ## remove '-b' option
    if '-b' in sys.argv:
        sys.argv.remove('-b')
        yp._batchMode = True

    '''
    if len(sys.argv) > 1:
        pattern = sys.argv[1]
        print '# pattern is', pattern
    else:
        print "No pattern given!"
        exit(0)
    '''
    pattern = "Syst"

    #BinMask LTX_HTX_NBX_NJX for canvas names
    basename = os.path.basename(pattern)
    mask = basename.replace("*","X_")

    # Define storage
    yds = yp.YieldStore("Sele")
    paths = []

    # Add files
    tptPath = "Yields/systs/topPt/MC/allSF_noPU/meth1A/merged/"; paths.append(tptPath)
    puPath = "Yields/systs/PU/MC/allSF/meth1A/merged/"; paths.append(puPath)
    wxsecPath = "Yields/systs/wXsec/MC/allSF_noPU/meth1A/merged/"; paths.append(wxsecPath)
    dlConstPath = "Yields/systs/DLConst/merged"; paths.append(dlConstPath)
    dlSlopePath = "Yields/systs/DLSlope/merged"; paths.append(dlSlopePath)
    #jerPath = "Yields/systs/JER/merged"; paths.append(jerPath)
    jerNoPath = "Yields/systs/JER_YesNo/merged"; paths.append(jerNoPath)
    btagPath = "Yields/systs/btag/hadFlavour/fixXsec/allSF_noPU/meth1A/merged/"; paths.append(btagPath)
    jecPath = "Yields/systs/JEC/MC/allSF_noPU/meth1A/merged/"; paths.append(jecPath)
    dlScaleMatchVarPath = "lumi22fb_DlMakeBinYields/ScaleMatchVar/merged"; paths.append(dlScaleMatchVarPath)
    dlPDFUncPath = "lumi22fb_DlMakeBinYields/PDFUnc-RMS/merged"; paths.append(dlPDFUncPath)

    for path in paths:
        yds.addFromFiles(path,("lep","sele"))

    yds.showStats()
    #print [name for name in yds.samples if ("syst" in name and "EWK" in name)]
    #exit(0)

    # Sys types
#    systs = ["btagHF","btagLF","Wxsec","PU"]#,"topPt"]#,"JEC"]
#    systs = ["btagHF","btagLF","Wxsec","PU","topPt"]#,"JEC"]
#    systs = ["btagHF","Wxsec","topPt","PU","DLSlope","DLConst"]#,"JEC"]
#    systs = ["JEC"]
#    systs = ["btagHF","btagLF"]
#    systs = ["btagLF","btagHF"]
#    systs = ["Wxsec","PU","JEC","btagHF","btagLF","topPt","DLConst","DLSlope","JER","ScaleMatchVar-Env","PDFUnc-RMS"]
#    systs = ["DLConst","DLSlope"]
#    systs = ["ScaleMatchVar-Env"]
    systs = ["ScaleMatchVar-Env","PDFUnc-RMS"]
    systNames = {
        "btagLF" : "b-mistag (light)",
        "btagHF" : "b-tag (b/c)",
        "JEC" : "JEC",
        "topPt" : "Top p_{T}",
        "PU" : "PU",
        "Wxsec" : "#sigma_{W}",
        #"JER" : "JER",
        "JER" : "JER Yes/No",
        "DLSlope" : "DL (Slope)",
        "DLConst" : "DL (Const)",
        }

    sysCols = [2,4,7,8,3,9,6] + range(40,50)#[1,2,3] + range(4,10)

    # Sample and variable
    #samp = "EWK"
    samps = ["EWK","TTJets","WJets","SingleTop","DY","TTV"]
    #samps = ['T_tWch','TToLeptons_tch','TBar_tWch', 'TToLeptons_sch',"EWK"]
    samp = samps[0]

    var = "Kappa"
    #var = "SR_SB"

    # canvs and hists
    hists = []
    canvs = []

    # read in central value
    hCentral = yp.makeSampHisto(yds,samp,var)
    print "hCentral done"
    yp.prepRatio(hCentral)

    for i,syst in enumerate(systs):
        yp.colorDict[syst+"_syst"] = sysCols[i]

        sname = samp+"_"+syst+"_syst"
        print "Making hist for", sname

        hist = yp.makeSampHisto(yds,sname,var,syst+"_syst")
        if syst in systNames: hist.SetTitle(systNames[syst])
        else: hist.SetTitle(syst)

        hist.GetYaxis().SetTitle("Relative uncertainty")
        hist.GetYaxis().SetTitleSize(0.04)
        hist.GetYaxis().SetTitleOffset(0.8)

        #yp.prepKappaHist(hist)
        #yp.prepRatio(hist)

        # normalize to central value
        #hist.Divide(hCentral)

        hists.append(hist)

    # make stack/total syst hists
    #total = yp.getTotal(hists)
    stack = yp.getStack(hists)
    sqHist = yp.getSquaredSum(hists)

    hCentralUncert = yp.getHistWithError(hCentral, sqHist)
    canv = yp.plotHists(var+"_"+samp+"_Syst",[stack,sqHist],[hCentral,hCentralUncert],"TM", 1200, 600)
#    canv = yp.plotHists(var+"_"+samp+"_Syst",[sqHist]+hists,[hCentral,hCentralUncert],"TM", 1200, 600)
#    canv = yp.plotHists(var+"_"+samp+"_Stat",[stack,sqHist],hCentral,"TM", 1200, 600)
    canvs.append(canv)
    if not yp._batchMode: raw_input("Enter any key to exit")

    # Save canvases
    exts = [".pdf",".png",".root"]
    #exts = [".pdf"]

    odir = "BinPlots/Syst/Combine/test/allSF_noPU_wJER_DL/Method1A/"
    #odir = "BinPlots/Syst/btag/hadronFlavour/allSF_noPU/Method1B/"
    if not os.path.isdir(odir): os.makedirs(odir)

    for canv in canvs:
        for ext in exts:
            canv.SaveAs(odir+mask+canv.GetName()+ext)

