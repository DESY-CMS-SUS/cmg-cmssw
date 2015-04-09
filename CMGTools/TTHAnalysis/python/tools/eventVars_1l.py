from CMGTools.TTHAnalysis.treeReAnalyzer import *
from ROOT import TLorentzVector, TVector2, std
import ROOT
import time
import itertools
import PhysicsTools.Heppy.loadlibs
import array
import operator

ROOT.gInterpreter.GenerateDictionary("vector<TLorentzVector>","TLorentzVector.h;vector") #need this to be able to use topness code

mt2wSNT = ROOT.heppy.mt2w_bisect.mt2w()
topness = ROOT.Topness.Topness()

def getPhysObjectArray(j): # https://github.com/HephySusySW/Workspace/blob/72X-master/RA4Analysis/python/mt2w.py
  px = j.pt*cos(j.phi )
  py = j.pt*sin(j.phi )
  pz = j.pt*sinh(j.eta )
  E = sqrt(px*px+py*py+pz*pz) #assuming massless particles...
  return array.array('d', [E, px, py,pz])


def mt_2(p4one, p4two):
  return sqrt(2*p4one.Pt()*p4two.Pt()*(1-cos(p4one.Phi()-p4two.Phi())))

def GetZfromM(vector1,vector2,mass):
  MT = sqrt(2*vector1.Pt()*vector2.Pt()*(1-cos(vector2.DeltaPhi(vector1))))
  if (MT<mass):
    Met2D = TVector2(vector2.Px(),vector2.Py())
    Lep2D = TVector2(vector1.Px(),vector1.Py())
    A = mass*mass/2.+Met2D*Lep2D
    Delta = vector1.E()*vector1.E()*(A*A-Met2D.Mod2()*Lep2D.Mod2())
    MetZ1 = (A*vector1.Pz()+sqrt(Delta))/Lep2D.Mod2()
    MetZ2 = (A*vector1.Pz()-sqrt(Delta))/Lep2D.Mod2()
  else:
    MetZ1 =vector1.Pz()*vector2.Pt()/vector1.Pt()
    MetZ2 =vector1.Pz()*vector2.Pt()/vector1.Pt()
    return [MT,MetZ1,MetZ2]

def minValueForIdxList(values,idxlist):
  cleanedValueList = [val for i,val in enumerate(values) if i in idxlist]
  if len(cleanedValueList)>0: return min(cleanedValueList)
  else: return -999
#  print cleanedValueList, min(cleanedValueList)#d, key=d.get)


