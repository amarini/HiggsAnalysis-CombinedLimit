from __future__ import absolute_import, print_function

import fnmatch
import json
import re

from HiggsAnalysis.CombinedLimit.PhysicsModel import *
from HiggsAnalysis.CombinedLimit.SMHiggsBuilder import SMHiggsBuilder
import six
import os

ALL_STXS_PROCS = {
    "Stage0": {
        "ggH*": "ggH",
        "bbH*": "ggH",
        "ggZH_had*": "ggH",
        "qqH*": "qqH",
        "ttH*": "ttH",
        "tH[Wq]*": "tH",
        "ggZH_lep*": "totZH_lep",
        "ZH_lep*": "totZH_lep",
        "WH_lep*": "WH_lep",
        #"[VWZ]H_had*": "qqH",
        "[VWZ]H_had*": "VH_had",
    }
}

CMS_to_LHCHCG_DecSimple = {
    "hww": "WW",
    "hzz": "ZZ",
    "hgg": "gamgam",
    "hbb": "bb",
    "hcc": "cc",
    "htt": "tautau",
    "hmm": "mumu",
    "hzg": "Zgam",
    "hgluglu": "gluglu",
    "hinv": "inv",
    "hss": "ss",
}


def getSTXSProdDecMode(bin, process, options):
    """Return a triple of (production)"""
    processSource = process
    decaySource = options.fileName + ":" + bin  # by default, decay comes from the datacard name or bin label
    if "_" in process:
        (processSource, decaySource) = (
            "_".join(process.split("_")[0:-1]),
            process.split("_")[-1],
        )
        for Y in ["2016", "2017", "2018"]:
            if Y in processSource.split("_")[-1]:
                processSource = "_".join(processSource.split("_")[0:-1])
    foundDecay = None
    for D in ALL_HIGGS_DECAYS:
        if D in decaySource:
            if foundDecay:
                raise RuntimeError("Validation Error: decay string %s contains multiple known decay names" % decaySource)
            foundDecay = CMS_to_LHCHCG_DecSimple[D]
    if not foundDecay:
        raise RuntimeError("Validation Error: decay string %s does not contain any known decay name" % decaySource)
    #
    foundEnergy = None
    for D in ["7TeV", "8TeV", "13TeV", "14TeV"]:
        if D in decaySource:
            if foundEnergy:
                raise RuntimeError("Validation Error: decay string %s contains multiple known energies" % decaySource)
            foundEnergy = D
    if not foundEnergy:
        for D in ["7TeV", "8TeV", "13TeV", "14TeV"]:
            if D in options.fileName + ":" + bin:
                if foundEnergy:
                    raise RuntimeError("Validation Error: decay string %s contains multiple known energies" % decaySource)
                foundEnergy = D
    if not foundEnergy:
        foundEnergy = "13TeV"  ## if using 81x, chances are its 13 TeV
        print("Warning: decay string %s does not contain any known energy, assuming %s" % (decaySource, foundEnergy))
    #
    return (processSource, foundDecay, foundEnergy)


class STXSBaseModel(PhysicsModel):
    def __init__(self, denominator="WW"):
        PhysicsModel.__init__(self)  # not using 'super(x,self).__init__' since I don't understand it
        self.floatMass = False
        self.denominator = denominator
        self.mergeBins = False
        self.mergeJson = ""
        self.addStage0 = False
        self.addHbbBoostedSplitting = False

    def preProcessNuisances(self, nuisances):
        # add here any pre-processed nuisances such as constraint terms for the mass profiling?
        return

    def setPhysicsOptions(self, physOptions):
        for po in physOptions:
            print(po)
            if po.startswith("higgsMassRange="):
                self.floatMass = True
                self.mHRange = po.replace("higgsMassRange=", "").split(",")
                print("The Higgs mass range:", self.mHRange)
                if len(self.mHRange) != 2:
                    raise RuntimeError("Higgs mass range definition requires two extrema")
                elif float(self.mHRange[0]) >= float(self.mHRange[1]):
                    raise RuntimeError("Extrama for Higgs mass range defined with inverterd order. Second must be larger the first")
            if po.startswith("mergejson="):
                self.mergeBins = True
                self.mergeJson = po.replace("mergejson=", "")
            if po.startswith("addStage0="):
                self.addStage0 = po.replace("addStage0=", "") in ["yes", "1", "Yes", "True", "true"]
            if po.startswith("addHbbBoostedSplitting="):
                self.addHbbBoostedSplitting = po.replace("addHbbBoostedSplitting=", "") in ["yes", "1", "Yes", "True", "true"]

    def doMH(self):
        if self.floatMass:
            if self.modelBuilder.out.var("MH"):
                self.modelBuilder.out.var("MH").setRange(float(self.mHRange[0]), float(self.mHRange[1]))
                self.modelBuilder.out.var("MH").setConstant(False)
            else:
                self.modelBuilder.doVar("MH[%s,%s]" % (self.mHRange[0], self.mHRange[1]))
            self.POIs += ",MH"
        else:
            if self.modelBuilder.out.var("MH"):
                self.modelBuilder.out.var("MH").setVal(self.options.mass)
                self.modelBuilder.out.var("MH").setConstant(True)
            else:
                self.modelBuilder.doVar("MH[%g]" % self.options.mass)

    def getYieldScale(self, bin, process):
        "Split in production and decay, and call getHiggsSignalYieldScale; return 1 for backgrounds"
        if not self.DC.isSignal[process]:
            return 1
        
        # Fix FWDH bins to SM
        if ("FWDH" in process)|("fwd" in process):
            return 1

        (processSource, foundDecay, foundEnergy) = getSTXSProdDecMode(bin, process, self.options)
        return self.getHiggsSignalYieldScale(processSource, foundDecay, foundEnergy)


