#!/bin/bash

# This installer (currently) works for Debian and Debian based distros such
# as Ubuntu, as well as Fedora and Red Hat. Other distros may or may not work.

# Look for apt-get or yum to decide whether we should use a deb or rpm
# type of installation. If more distro support is added later, a finer
# grained detection scheme will probably be necessary.

# If this entire script is run as root, all the files created under the user's home
# directory will be owned by root, which can cause permissioning and deletion
# problems. Only the copying of the binaries to locations outside the user's
# directories should be run as sudo, which is taken care of within this script.

XMDS_VERSION="2.2.2"
KNOWN_GOOD_XMDS_REVISION="2967"

if [ "$(whoami)" = "root" ]; then
  echo
  echo "It seems you are running this installer as root or with the \"sudo\" "
  echo "command. Unless you're sure you know what you're doing, please exit"
  echo "and re-run this installer as a normal user (i.e. without \"sudo\")."
  echo
  echo "Continue? (Y/N)"

  read reply
  if [ $reply = "N" -o $reply = "n" ]; then
    exit
  fi
fi

echo $reply

echo
echo
echo "*** XMDS2 installer v0.4 ***"
echo
echo "A standard install downloads the XMDS $XMDS_VERSION version of the code. This"
echo "is the default."
echo
echo "A developer install will download the latest cutting-edge version of"
echo "the XMDS code, which may include bugs. To perform a developer install,"
echo "run the installer with the --develop option."
echo
echo "In both cases an SVN repository will be created locally, and you can update"
echo "to the latest version of the code at any time by running the command"
echo "  make update"
echo "in the xmds-$XMDS_VERSION/ directory."
echo
echo

RPM_INSTALL=0
DEB_INSTALL=0
if [ `which apt-get | wc -l` -ne 0 ]; then
  echo; echo "apt-get found; assuming Debian packaging scheme"; echo
  DEB_INSTALL=1
elif [ `which yum | wc -l` -ne 0 ]; then
  echo; echo "yum found; assuming RPM packaging scheme"; echo
  RPM_INSTALL=1
else
  echo
  echo "ERROR!"
  echo "This installer only works on Debian, Debian-based distributions such"
  echo "as Ubuntu and Mint, Fedora and Red Hat. Since neither \"apt-get\" "
  echo "nor \"yum\" is available, installation can't proceed."
  echo
  echo "Aborting install."
  echo
  exit
fi

XMDS2_install_directory=$HOME"/xmds-$XMDS_VERSION"
NUM_CPUS=`cat /proc/cpuinfo | grep processor | wc -l`
DEVELOPER_INSTALL=0

# COMMITTER_INSTALL denotes whether the person installing is
# allowed to make commits to the sourceforge svn repository.
# If this is set to "1" via a command line argument, 
# an https checkout of the repo is made, and if the
# correct credentials are not stored on the user's machine
# (e.g. from previously committing to that repo), the installer
# prompts for the sourceforge username and password. This
# ensures the person can then commit to repo.
#
# If COMMITTER_INSTALL is set to "0", an http checkout is made
# (*NOT* an https checkout). This is the default. It means no
# credentials are demanded during the install phase, but that
# person cannot immediately make commits to the xmds repo.
# In order to get committer rights in future, the local repo
# must be switched from http to https via
# svn switch --relocate http://svn.code.sf.net/p/xmds/code https://svn.code.sf.net/p/xmds/code
COMMITTER_INSTALL=0

XMDS_CONFIGURE_STRING=""

parse_command_line_arguments() {
  for i in $@; do
    if [ $i = "--help" ] || [ $i = "-h" ]; then
      echo
      echo "This is the XMDS "$XMDS_VERSION" installer."
      echo
      echo "Usage: ./install [options]"
      echo
      echo "Options and arguments:"
      echo "--help          : this help text"
      echo
      echo "--develop       : perform a developer install, downloading the absolute" 
      echo "                  latest version of the code"
      echo
      echo "--commit-access : set up the local repo to allow commits to the XMDS SVN repo. A" 
      echo "                  developer account on the XMDS sourceforge project is required"
      echo
      echo "If no options are given, a standard install without commit access will be performed."
      echo
      exit
    elif [ $i = "--develop" ]; then
      DEVELOPER_INSTALL=1
    elif [ $i = "--commit-access" ]; then
      COMMITTER_INSTALL=1
    else
      echo "Unknown option:" $i
    fi
  done
}