class EventVars1L:
  def __init__(self):
    self.branches = [ "METCopyPt", "DeltaPhiLepW", "minDPhiBMET", "minDPhiJMET", "idxMinDPhiBMET", "mTClBPlusMET", "mTBJetMET", "mTLepMET", "mLepBJet",
                      ("nTightLeps25","I"),
                      ("nTightMu25","I"),("nTightEl25","I"),("nVetoLeps10","I"),
                      ("tightLeps25idx","I",10,"nTightLeps25"),("tightLeps25_DescFlag","I",10,"nTightLeps25"),
                      ("tightMu25idx","I",10,"nTightMu25"),
                      ("tightEl25idx","I",10,"nTightEl25"),("vetoLeps10idx","I",10,"nVetoLeps10"),
                      ("nTightLeps","I"),("tightLepsIdx","I",10,"nTightLeps"),("nVetoLeps","I"),("vetoLepsIdx","I",10,"nVetoLeps"),
                      ("nTightEl","I"),("tightElIdx","I",10,"nTightEl"),("nVetoEl","I"),("vetoElIdx","I",10,"nVetoEl"),
                      ("nTightMu","I"),("tightMuIdx","I",10,"nTightMu"),("nVetoMu","I"),("vetoMuIdx","I",10,"nVetoMu"),
                      ("nCentralJet30","I"),("centralJet30idx","I",100,"nCentralJet30"),("centralJet30_DescFlag","F",100,"nCentralJet30"),
                      ("nBJetCMVAMedium30","I"),("BJetCMVAMedium30idx","I",50,"nBJetCMVAMedium30"),
                      "nGoodBJets_allJets", "nGoodBJets",
                      "LSLjetptGT80", "htJet30j", "htJet30ja",
                      ("LepBMass","F",50,"nCentralJet30"), ("MTbnu","F",50,"nCentralJet30"),("Mtop","F",50,"nCentralJet30"),
                      ("MTtop","F",50,"nCentralJet30"), ("METovTop","F",50,"nCentralJet30"),("METTopPhi","F",50,"nCentralJet30"),
                      ("MtopDecor","F",50,"nCentralJet30"),
                      ("nBMinVariantsTopVars","I"),
                      ("TopVarsMTbnuMin","F",10,"nBMinVariantsTopVars"),("TopVarsLepBMassMin","F",10,"nBMinVariantsTopVars"),
                      ("TopVarsMTtopMin","F",10,"nBMinVariantsTopVars"),("TopVarsMtopMin","F",10,"nBMinVariantsTopVars"),
                      ("TopVarsMETovTopMin","F",10,"nBMinVariantsTopVars"),("TopVarsMtopDecorMin","F",10,"nBMinVariantsTopVars"),
                      "MTW","MW1","MW2",
                      "MT2W", "Topness",
                      "nHighPtTopTag", "nHighPtTopTagPlusTau23"
                      ]



    def listBranches(self):
      return self.branches[:]


    def __call__(self,event):

      # make python lists as Collection does not support indexing in slices
      genleps = [l for l in Collection(event,"genLep","ngenLep")]

      leps = [l for l in Collection(event,"LepGood","nLepGood")]
      jets = [j for j in Collection(event,"Jet","nJet")]

      fatjets = [j for j in Collection(event,"FatJet","nFatJet")]

      njet = len(jets); nlep = len(leps)

      metp4 = ROOT.TLorentzVector(0,0,0,0)
      metp4.SetPtEtaPhiM(event.met_pt,event.met_eta,event.met_phi,event.met_mass)
      pmiss  =array.array('d',[event.met_pt * cos(event.met_phi), event.met_pt * sin(event.met_phi)] )

      #isolation criteria as defined for PHYS14 1l synchronisation exercise
      ele_relisoCut = 0.14
      muo_relisoCut = 0.12
      #ele tight id --> >2
      #muo tight id ==1
      centralEta = 2.4

      muo_minirelisoCut = 0.2
      Lep_minirelisoCut = 0.4
      ele_minirelisoCut = 0.1

      goodEl_lostHits = 1
      goodEl_sip3d = 4

      goodEl_mvaPhys14_eta08_T = 0.73;
      goodEl_mvaPhys14_eta104_T = 0.57;
      goodEl_mvaPhys14_eta204_T = 0.05;

      tightLeps25 = []
      tightLeps25idx = []
      tightMu25 = []
      tightMu25idx = []
      tightEl25 = []
      tightEl25idx = []
      vetoLeps10 = []
      vetoLeps10idx = []
      vetoLeps10T10 = []
      vetoLeps10T10idx = []
      vetoLeps5 = []
      vetoLeps5idx = []
      vetoLeps5T5 = []
      vetoLeps5T5idx = []


      for i,l in enumerate(leps):
        if(abs(l.eta)<2.5):
          IsoMupT = False
          tightMu = False
          if l.pt>5 and l.pt<15 and l.miniRelIso<Lep_minirelisoCut and l.mediumMuonId==1 and abs(l.pdgId)==13 and l.sip3d<4.0: tightMu = True
          elif l.pt>15 and abs(l.pdgId)==13 and (l.miniRelIso<muo_minirelisoCut and l.mediumMuonId==1) and l.sip3d<4.0: tightMu = True

          tightEl = False
          idElEta = False

          IsoElpT = False
          if l.pt>25 and  abs(l.pdgId)==11 and abs(l.eta)<0.8 and l.mvaIdPhys14 > goodEl_mvaPhys14_eta08_T: idElEta = True
          elif l.pt>25 and abs(l.pdgId)==11 and abs(l.eta)>=0.8 and abs(l.eta)<1.44 and l.mvaIdPhys14 > goodEl_mvaPhys14_eta104_T: idElEta = True
          elif l.pt>25 and abs(l.pdgId)==11 and abs(l.eta)>=1.57 and l.mvaIdPhys14 > goodEl_mvaPhys14_eta204_T: idElEta = True

          if l.pt>5 and l.pt<25 and l.mvaSusy>0.53 and abs(l.pdgId)==11: IsoElpT = True
          elif l.pt>25 and l.miniRelIso<ele_minirelisoCut and abs(l.pdgId)==11: IsoElpT = True

          if l.pt>5 and l.pt<25 and abs(l.pdgId)==11 and abs(l.eta)<2.4 and (abs(l.eta) < 1.44 or abs(l.eta) > 1.57) and IsoElpT and l.lostHits <= goodEl_lostHits and  l.convVeto: tightEl = True
          elif l.pt>25 and abs(l.pdgId)==11 and abs(l.eta)<2.4 and (abs(l.eta) < 1.44 or abs(l.eta) > 1.57) and (IsoElpT and idElEta) and l.lostHits <= goodEl_lostHits and  l.convVeto and l.sip3d < goodEl_sip3d:
            tightEl = True

            if tightMu:
              tightMu25.append(l); tightMu25idx.append(i)
              tightLeps25.append(l); tightLeps25idx.append(i)
            elif tightEl:
              tightEl25.append(l); tightEl25idx.append(i)
              tightLeps25.append(l); tightLeps25idx.append(i)
            elif l.pt>5:
              vetoLeps10.append(l); vetoLeps10idx.append(i)

      #initialize the dictionary with a first entry
      ret = { 'nTightLeps25'   : len(tightLeps25) }
      ret['nTightMu25']  = len(tightMu25)
      ret['nTightEl25']  = len(tightEl25)
      ret['nVetoLeps10'] = len(vetoLeps10)

      ret['tightLeps25idx'] = tightLeps25idx
      ret['tightMu25idx']   = tightMu25idx
      ret['tightEl25idx']   = tightEl25idx
      ret['vetoLeps10idx']  = vetoLeps10idx


      ###########
      # new
      ###########

      hardTightLeps = []
      hardTightLepsIdx = []
      hardVetoLeps = []
      hardVetoLepsIdx = []

      softTightLeps = []
      softVetoLepsIdx = []
      softVetoLeps = []
      softVetoLepsIdx = []

      hardTightMu = []
      hardTightMuIdx = []
      hardVetoMu = []
      hardVetoMuIdx = []

      softTightMu = []
      softVetoMuIdx = []
      softVetoMu = []
      softVetoMuIdx = []

      hardTightEl = []
      hardTightElIdx = []
      hardVetoEl = []
      hardVetoElIdx = []

      softTightEl = []
      softVetoElIdx = []
      softVetoEl = []
      softVetoElIdx = []

      for idx,lep in enumerate(leps):

        # pass variables
        passID = false
        passIso = false

        # check acceptance
        if(abs(lep.eta)>2.5): continue

        # muons
        if(abs(lep.pdgId) == 13):

          # hard: pt > 25
          if lep.pt > 25:

            # ID and Iso check:
            if lep.mediumMuonId == 1 and lep.sip3d < 4.0: passID = true
            if lep.miniRelIso < muo_minirelisoCut:        passIso = true

            # fill
            if passID and passIso:
              hardTightLeps.append(lep); hardTightLepsIdx.append(idx);
              hardTightMu.append(lep); hardTightMuIdx.append(idx);
            else:
              hardVetoLeps.append(lep); hardVetoLepsIdx.append(idx);
              hardVetoMu.append(lep); hardVetoMuIdx.append(idx);

          # soft muons + tight veto
          elif lep.pt > 5:

            # veto fro tight if pt > 10
            if lep.pt > 10:
              hardVetoLeps.append(lep); hardVetoLepsIdx.append(idx);
              hardVetoMu.append(lep); hardVetoMuIdx.append(idx);

            # Soft leptons

            # ID check
            if lep.mediumMuonId == 1: passID = true
            # iso check
            if lep.pt < 15   and lep.miniRelIso < Lep_minirelisoCut: passIso = true
            elif lep.pt > 15 and lep.miniRelIso < muo_minirelisoCut: passIso = true

            # fill
            if passID and passIso:
              softTightLeps.append(lep); softTightLepsIdx.append(idx);
              softTightMu.append(lep); softTightMuIdx.append(idx);
            else:
              softVetoLeps.append(lep); softVetoLepsIdx.append(idx);
              softVetoMu.append(lep); softVetoMuIdx.append(idx);

        # electrons
        if(abs(lep.pdgId) == 11):

          # hard: pt > 25
          if lep.pt > 25:

            # Iso check:
            if lep.miniRelIso < ele_minirelisoCut: passIso = true
            # Eta dependent MVA ID check:
            if abs(lep.eta) < 0.8 and lep.mvaIdPhys14 > goodEl_mvaPhys14_eta08_T: passID = true
            elif abs(lep.eta) >= 0.8 and abs(lep.eta) < 1.44 and lep.mvaIdPhys14 > goodEl_mvaPhys14_eta104_T: passID = true
            elif abs(lep.eta) >= 1.57 and lep.mvaIdPhys14 > goodEl_mvaPhys14_eta204_T: passID = true
            # more checks:
            if not (lep.lostHits <= goodEl_lostHits and lep.convVeto and lep.sip3d < goodEl_sip3d): passID = false

            # fill
            if passID and passIso:
              hardTightLeps.append(lep); hardTightLepsIdx.append(idx);
              hardTightEl.append(lep); hardTightElIdx.append(idx);
            else:
              hardVetoLeps.append(lep); hardVetoLepsIdx.append(idx);
              hardVetoEl.append(lep); hardVetoElIdx.append(idx);

          # soft muons + tight veto
          elif lep.pt > 5:

            # veto fro tight if pt > 10
            if lep.pt > 10:
              hardVetoLeps.append(lep); hardVetoLepsIdx.append(idx);
              hardVetoEl.append(lep); hardVetoElIdx.append(idx);

            # Soft leptons
            # MVA(ID+Iso) check
            if lep.mvaSusy>0.53: passID = true
            # more checks:
            if not (lep.lostHits <= goodEl_lostHits and lep.convVeto and lep.sip3d < goodEl_sip3d): passID = false

            # fill
            if passID and passIso:
              softTightLeps.append(lep); softTightLepsIdx.append(idx);
              softTightEl.append(lep); softTightElIdx.append(idx);
            else:
              softVetoLeps.append(lep); softVetoLepsIdx.append(idx);
              softVetoEl.append(lep); softVetoElIdx.append(idx);

      # end lepton loop
      ####

      # choose common lepton collection: select hard or soft lepton
      if len(hardTightLeps) > 0:
        tightLeps = hardTightLeps
        tightLepsIdx = hardTightLepsIdx
        vetoLeps = hardVetoLeps
        vetoLepsIdx = hardVetoLepsIdx

        tightEl = hardTightEl
        tightElIdx = hardTightElIdx
        vetoEl = hardVetoEl
        vetoElIdx = hardVetoElIdx

        tightMu = hardTightMu
        tightMuIdx = hardTightMuIdx
        vetoMu = hardVetoMu
        vetoMuIdx = hardVetoMuIdx

      else: #if len(softTightLeps) > 0: or empty collection
        tightLeps = softTightLeps
        tightLepsIdx = softTightLepsIdx
        vetoLeps = softVetoLeps
        vetoLepsIdx = softVetoLepsIdx

        tightEl = softTightEl
        tightElIdx = softTightElIdx
        vetoEl = softVetoEl
        vetoElIdx = softVetoElIdx

        tightMu = softTightMu
        tightMuIdx = softTightMuIdx
        vetoMu = softVetoMu
        vetoMuIdx = softVetoMuIdx

      #initialize the dictionary with a first entry
