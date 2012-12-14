.. _Installation:

************
Installation
************

**XMDS2** can be installed on any unix-like system including Linux, Tru64, and Mac OS X.  It requires a C++ compiler, python, and several installed packages.  Many of these packages are optional, but a good idea to obtain full functionality.  

Installers
==========

The easiest way to get started is with an installer.  If we don't have an installer for your system, follow the :ref:`manual installation <ManualInstallation>` instructions.

.. tabularcolumns:: |c|c|c|

.. list-table::
    :widths: 15, 5, 5
    :header-rows: 0

    * - Linux (Ubuntu/Debian/Fedora/RedHat)

      - `Download Linux Installer <http://svn.code.sf.net/p/xmds/code/trunk/xpdeint/admin/linux_installer.sh>`_

      - :ref:`Learn more <linux_installation>`

    * - OS X 10.6/10.7

      - `Download OS X Installer <http://sourceforge.net/projects/xmds/files>`_

      - :ref:`Learn more <mac_installation>`
        
    * - Other systems

      - :ref:`Install from source <ManualInstallation>`
      
      -

If you have one of the supported operating systems listed above, but you find the installer doesn't work for you, please let us know by emailing xmds-devel <at> lists.sourceforge.net. If you'd like to tweak the linux installer to work on a distribution we haven't tested, we'd love you to do that and let us know!

.. _linux_installation:

Linux installer instructions
============================

The linux installer has currently only been tested with Ubuntu, Debian, Fedora, and Red Hat. Download the installer here: http://svn.code.sf.net/p/xmds/code/trunk/xpdeint/admin/linux_installer.sh

Once you have downloaded it, make the installer executable and run it by typing the following into a terminal::

  chmod u+x linux_installer.sh
  ./linux_installer.sh

Alternatively, if you wish to download and run the installer in a single step, you can use the following command::

  /bin/bash -c "$(wget -qO - http://svn.code.sf.net/p/xmds/code/trunk/xpdeint/admin/linux_installer.sh)"

The linux installer installs all XMDS2 dependencies from your native package manager where possible (``apt-get`` for Ubuntu/Debian, ``yum`` for Fedora/Red Hat) but will download and compile the source code for libraries not available through the package manager. This means you'll need to be connected to the internet when running the installer. The installer should not be run with administrative privileges; it will ask you to enter your admin password at the appropriate point. 

For instructions on how to install XMDS2 on systems where you lack administrative rights, see :ref:`ManualInstallation`.

By default, this installer will install a known stable version of XMDS, which can be updated at any time by navigating to the XMDS directory and typing 'make update'. To install the latest developer version at the beginning, simply run the installer with the ``--develop`` option.

Once XMDS2 has been installed, you can run it from the terminal by typing ``xmds2``. See the :ref:`QuickStartTutorial` for next steps.


.. _mac_installation:

Mac OS X Installation
=====================

Download
--------

Mac OS X 10.6 (Snow Leopard) or later XMDS 2 installer: http://sourceforge.net/projects/xmds/files/



Using the Mac OS X Installer
----------------------------

