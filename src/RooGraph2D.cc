/*******************************************************************
 * Andrea Carlo Marini (MIT)
 * Tue Dec  6 19:02:16 CET 2016
 * Implementation of a TGraph2D interpolation 
 *
 *
 * *****************************************************************/

#include "HiggsAnalysis/CombinedLimit/interface/RooGraph2D.h"

//#include <stdexcept>
//#include <fstream>
//#include <sstream>

RooGraph2D::RooGraph2D( const char*name, const char*title,
		RooAbsReal&xvar,RooAbsReal&yvar,TGraph2D*g):
	RooAbsReal(name,title),
	_xvar("xvar","Variable",this,xvar),
	_yvar("yvar","Variable",this,yvar)
{
	//_g.reset(g); // takes ownership
	_g=g;
	//_g2=(TGraph2D*)g->Clone(Form("g2_%s",g->GetName()));
	//_g=new TGraphDelaunay(_g2);
	//_g->SetName(Form("td_%s",g->GetName()));
	//
	//// trigger the construction of the interpolation system. Not sure it will be saved.
	//_g->FindAllTriangles ();
	_g->Interpolate(10.,10.);
	//((TGraphDelaunay2D*)fDelaunay)->ComputeZ(x, y);
}

//Copy constructor
RooGraph2D::RooGraph2D(const RooGraph2D &other, const char*newname):
	RooAbsReal(other,newname),
	_xvar("xvar",this,other._xvar),
	_yvar("yvar",this,other._yvar)
{
	_g = (TGraph2D*)other._g->Clone(Form("g2_%s",newname));
	//_g = (TGraphDelaunay*)other._g->Clone(Form("td3_%s",newname));
	//_g2 = (TGraph2D*) other._g2 -> Clone(Form("g3_%s",newname));
}

TObject *RooGraph2D::clone(const char *newname) const 
{
    return new RooGraph2D(*this, newname);
}

Double_t RooGraph2D::evaluate() const {
	return _g->Interpolate( _xvar,_yvar ) ;
}

ClassImp(RooGraph2D)