#      ret = { 'nTightLeps'   : len(tightLeps) }
      ret['nTightLeps'] = len(tightLeps)
      ret['tightLepsIdx'] = tightLepsIdx
      ret['nVetoLeps'] = len(vetoLeps)
      ret['vetoLepsIdx'] = vetoLepsIdx

      ret['nTightEl'] = len(tightEl)
      ret['tightElIdx'] = tightElIdx
      ret['nVetoEl'] = len(vetoEl)
      ret['vetoElIdx'] = vetoElIdx

      ret['nTightMu'] = len(tightMu)
      ret['tightMuIdx'] = tightMuIdx
      ret['nVetoMu'] = len(vetoMu)
      ret['vetoMuIdx'] = vetoMuIdx

      ########
      # JETS
      ########

      centralJet30 = []
      centralJet30idx = []
      for i,j in enumerate(jets):
        if j.pt>30 and abs(j.eta)<centralEta:
          centralJet30.append(j)
          centralJet30idx.append(i)

        ret['nCentralJet30']   = len(centralJet30)
        ret['centralJet30idx'] = centralJet30idx

        ret['LSLjetptGT80'] = 1 if sum([j.pt>80 for j in centralJet30])>=2 else 0

        ret['htJet30j']  = sum([j.pt for j in centralJet30])
        ret['htJet30ja'] = sum([j.pt for j in jets if j.pt>30])

        BJetCMVAMedium30 = []
        BJetCMVAMedium30idx = []
        NonBJetCMVAMedium30 = []
        for i,j in enumerate(centralJet30):
          if j.btagCMVA>0.732:
            BJetCMVAMedium30.append(j)
            BJetCMVAMedium30idx.append(centralJet30idx[i])
          else:
            NonBJetCMVAMedium30.append(j)
        ret['nBJetCMVAMedium30']    = len(BJetCMVAMedium30)
        ret['BJetCMVAMedium30idx']  = BJetCMVAMedium30idx

        ret['nGoodBJets']    = sum([j.btagCMVA>0.732 for j in centralJet30])
        ret['nGoodBJets_allJets']    = sum([j.btagCMVA>0.732 and j.pt>30 and abs(j.eta)<centralEta for j in jets]) # where is the working point defined?


        #plain copy of MET pt (just as an example and cross-check for proper friend tree production)
        ret["METCopyPt"] = metp4.Pt()

        # deltaPhi between the (single) lepton and the reconstructed W (lep + MET)
        dPhiLepW = -999 # set default value to -999 to spot "empty" entries
        if ret['nTightLeps']>=1:
          recoWp4 =  tightLeps[0].p4() + metp4
          dPhiLepW = tightLeps[0].p4().DeltaPhi(recoWp4)
        ret["DeltaPhiLepW"] = dPhiLepW

        ##################################################################
        # The following variables need to be double-checked for validity #
        ##################################################################

        # min deltaPhi between a (CMVA) b-jet and MET; needs to be double-checked
        minDPhiBMET    = 100
        idxMinDPhiBMET = -999
        for i, jet in enumerate(jets):
          if jet.btagCMVA>0.732:
            dPhiBMET = abs(jet.p4().DeltaPhi(metp4))
            if dPhiBMET<minDPhiBMET:
              minDPhiBMET=dPhiBMET
              idxMinDPhiBMET = i

        ret["idxMinDPhiBMET"] = idxMinDPhiBMET
        ret["minDPhiBMET"] = minDPhiBMET

        # min deltaPhi between a jet (first three jets) and MET; needs to be double-checked
        minDPhiJMET    = 100
        for i, jet in enumerate(jets[:3]):
          dPhiJMET = abs(jet.p4().DeltaPhi(metp4))
          if dPhiJMET<minDPhiJMET:
            minDPhiJMET=dPhiJMET

        ret["minDPhiJMET"] = minDPhiJMET



        # transverse mass of (closest (to MET) BJet, MET), (closest (to MET) BJet, lepton),
        # mass of (closest (to MET) BJet, lepton); need to be double-checked
        mTBJetMET      = -999
        mTLepMET       = -999
        mLepBJet       = -999
        if(idxMinDPhiBMET>=0):
          SumMetClosestBJet = jets[idxMinDPhiBMET].p4() + metp4
          ret["mTClBPlusMET"] = SumMetClosestBJet.Mt()
          mTBJetMET = mt_2(jets[idxMinDPhiBMET].p4(),metp4)
          if ret['nTightLeps']>=1:
            mLepBJet = (jets[idxMinDPhiBMET].p4() + tightLeps[0].p4()).M()
            mTLepMET = mt_2(tightLeps[0].p4(),metp4)
        else:
          ret["mTClBPlusMET"] = -999

        ret["mTBJetMET"] = mTBJetMET
        ret["mTLepMET"]  = mTLepMET
        ret["mLepBJet"]  = mLepBJet

        # projection of MET along (MET + lepton + (closest (to MET) BJet)) sum; needs to be double-checked...
        MetZ1 = -9999
        MetZ2 = -9999
        MTW = -9999
        MW1 = -9999
        MW2 = -9999
        neutrino1 = ROOT.TLorentzVector(0,0,0,0)
        neutrino2 = ROOT.TLorentzVector(0,0,0,0)
        if(ret['nTightLeps']==1) :
          NeutrZList = GetZfromM(tightLeps[0].p4(),metp4,81)
          MTW = NeutrZList[0]
          MetZ1= NeutrZList[1]
          MetZ2= NeutrZList[2]
          neutrino1.SetXYZM(metp4.Px(),metp4.Py(), MetZ1, 0)
          neutrino2.SetXYZM(metp4.Px(),metp4.Py(), MetZ2, 0)
          MW1 = (neutrino1+tightLeps[0].p4()).M()
          MW2 = (neutrino2+tightLeps[0].p4()).M()
        ret["MTW"]  = MTW
        ret["MW1"]  = MW1
        ret["MW2"]  = MW2
        # some extra plots

        MTbnu = []
        LepBMass = []
        MTtop = []
        Mtop = []
        METovTop = []
        METTopPhi = []
        MtopDecor = []


        if(ret['nTightLeps']==1) :
          for i,jet in  enumerate(centralJet30): #testing all jets as b-jet in top-reco
            ThisMTnub = sqrt(2*event.met_pt*jet.pt* (1-cos( metp4.DeltaPhi(jet.p4() ))))
            MTbnu.append(ThisMTnub)
            ThislepBMass = (tightLeps[0].p4()+jet.p4()).M()
            LepBMass.append(ThislepBMass )
            ThisMTtop =  sqrt( 81.*81. + ThislepBMass *ThislepBMass + ThisMTnub*ThisMTnub)
            MTtop.append(ThisMTtop)
            ThisMetovTop =  event.met_pt/(metp4+tightLeps[0].p4()+jet.p4()).Pt()
            METovTop.append(ThisMetovTop)
            ThisMetTop = metp4.DeltaPhi(metp4+tightLeps[0].p4()+jet.p4())
            METTopPhi.append(ThisMetTop)
            ThisMtop = (neutrino1+tightLeps[0].p4()+jet.p4()).M()
            if(ThisMtop>(neutrino2+tightLeps[0].p4()+jet.p4()).M()): ThisMtop = (neutrino2+tightLeps[0].p4()+jet.p4()).M() #take smaller mtop of the two nu pz-solutions
            Mtop.append(ThisMtop)
            ThisMtopDecor  = sqrt((tightLeps[0].p4()+jet.p4()).M()*(tightLeps[0].p4()+jet.p4()).M()+ (neutrino1+jet.p4()).M()*(neutrino1+jet.p4()).M()+81*81)
            if ThisMtopDecor > sqrt((tightLeps[0].p4()+jet.p4()).M()*(tightLeps[0].p4()+jet.p4()).M()+ (neutrino2+jet.p4()).M()*(neutrino2+jet.p4()).M()+81*81):
              ThisMtopDecor =  sqrt((tightLeps[0].p4()+jet.p4()).M()*(tightLeps[0].p4()+jet.p4()).M()+ (neutrino2+jet.p4()).M()*(neutrino2+jet.p4()).M()+81*81)
              MtopDecor.append(ThisMtopDecor)


        ret["MTbnu"] =MTbnu
        ret["LepBMass"]=LepBMass
        ret["MTtop"]=MTtop
        ret["Mtop"]=Mtop
        ret["METovTop"]=METovTop
        ret["METTopPhi"]=METTopPhi
        ret["MtopDecor"]=MtopDecor

