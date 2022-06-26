# Newer SW releases
source scl_source enable rh-git218
source scl_source enable llvm-toolset-7.0
source scl_source enable devtoolset-8
source scl_source enable rh-python38

export FLASK_APP=scurve
export FLASK_ENV=development
