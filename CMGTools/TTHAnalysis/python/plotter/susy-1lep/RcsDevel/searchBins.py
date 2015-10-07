# LT bins
binsLT = {}
binsLT['LT1'] = '250 < LT && LT < 350'
binsLT['LT2'] = '350 < LT && LT < 450'
binsLT['LT3'] = '450 < LT && LT < 600'
binsLT['LT3i'] = '450 < LT'
binsLT['LT4i'] = '600 < LT'

# HT bins
binsHT = {}
binsHT['HT0i'] = '500 < HT'
binsHT['HT0'] = '500 < HT && HT < 750'
binsHT['HT1'] = '750 < HT && HT < 1250'
binsHT['HT1i'] = '750 < HT'
binsHT['HT2i'] = '1250 < HT'
binsHT['HT01'] = '500 < HT && HT < 1250'

# NB bins
binsNB = {}
binsNB['NB0'] = 'nBJet == 0'
binsNB['NB1'] = 'nBJet == 1'
binsNB['NB2'] = 'nBJet == 2'
binsNB['NB0i'] = 'nBJet >= 0'
binsNB['NB1i'] = 'nBJet >= 1'
binsNB['NB2i'] = 'nBJet >= 2'
binsNB['NB3i'] = 'nBJet >= 3'

# NJ Bins
binsNJ = {}
binsNJ['NJ34'] = '3 <= nJet && nJet <= 4'
binsNJ['NJ4i'] = '4 <= nJet'
binsNJ['NJ45f9'] = '4 <= nJet && nJet <= 5'
binsNJ['NJ45f6'] = '4 <= nJet && nJet <= 5'
binsNJ['NJ68'] = '6 <= nJet && nJet <= 8'
binsNJ['NJ9i'] = '9 <= nJet'

## Signal/Control region (wrt dPhi)
binsSR = {}
binsSR['SR'] = 'isSR == 1'
binsCR = {}
binsCR['CR'] = 'isSR == 0'

################
# MAKE CUT LISTS
################

### QCD
cutQCD = {}

for nj_bin in ['NJ34']:#,'NJ45']:
    nj_cut = binsNJ[nj_bin]
    ltbins = ['LT1','LT2','LT3','LT4i']

    for lt_bin in ltbins:
        lt_cut = binsLT[lt_bin]

        for ht_bin in ['HT0i']:
            ht_cut = binsHT[ht_bin]

            for nb_bin in ['NB0']:
                nb_cut = binsNB[nb_bin]

                binname = "%s_%s_%s_%s" %(lt_bin,ht_bin,nb_bin,nj_bin)
                cutQCD[binname] = [("base",lt_bin,lt_cut),("base",ht_bin,ht_cut),("base",nb_bin,nb_cut),("base",nj_bin,nj_cut)]

### Inclusive NB,NJ,HT
cutIncl = {}

for nj_bin in ['NJ4i']:#,'NJ45']:
    nj_cut = binsNJ[nj_bin]
    ltbins = ['LT1','LT2','LT3','LT4i']

    for lt_bin in ltbins:
        lt_cut = binsLT[lt_bin]

        for ht_bin in ['HT0i']:
            ht_cut = binsHT[ht_bin]

            for nb_bin in ['NB0i']:
                nb_cut = binsNB[nb_bin]

                binname = "%s_%s_%s_%s" %(lt_bin,ht_bin,nb_bin,nj_bin)
                cutIncl[binname] = [("base",lt_bin,lt_cut),("base",ht_bin,ht_cut),("base",nb_bin,nb_cut),("base",nj_bin,nj_cut)]


### REAL SEARCH BINS (also for RCS)
cutDict = {}
cutDictf9 = {}

cutDictSR = {}
cutDictCR = {}

cutDictSRf9 = {}
cutDictCRf9 = {}

cutDictNJ45f6 = {}
cutDictNJ45f9 = {}
cutDictNJ68 = {}
cutDictNJ9i = {}