##        TopVarsJetIdx = []
        TopVarsMTbnuMin = []
        TopVarsLepBMassMin = []
        TopVarsMTtopMin = []
        TopVarsMtopMin = []
        TopVarsMETovTopMin = []
        TopVarsMtopDecorMin = []


        iBTagDict = {i: jets[idx].btagCMVA for i, idx in enumerate(centralJet30idx)}
        sortIdsByBTag = sorted(iBTagDict.items(), key=operator.itemgetter(1), reverse=True)
        bTaggedJetsSorted = sortIdsByBTag[:ret['nBJetCMVAMedium30']]
#        print bTaggedJetsSorted
        bTaggedJetsPPSorted = sortIdsByBTag[:ret['nBJetCMVAMedium30']+1]
#        print bTaggedJetsPPSorted
        ThreeBestBTags = sortIdsByBTag[:3]
#        print ThreeBestBTags
#        print sortIdsByBTag

        if(ret['nTightLeps']==1) :
          TopVarsMTbnuMin      .append(minValueForIdxList(MTbnu     , [ids[0] for ids in bTaggedJetsSorted]))
          TopVarsLepBMassMin   .append(minValueForIdxList(LepBMass  , [ids[0] for ids in bTaggedJetsSorted]))
          TopVarsMTtopMin      .append(minValueForIdxList(MTtop     , [ids[0] for ids in bTaggedJetsSorted]))
          TopVarsMtopMin       .append(minValueForIdxList(Mtop      , [ids[0] for ids in bTaggedJetsSorted]))
          TopVarsMETovTopMin   .append(minValueForIdxList(METovTop  , [ids[0] for ids in bTaggedJetsSorted]))
          TopVarsMtopDecorMin  .append(minValueForIdxList(MtopDecor , [ids[0] for ids in bTaggedJetsSorted]))

          TopVarsMTbnuMin      .append(minValueForIdxList(MTbnu     , [ids[0] for ids in bTaggedJetsPPSorted]))
          TopVarsLepBMassMin   .append(minValueForIdxList(LepBMass  , [ids[0] for ids in bTaggedJetsPPSorted]))
          TopVarsMTtopMin      .append(minValueForIdxList(MTtop     , [ids[0] for ids in bTaggedJetsPPSorted]))
          TopVarsMtopMin       .append(minValueForIdxList(Mtop      , [ids[0] for ids in bTaggedJetsPPSorted]))
          TopVarsMETovTopMin   .append(minValueForIdxList(METovTop  , [ids[0] for ids in bTaggedJetsPPSorted]))
          TopVarsMtopDecorMin  .append(minValueForIdxList(MtopDecor , [ids[0] for ids in bTaggedJetsPPSorted]))

          TopVarsMTbnuMin      .append(minValueForIdxList(MTbnu     , [ids[0] for ids in ThreeBestBTags]))
          TopVarsLepBMassMin   .append(minValueForIdxList(LepBMass  , [ids[0] for ids in ThreeBestBTags]))
          TopVarsMTtopMin      .append(minValueForIdxList(MTtop     , [ids[0] for ids in ThreeBestBTags]))
          TopVarsMtopMin       .append(minValueForIdxList(Mtop      , [ids[0] for ids in ThreeBestBTags]))
          TopVarsMETovTopMin   .append(minValueForIdxList(METovTop  , [ids[0] for ids in ThreeBestBTags]))
          TopVarsMtopDecorMin  .append(minValueForIdxList(MtopDecor , [ids[0] for ids in ThreeBestBTags]))



          mcMatchIdLep = tightLeps[0].mcMatchId
          iCorrectJet=-999
          correctJetBTagged = False
          if abs(mcMatchIdLep)==6:
            for i,jet in  enumerate(centralJet30):
              if abs(jet.mcFlavour)==5 and jet.mcMatchId==mcMatchIdLep:
                iCorrectJet=i
                if jet.btagCMVA>0.732: correctJetBTagged=True

          TopVarsMTbnuMin      .append(MTbnu     [iCorrectJet] if iCorrectJet>-999 else -999)
          TopVarsLepBMassMin   .append(LepBMass  [iCorrectJet] if iCorrectJet>-999 else -999)
          TopVarsMTtopMin      .append(MTtop     [iCorrectJet] if iCorrectJet>-999 else -999)
          TopVarsMtopMin       .append(Mtop      [iCorrectJet] if iCorrectJet>-999 else -999)
          TopVarsMETovTopMin   .append(METovTop  [iCorrectJet] if iCorrectJet>-999 else -999)
          TopVarsMtopDecorMin  .append(MtopDecor [iCorrectJet] if iCorrectJet>-999 else -999)

