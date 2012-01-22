.. _linux_installation:

Download
========

Linux installer script: http://xmds.svn.sourceforge.net/viewvc/xmds/trunk/xpdeint/admin/linux_installer


Linux Installation
==================

The Linux installer for Ubuntu / Debian / Fedora / Red Hat can be downloaded and executed with the following command::

    /bin/bash -c "$(wget -qO - http://xmds.svn.sf.net/viewvc/xmds/trunk/xpdeint/admin/linux_installer)"

Alternatively, you can download it from the link above, and type the following into a terminal::

    bash ./linux_installer
    

This script installs all XMDS dependencies from your native package manager (``apt-get`` for Ubuntu/Debian, ``yum`` for Fedora/Red Hat).  The script can only operate with administrative privileges.  The script will ask you to enter your admin password at the appropriate steps.  For instructions on how to install XMDS on systems where you lack administrative rights, see :ref:`ManualInstallation`.

Once XMDS has been installed, you can run it from the terminal by typing ``xmds2``. See the :ref:`QuickStartTutorial` for next steps.
