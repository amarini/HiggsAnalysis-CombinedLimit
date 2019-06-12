# . /cvmfs/cms.cern.ch/slc6_amd64_gcc530/external/gcc/5.3.0/etc/profile.d/init.sh 
# cd /cvmfs/cms.cern.ch/slc6_amd64_gcc530/lcg/root/6.06.00-cms/
# . ./bin/thisroot.sh
# cd -
# . /cvmfs/cms.cern.ch/slc6_amd64_gcc530/cms/vdt/v0.3.2-giojec/etc/profile.d/init.sh 
# . /cvmfs/cms.cern.ch/slc6_amd64_gcc530/external/boost/1.57.0-giojec/etc/profile.d/init.sh 
# . /cvmfs/cms.cern.ch/slc6_amd64_gcc530/external/xz/5.2.1/etc/profile.d/init.sh 
# export LD_LIBRARY_PATH=/cvmfs/cms.cern.ch/slc6_amd64_gcc530/external/pcre/8.37/lib/:${LD_LIBRARY_PATH}
# export PATH=${PATH}:${PWD}/exe:${PWD}/scripts
# export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:${PWD}/lib
# export PYTHONPATH=${PYTHONPATH}:${PWD}/lib/python:${PWD}/lib


######## test for parallel minuit
##tandalone.sh 
 source /cvmfs/cms.cern.ch/slc7_amd64_gcc820/external/gcc/8.2.0-pafccj/etc/profile.d/init.sh
 source /cvmfs/cms.cern.ch/slc7_amd64_gcc820/external/boost/1.67.0-pafccj/etc/profile.d/init.sh
 source /cvmfs/cms.cern.ch/slc7_amd64_gcc820/external/xz/5.2.2-pafccj/etc/profile.d/init.sh
 source /eos/cms/store/user/amarini/root-build/bin/this_root.sh
 export LD_LIBRARY_PATH=/cvmfs/cms.cern.ch/slc7_amd64_gcc820/external/pcre/8.37-pafccj/lib/:${LD_LIBRARY_PATH}
 export PATH=${PATH}:${PWD}/exe:${PWD}/scripts
 export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:${PWD}/lib
 export PYTHONPATH=${PYTHONPATH}:${PWD}/lib/python:${PWD}/lib


###  to compile root
#CMAKE_CXX_FLAGS="-fopenmp -D_GLIBCXX_PARALLEL"
#/cvmfs/sft.cern.ch/lcg/contrib/CMake/3.8.1/Linux-x86_64/bin/cmake -D afs=off -D cxx17=on -D cxx14=on -D gsl_shared=on -D xrootd=off  /tmp/amarini/root ; /cvmfs/sft.cern.ch/lcg/contrib/CMake/3.8.1/Linux-x86_64/bin/cmake --build . -- -j 16
#/cvmfs/sft.cern.ch/lcg/contrib/CMake/3.8.1/Linux-x86_64/bin/cmake -DCMAKE_INSTALL_PREFIX=/eos/cms/store/user/amarini/root-build -P cmake_install.cmake
