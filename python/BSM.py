from HiggsAnalysis.CombinedLimit.PhysicsModel import *

# math maybe useful
from math import *
# array used to save C-style objects in memory
from array import array
# os reads environment
import os
# ROOT used for TFile and Splines
import ROOT

class BSM(PhysicsModel):
    def __init__(self):
        PhysicsModel.__init__(self)
	## TODO: something like edm::FileInPath?
	self._dirname=os.environ["CMSSW_BASE"] "src/HiggsAnalysis/CombinedLimit/data/lhc-hxswg/bsm/"
	#from https://twiki.cern.ch/twiki/bin/view/LHCPhysics/LHCHXSWGMSSMNeutral
	self._filename="mhmodm_13TeV.root"
	self._txtname="xsec_13TeV_tHp_2016_2_5.txt"
	self._dbname="mhmodm.dat2"
	self._xvar = "MHp" # or MHp-MA
	self._doDeltaBeta=False
	self._debug=3 ## debug options, will be set to 0 when confident
	self._brtoget= [ "br_Hp_taunu","br_Hp_tb"]
	self._xstoget= [] # xs_gg_A see root file, 
	self._masstoget=["m_Hp"] ## this is kept for consistency with the other, should not been nor list nor modifiable
	self._mass=500.
	self._range=[0.1,100]
	self._tb=30.

    def _getObj(fIn,name):
	h=fIn.Get(name)
	if h==None:
		print "Object",name,"doesn't exist"
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
	fName=self._dirname +"/" + self._filename
	if self._debug>0 : print "Opening file:",fName
	fIn=ROOT.TFile.Open(fName) 

	if fIn == None:
		print "No such file or directory:",fName
		raise IOError	
	## get map between mA <-> mHp, accordingly to tb and xvar
	for m in self._masstoget:
		h = self._getObj(fIn,m)
		if self._xvar == "mHp":
			self._th2ToSpline(h,"mA","mHp","tb",invert=True)
		else: #"mA"
			self._th2ToSpline(h,"mHp","mA","tb")
	## get branching rations, as funciton of mA and tb
	for br in self._brtoget:
		h_br = self._getObj(fIn,br)
		self._th2ToSpline(h_br,br,"mA","tb")

	## get xsections
	for xs in self._xstoget:
		h_xs = self._getObj(fIn,xs)
		self._th2ToSpline(h_xs,xs,"mA","tb")

	return self
	
    def _readTxtFile(self):
	""" Read bare cross sections from a txt. For Hpm only."""
	if self._txtname == "" : return 
	fName= self._dirname+ "/" + self._txtname
	txt = open(fName) ## this already raise an exception

	tree = ROOT.TTree("tree_" +name ,"tree_"+name)
	xvar="mHp"
	yvar="tb"
	name="xs_Hp"
	if self._doDeltaBeta:
		yvar="tbeff"
	 	name="xs_Hp_bare"

	x=array('f',[0.])
	y=array('f',[0.])
	f=array('f',[0.])
	tree.Branch("f",f,"f/F")
	tree.Branch(xvar,x,xvar+"/F")
	tree.Branch(yvar,y,yvar+"/F")

	for line in txt:
		l = line.split('#')[0]
		l = l.replace('\n','')
		if l == "": continue
		try:
		   mhp  = float(l.split()[0])
		   tb   = float(l.split()[1])
		   xsec = float(l.split()[2])
		except IndexError, ValueError:
			print "Ignoring line: '" + line.replace('\n','') +"'"
			continue
		x[0] = mhp
		y[0] = tb
		f[0] = xsec
		if self._debug >= 3 :  print "* Filling xsec with",mhp,tb,"->",xsec
		tree.Fill()
	
	xv=self.modelBuilder.out.var(xvar)
	yv=self.modelBuilder.out.var(yvar)

	spline = ROOT.RooSplineND(name,"spline for " + th2.GetName() ,ROOT.RooArgList(xv,yv),tree,"f",1,true)
	self.modelBuilder.out._import(spline)

	if self._doDeltaBeta:
		## if not deltaBeta, xs_Hp has been already created
        	self.modelBuilder.factory_('expr::xs_Hp("@0/(1+@1)", xs_Hp_bare,db)')

	return self

    def _readDeltaBetaFile(self):
	""" Read deltabeta corrections from a txt. For Hpm only."""
	if not self._doDeltaBeta : return
	if self._dbname == "" : 
		self._doDeltaBeta=False
		if opts._debug>0: print "Setting DeltaBeta=False. No DB file given."
		return 

	fName= self._dirname+ "/" + self._dbname
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
			print "Ignoring line: '" + line.replace('\n','') +"'"
			continue
		if self._debug >= 3 :  print "* Filling db with",tb,"->",db
		x.append(tb)
		y.append(db)
	
	xv=self.modelBuilder.out.var(xvar)
	yv=self.modelBuilder.out.var(yvar)
	algo="CSPLINE"
        spline = ROOT.RooSpline1D(yvar, "file %s" % (fName), xv, len(x), array('d', x), array('d', y), algo)
	self.modelBuilder.out._import(spline)
	## construct finally tbeff
	self.modelBuilder.factory_('expr::tbeff("@0/TMath::Sqrt(1+@1)",tb,db)')

	return self


    def _th2ToSpline(self,th2,name,xvar="mA",yvar="tb",inversion=False):
	    ''' Costructa a RooSplineND  from a th2d.
	    x,y -> z
	    Inversion: z,y -> x in the th2d. name is still the name of the target,
	    '''
	    if (self.modelBuilder.out.function(name) != None): 
		    if self._debug >0 : print "DEBUG: Function:",name,"already in model"
		    return
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
		  tree.Fill()


	    xv=self.modelBuilder.out.var(xvar)
	    yv=self.modelBuilder.out.var(yvar)

	    spline = ROOT.RooSplineND(name,"spline for " + th2.GetName() ,ROOT.RooArgList(xv,yv),tree,"f",1,true)
	    self.modelBuilder.out._import(spline)

    def setPhysicsOptions(self,physOptions):
	if self._debug>0:print "Setting PhysicsModel Options"
	for po in physOptions:
		#if po.startswith("mass="):
		#	self.mass=float( po.replace('mass=','') )

		if po.startswith("verbose"):
			self._debug = 1
		if po.startswith("debug"):
			self._debug += 3
		if po.startswith("dir="):
			self._dirname=po.replace('dir=','')
		if po.startswith("xs="):
			self._xstoget= po.replace("xs=",'').split(',')
		if po.startswidth("br=")
			self._brtoget= po.replace("br=",'').split(',')
		if po.startswidth("mass=")
			self._mass= float(po.replace("mass=",''))
		if po.startswidth("tb=")
			self._tb= float(po.replace("tb=",''))
		if po.startswidth("fname=")
			self._filename=po.replace('fname=','')
		if po.startswidth("txtname=")
			self._txtname=po.replace('txtname=','')
		if po.startswidth("range=")
			self._range= [float(x) for x in po.replace('range=','').split(',') ]
		## TODO: How to fix MHP?

    def doParametersOfInterest(self):
        """Create POI and other parameters, and define the POI set."""
	## floating mHp, tb, are leaved for possible extensions
	if self._xvar == "mHp":
		if self._mass <10:
        		self.modelBuilder.doVar('mHp[500,200,3000]');
		else:
        		self.modelBuilder.doVar('mHp[%f]'%(self._mass));
	else : # mA
		if self._mass <10:
        		self.modelBuilder.doVar('mA[%f]'%(self._mass);
		else:
        		self.modelBuilder.doVar('mA[500,200,3000]');

	if self._tb>0:
        	self.modelBuilder.doVar('tb[%f]'%self._tb);
	else:
        	self.modelBuilder.doVar('tb[10,0,100]');

        self.modelBuilder.doVar('r[1,%f,%f]'%(self._range[0],self._range[1]));
        self.modelBuilder.doSet('POI','r')

	self._readRootFile()._readDeltaBetaFile()._readTxtFile()

        self.modelBuilder.factory_('expr::Scaling_HpTauNu("@0*@1*@2", r,xs_Hp,br_Hp_taunu)')
        self.modelBuilder.factory_('expr::Scaling_HpTopBottom("@0*@1*@2", r,xs_Hp,br_Hp_tb)')

        self.processScaling = { 'tobbottom':'HpTobBottom', 'taunu':'HpTauNu' }

	if self._debug>1:
        	self.modelBuilder.out.Print()
        
    def getYieldScale(self,bin,process):

        for prefix, model in self.processScaling.iteritems():
            if prefix in process:
                return 'Scaling_'+model
            
        return 1


bsm = BSM()

