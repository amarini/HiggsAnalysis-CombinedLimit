/*****************************************************************************
 * Authors:                                                                  *
 *  Andrea Carlo Marini,   MIT (MA),        andrea.carlo.marini@cern.ch        *
 *  Code based on roofit code.                                                                           *
 *                                                                           *
 *                                                                           *
 * Redistribution and use in source and binary forms,                        *
 * with or without modification, are permitted according to the terms        *
 * listed in LICENSE (http://roofit.sourceforge.net/license.txt)             *
 *****************************************************************************/

//////////////////////////////////////////////////////////////////////////////
/// \class RooMinimizerFcnSemiAnalytic
/// RooMinimizerFcnSemiAnalytic is an interface to the ROOT::Math::IBaseFunctionMultiDim,
/// a function that ROOT's minimisers use to carry out minimisations.
///

//#include "RooMinimizerFcnSemiAnalytic.h"
#include "HiggsAnalysis/CombinedLimit/interface/RooMinimizerFcnSemiAnalytic.h"

#include "RooAbsArg.h"
#include "RooAbsPdf.h"
#include "RooArgSet.h"
#include "RooRealVar.h"
#include "RooAbsRealLValue.h"
#include "RooMsgService.h"
#include "RooMinimizer.h"
#include "RooNaNPacker.h"

#include "TClass.h"
#include "TMatrixDSym.h"

#include <stdexcept>
#include <fstream>
#include <iomanip>
#include "RooAddition.h" // DEBUG & Print
#include "RooFormulaVar.h" //DEBUG & Print
//#include "HiggsAnalysis/CombinedLimit/interface/SimNLLDerivativesHelper.h" // DEBUG to have evaluate
//

using namespace std;


namespace {

// Helper function that wraps RooAbsArg::getParameters and directly returns the
// output RooArgSet. To be used in the initializer list of the RooMinimizerFcnSemiAnalytic
// constructor.
RooArgSet getParameters(RooAbsReal const& funct) {
    RooArgSet out;
    funct.getParameters(nullptr, out);
    return out;
}

} // namespace


RooMinimizerFcnSemiAnalytic::RooMinimizerFcnSemiAnalytic(RooAbsReal *funct, RooMinimizerSemiAnalytic* context, std::map<std::string,RooAbsReal*>* knownDerivatives,
			   bool verbose) :
  RooAbsMinimizerFcnSemiAnalytic(getParameters(*funct), context, verbose), 
    _funct(funct)
{
    _derivParamVec .clear();

    _knownDerivatives = knownDerivatives;
    for(unsigned int i = 0 ;i< _nDim;++i)
    {
        auto arg = _floatParamList->at(i);
        auto derivative = _knownDerivatives->find(arg->GetName()); 
        if (derivative == _knownDerivatives->end()){
            if(_verbose) std::cout<<"[DEBUG]:["<<__PRETTY_FUNCTION__<<"]:"<< "derivative for param "<<arg->GetName()<<" not found. I will use numerical derivatives."<<std::endl;
            _derivParamVec.push_back( nullptr );
        }
        else{
            if(_verbose) std::cout<<"[DEBUG]:["<<__PRETTY_FUNCTION__<<"]:"<< "derivative for param "<<arg->GetName()<<" found with name "<<derivative->second->GetName()<<"."<<std::endl;
            _derivParamVec.push_back( derivative->second );
        }
    }

}



RooMinimizerFcnSemiAnalytic::RooMinimizerFcnSemiAnalytic(const RooMinimizerFcnSemiAnalytic& other) : RooAbsMinimizerFcnSemiAnalytic(other), ROOT::Math::IMultiGradFunction(other),
  _funct(other._funct),
  _derivParamVec(other._derivParamVec)
{

  _knownDerivatives = other._knownDerivatives;
}


RooMinimizerFcnSemiAnalytic::~RooMinimizerFcnSemiAnalytic()
{}


