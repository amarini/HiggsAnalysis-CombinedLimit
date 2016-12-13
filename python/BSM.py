from HiggsAnalysis.CombinedLimit.PhysicsModel import *

# math maybe useful
from math import *
# array used to save C-style objects in memory
from array import array
# os reads environment
import os
# ROOT used for TFile and Splines
import ROOT
#temporary files for TTree
from tempfile import mkdtemp, mkstemp

class BSM(PhysicsModel):
    def __init__(self):
        PhysicsModel.__init__(self)
        self._dirname=os.environ["CMSSW_BASE"] + "/src/HiggsAnalysis/CombinedLimit/data/lhc-hxswg/bsm/"
        #from https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHXSWGMSSMNeutral
        self._filename="mhmodm_13TeV.root"
        self._txtname="xsec_13TeV_tHp_2016_2_5.txt"
        self._dbname="mhmodm.dat2"
        self._xvar = "mHp" # or mHp-mA
        self._doDeltaBeta=True ## 
        self._useSplinesND = False
        self._debug=3 ## debug options, will be set to 0 when confident
        self._brtoget= [ "br_Hp_taunu","br_Hp_tb"]
        self._xstoget= [] # xs_gg_A see root file, 
        self._masstoget=["m_Hp"] ## this is kept for consistency with the other, should not been nor list nor modifiable
        self._mass=500.
        self._range=[0.1,100]
        self._tb=30.
        self._tmpopen=False

    def _printString(self,what,level=1):
        ''' level 1= info, level 2 verbose, level 3 DEBUG'''
        if self._debug <level : return
        if  level ==-1 : levelString = "ERROR"
        elif level ==0 : levelString = "WARNING"
        elif level ==1 : levelString = "INFO"
        elif level ==2 : levelString = "VERBOSE"
        else: levelString = "DEBUG"
        
        print "["+levelString+"]",what
        
        return self

    def _setBenchmarkScenario(self, what):
        ''' Simplify life in picking up the correct files for the different scenarios'''
        self._txtname="xsec_13TeV_tHp_2016_2_5.txt"
        self._doDeltaBeta=True
        if what == "mhmodm":
            self._printString("Setting mhmodm scenario")
            self._filename="mhmodm_13TeV.root"
            self._dbname="mhmodm.dat2"
        elif what == "mhmodm-feynhiggs":
            self._printString("Setting mhmodm-feynhigs scenario")
            self._filename="feynhiggs/mhmodm_13TeV.root"
            self._dbname=""
            self._txtname=""
            self._doDeltaBeta=True
            self._xstoget . append("xs_Hp") # xs_gg_A see root file, 
            self._brtoget . append("db") # db
        elif what == "mhmodp":
            self._printString("Setting mhmodp scenario")
            self._filename="mhmodp_mu200_13TeV.root"
            self._dbname="mhmodp.dat2"
        elif what == "mhmaxup":
            self._printString("Setting mhmaxup scenario")
            self._filename="newmhmax_mu200_13TeV.root"
            self._dbname="mhmaxup.dat2"
        elif what == "tauphobic":
            self._printString("Setting tauphobic scenario")
            self._filename="tauphobic_13TeV.root"
            self._dbname="tauphobic.dat2"
        elif what == "lightstau":
            self._printString("Setting lightstau scenario")
            self._filename="lightstau1_13TeV.root"
            self._dbname="lightstau.dat2"
        elif what == "lightstop":
            self._printString("Setting lightstop scenario")
            self._filename="lightstopmod_13TeV.root"
            self._dbname="lightstop-new.dat2"
        elif what == "hMSSM":
            self._printString("Setting hMSSM scenario")
            self._filename="hMSSM_13TeV.root"
            self._dbname=""
            self._doDeltaBeta=False
        else:
            self._printString("Scenario '" + what + "' is not implemented" ,-1)
        return self

    def _print(self):
        print "-----------------------------------"
        print "Filename=",self._filename
        print "Txtname=",self._txtname
        print "DBname=",self._dbname
        print "xvar=",self._xvar
        print "useSplinesND=",self._useSplinesND
        print "doDeltaBeta=",self._doDeltaBeta
        print "debug=",self._debug
        print "br to get=",self._brtoget
        print "xs to get=",self._xstoget
        print "masses to get=",self._masstoget
        print "mass=",self._mass
        print "rRange=",self._range
        print "tb=",self._tb
        print "-----------------------------------"

    def _getObj(self,fIn,name):
        self._printString("Getting obj '" + name + "' from file: " + fIn.GetTitle(),3)
        h=fIn.Get(name)
        if h==None:
            self._printString("Object '" + name + "' not present in file: " + fIn.GetTitle(),-1) 
            raise IOError
        return h

    def _readRootFile(self):
        """ Read LHC XS WG ROOT files, 
        and build splines for 
        mA,tb -> MHp
        mA,tb -> xsec
        mA,tb -> br_Hp_taunu
        mA,tb -> br_Hp_topbottom
        """
        fName= os.path.join(self._dirname , self._filename)
        self._printString( "Opening file: "  + fName ,1)
        fIn=ROOT.TFile.Open(fName) 
        
        if fIn == None:
            self._printString("No such file or directory: " + fName ,-1)
            raise IOError
        
        ## get map between mA <-> mHp, accordingly to tb and xvar
        for m in self._masstoget:
            h = self._getObj(fIn,m)
            if self._xvar == "mHp":
                self._th2Interp(h,"mA","mHp","tb",True)
            else: #"mA"
                self._th2Interp(h,"mHp","mA","tb")
        ## get branching rations, as funciton of mA and tb
        for br in self._brtoget:
            h_br = self._getObj(fIn,br)
            self._th2Interp(h_br,br,"mA","tb")
        
        ## get xsections
        for xs in self._xstoget:
            h_xs = self._getObj(fIn,xs)
	    if xs== "xs_Hp" and self._doDeltaBeta:
		#   
		## assume that 
		if self._txtname != "": self._printString("Error txt name !=NULL and reading cross section with delta beta",-1)
        	self.modelBuilder.factory_('expr::tbeff("@0/TMath::Sqrt(1+@1)",tb,db)')
            	self._th2Interp(h_xs,xs + "_bare","mA","tbeff")
                self.modelBuilder.factory_('expr::xs_Hp("@0/(1+@1)", xs_Hp_bare,db)')
	    else:
            	self._th2Interp(h_xs,xs,"mA","tb")
        
        return self

    def _openTmpFile(self):
        ''' Open A temporary file for root TTree operations :('''
        if self._tmpopen: 
            self._fTmp.cd()
            return self
        self._tmpopen=True
        self._fd, self._temp_path=mkstemp()
        self._printString("Opening tmp file: " + self._temp_path,1)
        self._fTmp = ROOT.TFile.Open(self._temp_path,"RECREATE")
        self._fTmp.cd()
        return self

    def _closeTmpFile(self):
        if not self._tmpopen: 
            return self
        self._printString("Closing and destroying tmp file: " + self._temp_path,1)
        self._fTmp.Close()
        os.close(self._fd)
        os.remove(self._temp_path)
        self._tmpopen=False
        return self
        
    def _readTxtFile(self):
        """ Read bare cross sections from a txt. For Hpm only."""
        if self._txtname == "" : return 
        fName= os.path.join(self._dirname, self._txtname)
        self._printString("Opening file: " + fName,1)
        txt = open(fName) ## this already raise an exception
        
        #set variables names, accordingly to the options
        xvar="mHp"
        yvar="tb"
        name="xs_Hp"
        if self._doDeltaBeta:
            yvar="tbeff"
            name="xs_Hp_bare"
        
        if self._useSplinesND:
            self._openTmpFile() ## make sure tmp file is open and cd in
            tree = ROOT.TTree("tree_" +name ,"tree_"+name)
            x=array('f',[0.])
            y=array('f',[0.])
            f=array('f',[0.])
            tree.Branch("f",f,"f/F")
            tree.Branch(xvar,x,xvar+"/F")
            tree.Branch(yvar,y,yvar+"/F")
        else:
            g = ROOT.TGraph2D()
            g.SetName("graph_"+name)
        
        for line in txt:
            l = line.split('#')[0]
            l = l.replace('\n','')
            if l == "": continue
            try:
               mhp  = float(l.split()[0])
               tb   = float(l.split()[1])
               xsec = float(l.split()[2])
            except IndexError, ValueError:
                self._printString("Ignoring line: '" + line.replace('\n','') +"'",0)
                continue
            self._printString("* Filling xsec with " + str(mhp)  + "," + str(tb) + " -> " + str(xsec) ,3)
            if self._useSplinesND:
                x[0] = mhp
                y[0] = tb
                f[0] = xsec
                tree.Fill()
            else:
                g.SetPoint(g.GetN(), mhp,tb,xsec)
        
        self._printString("Getting xvar=" + xvar + " yvar=" + yvar,3)
        
        xv=self.modelBuilder.out.var(xvar)
        yv=self.modelBuilder.out.var(yvar)
        if xv==None: xv= self.modelBuilder.out.function(xvar)
        if yv==None: yv= self.modelBuilder.out.function(yvar)
        
        ## to check if variables are ok
        self._printString( " * " + xv.GetTitle() +", " + yv.GetTitle(), 3)
        
        # construct graph or splines
        self._printString("Constructing graph or spline",3)
        if self._useSplinesND:
            spline = ROOT.RooSplineND(name,"spline for " + name ,ROOT.RooArgList(xv,yv),tree,"f",1,True)
        else:
            spline = ROOT.RooGraph2D(name,"graph2D for "+ name, xv,yv, g )
        
        self._printString("Importing graph or spline:" + name,3)
        self.modelBuilder.out._import(spline)
        
        if self._doDeltaBeta:
            self._printString("Constructing delta beta target xsHp",3)
            ## if not deltaBeta, xs_Hp has been already created
            self.modelBuilder.factory_('expr::xs_Hp("@0/(1+@1)", xs_Hp_bare,db)')
        
        self._printString("Exit xs loop",3)
        return self

    def _readDeltaBetaFile(self):
        """ Read deltabeta corrections from a txt. For Hpm only."""
        if not self._doDeltaBeta : return self
        if self._dbname == "" : 
            #self._doDeltaBeta=False
            self._printString("No txt DB corrections given. (correct if reading from root file)",0)
            return  self
        
        fName= os.path.join(self._dirname, self._dbname)
        self._printString("Opening file: " + fName,1)
        txt = open(fName) ## this already raise an exception
        x=[]
        y=[]
        xvar="tb"
        yvar="db"
        
        for line in txt:
            l = line.split('#')[0]
            l = l.replace('\n','')
            if l == "": continue
            if 'https' in l : continue
            if 'deltab' in l : continue
            try:
                tb  = float(l.split()[0])
                db  = float(l.split()[1])
            except IndexError, ValueError:
                self._printString("Ignoring line: '" + line.replace('\n','') +"'",0)
                continue
            self._printString("* Filling db with " + str(tb) + " -> " + str(db) ,3)
            x.append(tb)
            y.append(db)
        
        xv=self.modelBuilder.out.var(xvar)
        yv=self.modelBuilder.out.var(yvar)
        if xv==None: xv= self.modelBuilder.out.function(xvar)
        if yv==None: yv= self.modelBuilder.out.function(yvar)
        
        self._printString("Importing db, and tbeff",3)
        
        algo="CSPLINE"
        spline = ROOT.RooSpline1D("db", "file %s" % (fName), xv, len(x), array('d', x), array('d', y), algo)
        self.modelBuilder.out._import(spline)
        ## construct finally tbeff
        self.modelBuilder.factory_('expr::tbeff("@0/TMath::Sqrt(1+@1)",tb,db)')
        
        return self

    def _th2Interp(self,th2,name,xvar="mA",yvar="tb",inversion=False):
        ''' Choose the correct interpolation function '''
        if self._useSplinesND:
            return self._th2ToSpline(th2,name,xvar,yvar,inversion)
        else: 
            return self._th2ToGraph(th2,name,xvar,yvar,inversion)

    def _th2ToGraph(self,th2,name,xvar="mA",yvar="tb",inversion=False):
        ''' Use Tgraph2D as interpolation functions, trough RooGraph2D'''
        if (self.modelBuilder.out.function(name) != None): 
            self._printString("Function '"+name+"' already in the model",0)
            return self
        
        if self._useSplinesND: 
            return  self
        
        self._printString("Constructing tgraph for '"+name+"' xvar=" + xvar + " yvar=" + yvar,2)
        
	if th2.InheritsFrom("TGraph2D"):
	     if inversion:
		g=ROOT.TGraph2D()
        	g.SetName("graph2d_"+name)
		for i in range(0,th2.GetN()):
			g.SetPoint( i, th2.GetZ()[i],th2.GetY()[i],th2.GetX()[i])
	     else:
		g=th2.Clone()
	else:
        	g=ROOT.TGraph2D( ) 
        	g.SetName("graph2d_"+name)
        	
        	for xBin in range(1,th2.GetNbinsX()+1):
        	    for yBin in range(1,th2.GetNbinsY()+1):
        	        y = th2.GetYaxis().GetBinCenter(yBin)
        	        x = th2.GetXaxis().GetBinCenter(xBin)
        	        z = th2.GetBinContent(xBin,yBin)
        	        if inversion:
        	            self._printString("* Filling '"+name+"' with " + str(z) + "," + str(y) + " -> " + str(x),3)
        	            g.SetPoint(g.GetN(), z,y,x)
        	        else:
        	            self._printString("* Filling '"+name+"' with " + str(x) + "," + str(y) + " -> " + str(z),3)
        	            g.SetPoint(g.GetN(), x,y,z)
        	
        xv=self.modelBuilder.out.var(xvar)
        yv=self.modelBuilder.out.var(yvar)
        if xv==None: xv= self.modelBuilder.out.function(xvar)
        if yv==None: yv= self.modelBuilder.out.function(yvar)
        
        if xv==None or yv == None:
            self._printString("At least one of " + xvar +", "+yvar + " doesn't exist and should",-1)
        
        self._printString("Constructing and importing '"+name+"'",3)
        spline = ROOT.RooGraph2D(name,"graph for " + th2.GetName() ,xv,yv,g)
        self.modelBuilder.out._import(spline)
        return self

    def _th2ToSpline(self,th2,name,xvar="mA",yvar="tb",inversion=False):
        ''' Costructa a RooSplineND  from a th2d.
        x,y -> z
        Inversion: z,y -> x in the th2d. name is still the name of the target,
        '''
        if (self.modelBuilder.out.function(name) != None): 
            self._printString("Function '"+name+"' already in the model",0)
            return self
        
        if not self._useSplinesND: 
            return self 
        
        self._openTmpFile() ## make sure tmp file is open and cd in
        tree = ROOT.TTree("tree_" +name ,"tree_"+name)
        x=array('f',[0.])
        y=array('f',[0.])
        f=array('f',[0.])
        tree.Branch("f",f,"f/F")
        tree.Branch(xvar,x,xvar+"/F")
        tree.Branch(yvar,y,yvar+"/F")
        
        for xBin in range(1,th2.GetNbinsX()+1):
            for yBin in range(1,th2.GetNbinsY()+1):
                y[0]= th2.GetYaxis().GetBinCenter(yBin)
                x[0]= th2.GetXaxis().GetBinCenter(xBin)
                f[0]= th2.GetBinContent(xBin,yBin)
                if inversion:
                    f[0]= th2.GetXaxis().GetBinCenter(xBin)
                    x[0]= th2.GetBinContent(xBin,yBin)
                
                self._printString("* Filling spline "+ name +"("+xvar +","+yvar +"): " + str(x[0])  + " " + str(y[0]) + " " + str(f[0]),3)
                tree.Fill()
        
        
        xv=self.modelBuilder.out.var(xvar)
        yv=self.modelBuilder.out.var(yvar)
        if xv==None: xv= self.modelBuilder.out.function(xvar)
        if yv==None: yv= self.modelBuilder.out.function(yvar)
        
        if xv==None or yv == None:
                self._printString("At least one of " + xvar +", "+yvar + " doesn't exist and should",-1)
        
        self._printString("Constructing and importing '"+name+"'",3)
        
        spline = ROOT.RooSplineND(name,"spline for " + th2.GetName() ,ROOT.RooArgList(xv,yv),tree,"f",1,True)
        self.modelBuilder.out._import(spline)
        
        return self

    def setPhysicsOptions(self,physOptions):
        ''' Set Physics model options '''
        self._printString("Setting PhysicsModel Options",1)
        for po in physOptions:
            if po.startswith("verbose"):
                self._debug = 1
            elif po.startswith("debug"):
                self._debug += 3
            elif po.startswith("dir="):
                self._dirname=po.replace('dir=','')
            elif po.startswith("xs="):
                self._xstoget= po.replace("xs=",'').split(',')
            elif po.startswith("br="):
                self._brtoget= po.replace("br=",'').split(',')
            elif po.startswith("mass="):
                self._mass= float(po.replace("mass=",''))
            elif po.startswith("tb="):
                self._tb= float(po.replace("tb=",''))
            elif po.startswith("fname="):
                self._filename=po.replace('fname=','')
            elif po.startswith("txtname="):
                self._txtname=po.replace('txtname=','')
            elif po.startswith("range="):
                self._range= [float(x) for x in po.replace('range=','').split(',') ]
            elif po.startswith("xvar="):
                self._xvar=po.replace('xvar=','')
            elif po.startswith("deltabeta="):
                self._doDeltaBeta=bool(po.replace('fname=',''))
            elif po.startswith("scenario="):
                self._setBenchmarkScenario(po.replace('scenario=',''))
        if self._debug>0:
            self._print()

    def doParametersOfInterest(self):
        """Create POI and other parameters, and define the POI set."""
        ## floating mHp, tb, are left for possible extensions, the model do not have this restrictions
        if self._xvar == "mHp":
            if self._mass <10:
                self.modelBuilder.doVar('mHp[500,200,3000]')
            else:
                self.modelBuilder.doVar('mHp[%f]'%(self._mass))
        else : # mA
            if self._mass <10:
                self.modelBuilder.doVar('mA[%f]'%(self._mass) )
            else:
                self.modelBuilder.doVar('mA[500,200,3000]')
        
        if self._tb>0:
            self.modelBuilder.doVar('tb[%f]'%self._tb);
        else:
            self.modelBuilder.doVar('tb[10,0,100]');
        
        self.modelBuilder.doVar('r[1,%f,%f]'%(self._range[0],self._range[1]));
        self.modelBuilder.doSet('POI','r')
        
        if self._useSplinesND:
            self._openTmpFile()
        self._readRootFile()._readDeltaBetaFile()._readTxtFile()
        if self._useSplinesND:
            self._closeTmpFile()
        
        self.modelBuilder.factory_('expr::Scaling_HpTauNu("@0*@1*@2", r,xs_Hp,br_Hp_taunu)')
        self.modelBuilder.factory_('expr::Scaling_HpTopBottom("@0*@1*@2", r,xs_Hp,br_Hp_tb)')
        
        self.processScaling = { 'tobbottom':'HpTobBottom', 
                                'taunu':'HpTauNu',"Hptntj_Hp":"HpTauNu",
                              }
        
        if self._debug>1:
            self._printString(" --------- WS ----------",2)
            self.modelBuilder.out.Print()
            self._printString(" -----------------------",2)
        
    def getYieldScale(self,bin,process):

        for prefix, model in self.processScaling.iteritems():
            if prefix in process:
		self._printString("Scaling process '"+ process+"' by " + 'Scaling_'+ model,3) 
                return 'Scaling_'+model
            
        return 1

# define an instantiation of the class
bsm = BSM()

