
#ifndef ROO_REGULARIZATION
#define ROO_REGULARIZATION
//------------H 
#include "RooConstVar.h"
#include "RooListProxy.h"
#include "RooAbsReal.h"
#include "RooRealVar.h"
#include "RooAbsPdf.h"
#include "RooAbsArg.h"
#include "RooArgList.h"

#include <iostream>
#include <vector>

using namespace std;

//--class declaration
//class RooAbsArg;
//class RooAbsPdf;
//class RooAbsReal;
class RooRealProxy;
class RooArgList;


//class RooRegularization: public RooAbsPdf{
class RooRegularization: public RooAbsReal{
public:
	RooRegularization();
	//RooRegularization(const char *name, const char* title , double delta, const char* binsStr);
	//RooRegularization(const char *name, const char* title , double delta, vector<string> binsReg);
	RooRegularization(const char *name, const char* title , RooRealVar delta, RooArgList l)
			{ RooRegularization(name,title,delta.getVal(),&l);}

	RooRegularization(const char *name, const char* title , double delta, RooArgList *l);
	RooRegularization(const char *name, const char* title , double delta, RooArgList l)
			{ RooRegularization(name,title,delta,&l);}

	
	//RooRegularization(const char *name, const char* title , RooAbsReal& delta, RooAbsReal& bin0) { RooRegularization(name,title,delta.getVal(),bin0.getVal());};
	//RooRegularization(const char *name, const char* title , RooAbsReal& delta, RooAbsReal& bin0, RooAbsReal& bin1) { RooRegularization(name,title,delta.getVal(),bin0.getVal(),bin1.getVal());};
	//RooRegularization(const char *name, const char* title , RooAbsReal& delta, RooAbsReal& bin0, RooAbsReal& bin1, RooAbsReal& bin2) { RooRegularization(name,title,delta.getVal(),bin0.getVal(),bin1.getVal(),bin2.getVal());};
	//RooRegularization(const char *name, const char* title , RooAbsReal& delta, RooAbsReal& bin0, RooAbsReal& bin1, RooAbsReal& bin2, RooAbsReal& bin3) { RooRegularization(name,title,delta.getVal(),bin0.getVal(),bin1.getVal(),bin2.getVal(),bin3.getVal());};
	//RooRegularization(const char *name, const char* title , RooAbsReal& delta, RooAbsReal& bin0, RooAbsReal& bin1, RooAbsReal& bin2, RooAbsReal& bin3, RooAbsReal& bin4) { RooRegularization(name,title,delta.getVal(),bin0.getVal(),bin1.getVal(),bin2.getVal(),bin3.getVal(),bin4.getVal());};
	//RooRegularization(const char *name, const char* title , RooAbsReal& delta, RooAbsReal& bin0, RooAbsReal& bin1, RooAbsReal& bin2, RooAbsReal& bin3, RooAbsReal& bin4, RooAbsReal& bin5) { RooRegularization(name,title,delta.getVal(),bin0.getVal(),bin1.getVal(),bin2.getVal(),bin3.getVal(),bin4.getVal(),bin5.getVal());};

	RooRegularization(const RooRegularization &other, const char*name=0);
	virtual TObject * clone(const char* newname)const{return new RooRegularization(*this,newname);}
	inline virtual ~RooRegularization(){};


	//this function is not normalized
	 Int_t getAnalyticalIntegral(const RooArgSet& integSet, RooArgSet& anaIntSet) {return 1;}
	 Double_t analyticalIntegral(Int_t code) {return 1;}

protected:
	Double_t evaluate() const ;
	Double_t getLogVal(const RooArgSet *set=0) const;

	Double_t delta;
	//vector<string> bins;

private:
//	RooRealProxy xvar_;
	RooArgList list_;

ClassDef(RooRegularization,1);
};

#endif
//-----------------
