#include "../interface/RooRegularization.h"

#include "RooFit.h"

#include <math.h>

#include "RooRealVar.h"
#include "RooAddPdf.h"

#include <stdexcept>



ClassImp(RooRegularization)


RooRegularization::RooRegularization(){}
RooRegularization::RooRegularization(const char *name, const char* title , double deltaReg, vector<string>binsReg){
	SetName(name);
	SetTitle(title);
	delta=deltaReg;
	bins=binsReg;
}

RooRegularization::RooRegularization(const char* name, const char* title, double delta,const char* binsStr)
	{
	string binsStr2(binsStr);
	vector<string> v;
	while(size_t pos=binsStr2.find(','))
		{
		string token = binsStr2.substr(0,pos);
		v.push_back(token);
		binsStr2.erase(0,pos+1);
		if(pos==string::npos)break;
		}
	RooRegularization(name,title,delta,v);
	}

RooRegularization::RooRegularization(const RooRegularization &other, const char*name){
	SetTitle(other.GetTitle());	
	if ( name) SetName(name);
	else SetName(other.GetName());
	delta=other.delta;
	bins=other.bins;
}

Double_t RooRegularization::evaluate() const {
//	Double_t ret=0;	
	throw  std::invalid_argument("RooRegularization::evaluate() called \n");
//	ret *= delta;
}
Double_t RooRegularization::getLogVal(const RooArgSet *set) const {
	Double_t ret=0;	
	
	//Double_t getRealValue(const char* name, Double_t defVal = 0, Bool_t verbose = kFALSE) const
	//
	/* -1 1
	 * 1  -2 1
	 * 0   1 -2 1
	 */
	int N=bins.size();
	for (int i=0;i<N;i++)
	{
	Double_t row=0;
		for (int j=0;j<N;j++)
			{
			//check that name is in the set -- should abort if not
			(*set)[bins[j].c_str()];
			//---
			if (  (i==0) || (i==N-1)  )
				{
				if (j==i) row +=  -1.* set->getRealValue(bins[j].c_str());
				if ( abs(j-i) ==1) row +=1* set->getRealValue(bins[j].c_str());
				}
			else {
				if (j==i) row +=  -2.* set->getRealValue(bins[j].c_str());
				if ( abs(j-i) ==1) row +=1 * set->getRealValue(bins[j].c_str());
				}
			}
	ret+=row*row;
	}
		
	ret *= delta;
	return ret;
}