#          print "strange"
          foundCorrectBJetAndIsTagged = iCorrectJet>-999 and correctJetBTagged
#          print "strange2"
          TopVarsMTbnuMin      .append(MTbnu     [iCorrectJet] if foundCorrectBJetAndIsTagged else -999)
          TopVarsLepBMassMin   .append(LepBMass  [iCorrectJet] if foundCorrectBJetAndIsTagged else -999)
          TopVarsMTtopMin      .append(MTtop     [iCorrectJet] if foundCorrectBJetAndIsTagged else -999)
          TopVarsMtopMin       .append(Mtop      [iCorrectJet] if foundCorrectBJetAndIsTagged else -999)
          TopVarsMETovTopMin   .append(METovTop  [iCorrectJet] if foundCorrectBJetAndIsTagged else -999)
          TopVarsMtopDecorMin  .append(MtopDecor [iCorrectJet] if foundCorrectBJetAndIsTagged else -999)


          for i,jet in  enumerate(centralJet30): #testing all jets as b-jet in top-reco
            if centralJet30idx[i]==idxMinDPhiBMET:
              TopVarsMTbnuMin      .append(MTbnu    [i] if idxMinDPhiBMET!=-999 else -999)
              TopVarsLepBMassMin   .append(LepBMass [i] if idxMinDPhiBMET!=-999 else -999)
              TopVarsMTtopMin      .append(MTtop    [i] if idxMinDPhiBMET!=-999 else -999)
              TopVarsMtopMin       .append(Mtop     [i] if idxMinDPhiBMET!=-999 else -999)
              TopVarsMETovTopMin   .append(METovTop [i] if idxMinDPhiBMET!=-999 else -999)
              TopVarsMtopDecorMin  .append(MtopDecor[i] if idxMinDPhiBMET!=-999 else -999)

        else:
          for i in range(6):
            TopVarsMTbnuMin      .append(-999)
            TopVarsLepBMassMin   .append(-999)
            TopVarsMTtopMin      .append(-999)
            TopVarsMtopMin       .append(-999)
            TopVarsMETovTopMin   .append(-999)
            TopVarsMtopDecorMin  .append(-999)


        ret["nBMinVariantsTopVars"]=6

        ret["TopVarsMTbnuMin"]    =TopVarsMTbnuMin
        ret["TopVarsLepBMassMin"] =TopVarsLepBMassMin
        ret["TopVarsMTtopMin"]    =TopVarsMTtopMin
        ret["TopVarsMtopMin"]     =TopVarsMtopMin
        ret["TopVarsMETovTopMin"] =TopVarsMETovTopMin
        ret["TopVarsMtopDecorMin"]=TopVarsMtopDecorMin



        centralJet30_DescFlag = []
        tightLeps_DescFlag = []

        for i,l in enumerate(tightLeps):
          if abs(l.mcMatchId)==6: tightLeps_DescFlag.append(1)    #top
          elif abs(l.mcMatchId)==24: tightLeps_DescFlag.append(2) #W-boson
          else: tightLeps_DescFlag.append(0)

        for i,j in enumerate(centralJet30):
          if abs(j.mcMatchId)==6:
            if len(genleps)>0 and abs(genleps[0].sourceId) ==6 and abs(j.mcFlavour)==5:
              if j.mcMatchId==genleps[0].sourceId:
                centralJet30_DescFlag.append(genleps[0].charge)
              else:
                centralJet30_DescFlag.append(2)
            elif abs(j.mcFlavour) not in [0,5,21]:
              centralJet30_DescFlag.append(3)
            else: centralJet30_DescFlag.append(-999) #; print "should not happen..."
          else: centralJet30_DescFlag.append(0)


        ret["centralJet30_DescFlag"]=centralJet30_DescFlag
        ret["tightLeps_DescFlag"]=tightLeps_DescFlag



