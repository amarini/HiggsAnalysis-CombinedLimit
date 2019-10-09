#using standandalone. replace ../../[..] with $(ROOFITSYS)
CXXFLAGS:=$(shell root-config --cflags) -ggdb -O2  -I ../../../../ -I ../.. -I ../../src -I ../../include -fPIC -D NDEBUG
LDFLAGS:=$(shell root-config --ldflags --libs) -L ../../lib -lRooFitCore -lRooStats -lRooFit -lFoam -lMinuit -lstdc++ -lHiggsAnalysisCombinedLimit -fPIC

SOURCES:=$(wildcard *.cxx)
EXES=$(SOURCES:%.cxx=%.exe)

.PHONY: all
all: $(EXES)

$(EXES): %.exe: %.cxx
	gcc $(CXXFLAGS) $(LDFLAGS) $< -o $@

.PHONY: clean
clean:
	rm *.exe