class StageZero(STXSBaseModel):
    "Allow different signal strength fits for the stage-0 model"

    def __init__(self, denominator="WW"):
        STXSBaseModel.__init__(self)  # not using 'super(x,self).__init__' since I don't understand it
        self.POIs = ""

    def doVar(self, x, constant=True):
        self.modelBuilder.doVar(x)
        vname = re.sub(r"\[.*", "", x)
        self.modelBuilder.out.var(vname).setConstant(constant)
        print("SignalStrengths:: declaring %s as %s" % (vname, x))

    def doParametersOfInterest(self):
        """Create POI out of signal strengths (and MH)"""
        pois = []

        allProds = []
        for regproc in ALL_STXS_PROCS["Stage0"].keys():
            P = ALL_STXS_PROCS["Stage0"][regproc]
            if P in allProds:
                continue
            allProds.append(P)
            self.doVar("mu_XS_%s[1,0,5]" % P)
            pois.append("mu_XS_%s" % P)

        print(pois)
        self.POIs = ",".join(pois)

        self.doMH()
        print("Default parameters of interest: ", self.POIs)
        self.modelBuilder.doSet("POI", self.POIs)
        self.SMH = SMHiggsBuilder(self.modelBuilder)
        self.setup()

    def setup(self):
        for d in SM_HIGG_DECAYS + ["hss"]:
            self.SMH.makeBR(d)
        allProds = []
        for regproc in ALL_STXS_PROCS["Stage0"].keys():
            P = ALL_STXS_PROCS["Stage0"][regproc]
            if P in allProds:
                continue
            allProds.append(P)
            muXS = "mu_XS_%s" % P
            self.modelBuilder.factory_("expr::scaling_" + P + '_13TeV("@0",' + muXS + ")")

    def getHiggsSignalYieldScale(self, production, decay, energy):
        for regproc in ALL_STXS_PROCS["Stage0"].keys():
            if fnmatch.fnmatch(production, regproc):
                return "scaling_%s_%s" % (
                    ALL_STXS_PROCS["Stage0"][regproc],
                    energy,
                )

        # raise RuntimeError, "No production process matching %s for Stage0 found !"%production
        print("WARNING: No production process matching %s for Stage0 found, will scale by 1 !" % production)
        return 1



class StageZeroRatio(STXSBaseModel):
    "Allow different signal strength fits for the stage-0 model"

    def __init__(self, denominator="WW"):
        STXSBaseModel.__init__(self)  # not using 'super(x,self).__init__' since I don't understand it
        self.denominator = denominator
        self.POIs = ""

    def doVar(self, x, constant=True):
        self.modelBuilder.doVar(x)
        vname = re.sub(r"\[.*", "", x)
        self.modelBuilder.out.var(vname).setConstant(constant)
        print("SignalStrengths:: declaring %s as %s" % (vname, x))

    def doParametersOfInterest(self):
        """Create POI out of signal strengths (and MH)"""
        pois = []

        allProds = []
        for regproc in ALL_STXS_PROCS["Stage0"].keys():
            P = ALL_STXS_PROCS["Stage0"][regproc]
            if P in allProds:
                continue
            allProds.append(P)
            for dec in SM_HIGG_DECAYS:
                D = CMS_to_LHCHCG_DecSimple[dec]
                if D == self.denominator:
                    if not "mu_XS_%s_x_BR_%s" % (P, self.denominator) in pois:
                        self.doVar("mu_XS_%s_x_BR_%s[1,0,5]" % (P, self.denominator))
                        pois.append("mu_XS_%s_x_BR_%s" % (P, self.denominator))
                else:
                    if not "mu_BR_%s_r_BR_%s" % (D, self.denominator) in pois:
                        self.doVar("mu_BR_%s_r_BR_%s[1,0,5]" % (D, self.denominator))
                        pois.append("mu_BR_%s_r_BR_%s" % (D, self.denominator))
                        #Need to reparameterize Gammabb/GammaZZ as Gammabb/GammaZZ*(1+sum an((mb/2.787)^n-1))
                        #with a1= -0.07086, a2=1.144, a3=-0.1361, a4=0.06038, a5=-0.01167

        print(pois)
        self.POIs = ",".join(pois)

        self.doMH()
        print("Default parameters of interest: ", self.POIs)
        self.modelBuilder.doSet("POI", self.POIs)
        self.SMH = SMHiggsBuilder(self.modelBuilder)
        self.setup()

    def setup(self):
        for d in SM_HIGG_DECAYS + ["hss"]:
            self.SMH.makeBR(d)
        allProds = []
        for regproc in ALL_STXS_PROCS["Stage0"].keys():
            P = ALL_STXS_PROCS["Stage0"][regproc]
            if P in allProds:
                continue
            allProds.append(P)
            allDecs = []
            for dec in SM_HIGG_DECAYS:
                D = CMS_to_LHCHCG_DecSimple[dec]
                if D in allDecs:
                    continue
                allDecs.append(D)
                if D == self.denominator:
                    muXSBR = "mu_XS_%s_x_BR_%s" % (P, self.denominator)
                    self.modelBuilder.factory_("expr::scaling_" + P + "_" + D + '_13TeV("@0",' + muXSBR + ")")
                else:
                    muXSBR = "mu_XS_%s_x_BR_%s" % (P, self.denominator)
                    muBR = "mu_BR_%s_r_BR_%s" % (D, self.denominator)
                    self.modelBuilder.factory_("expr::scaling_" + P + "_" + D + '_13TeV("@0*@1",' + muXSBR + "," + muBR + ")")

    def getHiggsSignalYieldScale(self, production, decay, energy):
        for regproc in ALL_STXS_PROCS["Stage0"].keys():
            if fnmatch.fnmatch(production, regproc):
                return "scaling_%s_%s_%s" % (
                    ALL_STXS_PROCS["Stage0"][regproc],
                    decay,
                    energy,
                )

        # raise RuntimeError, "No production process matching %s for Stage0 found !"%production
        print("WARNING: No production process matching %s for Stage0 found, will scale by 1 !" % production)
        return 1

