from CMGTools.TTHAnalysis.treeReAnalyzer import *
import ROOT


class EventVars1LWeightsForSystematics:
    def __init__(self):
        self.branches = ["GenTopPt", "GenAntiTopPt", "TopPtWeight", "GenTTBarPt", "GenTTBarWeight", "ISRTTBarWeight", "GenGGPt", "ISRSigUp", "ISRSigDown"
                         ]

    def listBranches(self):
        return self.branches[:]

    def __call__(self,event,keyvals):

        if event.isData: return {}
        #
        genParts = [l for l in Collection(event,"GenPart","nGenPart")]

        GenTopPt = -999
        GenTopIdx = -999
        GenAntiTopPt = -999
        GenAntiTopIdx = -999
        TopPtWeight = 1.
        GenTTBarPt = -999
        GenTTBarWeight = 1.
        ISRTTBarWeight = 1.
        GenGGPt = -999
        ISRSigUp = 1.
        ISRSigDown = 1.

        nGenTops = 0
        GluinoIdx = []
        for i_part, genPart in enumerate(genParts):
            if genPart.pdgId ==  6:
                GenTopPt = genPart.pt
                GenTopIdx = i_part
            if genPart.pdgId == -6:
                GenAntiTopPt = genPart.pt
                GenAntiTopIdx = i_part
            if abs(genPart.pdgId) ==  6: nGenTops+=1

            if genPart.pdgId == 1000021:
                GluinoIdx.append(i_part)
            
        if len(GluinoIdx)==2:
            GenGluinoGluinop4 = genParts[GluinoIdx[0]].p4()+ genParts[GluinoIdx[1]].p4()
            GenGluinoGluinoPt = GenGluinoGluinop4.Pt()
            GenGGPt = GenGluinoGluinoPt
            if GenGluinoGluinoPt > 400: ISRSigUp = 1.15; ISRSigDown = 0.85
            if GenGluinoGluinoPt > 600: ISRSigUp = 1.30; ISRSigDown = 0.70
                

        if GenTopPt!=-999 and GenAntiTopPt!=-999 and nGenTops==2:
            SFTop     = exp(0.156    -0.00137*GenTopPt    )
            SFAntiTop = exp(0.156    -0.00137*GenAntiTopPt)
            TopPtWeight = sqrt(SFTop*SFAntiTop)
            if TopPtWeight<0.5: TopPtWeight=0.5

            if GenAntiTopIdx!=-999 and GenTopIdx!=-999:
                GenTTBarp4 = genParts[GenTopIdx].p4()+ genParts[GenAntiTopIdx].p4()
                GenTTBarPt = GenTTBarp4.Pt()
                if GenTTBarPt>120: GenTTBarWeight= 0.95
                if GenTTBarPt>150: GenTTBarWeight= 0.90
                if GenTTBarPt>250: GenTTBarWeight= 0.80
                if GenTTBarPt>400: GenTTBarWeight= 0.70

                if GenTTBarPt>400: ISRTTBarWeight = 0.85
                if GenTTBarPt>600: ISRTTBarWeight = 0.7


        ret    =  { 'GenTopPt'   : GenTopPt } #initialize the dictionary with a first entry
        ret['GenAntiTopPt'] = GenAntiTopPt
        ret['TopPtWeight']  = TopPtWeight
        ret['GenTTBarPt']  = GenTTBarPt
        ret['GenTTBarWeight'] = GenTTBarWeight
        ret['ISRTTBarWeight' ]  = ISRTTBarWeight
        ret['GenGGPt'] = GenGGPt
        ret['ISRSigUp' ]  = ISRSigUp
        ret['ISRSigDown'] = ISRSigDown
        return ret

if __name__ == '__main__':
    from sys import argv
    file = ROOT.TFile(argv[1])
    tree = file.Get("tree")
    class Tester(Module):
        def __init__(self, name):
            Module.__init__(self,name,None)
            self.sf = EventVars1LWeightsForSystematics()
        def analyze(self,ev):
            print "\nrun %6d lumi %4d event %d: leps %d" % (ev.run, ev.lumi, ev.evt, ev.nLepGood)
#            tree.Show(0)
            print self.sf(ev)
    el = EventLoop([ Tester("tester") ])
    el.loop([tree], maxEvents = 50)