A self-contained installer for Mac OS X 10.6 (Snow Leopard) and later is available from the link above. This installer is only compatible with Intel Macs.  This means that the older PowerPC architecture is *not supported*.  Xcode (Apple's developer tools) is required to use this installer. Xcode is available for free from the Mac App Store for 10.7 or later, and is available on the install disk of earlier Macs as an optional install.  For users of earlier operating systems (10.6.8 or earlier), it is possible to find a free copy of earlier versions of XCode on the Apple developer website (3.2.6 was the Snow Leopard compatible version). You will be prompted to install it if you haven't already.

Once you have downloaded the XMDS installer, installation is as simple as dragging it to your Applications folder or any other location.  Click the XMDS application to launch it, and press the "Launch XMDS Terminal" button to open a Terminal window customised to work with XMDS.  The first time you do this, the application will complete the installation process.  This process can take a few minutes, but is only performed once.

The terminal window launched by the XMDS application has environment variables set for using this installation of XMDS.  You can run XMDS in this terminal by typing ``xmds2``.  See the :ref:`QuickStartTutorial` for next steps.

To uninstall XMDS, drag the XMDS application to the trash. XMDS places some files in the directory ``~/Library/XMDS``. Remove this directory to completely remove XMDS from your system.

This package includes binaries for `OpenMPI <http://www.open-mpi.org>`_, `FFTW <http://www.fftw.org>`_, `HDF5 <http://www.hdfgroup.org/HDF5>`_ and `GSL <http://www.gnu.org/software/gsl>`_. These binaries are self-contained and do not overwrite any existing installations.

.. _ManualInstallation:

Manual installation from source
===============================

This installation guide will take you through a typical full install step by step. A large part of this procedure is obtaining and installing other libraries that XMDS2 requires, before installing XMDS2 itself. 

While the instructions below detail these packages individually, if you have administrative privileges (or can request packages from your administrator) and if you are using an Ubuntu, Debian, Fedora or Red Hat linux distribution, you can install all required and optional dependencies (but not XMDS2 itself) via

Ubuntu / Debian::

  sudo apt-get install build-essential subversion libopenmpi-dev openmpi-bin python-dev python-setuptools python-cheetah python-numpy python-pyparsing python-lxml python-mpmath libhdf5-serial-dev libgsl0-dev python-sphinx python-h5py libatlas-base-dev

Fedora / Red Hat::

  sudo yum install gcc gcc-c++ make automake subversion openmpi-devel python-devel python-setuptools python-cheetah numpy gsl-devel python-sphinx libxml2-devel libxslt-devel atlas-devel hdf5-devel pyparsing pyparsing python-lxml python-mpmath h5py

You will still have to download and build FFTW 3.3 from source (see below) since prebuilt packages with MPI and AVX support are not currently available in the repositories.

Also note that this guide adds extra notes for users wishing to install XMDS2 using the SVN repository.  This requires a few extra steps, but allows you to edit your copy, and/or update your copy very efficiently (with all the usual advantages and disadvantages of using unreleased material).

0. You will need a copy of XMDS2.  
    The current release can be found at `Sourceforge <http://sourceforge.net/projects/xmds/>`_, and downloaded as a single file.
    Download this file, and expand it in a directory where you want to keep the program files.
    
    * Developer-only instructions: You can instead check out a working copy of the source using SVN. 
      In a directory where you want to check out the repository, run:
      ``svn checkout https://xmds.svn.sourceforge.net/svnroot/xmds/trunk/xpdeint .``
      (Only do this once.  To update your copy, type ``svn up`` or ``make update`` in the same directory, and then repeat any developer-only instructions below).
    
#. You will need a working C++ compiler.  
    For Mac OS X, this means that the developer tools (XCode) should be installed.
    One common free compiler is `gcc <http://gcc.gnu.org/>`_.  It can be downloaded using your favourite package manager.
    XMDS2 can also use Intel's C++ compiler if you have it. 
    Intel's compiler typically generates faster code than gcc, but it isn't free.

#. You will need a `python distribution <http://www.python.org/>`_.  

   * Mac OS X: It is pre-installed on Mac OS X 10.5 or later.
   * Linux: It should be pre-installed. If not, install using your favourite package manager.
   
    We require python 2.4 or greater. XMDS2 does not support Python 3.
   

#. Install setuptools.
    If you have root (sudo) access, the easy way to install this is by executing
    ez_setup.py from the repository. Simply type ``sudo python ez_setup.py``

       If you want to install into your home directory without root access, this is more complex:
       
       a) First create the path ~/lib/python2.5/site-packages (assuming you installed python version 2.5) and ~/bin
          Add "export PYTHONPATH=~/lib/python2.5/site-packages:$PYTHONPATH" and "export PATH=~/bin:$PATH" (if necessary)
          to your .bashrc file (and run ". ~/.bashrc")
       
       b) If necessary install setuptools, by executing ez_setup.py from the repository.
          ``python ez_setup.py --prefix=~``
          
    If you use Mac OS X 10.5 or later, or installed the Enthought Python Distribution on Windows, then setuptools is already installed.
    Though if the next step fails, you may need to upgrade setuptools.  To do that, type ``sudo easy_install -U setuptools``

#. Install HDF5 and FFTW3 (and optionally MPI).
    .. _hdf5_Installation:
    
    #. **HDF5** is a library for reading and writing the `Hierarchical Data Format <http://www.hdfgroup.org/HDF5/>`_.
         This is a standardised data format which it is suggested that people use in preference to the older 'binary' output (which is 
         compatible with xmds-1). The advantage of HDF5 is that this data format is understood by a variety of other tools. xsil2graphics2
         provides support for loading data created in this format into Mathematica and Matlab.
         
         XMDS2 only requires the single process version of HDF5, so there is no need to install the MPI version.
       
         \* Sidebar: Installing HDF5 from source follows a common pattern, which you may find yourself repeating later:  
         
            #. After extracting the source directory, type ``configure`` and then add possible options.
            
                (For HDF5, install with the ``--prefix=/usr/local/`` option if you want XMDS2 to find the library automatically.  This is rarely needed for other packages.)
                
            #. Once that is finished, type ``make``.  Then wait for that to finish, which will often be longer than you think.
            
            #. Finally, type ``sudo make install`` to install it into the appropriate directory.
        
    #. **FFTW** is the library XMDS2 uses for Fourier transforms. 
         This is the transform most people will use in their simulations. If you need
         support for MPI distributed simulations, you must configure FFTW to use MPI.
  
         FFTW is available for free at the `FFTW website <http://www.fftw.org/>`_.
         To configure and compile it, follow the steps described in the HDF5 sidebar above.  
         You may wish to add the ``--enable-mpi --disable-fortran`` options to the ``configure`` command.

    #. **MPI** is an API for doing parallel processing.
         XMDS2 can use MPI to parallelise simulations on multi-processor/multi-core computers, or clusters of computers.
         Many supercomputing systems come with MPI libraries pre-installed.
         The `Open MPI <http://www.open-mpi.org/>`_ project has free distributions of this library available.
		 
	 If you intend to take advantage of XMDS2's multi-processing features, you must install MPI, and configure FFTW3 to use it.



