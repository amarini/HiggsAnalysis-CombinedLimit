import os
import sys
from subprocess import call, check_output
import threading
from Queue import Queue
import time
import math
from optparse import OptionParser, OptionGroup
#############
file="mhmodm-LHCHXSWG.in"
m0=180
m1=1000
tb0=1
tb1=100
dM=1
dtb=1
####################
parser=OptionParser()
parser.add_option("","--ncore",type='int',help="num. of core. [%default]",default=16)
parser.add_option("","--no-root",dest="do_root",action='store_false',help="do the root production [%default]",default=True)
parser.add_option("","--no-feyn",dest="do_feyn",action='store_false',help="do the feyn production [%default]",default=True)
(opts,args)=parser.parse_args()

threads=[]
masses=[]
tbs=[]


def drange(start, stop, step):
        ''' Return a floating range list. Start and stop are included in the list if possible.'''
        r = start
        while r <= stop:
                yield r
                r += step

def prange(start, stop, step):
        ''' Return a floating range list. Start and stop are included in the list if possible.'''
	print "Called prange with params",start,stop,step
	if step <1.0:
		raise ValueError
        r = start
        while r <= stop:
                yield r
                r *= step

masses =  [x for x in prange(m0,m1,math.pow(m1/m0,1./400.))] + [200,300,400,500,750,1000,2000,2500,3000]
tbs= [x for x in drange(0,1,.05)] + [x for x in drange(tb0,tb1,.5)]

print "MASSES=",masses
print "TB=",tbs

dir="/tmp/amarini/"+file.replace("-LHCHXSWG.in","")
call("mkdir -p %s"%dir,shell=True)
call("ln -s $PWD/FeynHiggs %s/"%dir,shell=True)

def parallel(tb,m,counter):
	fname="%s.%d.in"%(file.replace('\.in',''),counter)
	dest = "%s/%s"% (dir,fname)
	call("cp -v %s %s"%(file,dest) ,shell=True) 
	call("sed -i'' 's/\(^TB\ *\)[0-9]*/\\1%f/' %s"%(tb,dest),shell=True)
	call("sed -i'' 's/\(^MA0\ *\)[0-9]*/\\1%f/' %s"%(m,dest),shell=True)
	call("cd %s && ./FeynHiggs %s > %s.feyn"%(dir,fname,fname),shell=True)

counter=0
if opts.do_feyn:
  for tb in tbs:
     for m in masses:
	while threading.activeCount() >= opts.ncore:
				print "sleep ...."
				time.sleep(1)
	#parallel(tb,m,counter)
	t= threading.Thread(target=parallel,args=(tb,m,counter,) )
	t.start()
	threads.append(t)
	counter+=1

for t in threads:
	t.join()

print "Done p1"
if not opts.do_root: exit(0)
print "Collecting results"
import ROOT
from glob import glob

l = glob( dir +"/*feyn")
#print "l=",l

out=file.replace("-LHCHXSWG.in","")
fOut=ROOT.TFile.Open("./%s_13TeV.root"%out,"RECREATE")
gMHp=ROOT.TGraph2D()
gMHp.SetName("m_Hp")

gBRtaunu=ROOT.TGraph2D()
gBRtaunu.SetName("br_Hp_taunu")

gBRtb=ROOT.TGraph2D()
gBRtb.SetName("br_Hp_tb")

gXSHp=ROOT.TGraph2D()
gXSHp.SetName("xs_Hp")


def printPartial(n,tot):
	k=30
	f = int(float(n)/tot*k)
	line="\r["+ ("*"*f) + (" "*(k-f)) + "] = %.1f%%"%(float(n)/tot*100) 
	print line,
	sys.stdout.flush()

for idx,f in enumerate(l):
   if idx%10 == 0:	printPartial(idx,len(l))
   try:

	cmd={}
	cmd["ignore"]="cat " + f +" | grep 'Cannot open'"
	cmd["ignore2"] = "grep -ri 'FHHiggsCorr\ error' " + f
	cmd["ma"]="cat "+f+"| grep '| MA0' | tail -n -1"
	cmd["mhp"]="cat "+f+"| grep '| MHp' | tail -n -1"
	cmd["tb"]="cat "+f+"| grep '| TB' | tail -n -1"
	cmd["brtn"]="cat "+f+"| grep -i '%| Hp-nu_tau-tau'"
	cmd["brtb"]="cat "+f+"| grep -i '%| Hp-t-b'"
	cmd["xshp"]="cat "+f+"| grep -i 'prod:alt-t-Hp'"
	try:
	   ignore  = call(cmd["ignore"],shell=True)
	except:
	   ignore  = call(cmd["ignore"],shell=True)
	if ignore == 0 :
		continue
	try:
	   ignore2  = call(cmd["ignore2"],shell=True)
	except:
	   ignore2  = call(cmd["ignore2"],shell=True)
	if ignore2 == 0 : continue
	try:
	   ma=float(check_output(cmd["ma"],shell=True).split()[3])
	except: ## try twice
	   ma=float(check_output(cmd["ma"],shell=True).split()[3])
	try:
	   mhp=float(check_output(cmd["mhp"],shell=True).split()[3])
	except:
	   mhp=float(check_output(cmd["mhp"],shell=True).split()[3])
	try:
	   tb=float(check_output(cmd["tb"],shell=True).split()[3])
	except:
	   tb=float(check_output(cmd["tb"],shell=True).split()[3])
	try:
	   br_taunu = float(check_output(cmd["brtn"],shell=True ) .split()[4])
	except:
	   br_taunu = float(check_output(cmd["brtn"],shell=True ) .split()[4])
	#'%  Channel                  Gamma          BR  '
	#'%| Hp-nu_tau-tau        =     6.36317       0.201915'
	try:
	   br_tb = float(check_output(cmd["brtb"] ,shell=True) .split()[4])
	except:
	   br_tb = float(check_output(cmd["brtb"] ,shell=True) .split()[4])
	   # it's in fb not it pb
	try:
	   xs_Hp = float(check_output(cmd["xshp"] ,shell=True) .split()[3]) / 1000.
	except ValueError :
	   # some times it wrotes 5-149 instead of 5E-149
	   xs_Hp = float(check_output(cmd["xshp"] ,shell=True).split()[3].replace("-","E-")) / 1000.
	except:
	   xs_Hp = float(check_output(cmd["xshp"] ,shell=True) .split()[3]) / 1000.
        gXSHp.SetPoint(gXSHp.GetN(), ma, tb, xs_Hp)
        gBRtb.SetPoint(gBRtb.GetN(), ma, tb, br_tb)
        gBRtaunu.SetPoint(gBRtaunu.GetN(), ma, tb, br_taunu)
        gMHp.SetPoint(gMHp.GetN(), ma, tb , mhp)
   except Exception as e:
	print "Got exception",e,"with cmd",cmd
	print "Ignoring this file"
	continue

fOut.cd()
gXSHp.Write()
gBRtaunu.Write()
gBRtb.Write()
gMHp.Write()

print "Done p2"