class StageZeroRunningmb(STXSBaseModel):
    "Allow different signal strength fits for the stage-0 model, for measuring running b quark mass"

    def __init__(self, denominator="ZZ", profileBR=False, analytic=False):
        STXSBaseModel.__init__(self)  # not using 'super(x,self).__init__' since I don't understand it
        self.denominator = denominator
        self.POIs = ""
        if self.denominator != 'ZZ':
            raise ValueError("Denominator is different from ZZ. Check if implementation is ok.")
        datadir = os.environ["CMSSW_BASE"] + "/src/HiggsAnalysis/CombinedLimit/data/lhc-hxswg"
        self.mbparam =os.path.join(datadir,"sm/mbparam.txt")
        self.profileBR=profileBR
        self.analytic = analytic ### analytic parametrization

        if not self.profileBR and self.analytic:
            raise ValueError("analytic => profileBR")

    def doVar(self, x, constant=True):
        self.modelBuilder.doVar(x)
        vname = re.sub(r"\[.*", "", x)
        self.modelBuilder.out.var(vname).setConstant(constant)
        print("SignalStrengths:: declaring %s as %s" % (vname, x))

    def doParametersOfInterest(self):
        """Create POI out of signal strengths (and MH)"""
        pois = []

        allProds = []
        for regproc in ALL_STXS_PROCS["Stage0"].keys():
            P = ALL_STXS_PROCS["Stage0"][regproc]
            if P in allProds:
                continue
            allProds.append(P)
            if not self.profileBR:
                print("Doing poi:","mu_XS_%s[1,0,5]"%P)
                self.doVar("mu_XS_%s[1,0,5]"%P)
                pois.append("mu_XS_%s"%P)
            for dec in SM_HIGG_DECAYS:
                D = CMS_to_LHCHCG_DecSimple[dec]
                if self.profileBR:
                    if D == self.denominator:
                        if not "mu_XS_%s_x_BR_%s" % (P, self.denominator) in pois:
                            print ( "Doing POI","mu_XS_%s_x_BR_%s" % (P, self.denominator))
                            self.doVar("mu_XS_%s_x_BR_%s[1,0,5]" % (P, self.denominator))
                            pois.append("mu_XS_%s_x_BR_%s" % (P, self.denominator))
                    else:
                        if not "mu_BR_%s_r_BR_%s" % (D, self.denominator) in pois:
                            print("Doing POI","mu_BR_%s_r_BR_%s[1,0,5]" % (D, self.denominator))
                            self.doVar("mu_BR_%s_r_BR_%s[1,0,5]" % (D, self.denominator))
                            pois.append("mu_BR_%s_r_BR_%s" % (D, self.denominator))

        self.doVar("mb[2.787,0,5]")
        pois.append("mb")
                        #Need to reparameterize Gammabb/GammaZZ as Gammabb/GammaZZ*(1+sum an((mb/2.787)^n-1))
                        #with a1= -0.07086, a2=1.144, a3=-0.1361, a4=0.06038, a5=-0.01167. Gammabb/GammaZZsm =22 (do we need it?)

        print("POIs=",pois)
        self.POIs = ",".join(pois)

        self.doMH()
        print("Default parameters of interest: ", self.POIs)
        self.modelBuilder.doSet("POI", self.POIs)
        self.SMH = SMHiggsBuilder(self.modelBuilder)
        

        self.setup()
    
        #cat ../data/lhc-hxswg/sm/mbparam.txt
        # 0        1            2          3              4                     5                     6               7                 8                 9                         10                    11       
        # mb_gev width_zz_gev zz_vs_ref bb_over_zz_vs_ref tautau_over_zz_vs_ref mumu_over_zz_vs_ref ss_over_zz_vs_ref cc_over_zz_vs_ref gg_over_zz_vs_ref gammagamma_over_zz_vs_ref zgamma_over_zz_vs_ref ww_over_zz_vs_ref total_over_zz_vs_ref
    def makeWidth(self, decay):
        if decay == "hww":
            print("Spline: gamma_hww_o_hzz_SM")
            self.SMH.textToSpline("gamma_hww_o_hzz_SM", self.mbparam, ycol=11, xvar="mb")
        if decay == "hzz":
            print("Spline: Gamma_hzz_SM")
            self.SMH.textToSpline("Gamma_hzz_SM", self.mbparam, ycol=2,xvar="mb") ## capital Gamma is 
        if decay == "hgg": ## gamma gamma - not gluon-gluon
            print("Spline: gamma_hgg_o_hzz_SM")
            self.SMH.textToSpline("gamma_hgg_o_hzz_SM", self.mbparam, ycol=9,xvar="mb")
        if decay == "hzg":
            print("Spline: gamma_hzg_o_hzz_SM")
            self.SMH.textToSpline("gamma_hzg_o_hzz_SM", self.mbparam, ycol=10,xvar="mb")
        if decay == "hbb":
            print("Spline: gamma_hbb_o_hzz_SM")
            self.SMH.textToSpline("gamma_hbb_o_hzz_SM", self.mbparam, ycol=3,xvar="mb")
        if decay == "htt":
            print("Spline: gamma_htt_o_hzz_SM")
            self.SMH.textToSpline("gamma_htt_o_hzz_SM", self.mbparam, ycol=4,xvar="mb")
        if decay == "hmm":
            print("Spline: gamma_hmm_o_hzz_SM")
            self.SMH.textToSpline("gamma_hmm_o_hzz_SM", self.mbparam, ycol=5,xvar="mb")
        if decay == "hss":
            print("Spline: gamma_hss_o_hzz_SM")
            self.SMH.textToSpline("gamma_hss_o_hzz_SM", self.mbparam, ycol=6,xvar="mb")
        if decay == "hcc":
            print("Spline: gamma_hcc_o_hzz_SM")
            self.SMH.textToSpline("gamma_hcc_o_hzz_SM", self.mbparam, ycol=7,xvar="mb")
        if decay == "hgluglu":
            print("Spline: gamma_hgluglu_o_hzz_SM")
            self.SMH.textToSpline("gamma_hgluglu_o_hzz_SM", self.mbparam, ycol=8,xvar="mb")
        if decay == "htoptop":
            pass
            #self.SMH.textToSpline("gamma_hgluglu_o_hzz_SM", self.mbparam, ycol=8)
        if decay == "tot": ## in the spline this is Gamma_tot / Gamma_ZZ vs SM.
            print("Spline: gamma_tot_o_hzz_SM")
            self.SMH.textToSpline("gamma_tot_o_hzz_SM", self.mbparam, ycol=12,xvar="mb")

    def setup(self):
        print("[StageZeroRunningmb], profileBR=",self.profileBR)
        
        if not self.profileBR:
            self.makeWidth("tot")

        for d in SM_HIGG_DECAYS + ["hss"]:
            if not self.profileBR or (d == 'hbb' and not self.analytic):
                self.makeWidth(d)
            if self.profileBR:
                self.SMH.makeBR(d) ## do I need the BR ?
        allProds = []