#        print "done"

        #add topness and mt2W-variable (timing issue with topness: slows down the friend tree production by a factor of ~3)
        ret['Topness']=-999
        mt2w_values=[]
        if ret['nTightLeps']>=1: #topness and mt2w only make sense for
          lep = getPhysObjectArray(tightLeps[0])
          if ret['nBJetCMVAMedium30']==0 and ret['nCentralJet30']>=3: #All combinations from the highest three light (or b-) jets
            consideredJets = [ getPhysObjectArray(jet) for jet in NonBJetCMVAMedium30[:3] ] # only throw arrays into the permutation business
            ftPerms = itertools.permutations(consideredJets, 2)
            for perm in ftPerms:
              mt2wSNT.set_momenta(lep, perm[0], perm[1], pmiss)
              mt2w_values.append(mt2wSNT.get_mt2w())
          elif ret['nBJetCMVAMedium30']==1 and ret['nCentralJet30']>=2: #All combinations from one b and the highest two light jets
            consideredJets = [ getPhysObjectArray(jet) for jet in NonBJetCMVAMedium30[:2] ] # only throw arrays into the permutation business
            consideredJets.append(getPhysObjectArray(BJetCMVAMedium30[0]))
            ftPerms = itertools.permutations(consideredJets, 2)
            for perm in ftPerms:
              mt2wSNT.set_momenta(lep, perm[0], perm[1], pmiss)
              mt2w_values.append(mt2wSNT.get_mt2w())
          elif ret['nBJetCMVAMedium30']==2:
            consideredJets = [ getPhysObjectArray(jet) for jet in BJetCMVAMedium30[:2] ] # only throw arrays into the permutation business
            ftPerms = itertools.permutations(consideredJets, 2)
            for perm in ftPerms:
              mt2wSNT.set_momenta(lep, perm[0], perm[1], pmiss)
              mt2w_values.append(mt2wSNT.get_mt2w())
          elif ret['nBJetCMVAMedium30']>=3: #All combinations from the highest three b jets
            consideredJets = [ getPhysObjectArray(jet) for jet in BJetCMVAMedium30[:3] ] # only throw arrays into the permutation business
            ftPerms = itertools.permutations(consideredJets, 2)
            for perm in ftPerms:
              mt2wSNT.set_momenta(lep, perm[0], perm[1], pmiss)
              mt2w_values.append(mt2wSNT.get_mt2w())

            p4_jets = std.vector(TLorentzVector)();
            bdisc_jets = std.vector('float')();

            for jet in centralJet30:
              jetTLorentz = ROOT.TLorentzVector(0,0,0,0)
              jetTLorentz.SetPtEtaPhiM(jet.pt, jet.eta, jet.phi, jet.mass)
              p4_jets.push_back(jetTLorentz)
              bdisc_jets.push_back(jet.btagCMVA)

            lepTLorentz = ROOT.TLorentzVector(0,0,0,0)
            lepTLorentz.SetPtEtaPhiM(tightLeps[0].pt, tightLeps[0].eta, tightLeps[0].phi, tightLeps[0].mass)

            if ret['nCentralJet30']>=3: # does not seem to work for njet =3 ??! # need to edit btag working point in the code...!! did not quickly find a twiki with official phys14 cmva working points
              tempTopness = topness.GetTopness(p4_jets,bdisc_jets,lepTLorentz,metp4) #this is really slow!
              if tempTopness <=0:
                print tempTopness, "this will fail"
                ret['Topness'] = log(tempTopness) #this is really slow!
        if len(mt2w_values)>0:
          ret["MT2W"]=min(mt2w_values)
        else:
          ret["MT2W"]=-999

        ret['nHighPtTopTag']=0
        ret['nHighPtTopTagPlusTau23']=0
        for i,j in enumerate(fatjets):
          if j.nSubJets >2 and j.minMass>50 and j.topMass>140 and j.topMass<250:
            ret['nHighPtTopTag'] += 1
            if j.tau3/j.tau2 < 0.6:
              ret['nHighPtTopTagPlusTau23'] += 1


#        print "about to return"
        return ret

if __name__ == '__main__':
  from sys import argv
  file = ROOT.TFile(argv[1])
  tree = file.Get("tree")
  class Tester(Module):
    def __init__(self, name):
      Module.__init__(self,name,None)
      self.sf = EventVars1L()
      def analyze(self,ev):
        print "\nrun %6d lumi %4d event %d: leps %d" % (ev.run, ev.lumi, ev.evt, ev.nLepGood)
        print self.sf(ev)
    el = EventLoop([ Tester("tester") ])
    el.loop([tree], maxEvents = 50)


