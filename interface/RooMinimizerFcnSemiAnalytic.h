/*****************************************************************************
 * Authors:                                                                  *
 *  Andrea Carlo Marini,   MIT (MA),        andrea.carlo.marini@cern.ch        *
 * Redistribution and use in source and binary forms,                        *
 * with or without modification, are permitted according to the terms        *
 * listed in LICENSE (http://roofit.sourceforge.net/license.txt)             *
 *****************************************************************************/


#ifndef ROO_MINIMIZER_FCN_SEMIANALYTIC
#define ROO_MINIMIZER_FCN_SEMIANALYTIC

#include "Math/IFunction.h"
#include "Fit/ParameterSettings.h"
#include "Fit/FitResult.h"

#include "RooAbsReal.h"
#include "RooArgList.h"

#include <fstream>
#include <vector>
#include <map>

#include <RooAbsMinimizerFcn.h>
#include "RooAbsMinimizerFcnSemiAnalytic.h"

template<typename T> class TMatrixTSym;
using TMatrixDSym = TMatrixTSym<double>;

// forward declaration
class RooMinimizerSemiAnalytic;

class RooMinimizerFcnSemiAnalytic : public RooAbsMinimizerFcnSemiAnalytic, 
    //public ROOT::Math::IBaseFunctionMultiDim 
    public ROOT::Math::IMultiGradFunction 
{

public:
   RooMinimizerFcnSemiAnalytic(RooAbsReal *funct, RooMinimizerSemiAnalytic *context,  std::map<std::string,RooAbsReal*>* knownDerivatives,  bool verbose = false);
   RooMinimizerFcnSemiAnalytic(const RooMinimizerFcnSemiAnalytic &other);
   virtual ~RooMinimizerFcnSemiAnalytic();

  ROOT::Math::IMultiGradFunction* Clone() const override;
   unsigned int NDim() const override { return getNDim(); }

   std::string getFunctionName() const override;
   std::string getFunctionTitle() const override;

   void setOptimizeConstOnFunction(RooAbsArg::ConstOpCode opcode, Bool_t doAlsoTrackingOpt) override;

   void setOffsetting(Bool_t flag) override;
   //Bool_t SetDerivativeParamVal(int index, double value) const;

private:
  double DoEval(const double * x) const override;  
  double DoDerivative(const double * x,unsigned int icoord) const override;  
  // semi-analytic. The following function is called by DoDerivative if analytical derivative is not present.
  virtual double DoNumericalDerivative(const double * x,int icoord) const;  

   RooAbsReal *_funct;
  std::map<std::string,RooAbsReal*> *_knownDerivatives; // does not own them. Otherwise needs to design ad hoc copy constructors.
    std::vector<RooAbsReal*> _derivParamVec ; // vector of derivative functions - algined with the one above
   //std::unique_ptr<RooArgList> _derivParamList;
   //std::unique_ptr<RooArgList> _floatParamList;
  int _useNumDerivatives{1};// 0 = ROOT (not-impl), 1 re-implementation of gsl 5 point, 2 re-implementation of gsl 3 point
};

#endif
