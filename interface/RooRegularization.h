
#ifndef ROO_REGULARIZATION
#define ROO_REGULARIZATION
//------------H 
#include "RooConstVar.h"
#include "RooListProxy.h"
#include "RooAbsReal.h"
#include "RooAbsPdf.h"
#include "RooAbsArg.h"

#include <iostream>
#include <vector>

using namespace std;

//--class declaration
//class RooAbsArg;
//class RooAbsPdf;
//class RooAbsReal;
class RooRealProxy;
class RooArgList;


class RooRegularization: public RooAbsPdf{
public:
	RooRegularization();
	RooRegularization(const char *name, const char* title , double delta, const char* binsStr);
	RooRegularization(const char *name, const char* title , double delta, vector<string> binsReg);
	RooRegularization(const RooRegularization &other, const char*name=0);
	virtual TObject * clone(const char* newname)const{return new RooRegularization(*this,newname);}
	inline virtual ~RooRegularization(){};

private:
	Double_t evaluate() const ;
	Double_t getLogVal(const RooArgSet *set=0) const;

	Double_t delta;
	vector<string> bins;

ClassDef(RooRegularization,1);
};

#endif
//-----------------