install_FFTW_from_source() {

  # FFTW 3.3 wasn't in the repos, so install manually from source
  current_directory=`pwd`
  
  cd $XMDS2_install_directory

  echo; echo "Downloading FFTW from www.fftw.org..."; echo

  fftwversion="3.3.4"
  wget http://www.fftw.org/fftw-${fftwversion}.tar.gz
  
  if [ ! -f fftw-${fftwversion}.tar.gz ]; then
    # Fall back to the known-to-exist 3.3.1
    fftwversion="3.3.1"
    wget ftp://ftp.fftw.org/pub/fftw/old/fftw-${fftwversion}.tar.gz
    
    # If *that's* not present, we can't continue
    if [ ! -f fftw-${fftwversion}.tar.gz ]; then
      echo
      echo "ERROR: Couldn't obtain fftw-${fftwversion}.tar.gz or fftw-${fftwversion}.tar.gz from www.fftw.org."
      echo "Aborting install."
      exit
    fi
  fi

  # Unpack the FFTW archive and install it under the user's home directory structure.
  # This avoids conflicting with any other version of FFTW that may have been
  # installed system-wide. Later we'll tell XMDS to use this specific version.

  FFTW_install_directory=$XMDS2_install_directory"/fftw-"$fftwversion
  tar -xzf fftw-${fftwversion}.tar.gz
  rm fftw-${fftwversion}.tar.gz

  # Need quotes in the below in case path contains spaces
  cd "$FFTW_install_directory"

  echo
  echo "Installing FFTW. This can take several minutes if you only have a single CPU."
  
  NO_COMPILER_SUPPORT_FOR_AVX=0  

  echo "  Configuring FFTW with single precision option..."

  ./configure --disable-fortran --enable-mpi --enable-single --enable-sse2 --enable-openmp --enable-avx --prefix=$FFTW_install_directory > installer.log
  if [ $? -ne 0 ]; then
    # Nonzero error code returned, so something went wrong
    echo "    Configuration failed. Retrying without assuming your compiler supports AVX..."
    ./configure --disable-fortran --enable-mpi --enable-single --enable-sse2 --enable-openmp --prefix=$FFTW_install_directory > installer.log
    if [ $? -ne 0 ]; then
      # Still no success, so bail out
      echo "Configuration failed due to some unknown reason. Aborting install."
      echo "Check installer.log in "$FFTW_install_directory " for more information."
      echo
      exit
    else
      echo "    Configuration successful!"
      NO_COMPILER_SUPPORT_FOR_AVX=1
    fi
  fi

  rm -f installer.log > /dev/null

  echo "  Compiling FFTW with single precision option..."
  # The single precision install produces lots of warnings, so redirect both stdout and
  # stderror to /dev/null
  make -j $NUM_CPUS > /dev/null 2>&1
  
  echo "  Installing single precision libraries..."
  make install > /dev/null

  # Note: if precision is not specified, FFTW will compile double-precision libs by default
  echo "  Configuring FFTW with double precision option..."
  if [ $NO_COMPILER_SUPPORT_FOR_AVX -eq 1 ]; then
    ./configure --disable-fortran --enable-mpi --enable-sse2 --enable-openmp --prefix=$FFTW_install_directory > /dev/null
  else
    ./configure --disable-fortran --enable-mpi --enable-sse2 --enable-avx --enable-openmp --prefix=$FFTW_install_directory > /dev/null
  fi

  echo "  Compiling FFTW with double precision option..."
  make -j $NUM_CPUS > /dev/null

  echo "  Installing double precision libraries..."
  make install > /dev/null

  XMDS_CONFIGURE_STRING=$XMDS_CONFIGURE_STRING" --lib-path "$FFTW_install_directory"/lib"
  XMDS_CONFIGURE_STRING=$XMDS_CONFIGURE_STRING" --include-path "$FFTW_install_directory"/include"

  cd $current_directory
  echo
  echo "FFTW installed!"
  echo
}


