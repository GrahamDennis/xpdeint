.. _Installation:

Installation
============

**XMDS2** can be installed on any unix-like system including linux, Tru64, Mac OS X.  It requires a C++ compiler, python, and several installed packages.  Many of these packages are optional, but a good idea to obtain full functionality.  This installation guide will take you through a typical full install step by step, although many of the packages are likely already available on any given system.

This guide adds extra notes for users wishing to install XMDS2 using the SVN repository.  This requires a few extra steps, but allows you to edit your copy, and/or update your copy very efficiently (with all the usual advantages and disadvantages of using unreleased material).

0. You will need a copy of XMDS2.  
    The current release can be found at `Sourceforge <http://sourceforge.net/projects/xmds/>`_, and downloaded as a single file.
    Download this file, and expand it in a directory where you want to keep the program files.
    
    * Developer-only instructions: You can instead check out a working copy of the source using SVN. 
      In a directory where you want to check out the repository, run:
      ``svn checkout https://xmds.svn.sourceforge.net/svnroot/xmds/trunk/xpdeint .``
      (Only do this once.  To update your copy, type ``svn up`` or ``make update`` in the same directory, and then repeat any developer-only instructions below).
    
#. You will need a working C++ compiler.  
    For Mac OS X, this means that the developer tools should be installed.
    One common free compiler is `gcc <http://gcc.gnu.org/>`_.  It can be downloaded using your favourite package manager.
    XMDS2 can also use Intel's C++ compiler if you have it. 
    Intel's compiler typically generates faster code than gcc, but it isn't free.

#. You will need a `python distribution <http://www.python.org/>`_.  

   * Mac OS X: It is pre-installed on Mac OS X 10.5 or later.
   * Linux: Install this using your favourite package manager.
   * Windows: One way to install Python and related packages is via the `Enthought Python Distribution <http://www.enthought.com/products/epd.php>`_. 
   
    We require python 2.4 or greater. (2.5 recommended).
   

#. Install setuptools.
    If you have root (sudo) access, the easy way to install this is by executing
    ez_setup.py from the repository. Simply type ``sudo python ez_setup.py``

       If you want to install into your home directory without root access, this is more complex:
       
       a) First create the path ~/lib/python2.5/site-packages (assuming you installed python version 2.5) and ~/bin
          Add "export PYTHONPATH=~/lib/python2.5/site-packages:$PYTHONPATH" and "export PATH=~/bin:$PATH" (if necessary)
          to your .bashrc file (and run ". ~/.bashrc")

       b) If necessary install setuptools, by executing ez_setup.py from the repository.
          "python ez_setup.py --prefix=~"
          
    If you use Mac OS X 10.5 or later, or installed the Enthought Python Distribution on Windows, then setuptools is already installed.
    Though if the next step fails, you may need to upgrade setuptools.  To do that, type ``sudo easy_install -U setuptools``


#. Install Cheetah version 2.0.1 or later, pyparsing, and (optionally) lxml. 
    If you have root access, this is as easy as:
    ``sudo easy_install Cheetah``, ``sudo easy_install pyparsing`` and ``sudo easy_install lxml`` respectively.
    
        You will need to have 'libxml2' and 'libxslt' installed (via your choice of package manager) if you want to install lxml.  
        They are preinstalled on Mac OS X.

    If you don't have root access or want to install into your home directory, use:
    ``easy_install --prefix=~ Cheetah`` (etc.)

    Note that lxml is not required for XMDS2 to run. If it is installed, it is used to validate
    the xmds script passed to XMDS2 to check that there isn't any invalid syntax or typos that
    XMDS2 wouldn't have otherwise noticed. Also note that installing lxml is a bit tricky on Mac
    OS X Leopard because Apple shipped an old version of libxml2 with the system.
    (This problem does not exist on Snow Leopard.)

    * Developer only instructions: The Cheetah templates (\*.tmpl) must be compiled into python.
        To do this, run ``make`` in the xmds2/ directory.