ROOT::Math::IMultiGradFunction* RooMinimizerFcnSemiAnalytic::Clone() const
{
  return new RooMinimizerFcnSemiAnalytic(*this) ;
}

void RooMinimizerFcnSemiAnalytic::setOptimizeConstOnFunction(RooAbsArg::ConstOpCode opcode, Bool_t doAlsoTrackingOpt)
{
   _funct->constOptimizeTestStatistic(opcode, doAlsoTrackingOpt);
}

/// Evaluate function given the parameters in `x`.
double RooMinimizerFcnSemiAnalytic::DoEval(const double *x) const {
  //std::cout<<"[DEBUG]:["<<__PRETTY_FUNCTION__<<"]:"<< "DoEval"<<std::endl; // run with -v3 to get it

  // Set the parameter values for this iteration
  for (unsigned index = 0; index < _nDim; index++) {
    if (_logfile) (*_logfile) << x[index] << " " ;
    SetPdfParamVal(index,x[index]);
  }

  // Calculate the function for these parameters
  RooAbsReal::setHideOffset(kFALSE) ;
  double fvalue = _funct->getVal();
  RooAbsReal::setHideOffset(kTRUE) ;

  if (!std::isfinite(fvalue) || RooAbsReal::numEvalErrors() > 0 || fvalue > 1e30) {
    printEvalErrors();
    RooAbsReal::clearEvalErrorLog() ;
    _numBadNLL++ ;

    if (_doEvalErrorWall) {
      const double badness = RooNaNPacker::unpackNaN(fvalue);
      fvalue = (std::isfinite(_maxFCN) ? _maxFCN : 0.) + _recoverFromNaNStrength * badness;
    }
  } else {
    if (_evalCounter > 0 && _evalCounter == _numBadNLL) {
      // This is the first time we get a valid function value; while before, the
      // function was always invalid. For invalid  cases, we returned values > 0.
      // Now, we offset valid values such that they are < 0.
      _funcOffset = -fvalue;
    }
    fvalue += _funcOffset;
    _maxFCN = std::max(fvalue, _maxFCN);
  }

  // Optional logging
  if (_logfile)
    (*_logfile) << setprecision(15) << fvalue << setprecision(4) << endl;
  if (_verbose) {
    cout << "\nprevFCN" << (_funct->isOffsetting()?"-offset":"") << " = " << setprecision(10)
         << fvalue << setprecision(4) << "  " ;
    cout.flush() ;
  }

  _evalCounter++ ;

  return fvalue;
}

/// Set derivative value of parameter i.
//Bool_t RooMinimizerFcnSemiAnalytic::SetDerivativeParamVal(int index, double value) const
//{
//  auto par = static_cast<RooRealVar*>(&(*_derivParamVec)[index]);
//
//  if (par->getVal()!=value) {
//    if (_verbose) cout << par->GetName() << "=" << value << ", " ;
//    
//    par->setVal(value);
//    return kTRUE;
//  }
//
//  return kFALSE;
//}