#. There are a range of optional installs.  We recommend that you install them all if possible:

    #. A Matrix library like `ATLAS <http://math-atlas.sourceforge.net/>`_, Intel's `MKL <http://software.intel.com/en-us/intel-mkl/>`_ or the `GNU Scientific library (GSL) <http://www.gnu.org/software/gsl/>`_ 
         These libraries allow efficient implementation of transform spaces other than Fourier space.
         Mac OS X comes with its own (fast) matrix library.
    
    #. **numpy** is a tool that XMDS2 uses for automated testing.
         It can be installed with ``sudo easy_install numpy``. 
         
         Mac OS X 10.5 and later come with numpy.
         
    #. **lxml** is used to validate the syntax of scripts passed to XMDS2. 
         If you have root access, this can be installed with the command ``sudo easy_install lxml``

         You will need to have 'libxml2' and 'libxslt' installed (via your choice of package manager) to install lxml.  
         Sufficient versions are preinstalled on Mac OS X 10.6.

         If you don't have root access or want to install into your home directory, use:
            ``easy_install --prefix=~ lxml``

    #. **h5py** is needed for checking the results of XMDS2 tests that generate HDF5 output.
           h5py requires numpy version 1.0.3 or later. 
           
           Upgrading `h5py <http://h5py.alfven.org/>`_ on Mac OS X is best done with the source of the package, as the easy_install option can get confused with multiple numpy versions.
           (Mac OS X Snow Leopard comes with version 1.2.1). 
           After downloading the source, execute ``python ./setup.py build`` in the source directory, and then ``python ./setup.py install`` to install it.  

#. Install XMDS2 into your python path by running (in the xmds-2.1.2/ directory):
    ``sudo ./setup.py develop``

    If you want to install it into your home directory, type ``./setup.py develop --prefix=~``
    
    This step requires access to the net, as it downloads any dependent packages.  If you are behind a firewall, you may need to set your HTTP_PROXY environment variable in order to do this.

    * Developer only instructions: 
        The Cheetah templates (\*.tmpl) must be compiled into python.
        To do this, run ``make`` in the xmds-2.1.2/ directory.

    * Developer-only instructions: 
        If you have 'numpy' installed, test XMDS2 by typing ``./run_tests.py`` in the xmds-2.1.2/ directory.
        The package 'numpy' is one of the optional packages, with installation instructions below.
       
    * Developer-only instructions: 
        To build the user documentation, you first need to install sphinx, either via your package manager or:
        ``sudo easy_install Sphinx``

        Then, to build the documentation, in the xmds-2.1.2/admin/userdoc-source/ directory run: ``make html``

        If this results in an error, you may need to run ``sudo ./setup.py develop``

        The generated html documentation will then be found at xmds-2.1.2/documentation/index.html
		
#. Configure XMDS2 by typing ``xmds2 --reconfigure``.  If XMDS2 is unable to find a library, you can tell XMDS2 where these libraries are located by adding ``include`` and ``lib`` search paths using the ``--include-path`` and ``--lib-path`` options.  For example, if FFTW3 is installed in ``/apps/fftw3`` with headers in ``/apps/fftw3/include/`` and the libraries in ``/apps/fftw3/lib``, (re)configure XMDS2 by typing:

	* ``xmds2 --reconfigure --include-path /apps/fftw3/include --lib-path /apps/fftw3/lib``.
	
	If you need to use additional compiler or link flags for XMDS2 to use certain libraries, set the ``CXXFLAGS`` or ``LINKFLAGS`` environment variables before calling ``xmds2 --reconfigure``.  For example, to pass the compiler flag ``-pedantic`` and the link flag ``-lm``, use:
	
	* ``CXXFLAGS="-pedantic" LINKFLAGS="-lm" xmds2 --reconfigure``.

**Congratulations!** You should now have a fully operational copy of xmds2 and xsil2graphics2.  You can test your copy using examples from the "xmds-2.1.2/examples" directory, and follow the worked examples in the :ref:`QuickStartTutorial` and :ref:`WorkedExamples`.



