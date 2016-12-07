/*******************************************************************
 * Andrea Carlo Marini (MIT)
 * Tue Dec  6 19:02:16 CET 2016
 * Implementation of a TGraph2D interpolation 
 *
 *
 * *****************************************************************/

#ifndef ROO_GRAPH2D
#define ROO_GRAPH2D

#include "TGraph2D.h"
#include "RooAbsReal.h"
#include "RooRealProxy.h"
#include <memory>

class RooGraph2D : public RooAbsReal
{
private:
	RooRealProxy _xvar, _yvar;
	//std::unique_ptr<TGraph2D> _g;
	TGraph2D* _g{NULL};
protected:
	Double_t evaluate() const;
public:
	//default constructor
	RooGraph2D(){delete _g;}
	// takes ownership of g pointer
	RooGraph2D( const char *name, const char* title,
			RooAbsReal&xvar, RooAbsReal&yvar,
			TGraph2D*g 
		);
	// copy constructor
	RooGraph2D( const RooGraph2D &other, const char*newname=0);
	// destructor
	~RooGraph2D(){}
	// clone
	TObject*clone(const char*newname) const;

	ClassDef(RooGraph2D,1)
};

#endif