double RooMinimizerFcnSemiAnalytic::DoDerivative(const double * x, unsigned int icoord) const{
    //std::cout<<"[DEBUG]:["<<__PRETTY_FUNCTION__<<"]:"<< "DoDerivative:"<<icoord<<std::endl; // run with -v3 to get it
  RooAbsReal::setHideOffset(kFALSE) ;


  // Set the parameter values for this iteration
  for (unsigned int index = 0; index < _nDim; index++) {
    if (_logfile) (*_logfile) << x[index] << " " ;
    //std::cout<<"[DEBUG]:["<<__PRETTY_FUNCTION__<<"]:"<< "Calling SetPdfParamVal:"<<index<<", "<<x[index]<<std::endl; //
    SetPdfParamVal(index,x[index]);
  }

    //std::cout<<"[DEBUG]:["<<__PRETTY_FUNCTION__<<"]:"<< "> Compute Derivatives"<<std::endl; //
  // compute Derivative
  if (_derivParamVec.size()<icoord) 
    {
    throw std::runtime_error(Form("Derivative vector is too small. (requested coordinate) %u < (derivative size) %lu",icoord,_derivParamVec.size()));
    }
  if (_derivParamVec[icoord] == nullptr) {
      std::cout<<"[RooMinimizerFcnSemiAnalytic][DEBUG]"<< "Doing numerical derivative for "<<icoord<<" at theta="<<x[icoord] <<" Param: "<< _floatParamList->at(icoord)->GetName()<<std::endl;
      
      double r = DoNumericalDerivative(x,icoord);

      std::cout<<"------------------"<<r<<std::endl;
      return r; 
  }

  //verify correctness of analytical derivatives // DEBUG
  
  if (true){
      std::cout<<"[RooMinimizerFcnSemiAnalytic][DEBUG]"<< "Doing derivative for "<<icoord<<" at theta="<<x[icoord] <<std::endl;
      std::cout<<"param "; for (unsigned int index = 0; index < _nDim; index++) { std::cout<< x[index] <<","; } ; std::cout<<endl;
      std::cout<< "----------- NUMERICAL: "<< DoNumericalDerivative(x,icoord)<<std::endl;
      std::cout<< "----------- ANALYTICAL (getVal): "<< _derivParamVec[icoord]->getVal()<<std::endl;
      std::cout<< "----------- "<<std::endl;

  }
  
  Double_t ret =   _derivParamVec[icoord]->getVal();
  RooAbsReal::setHideOffset(kTRUE) ;
  return ret;

}

