#ifndef SimpleGaussianConstraint_h
#define SimpleGaussianConstraint_h

#include <RooGaussian.h>

class SimpleGaussianConstraint : public RooGaussian {
    public:
        SimpleGaussianConstraint() {};
        SimpleGaussianConstraint(const char *name, const char *title,
                RooAbsReal& _x, RooAbsReal& _mean, RooAbsReal& _sigma):
            RooGaussian(name,title,_x,_mean,_sigma) { init(); }
        SimpleGaussianConstraint(const SimpleGaussianConstraint& other, const char* name=0) :
            RooGaussian(other, name) { init(); }
        SimpleGaussianConstraint(const RooGaussian &g) : RooGaussian(g, "") { init(); }

        virtual TObject* clone(const char* newname) const { return new SimpleGaussianConstraint(*this,newname); }
        inline virtual ~SimpleGaussianConstraint() { }

        const RooAbsReal & getX() const { return x.arg(); }
        const RooAbsReal & getMean() const { return mean.arg(); }
        const RooAbsReal & getSigma() const { return sigma.arg(); }

        double getLogValFast() const { 
            if (_valueDirty) {
                Double_t arg = x - mean;  
                //Double_t sig = sigma ;
                //return -0.5*arg*arg/(sig*sig);
                _value = scale_*arg*arg;
                //_valueDirty = false;
                _valueDirty = true; // something wrong with cache?
            }
            return _value;
        }

        static RooGaussian * make(RooGaussian &c) ;
    private:
        double scale_;
        void init() ;

        ClassDef(SimpleGaussianConstraint,1) // Gaussian PDF with fast log
};

#endif