install_HDF5_from_source() {
  current_directory=`pwd`

  HDF5_install_directory=$XMDS2_install_directory"/hdf5-1.8.8"
  
  cd $XMDS2_install_directory
  echo; echo "Downloading HDF5 1.8.8 from www.hdfgroup.org.."; echo
  wget http://www.hdfgroup.org/ftp/HDF5/prev-releases/hdf5-1.8.8/src/hdf5-1.8.8.tar.gz

  # Make sure the HDF5 1.8.8 archive is present
  if [ ! -f hdf5-1.8.8.tar.gz ]; then
    echo
    echo "ERROR: Couldn't obtain hdf5-1.8.8.tar.gz from www.hdfgroup.org."
    echo "Aborting install."
    exit
  fi

  # Unpack the HDF5 1.8.8 archive and install it in the user's home directory structure.
  # This avoids conflicting with any other version of HDF5 that may have been
  # installed system-wide. Later we'll tell XMDS to use this specific version.  
  tar -xzf hdf5-1.8.8.tar.gz
  rm hdf5-1.8.8.tar.gz
  cd $HDF5_install_directory

  echo
  echo "Installing HDF5. This can take several minutes if you only have a single CPU."
  echo "  Configuring HDF5..."
  ./configure --prefix=$HDF5_install_directory > installer.log
  if [ $? -ne 0 ]; then
    # Nonzero error code returned, so something went wrong
    echo "\nConfiguration failed due to some unknown reason."
    echo "As HDF5 is required for XMDS2, I am aborting the install."
    echo "Check installer.log in "$HDF5_install_directory " for more information."
    echo
    exit
  fi

  rm -f installer.log > /dev/null

  echo "  Compiling HDF5..."
  # The HDF5 compile produces stupid amounts of warnings, so if
  # I echo the error stream to standard out, the user will see pages
  # and pages of scary stuff. Consequently just dump everything to /dev/null
  make -j $NUM_CPUS > /dev/null 2>&1
  
  echo "  Copying libraries..."
  make install > /dev/null

  XMDS_CONFIGURE_STRING=$XMDS_CONFIGURE_STRING" --lib-path "$HDF5_install_directory"/lib"
  XMDS_CONFIGURE_STRING=$XMDS_CONFIGURE_STRING" --include-path "$HDF5_install_directory"/include"

  cd $current_directory
  echo
  echo "HDF5 installed!"
  echo
}


parse_command_line_arguments $@

if [ $DEVELOPER_INSTALL -eq 1 ]; then
  echo "Performing developer install..."
else
  echo "Performing standard install..."
fi
echo
echo
echo "By default XMDS will be installed in " $XMDS2_install_directory
echo "Press [ENTER] to accept this default, or enter a new path:"
read reply

if [ ! -z $reply ]; then
  XMDS2_install_directory=$reply
fi

# check if XMDS directory exists, if not create it
if [ ! -d $XMDS2_install_directory ]; then
  mkdir $XMDS2_install_directory
fi

echo
echo "Installing required packages..."
echo

if [ $DEB_INSTALL -eq 1 ]; then
  # Begin Debian package install
  sudo apt-get -y install build-essential subversion libopenmpi-dev openmpi-bin python-dev python-setuptools python-cheetah python-numpy python-pyparsing python-lxml python-mpmath libhdf5-serial-dev libgsl0-dev python-sphinx python-h5py wget libatlas-base-dev

  COMPLETION_MESSAGE=$COMPLETION_MESSAGE"\nA generic version of ATLAS (a linear algebra library) was installed. Building a\n"
  COMPLETION_MESSAGE=$COMPLETION_MESSAGE"version specifically tuned to your local machine can lead to considerable speed\n"
  COMPLETION_MESSAGE=$COMPLETION_MESSAGE"increases when using matrix transforms such as bessel, hermite-gauss etc.\n"
  COMPLETION_MESSAGE=$COMPLETION_MESSAGE"See Optimization Hints in the documentation at xmds.org for details.\n"
  # End Debian packages install
