#ifndef ROO_SIMPLE_CACHE_SENTRY
#define ROO_SIMPLE_CACHE_SENTRY

#include "RooRealVar.h"
#include "RooSetProxy.h"
#include "TIterator.h"

class SimpleCacheSentry : public RooAbsArg {
    public:
        SimpleCacheSentry() ;
        SimpleCacheSentry(const char *name, const char *title) ;
        SimpleCacheSentry(const RooRealVar &var) ;
        SimpleCacheSentry(const RooAbsCollection &vars) ;
        SimpleCacheSentry(const RooAbsArg &func, const RooArgSet *obs=0) ;
        SimpleCacheSentry(const SimpleCacheSentry &other, const char *newname = 0) ;
        RooSetProxy & deps() { return _deps; }
        const RooArgSet & deps() const { return _deps; }
        void addArg(const RooAbsArg &arg) { _deps.add(arg); }
        void addVar(const RooRealVar &var) { _deps.add(var); } 
        void addVars(const RooAbsCollection &vars) ; 
        void addFunc(const RooAbsArg &func, const RooArgSet *obs=0) ;
        bool good() const { return !isValueDirty(); } 
        bool empty() const { return _deps.getSize() == 0; }
        void reset() { clearValueDirty(); } 
        // base class methods to be implemented
        virtual TObject* clone(const char* newname) const override { return new SimpleCacheSentry(*this, newname); }
        virtual RooAbsArg *createFundamental(const char* newname=0) const override { return 0; }
        virtual Bool_t readFromStream(std::istream& is, Bool_t compact, Bool_t verbose=kFALSE) override { return false; }
        virtual void writeToStream(std::ostream& os, Bool_t compact) const override { }
        virtual Bool_t operator==(const RooAbsArg& other) const { return this == &other; }
        virtual void syncCache(const RooArgSet* nset=0) override {}
        virtual void copyCache(const RooAbsArg* source, Bool_t valueOnly=kFALSE, Bool_t setValDirty=kTRUE) override {}
        virtual void attachToTree(TTree& t, Int_t bufSize=32000)override {}
        virtual void attachToVStore(RooVectorDataStore& vstore)override {}
        virtual void setTreeBranchStatus(TTree& t, Bool_t active)override {}
        virtual void fillTreeBranch(TTree& t)override {}
	    virtual Bool_t isIdentical(const RooAbsArg& other, Bool_t assumeSameType=kFALSE) const ;
        
        Bool_t operator==(const RooAbsArg& other) override {return isIdentical(other);} ;
	    Bool_t isIdentical(const RooAbsArg& other, Bool_t assumeSameType=kFALSE) override {return isIdentical(other,assumeSameType);} ;

    private:
        RooSetProxy _deps;
        ClassDef(SimpleCacheSentry,1) 
};

#endif