double RooMinimizerFcnSemiAnalytic::DoNumericalDerivative(const double * x,int icoord) const
{
    //std::cout<<"[DEBUG]:["<<__PRETTY_FUNCTION__<<"]:"<< "DoNumericalDerivative:"<<icoord<<std::endl; // run with -v3 to get it
    // ROOT 
    if (_useNumDerivatives==0) {
        //return ROOT::Math::MultiNumGradFunction::DoDerivative(x,icoord);
        //copied from ROOT::Math::MultiNumGradFunction::DoDerivative

        // calculate derivative using mathcore derivator class
        // step size can be changes using SetDerivPrecision()
        // this also use gsl.

        //static double kPrecision = std::sqrt ( std::numeric_limits<double>::epsilon() );
        //double x0 = std::abs(x[icoord]);
        //double step = (x0 > 0) ? kPrecision * x0 : kPrecision;
        // this seems to work better than above
        //double step = (x0>0) ? std::max( fgEps* x0, 8.0*kPrecision*(x0 + kPrecision) ) : kPrecision;
        //return ROOT::Math::Derivator::Eval(*fFunc, x, icoord, step);
        throw std::logic_error("Unimplemented");
    }
    if (_useNumDerivatives==1){
        /*
                 *
        ROOT use this has step above, maybe copy it dynamically? TODO
        double MultiNumGradFunction::fgEps = 0.001;
         
         double MultiNumGradFunction::DoDerivative (const double * x, unsigned int icoord  ) const 
               // calculate derivative using mathcore derivator class
            // step size can be changes using SetDerivPrecision()
         
            static double kPrecision = std::sqrt ( std::numeric_limits<double>::epsilon() );
            double x0 = std::abs(x[icoord]);
            //double step = (x0 > 0) ? kPrecision * x0 : kPrecision;
            // this seems to work better than above
            double step = (x0>0) ? std::max( fgEps* x0, 8.0*kPrecision*(x0 + kPrecision) ) : kPrecision;
         */

        // from gsl_deriv_central -> central_deriv
        /* Compute the derivative using the 5-point rule (x-h, x-h/2, x,
           x+h/2, x+h). Note that the central point is not used.  

           Compute the error using the difference between the 5-point and
           the 3-point rule (x-h,x,x+h). Again the central point is not
           used. */
  RooAbsReal::setHideOffset(kFALSE) ;

        // smallest number representable in doubles
        static double kPrecision = std::sqrt ( std::numeric_limits<double>::epsilon() );
        static double fgEps = 0.001;

        double ax0 = std::abs(x[icoord]);
        //double step = (x0 > 0) ? kPrecision * x0 : kPrecision;
        // this seems to work better than above
        double h = (ax0>0) ? std::max( fgEps* ax0, 8.0*kPrecision*(ax0 + kPrecision) ) : kPrecision;
        //static const double h=std::numeric_limits<double>::epsilon()*8.;
        const double hhalf=h/2.;

        //double f0 = _funct->getVal();
        //double x0 = x[icoord];

        SetPdfParamVal(icoord,x[icoord]-h);
        double fm1 = _funct->getVal();
        SetPdfParamVal(icoord,x[icoord]+h);
        double fp1 = _funct->getVal();

        SetPdfParamVal(icoord,x[icoord]-hhalf);
        double fmh = _funct->getVal();
        SetPdfParamVal(icoord,x[icoord]+hhalf);
        double fph = _funct->getVal();

  RooAbsReal::setHideOffset(kTRUE) ;

        double r3 = 0.5 * (fp1 - fm1);
        double r5 = (4.0 / 3.0) * (fph - fmh) - (1.0 / 3.0) * r3;

        // don't do counts I'm not using.
        //double e3 = (fabs (fp1) + fabs (fm1)) * GSL_DBL_EPSILON;
        //double e5 = 2.0 * (fabs (fph) + fabs (fmh)) * GSL_DBL_EPSILON + e3;

        /* The next term is due to finite precision in x+h = O (eps * x) */

        //double dy = std::max (fabs (r3 / h), fabs (r5 / h)) *(fabs (x) / h) * GSL_DBL_EPSILON;

        /* The truncation error in the r5 approximation itself is O(h^4).
           However, for safety, we estimate the error from r5-r3, which is
           O(h^2).  By scaling h we will minimise this estimated error, not
           the actual truncation error in r5. */

        //*result = r5 / h;
        //*abserr_trunc = fabs ((r5 - r3) / h); /* Estimated truncation error O(h^2) */
        //*abserr_round = fabs (e5 / h) + dy;   /* Rounding error (cancellations) */
        // reset
        SetPdfParamVal(icoord,x[icoord]);
        return r5 /h ;
    }

    if (_useNumDerivatives==2){
        /* Compute the derivative using the 5-point rule (x-h, x-h/2, x,
           x+h/2, x+h). Note that the central point is not used.  

           Compute the error using the difference between the 5-point and
           the 3-point rule (x-h,x,x+h). Again the central point is not
           used. */

        // smallest number representable in doubles
        static double kPrecision = std::sqrt ( std::numeric_limits<double>::epsilon() );
        static double fgEps = 0.001;

        double ax0 = std::abs(x[icoord]);
        //double step = (x0 > 0) ? kPrecision * x0 : kPrecision;
        // this seems to work better than above
        double h = (ax0>0) ? std::max( fgEps* ax0, 8.0*kPrecision*(ax0 + kPrecision) ) : kPrecision;
        //static const double h=std::numeric_limits<double>::epsilon()*8.;

        SetPdfParamVal(icoord,x[icoord]-h);
        double fm1 = _funct->getVal();
        SetPdfParamVal(icoord,x[icoord]+h);
        double fp1 = _funct->getVal();

        double r3 = 0.5 * (fp1 - fm1);

        // reset
        SetPdfParamVal(icoord,x[icoord]);
        return r3 /h ;
    }
    throw std::runtime_error(Form("Numerical derivatives method un-implemented: %d",_useNumDerivatives));
}


std::string RooMinimizerFcnSemiAnalytic::getFunctionName() const
{
   return _funct->GetName();
}

std::string RooMinimizerFcnSemiAnalytic::getFunctionTitle() const
{
   return _funct->GetTitle();
}

void RooMinimizerFcnSemiAnalytic::setOffsetting(Bool_t flag)
{
   _funct->enableOffsetting(flag);
}