elif [ $RPM_INSTALL -eq 1 ]; then
  # Begin RPM packages install
  sudo yum -y install gcc gcc-c++ make automake subversion openmpi-devel python-devel python-setuptools python-cheetah numpy gsl-devel python-sphinx wget libxml2-devel libxslt-devel
  
  # Find the optimum ATLAS version (i.e. CBLAS implementation) and install it
  SUCCESS=0
  if [ $SUCCESS -eq 0 ] && [ `cat /proc/cpuinfo | grep sse3 |wc -l` -gt 0 ]; then
    sudo yum -y install atlas-sse3-devel
    if [ $? -eq 0 ]; then
        SUCCESS=1;
    fi
  fi
  
  if [ $SUCCESS -eq 0 ] && [ `cat /proc/cpuinfo | grep sse2 |wc -l` -gt 0 ]; then
    sudo yum -y install atlas-sse2-devel
    if [ $? -eq 0 ]; then
        SUCCESS=1;
    fi
  fi
  
  if [ $SUCCESS -eq 0 ]; then
    sudo yum -y install atlas-devel
  fi

  # The default Red Hat repo doesn't have hdf5-dev, but Fedora does. 
  # Check if this package is available. If it is, install via the 
  # package manager, otherwise download, compile and install the HDF5 source code.

  if [ `yum info hdf5-devel | grep hdf5-devel | wc -l` -gt 0 ]; then
    sudo yum -y install hdf5-devel
  else
    echo
    echo "The HDF5 package isn't available in your standard repositories."
    echo "I will download, compile and install the HDF5 source code."
    install_HDF5_from_source
  fi
  
  # The packages h5py, pyparsing, python-lxml, and python-mpmath are not available
  # in the default Red Hat repository, but are are in the EPEL repository. See if
  # they're available; if so use yum to get them, if not use easy_install

  if [ `yum info pyparsing | grep pyparsing | wc -l` -gt 0 ]; then
    sudo yum -y install pyparsing
  else
    sudo easy_install pyparsing
  fi

  if [ `yum info python-lxml | grep python-lxml | wc -l` -gt 0 ]; then
    sudo yum -y install python-lxml
  else
    sudo easy_install lxml
  fi

  if [ `yum info h5py | grep h5py | wc -l` -gt 0 ]; then
    sudo yum -y install h5py
  else
    if [ -z $HDF5_install_directory ]; then
      sudo easy_install h5py
    else
      sudo /bin/bash -c "export HDF5_DIR=${HDF5_install_directory}; easy_install h5py;"
    fi
  fi

  if [ `yum info python-mpmath | grep python-mpmath | wc -l` -gt 0 ]; then
    sudo yum -y install python-mpmath
  else
    sudo easy_install mpmath
  fi

  # End RPM packages install
fi

# Some distros put MPI libraries and binaries in a location that
# isn't in the default search path, allowing multiple MPI versions
# to coexist. This can also happen with the ATLAS CBLAS libraries.
# Since we need to know where they are in order to compile stuff,
# find where they are located.

ld_search_string=`ld --verbose | grep SEARCH`

echo
echo "Searching for correct BLAS implementation on your machine. This may take some time..."
echo

# Find the CBLAS library, and make sure it's not the GSL one
CBLASLIB=`sudo find /usr/lib* -name *libcblas.so | grep -v -i gsl | head --lines=1`
CBLASLIBDIR=`dirname $CBLASLIB`
if [ `echo $ld_search_string | grep $CBLASLIBDIR | wc -w` -eq 0 ]; then
  # CBLAS library not in standard linker path
  # Need to add it to the XMDS configure string
  XMDS_CONFIGURE_STRING=$XMDS_CONFIGURE_STRING" --lib-path "$CBLASLIBDIR
fi

CBLASHEADER=`sudo find /usr -name cblas.h | grep -v -i gsl | head --lines=1`
CBLASHEADERDIR=`dirname $CBLASHEADER`
if [ ! $CBLASHEADERDIR = "/usr/include" ]; then
  if [ ! $CBLASHEADERDIR = "/usr/local/include" ]; then
    XMDS_CONFIGURE_STRING=$XMDS_CONFIGURE_STRING" --include-path "$CBLASHEADERDIR
  fi
fi

# Some distros don't have mpicc, mpic++ and mpirun in their default executable path, so we need to do stuff
# to be able to use it. The user also must do stuff.
if [ `which mpicc | wc -l` -eq 0 ]; then
    # On some RedHat systems, we need to source /etc/profile.d/openmpi.sh
    if [ -r /etc/profile.d/openmpi.sh ]; then
        source /etc/profile.d/openmpi.sh;
        load_openmpi;
        COMPLETION_MESSAGE="\nYou must add the line 'load_openmpi' to the end of your login \nscript (probably ~/.bashrc) to use MPI.\n If you wish to load a \ndifferent MPI implementation, you can use 'module avail' to see \nwhat implementations are available as alternatives."
    elif [ `which modulecmd | wc -l` -eq 1 ]; then
        # This is the case for Fedora
        source /etc/profile
        module load mpi;
        COMPLETION_MESSAGE="\nYou must add the line 'module load mpi' to the end of your \nlogin script (probably ~/.bashrc) to use MPI.\nIf you have multiple versions of MPI installed on your system \nand wish to use one that's not the default implementation, you \ncan use 'module avail' to see what is available and 'module load' \nthat version instead.\n"
    fi
fi


# Install FFTW3.3 from package manager if available, otherwise build from source
echo
if [ $DEB_INSTALL -eq 1 ]; then
  echo "Checking if MPI-enabled FFTW available in repository..."
  if [ `apt-cache --names-only search libfftw3-mpi-dev | wc -l` -ne 0 ]; then
    echo "Yes, it is available"
    echo "Installing FFTW via package manager"
    sudo apt-get -y install libfftw3-dev libfftw3-mpi-dev 
  else 
    echo "MPI-enabled FFTW not available in repository. Downloading, compiling and installing from source"
    install_FFTW_from_source
  fi