#SM_HIGG_DECAYS = ["hww", "hzz", "hgg", "htt", "hbb", "hzg", "hmm", "hcc", "hgluglu"]
        for dec in SM_HIGG_DECAYS + ["hss"]:
            D = CMS_to_LHCHCG_DecSimple[dec]


        for regproc in ALL_STXS_PROCS["Stage0"].keys():
            P = ALL_STXS_PROCS["Stage0"][regproc]
            if P in allProds:
                continue
            allProds.append(P)
            allDecs = []
            for dec in SM_HIGG_DECAYS:
                D = CMS_to_LHCHCG_DecSimple[dec]
                if D in allDecs:
                    continue
                allDecs.append(D)
                if self.profileBR:
                    if D == self.denominator:
                        ## GammaZ o GammaTot
                        muXSBR = "mu_XS_%s_x_BR_%s" % (P, self.denominator)
                        self.modelBuilder.factory_("expr::scaling_" + P + "_" + D + '_13TeV("@0",'+muXSBR+',)')
                    elif D =="bb":
                        muXSBR = "mu_XS_%s_x_BR_%s" % (P, self.denominator)
                        if self.analytic:
                            self.modelBuilder.factory_("expr::scaling_" + P + "_" + D + '_13TeV("@0*(1-0.07086*(@1/2.787-1) + 1.144*(pow((@1/2.787),2)-1) -0.1361*(pow((@1/2.787),3)-1) + 0.06038*(pow((@1/2.787),4)-1) - 0.01167*(pow((@1/2.787),5)-1))",' + muXSBR + "," + "mb" + ")")
                        else:
                            self.modelBuilder.factory_("expr::scaling_"+ P + "_" + D + '_13TeV("@0*@1",gamma_'+dec+'_o_hzz_SM, '+muXSBR+')')
                    else:
                        muXSBR = "mu_XS_%s_x_BR_%s" % (P, self.denominator)
                        muBR = "mu_BR_%s_r_BR_%s" % (D, self.denominator)
                        self.modelBuilder.factory_("expr::scaling_" + P + "_" + D + '_13TeV("@0*@1",' + muXSBR + "," + muBR + ")")

                else: ## not self.profileBR
                    if D == self.denominator:
                        ## GammaZ o GammaTot . Gamma_tot is actually Gamma_tot_o_Gamma_ZZ in the splines
                        self.modelBuilder.factory_("expr::scaling_" + P + "_" + D + '_13TeV("@0/@1",mu_XS_'+P+',gamma_tot_o_hzz_SM)')
                    else: #D =="bb":
                        ## gamma_hbb_o_hzz_SM * Gamma_ZZ / Gamma_tot
                        self.modelBuilder.factory_("expr::scaling_"+ P + "_" + D + '_13TeV("@0*@2/@1",gamma_'+dec+'_o_hzz_SM,gamma_tot_o_hzz_SM,mu_XS_'+P+')')


    def getHiggsSignalYieldScale(self, production, decay, energy):
        for regproc in ALL_STXS_PROCS["Stage0"].keys():
            if fnmatch.fnmatch(production, regproc):
                return "scaling_%s_%s_%s" % (
                    ALL_STXS_PROCS["Stage0"][regproc],
                    decay,
                    energy,
                )

        # raise RuntimeError, "No production process matching %s for Stage0 found !"%production
        print("WARNING: No production process matching %s for Stage0 found, will scale by 1 !" % production)
        return 1