#. There are a range of optional installs.  We recommend that you install them if possible:
    .. _hdf5_Installation:
    
    #. **HDF5** is a library for reading and writing the `Heirachical Data Format <http://www.hdfgroup.org/HDF5/>`_.
       This is a standardised data format which it is suggested that people use in preference to the older 'binary' output (which is 
       compatible with xmds-1). The advantage of HDF5 is that this data format is understood by a variety of other tools. xsil2graphics2
       provides support for loading data created in this format into Mathematica and Matlab.
       
       After downloading the latest package, install with the ``--prefix=/usr/local/`` option if you want XMDS2 to find the library automatically.
       
    #. **MPI** is an API for doing parallel processing on multi-processor/multi-core computers, or clusters of computers.
         Many supercomputing systems (and Mac OS X) come with MPI libraries pre installed.
         The `Open MPI <http://www.open-mpi.org/>`_ project has free distributions of this library for other machines.
    
    #. **FFTW** is the library XMDS2 uses for Fourier transforms, which is the transform most people will be using. 
         If you need
         support for MPI distributed simulations, you must install the alpha version.  Both the stable and alpha versions are available for
         free at the `FFTW website <http://www.fftw.org/>`_.

         NOTE: As of current writing, the latest version of fftw3 (3.3alpha1) does not compile on Snow Leopard.
         FFTW-3.2.2 compiles fine on Snow Leopard, but if you need MPI support, you must use the alpha version.
         A patch for this bug exists in admin/fftw3-SnowLeopard.patch
         This patch has been submitted upstream, however no response has been received as yet.
         I hope that the patch makes it into the next release of fftw3.
         
         To apply the patch run (in the fftw-3 directory):
         ``patch -p0 < ~/path/to/xmds2/admin/fftw3-SnowLeopard.patch``
         
         Then configure/compile as normal.

    #. **mpmath** is a library for arbitrary precision floating point math. 
         This package is needed for the matrix-based transforms like Bessel and Hermite-Gauss.
         Install from package manager or ``sudo easy_install mpmath``
           
    #. A Matrix library like `ATLAS <http://math-atlas.sourceforge.net/>`_, or Intel's `MKL <http://software.intel.com/en-us/intel-mkl/>`_ allows efficient implementation of transform spaces other than Fourier space.
         Mac OS X comes with its own (fast) matrix library.
         
         The `GNU Scientific library (GSL) <http://www.gnu.org/software/gsl/>`_ is another free matrix library.
    
    #. **numpy** is a tool that XMDS2 uses for automated testing.
         It can be installed with ``sudo easy_install numpy``. 
         
         Mac OS X 10.5 and later come with numpy.
         
    #. **h5py** is needed for checking the results of XMDS2 tests that generate HDF5 output.
           h5py requires numpy version 1.0.3 or later. 
           
           Mac OS X Leopard comes with 1.0.1, so this must be upgraded on such systems.
           Upgrading h5py on Mac OS X is best done with the source of the package, as the easy_install option can get confused with multiple numpy versions.
           Mac OS X Snow Leopard comes with version 1.2.1
         

#. Install XMDS2 into your python path by running (in the xmds2/ directory):
    ``sudo ./setup.py develop``

    If you want to install it into your home directory, type ``./setup.py develop --prefix=~``

    * Developer-only instructions: If you have 'numpy' installed, test XMDS2 by typing ``./run_tests.py`` in the xmds2/ directory.
       The package 'numpy' is one of the optional packages, with installation instructions below.
       
    * Developer-only instructions: To build the user documentation, you first need to install sphinx, either via your package manager or:
           ``sudo easy_install Sphinx``

           Then, to build the documentation, in the xmds2/admin/userdoc-source/ directory run: ``make html``

           If this results in an error, you may need to run ``sudo ./setup.py develop``

           The generated html documentation can now be found at xmds2/documentation/index.html

**Congratulations!** You should now have a fully operational copy of xmds2 and xsil2graphics2.  You can test your copy using examples from the "xmds2/examples" directory, and follow the worked examples in the :ref:`QuickStartTutorial` and :ref:`WorkedExamples`.