for nj_bin in ['NJ45f6','NJ68']:#binsNJ.iteritems():
    nj_cut = binsNJ[nj_bin]

    ltbins = ['LT1','LT2','LT3','LT4i']

    for lt_bin in ltbins:#binsLT.iteritems():
        lt_cut = binsLT[lt_bin]

        htbins = []

        if lt_bin in ['LT1']:
            htbins += ['HT0','HT1i']
        if lt_bin in ['LT2']:
            htbins += ['HT0','HT1']
        if lt_bin in ['LT2','LT3','LT4i']:
            htbins += ['HT2i']
        if lt_bin in ['LT3','LT4i']:
            htbins += ['HT01']

        #for ht_bin,ht_cut in binsHT.iteritems():
        for ht_bin in htbins:
            ht_cut = binsHT[ht_bin]

            nbbins = []

            # Match NB bins
            if lt_bin in ['LT1','LT2','LT3','LT4i']:
                nbbins += ['NB1'] # NB1 present in all NJ,LT bins
            if lt_bin in ['LT4i']:
                nbbins += ['NB2i'] # NB2i present in all NJ,LT bins

            if lt_bin in ['LT1','LT2','LT3']:
                # Signal region binning
                if nj_bin in ['NJ68']:
                    nbbins += ['NB2','NB3i']
                # Side band  binning
                if nj_bin in ['NJ45f6']:
                    nbbins += ['NB2i']

            for nb_bin in nbbins:
                nb_cut = binsNB[nb_bin]

                binname = "%s_%s_%s_%s" %(lt_bin,ht_bin,nb_bin,nj_bin)
                cutDict[binname] = [("base",lt_bin,lt_cut),("base",ht_bin,ht_cut),("base",nb_bin,nb_cut),("base",nj_bin,nj_cut)]

                # split to SR/CR
                for sr_bin in ['SR']:
                    sr_cut = binsSR[sr_bin]

                    binname = "%s_%s_%s_%s_%s" %(lt_bin,ht_bin,nb_bin,nj_bin,sr_bin)
                    cutDictSR[binname] = [("base",lt_bin,lt_cut),("base",ht_bin,ht_cut),("base",nb_bin,nb_cut),("base",nj_bin,nj_cut),("base",sr_bin,sr_cut)]

                for cr_bin in ['CR']:
                    cr_cut = binsCR[cr_bin]

                    binname = "%s_%s_%s_%s_%s" %(lt_bin,ht_bin,nb_bin,nj_bin,cr_bin)
                    cutDictCR[binname] = [("base",lt_bin,lt_cut),("base",ht_bin,ht_cut),("base",nb_bin,nb_cut),("base",nj_bin,nj_cut),("base",cr_bin,cr_cut)]


### FIXME
for nj_bin in ['NJ45f9','NJ9i']:#binsNJ.iteritems():
    nj_cut = binsNJ[nj_bin]

    ltbins = ['LT1','LT2','LT3i']

    for lt_bin in ltbins:#binsLT.iteritems():
        lt_cut = binsLT[lt_bin]

        htbins = []


        ### FIXME
        if lt_bin in ['LT1', 'LT2']:
            htbins += ['HT0i','HT01','HT2i']
        if lt_bin in ['LT3i']:
            htbins += ['HT0i']

        #for ht_bin,ht_cut in binsHT.iteritems():
        for ht_bin in htbins:
            ht_cut = binsHT[ht_bin]

            nbbins = []

            # Match NB bins
            if lt_bin in ['LT1','LT2'] and not ht_bin in['HT0i']:
                # Signal region binning
                if nj_bin in ['NJ9i']:
                    nbbins += ['NB1','NB2']
                # Side band  binning
                if nj_bin in ['NJ45f9']:
                    nbbins += ['NB1','NB2i']

            if lt_bin in ['LT3i']:
                nbbins += ['NB1i']

            if lt_bin in ['LT1','LT2'] and ht_bin in ['HT0i']:
                if nj_bin in ['NJ9i']:
                    nbbins += ['NB3i']
                # Side band  binning
                if nj_bin in ['NJ45f9']:
                    nbbins += ['NB2i']



            for nb_bin in nbbins:
                nb_cut = binsNB[nb_bin]

                binname = "%s_%s_%s_%s" %(lt_bin,ht_bin,nb_bin,nj_bin)

                cutDictf9[binname] = [("base",lt_bin,lt_cut),("base",ht_bin,ht_cut),("base",nb_bin,nb_cut),("base",nj_bin,nj_cut)]

                                # split to SR/CR

                for sr_bin in ['SR']:
                    sr_cut = binsSR[sr_bin]

                    binname = "%s_%s_%s_%s_%s" %(lt_bin,ht_bin,nb_bin,nj_bin,sr_bin)
                    cutDictSRf9[binname] = [("base",lt_bin,lt_cut),("base",ht_bin,ht_cut),("base",nb_bin,nb_cut),("base",nj_bin,nj_cut),("base",sr_bin,sr_cut)]

                for cr_bin in ['CR']:
                    cr_cut = binsCR[cr_bin]

                    binname = "%s_%s_%s_%s_%s" %(lt_bin,ht_bin,nb_bin,nj_bin,cr_bin)
                    cutDictCRf9[binname] = [("base",lt_bin,lt_cut),("base",ht_bin,ht_cut),("base",nb_bin,nb_cut),("base",nj_bin,nj_cut),("base",cr_bin,cr_cut)]

