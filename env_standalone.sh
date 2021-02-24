
SCRAM_ARCH=cc8_amd64_gcc8
 . /cvmfs/cms.cern.ch/${SCRAM_ARCH}/external/gcc/8.4.0/etc/profile.d/init.sh
 . /cvmfs/cms.cern.ch/${SCRAM_ARCH}/lcg/root/6.22.03-ghbfee2/bin/thisroot.sh
 . /cvmfs/cms.cern.ch/${SCRAM_ARCH}/external/gsl/2.6-bcolbf2/etc/profile.d/init.sh
 . /cvmfs/cms.cern.ch/${SCRAM_ARCH}/external/tbb/2020_U2-ghbfee/etc/profile.d/init.sh
 . /cvmfs/cms.cern.ch/${SCRAM_ARCH}/cms/vdt/0.4.0-ghbfee/etc/profile.d/init.sh
 . /cvmfs/cms.cern.ch/${SCRAM_ARCH}/external/boost/1.72.0-gchjei/etc/profile.d/init.sh
 . /cvmfs/cms.cern.ch/${SCRAM_ARCH}/external/pcre/8.43-bcolbf2/etc/profile.d/init.sh
 . /cvmfs/cms.cern.ch/${SCRAM_ARCH}/external/libpng/1.6.37-bcolbf2/etc/profile.d/init.sh
 . /cvmfs/cms.cern.ch/${SCRAM_ARCH}/external/zlib/1.2.11-bcolbf2/etc/profile.d/init.sh
 export PATH=${PATH}:${PWD}/exe:${PWD}/scripts
 export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:${PWD}/lib
 export PYTHONPATH=${PYTHONPATH}:${PWD}/lib/python:${PWD}/lib