class StageOnePTwo(STXSBaseModel):
    "Allow different signal strength fits for the stage-1.2 model"

    def __init__(self):
        STXSBaseModel.__init__(self)  # not using 'super(x,self).__init__' since I don't understand it
        self.POIs = "mu"
        from HiggsAnalysis.CombinedLimit.STXS import stage1_2_procs, stage1_2_fine_procs, stage1_2_merged_procs
        self.stage1_2_fine_procs = stage1_2_fine_procs
        self.PROCESSES = [x for v in six.itervalues(stage1_2_procs) for x in v]
        self.FINEPROCESSES = [x for v in six.itervalues(stage1_2_fine_procs) for x in v]
        self.mergeSchemes = {}
        self.mergeSchemes["prod_only"] = {}
        self.mergeSchemes["prod_times_dec"] = {}
        # Fix for HWW (merged procs in datacard)
        self.stage1_2_merged_procs = stage1_2_merged_procs
        self.MERGEDPROCESSES = []

    def doVar(self, x, constant=True):
        self.modelBuilder.doVar(x)
        vname = re.sub(r"\[.*", "", x)
        self.modelBuilder.out.var(vname).setConstant(constant)
        print("SignalStrengths:: declaring %s as %s" % (vname, x))

    def doParametersOfInterest(self):
        """Create POI out of signal strengths (and MH)"""

        if self.mergeBins:
            with open(self.mergeJson) as f:
                self.mergeSchemes = json.load(f)
                self.modelBuilder.stringout = json.dumps(self.mergeSchemes)
            f.close()

        # Add stage 0 processes
        if self.addStage0:
            from HiggsAnalysis.CombinedLimit.STXS import stage0_procs
            PROCESSES_STAGE0 = [x for v in six.itervalues(stage0_procs) for x in v]
            for proc_stage0 in PROCESSES_STAGE0:
                if proc_stage0 not in self.PROCESSES: self.PROCESSES.append(proc_stage0)

        allProds = []
        for registered_proc in self.PROCESSES:
            P = registered_proc
            if P in allProds:
                continue
            allProds.append(P)
            self.doVar("mu_XS_%s[1,0,5]" % (P))
            for merged_prod_bin in self.mergeSchemes["prod_only"]:
                if P in self.mergeSchemes["prod_only"][merged_prod_bin]:
                    self.doVar("mu_XS_%s[1,0,5]" % (merged_prod_bin))
            for dec in SM_HIGG_DECAYS:
                D = CMS_to_LHCHCG_DecSimple[dec]
                self.doVar("mu_XS_%s_BR_%s[1,0,5]" % (P, D))
                for merged_proddec_bin in self.mergeSchemes["prod_times_dec"]:
                    if P in self.mergeSchemes["prod_times_dec"][merged_proddec_bin]:
                        self.doVar("mu_XS_%s_BR_%s[1,0,5]" % (merged_proddec_bin, D))
        for dec in SM_HIGG_DECAYS:
            D = CMS_to_LHCHCG_DecSimple[dec]
            self.doVar("mu_BR_%s[1,0,5]" % (D))

        # Fix for H->bb boosted to fit split bins
        if self.addHbbBoostedSplitting:
            # Define finer split bin POIs in dict
            del self.stage1_2_fine_procs["qqH_GE2J_MJJ_GT350_PTH_GT200"]
            self.stage1_2_fine_procs["qqH_GE2J_MJJ_1000_1500_PTH_GT200"] = ["qqH_GE2J_MJJ_1000_1500_PTH_GT200_PTHJJ_0_25", "qqH_GE2J_MJJ_1000_1500_PTH_GT200_PTHJJ_GT25"]
            self.stage1_2_fine_procs["qqH_GE2J_MJJ_GT1500_PTH_GT200"] = ["qqH_GE2J_MJJ_GT1500_PTH_GT200_PTHJJ_0_25", "qqH_GE2J_MJJ_GT1500_PTH_GT200_PTHJJ_GT25"]
            # Save POIs in workspace
            for registered_proc in ["qqH_GE2J_MJJ_1000_1500_PTH_GT200", "qqH_GE2J_MJJ_GT1500_PTH_GT200"]:
                P = registered_proc
                allProds.append(P)
                self.doVar("mu_XS_%s[1,0,5]" % (P))
                for dec in SM_HIGG_DECAYS:
                    D = CMS_to_LHCHCG_DecSimple[dec]
                    self.doVar("mu_XS_%s_BR_%s[1,0,5]" % (P, D))

        self.doMH()
        self.doVar("mu[1,0,5]")
        self.modelBuilder.doSet("POI", self.POIs)
        self.SMH = SMHiggsBuilder(self.modelBuilder)
        self.setup()

    def setup(self):
        for d in SM_HIGG_DECAYS + ["hss"]:
            self.SMH.makeBR(d)
        allProds = []
        for P in self.PROCESSES:
            if P in allProds:
                continue
            allProds.append(P)
            allDecs = []
            for dec in SM_HIGG_DECAYS:
                D = CMS_to_LHCHCG_DecSimple[dec]
                if D in allDecs:
                    continue
                allDecs.append(D)
                terms = ["mu", "mu_XS_%s" % P, "mu_BR_" + D, "mu_XS_%s_BR_%s" % (P, D)]
                for merged_prod_bin in self.mergeSchemes["prod_only"]:
                    if P in self.mergeSchemes["prod_only"][merged_prod_bin]:
                        terms += ["mu_XS_%s" % merged_prod_bin]
                for merged_proddec_bin in self.mergeSchemes["prod_times_dec"]:
                    if P in self.mergeSchemes["prod_times_dec"][merged_proddec_bin]:
                        terms += ["mu_XS_%s_BR_%s" % (merged_proddec_bin, D)]
                self.modelBuilder.factory_("prod::scaling_%s_%s_13TeV(%s)" % (P, D, ",".join(terms)))
                self.modelBuilder.out.function("scaling_%s_%s_13TeV" % (P, D)).Print("")

        for P in self.FINEPROCESSES:
            print("WARNING: process %s is treated as a stage1_2_fine process; no separate scaling parameter for it will enter" % P)
            if P in allProds:
                continue
            allProds.append(P)
            allDecs = []
            for dec in SM_HIGG_DECAYS:
                D = CMS_to_LHCHCG_DecSimple[dec]
                if D in allDecs:
                    continue
                allDecs.append(D)
                for stxs12binname in self.stage1_2_fine_procs:
                    if P in self.stage1_2_fine_procs[stxs12binname]:
                        terms = ["mu", "mu_XS_%s" % stxs12binname, "mu_BR_" + D, "mu_XS_%s_BR_%s" % (stxs12binname, D)]
                        for merged_prod_bin in self.mergeSchemes["prod_only"]:
                            if stxs12binname in self.mergeSchemes["prod_only"][merged_prod_bin]:
                                terms += ["mu_XS_%s" % merged_prod_bin]
                        for merged_proddec_bin in self.mergeSchemes["prod_times_dec"]:
                            if stxs12binname in self.mergeSchemes["prod_times_dec"][merged_proddec_bin]:
                                terms += ["mu_XS_%s_BR_%s" % (merged_proddec_bin, D)]
                self.modelBuilder.factory_("prod::scaling_%s_%s_13TeV(%s)" % (P, D, ",".join(terms)))
                self.modelBuilder.out.function("scaling_%s_%s_13TeV" % (P, D)).Print("")

        # Fix for merged procs in datacard: e.g. VH leptonic bins in H->WW (STXS)
        # Must account for merged-bin signal strengths, which complicates the situation
        for D, merged_bins in self.stage1_2_merged_procs.items():
            for P, components in merged_bins.items():
                terms = ["mu", "mu_BR_"+D]
                terms_sum = []
                for stxs12binname, frac in components.items():
                    terms_stxs12 = []
                    self.doVar("frac_scaling_%s_component_%s_13TeV[%s,%s,%s]" % (stxs12binname, D, frac, frac, frac))
                    self.modelBuilder.out.var("frac_scaling_%s_component_%s_13TeV"% (stxs12binname, D)).setConstant(True) 
                    terms_stxs12 += ["frac_scaling_%s_component_%s_13TeV"% (stxs12binname, D), "mu_XS_%s" % stxs12binname, "mu_XS_%s_BR_%s" % (stxs12binname, D)]
                    for merged_prod_bin in self.mergeSchemes["prod_only"]:
                        if stxs12binname in self.mergeSchemes["prod_only"][merged_prod_bin]:
                            terms_stxs12 += ["mu_XS_%s" % merged_prod_bin]
                    for merged_proddec_bin in self.mergeSchemes["prod_times_dec"]:
                        if stxs12binname in self.mergeSchemes["prod_times_dec"][merged_proddec_bin]:
                            terms_stxs12 += ["mu_XS_%s_BR_%s" % (merged_proddec_bin, D)]
                    self.modelBuilder.factory_("prod::scaling_%s_component_%s_13TeV(%s)" % (stxs12binname, D, ",".join(terms_stxs12)))
                    terms_sum += ["scaling_%s_component_%s_13TeV" % (stxs12binname, D)]
    
                self.modelBuilder.factory_("sum::scaling_%s_sum_%s_13TeV(%s)" % (P, D, ",".join(terms_sum)))
                terms += ["scaling_%s_sum_%s_13TeV" % (P, D)]
                self.modelBuilder.factory_("prod::scaling_%s_%s_13TeV(%s)" % (P, D, ",".join(terms)))
                if P not in self.MERGEDPROCESSES:
                    self.MERGEDPROCESSES.append(P)
    
    
    def getHiggsSignalYieldScale(self, production, decay, energy):
        # Catch for H->Zgam: taken from STXStoSMEFT model
        if (decay == "Zgam") | ("bkg" in production):
            production = production.split("_")[0]

        for regproc in self.PROCESSES:
            if fnmatch.fnmatch(production, regproc):
                return "scaling_%s_%s_%s" % (regproc, decay, energy)

        for regproc in self.FINEPROCESSES:
            if fnmatch.fnmatch(production, regproc):
                return "scaling_%s_%s_%s" % (regproc, decay, energy)

        for regproc in self.MERGEDPROCESSES:
            if fnmatch.fnmatch(production, regproc):
                return "scaling_%s_%s_%s" % (regproc, decay, energy)

        # raise RuntimeError, "No production process matching %s for Stage0 found !"%production
        print("WARNING: No production process matching %s for Stage1.2 found, will scale by 1 !" % production)
        return 1


