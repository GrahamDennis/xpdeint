.. _mac_installation:

Download
========

Mac OS X 10.6 (Snow Leopard) or later XMDS 2.1 installer: http://sourceforge.net/projects/xmds/files/xmds-2.1-osx.zip


Mac OS X Installation
=====================

A self-contained installer for Mac OS X 10.6 (Snow Leopard) and later is available from the link above. This installer is only compatible with Intel Macs.  This means that the older PowerPC architecture is *not supported*.  Xcode (Apple's developer tools) is required to use this installer. Xcode is available for free from the Mac App Store, and you will be prompted to install it if you haven't already.

Once you have downloaded the XMDS installer, installation is as simple as dragging it to your Applications folder or any other location.  Click the XMDS application to launch it, and press the "Launch XMDS Terminal" button to open a Terminal window customised to work with XMDS.  The first time you do this, the application will complete the installation process.  This process can take a few minutes, but is only performed once.

You can run XMDS in the XMDS terminal by typing ``xmds2``. See the :ref:`QuickStartTutorial` for next steps.

To uninstall XMDS, drag the XMDS application to the trash. XMDS places some files in the directory ``~/Library/XMDS``. Remove this directory to completely remove XMDS from your system.

This package includes binaries for `OpenMPI <http://www.open-mpi.org>`_, `FFTW <http://www.fftw.org>`_, `HDF5 <http://www.hdfgroup.org/HDF5>`_ and `GSL <http://www.gnu.org/software/gsl>`_. These binaries are self-contained and do not overwrite any existing installations.