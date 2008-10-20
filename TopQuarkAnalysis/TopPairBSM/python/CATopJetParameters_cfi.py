import FWCore.ParameterSet.Config as cms

# Cambridge-Aachen top jet producer parameters
# $Id
CATopJetParameters = cms.PSet(
    algorithm = cms.int32(1),               # 0 = KT, 1 = CA, 2 = anti-KT
    centralEtaCut = cms.double(2.5),        # eta for defining "central" jets                                     
    sumEtEtaCut = cms.double(3.0),          # eta for event SumEt                                                 
    etFrac = cms.double(0.7),               # fraction of event sumEt / 2 for a jet to be considered "hard"
    useAdjacency = cms.bool(False),         # veto adjacent subjets
    useMaxTower = cms.bool(False),          # use max tower in adjacency criterion, otherwise use centroid
    ptBins = cms.vdouble(500,800,1300),     # pt bins over which cuts vary                                        
    rBins = cms.vdouble(0.8,0.6,0.4),       # cone size bins                                                      
    ptFracBins = cms.vdouble(0.1,0.05,0.05),# minimum fraction of central jet pt for subjets
    nCellBins = cms.vint32(1,1,1) ,         # number of cells apart for two subjets to be considered "adjacent"
    debugLevel = cms.untracked.int32(0)     # debug level
)