elif [ $RPM_INSTALL -eq 1 ]; then
  # Note Fedora 18 has fftw-3.3.3-4, fftw-devel-3.3.3-4, fftw-libs-3.3.3-4, 
  # fftw-libs-double-3.3.3-4, fftw-libs-single-3.3.3-4, fftw-libs-quad-3.3.3-4.
  # The fftw-devel-3.3.3-4 metapackage pulls in all the other libs: single, double, 
  # quad and long double, plus OpenMP libs, as well as FFTW headers.
  # As of Fedora 18, these libs are built with threads and OpenMP support, 
  # but *NOT* MPI support, so we still have to build from source. 
  install_FFTW_from_source
fi


# Fetch the XMDS2 source files
echo
echo "Contacting sourceforge to checkout XMDS2 source code. Please wait..."
echo

if [ $COMMITTER_INSTALL -eq 1 ]; then
  SVN_REPOSITORY="https://svn.code.sf.net/p/xmds/code/trunk/xpdeint"
else
  SVN_REPOSITORY="http://svn.code.sf.net/p/xmds/code/trunk/xpdeint"
fi

if [ $DEVELOPER_INSTALL -eq 1 ]; then
  # Fetch the latest XMDS2 source code from sourceforge
  cd $XMDS2_install_directory
  svn checkout $SVN_REPOSITORY .
else
  # Fetch a known good version of the XMDS2 source code from sourceforge
  cd $XMDS2_install_directory
  svn checkout -r $KNOWN_GOOD_XMDS_REVISION $SVN_REPOSITORY .
fi

# Compile the Cheetah templates into Python
echo
echo "Compiling Cheetah templates..."
echo
make

# Creates the xmds2 and xsil2graphics2 files in /usr/bin (or wherever), 
# and copy xmds2 python code into the python install path (typically 
# something like /usr/lib/python2.7/site-packages), and tells Python
# about the new package.
echo
echo "Installing XMDS..."
echo
sudo ./setup.py develop

echo
echo "Configuring XMDS with configure string: " $XMDS_CONFIGURE_STRING
echo

xmds2 --reconfigure $XMDS_CONFIGURE_STRING

# Build the HTML documentation
cd $XMDS2_install_directory"/admin/userdoc-source"
make html

# Fedora uses an OpenMPI library that assumes infiniband support. This 
# results in warnings when MPI-enabled scripts are run. Inform the user
# that these warnings can be killed if they really don't have the hardware
if [ $RPM_INSTALL -eq 1 ]; then
  # If the user doesn't have at least 2 processors they're not going to use MPI
  if [ $NUM_CPUS -gt 1 ]; then
    cd $XMDS2_install_directory"/examples"
    xmds2 diffusion_mpi.xmds > /dev/null 2>&1
    mpirun -np 2 diffusion_mpi > mpi_test_log 2>&1
    if [ `grep "unable to find any relevant network interfaces" mpi_test_log | wc -l` -gt 0 ]; then
      OMPI_CONF_FILE=`sudo find /etc -name openmpi-mca-params.conf | head --lines=1`
      COMPLETION_MESSAGE=$COMPLETION_MESSAGE"Your machine appears to lack Infiniband hardware, which means if you run\n"
      COMPLETION_MESSAGE=$COMPLETION_MESSAGE"MPI-enabled XMDS2 scripts you will get warnings that the hardware can't be\n"
      COMPLETION_MESSAGE=$COMPLETION_MESSAGE"found. If you know your machine doesn't have such hardware, it is safe to\n"
      COMPLETION_MESSAGE=$COMPLETION_MESSAGE"disable these warnings now by entering\n"
      COMPLETION_MESSAGE=$COMPLETION_MESSAGE"sudo sh -c \"echo 'btl = ^openib' >> "$OMPI_CONF_FILE"\"\n"
    fi
    rm mpi_test_log
  fi
fi


echo
echo "If no errors are displayed above, XMDS $XMDS_VERSION is installed!"
echo
echo "To see the HTML documentation, point your browser at" $XMDS2_install_directory"/documentation/index.html"
echo "or go to www.xmds.org"
echo
echo "Release notes and instructions can be found in" $XMDS2_install_directory
echo
echo "You can always update to the latest version of XMDS at any time by running \"make update\" "
echo "in the top level xmds-$XMDS_VERSION/ directory."
echo
echo "NOTES ON YOUR PARTICULAR INSTALL:"
echo
echo -e ${COMPLETION_MESSAGE}