class StageOnePTwoRatio(STXSBaseModel):
    "Allow different signal strength fits for the stage-1.2 model"

    def __init__(self, denominator="WW"):
        STXSBaseModel.__init__(self)  # not using 'super(x,self).__init__' since I don't understand it
        self.denominator = denominator
        self.POIs = "mu"
        from HiggsAnalysis.CombinedLimit.STXS import stage1_2_procs, stage1_2_fine_procs, stage1_2_merged_procs
        self.stage1_2_fine_procs = stage1_2_fine_procs
        self.PROCESSES = [x for v in six.itervalues(stage1_2_procs) for x in v]
        self.FINEPROCESSES = [x for v in six.itervalues(stage1_2_fine_procs) for x in v]
        self.mergeSchemes = {}
        self.mergeSchemes["prod_only"] = {}
        self.mergeSchemes["prod_times_dec"] = {}
        # Fix for HWW (merged procs in datacard)
        self.stage1_2_merged_procs = stage1_2_merged_procs
        self.MERGEDPROCESSES = []

    def doVar(self, x, constant=True):
        self.modelBuilder.doVar(x)
        vname = re.sub(r"\[.*", "", x)
        self.modelBuilder.out.var(vname).setConstant(constant)
        print("SignalStrengths:: declaring %s as %s" % (vname, x))

    def doParametersOfInterest(self):
        """Create POI out of signal strengths (and MH)"""
        pois = []

        if self.mergeBins:
            with open(self.mergeJson) as f:
                self.mergeSchemes = json.load(f)
                self.modelBuilder.stringout = json.dumps(self.mergeSchemes)
            f.close()

        allProds = []
        for registered_proc in self.PROCESSES:
            P = registered_proc
            if P in allProds:
                continue
            allProds.append(P)
            for dec in SM_HIGG_DECAYS:
                D = CMS_to_LHCHCG_DecSimple[dec]
                if D == self.denominator:
                    self.doVar("mu_XS_%s_x_BR_%s[1,0,5]" % (P, self.denominator))
                    pois.append("mu_XS_%s_x_BR_%s[1,0,5]" % (P, self.denominator))
                    for merged_proddec_bin in self.mergeSchemes["prod_times_dec"]:
                        if P in self.mergeSchemes["prod_times_dec"][merged_proddec_bin]:
                            self.doVar("mu_XS_%s_x_BR_%s[1,0,5]" % (merged_proddec_bin, self.denominator))
                            pois.append("mu_XS_%s_x_BR_%s[1,0,5]" % (merged_proddec_bin, self.denominator))
                else:
                    if not "mu_BR_%s_r_BR_%s" % (D, self.denominator) in pois:
                        self.doVar("mu_BR_%s_r_BR_%s[1,0,5]" % (D, self.denominator))
                        pois.append("mu_BR_%s_r_BR_%s[1,0,5]" % (D, self.denominator))

        self.doMH()
        self.doVar("mu[1,0,5]")
        self.modelBuilder.doSet("POI", self.POIs)
        self.SMH = SMHiggsBuilder(self.modelBuilder)
        self.setup()

    def setup(self):
        for d in SM_HIGG_DECAYS + ["hss"]:
            self.SMH.makeBR(d)
        allProds = []
        for P in self.PROCESSES:
            if P in allProds:
                continue
            allProds.append(P)
            allDecs = []
            for dec in SM_HIGG_DECAYS:
                D = CMS_to_LHCHCG_DecSimple[dec]
                if D in allDecs:
                    continue
                allDecs.append(D)
                terms = ["mu_XS_%s_x_BR_%s"% (P, self.denominator)] 
                for merged_proddec_bin in self.mergeSchemes["prod_times_dec"]:
                    if P in self.mergeSchemes["prod_times_dec"][merged_proddec_bin]:
                        terms += ["mu_XS_%s_x_BR_%s" % (merged_proddec_bin, self.denominator)]
                if D != self.denominator:
                    terms += ["mu_BR_%s_r_BR_%s" % (D, self.denominator)]
                self.modelBuilder.factory_("prod::scaling_%s_%s_13TeV(%s)" % (P, D, ",".join(terms)))
                self.modelBuilder.out.function("scaling_%s_%s_13TeV" % (P, D)).Print("")

        for P in self.FINEPROCESSES:
            print("WARNING: process %s is treated as a stage1_2_fine process; no separate scaling parameter for it will enter" % P)
            if P in allProds:
                continue
            allProds.append(P)
            allDecs = []
            for dec in SM_HIGG_DECAYS:
                D = CMS_to_LHCHCG_DecSimple[dec]
                if D in allDecs:
                    continue
                allDecs.append(D)
                for stxs12binname in self.stage1_2_fine_procs:
                    if P in self.stage1_2_fine_procs[stxs12binname]:
                        terms = ["mu_XS_%s_x_BR_%s" % (stxs12binname, self.denominator)]
                        for merged_proddec_bin in self.mergeSchemes["prod_times_dec"]:
                            if stxs12binname in self.mergeSchemes["prod_times_dec"][merged_proddec_bin]:
                                terms += ["mu_XS_%s_x_BR_%s" % (merged_proddec_bin, self.denominator)]
                if D != self.denominator:
                    terms += ["mu_BR_%s_r_BR_%s" % (D, self.denominator)]
                self.modelBuilder.factory_("prod::scaling_%s_%s_13TeV(%s)" % (P, D, ",".join(terms)))
                self.modelBuilder.out.function("scaling_%s_%s_13TeV" % (P, D)).Print("")

        # Fix for merged procs in datacard: e.g. VH leptonic bins in H->WW (STXS)
        # Must account for merged-bin signal strengths, which complicates the situation
        for D, merged_bins in self.stage1_2_merged_procs.items():
            for P, components in merged_bins.items():
                terms = ["mu_BR_%s_r_BR_%s" % (D, self.denominator)]
                terms_sum = []
                for stxs12binname, frac in components.items():
                    terms_stxs12 = []
                    self.doVar("frac_scaling_%s_component_%s_13TeV[%s,%s,%s]" % (stxs12binname, D, frac, frac, frac))
                    self.modelBuilder.out.var("frac_scaling_%s_component_%s_13TeV"% (stxs12binname, D)).setConstant(True) 
                    terms_stxs12 += ["frac_scaling_%s_component_%s_13TeV"% (stxs12binname, D), "mu_XS_%s_x_BR_%s" % (stxs12binname, self.denominator)]
                    for merged_proddec_bin in self.mergeSchemes["prod_times_dec"]:
                        if stxs12binname in self.mergeSchemes["prod_times_dec"][merged_proddec_bin]:
                            terms_stxs12 += ["mu_XS_%s_x_BR_%s" % (merged_proddec_bin, self.denominator)]
                    self.modelBuilder.factory_("prod::scaling_%s_component_%s_13TeV(%s)" % (stxs12binname, D, ",".join(terms_stxs12)))
                    terms_sum += ["scaling_%s_component_%s_13TeV" % (stxs12binname, D)]
    
                self.modelBuilder.factory_("sum::scaling_%s_sum_%s_13TeV(%s)" % (P, D, ",".join(terms_sum)))
                terms += ["scaling_%s_sum_%s_13TeV" % (P, D)]
                self.modelBuilder.factory_("prod::scaling_%s_%s_13TeV(%s)" % (P, D, ",".join(terms)))
                if P not in self.MERGEDPROCESSES:
                    self.MERGEDPROCESSES.append(P)


    def getHiggsSignalYieldScale(self, production, decay, energy):
        # Catch for H->Zgam: taken from STXStoSMEFT model
        if (decay == "Zgam") | ("bkg" in production):
            production = production.split("_")[0]

        for regproc in self.PROCESSES:
            if fnmatch.fnmatch(production, regproc):
                return "scaling_%s_%s_%s" % (regproc, decay, energy)

        for regproc in self.FINEPROCESSES:
            if fnmatch.fnmatch(production, regproc):
                return "scaling_%s_%s_%s" % (regproc, decay, energy)

        for regproc in self.MERGEDPROCESSES:
            if fnmatch.fnmatch(production, regproc):
                return "scaling_%s_%s_%s" % (regproc, decay, energy)


        # raise RuntimeError, "No production process matching %s for Stage0 found !"%production
        print("WARNING: No production process matching %s for Stage1.2 found, will scale by 1 !" % production)
        return 1


stage0 = StageZero()
stage0RatioZZ = StageZeroRatio("ZZ")
stage0mbb = StageZeroRunningmb("ZZ")
stage0mbbv2 = StageZeroRunningmb("ZZ",profileBR=True)
stage0mbbv3 = StageZeroRunningmb("ZZ",profileBR=True,analytic=True)
stage12 = StageOnePTwo()
stage12RatioZZ = StageOnePTwoRatio("ZZ")
