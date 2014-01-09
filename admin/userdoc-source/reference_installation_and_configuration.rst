:: index:: Configure, Reconfigure, XMDS2 runtime options

.. _ReferenceConfigurationInstallationRuntime:

Configuration, installation and runtime options
===============================================

Running the 'xmds2' program with the option '--help', gives several options that can change its behaviour at runtime.  These include:
  * '-o' or '--output', which overrides the name of the output file to be generated
  * '-n' or '--no-compile', which generates the C code for the simulation, but does not try to compile it
  * '-v' or '--verbose', which gives verbose output about compilation flags.
  * '-g' or '--debug', which compiles the simulation in debug mode (compilation errors refer to lines in the source, not the .xmds file). This option implies '-v'. This option is mostly useful when debugging XMDS code generation.
  * '--waf-verbose', which makes ``waf`` be very verbose when configuring XMDS or compiling simulations.  This option is intended for developer use only to aid in diagnosing problems with ``waf``.

It also has commands to configure XMDS2 and recheck the installation.  If your program requires extra paths to compile, you can configure XMDS2 to include those paths by default.  Simply use the command

.. code-block:: bash

    $ xmds2 --configure --include-path /path/to/include --lib-path /path/to/lib 

Alternatively, you can set the ``CXXFLAGS`` or ``LINKFLAGS`` environment variables before calling ``xmds2 --reconfigure``.  For example, to pass the compiler flag ``-pedantic`` and the link flag ``-lm`` using the bash shell, use:

.. code-block:: bash

    $ export CXXFLAGS="-pedantic"
    $ export LINKFLAGS="-lm" 
    $ xmds2 --reconfigure``
    
This method can also be used to change the default compilers for standard and parallel processing, using the CXX and MPICXX flags respectively.

Running XMDS2 with the '--configure' option also searches for packages that have been installed since you last installed or configured XMDS2.  If you wish to run 'xmds2 --configure' with the same extra options as last time, simply use the command:

.. code-block:: bash

    $ xmds2 --reconfigure

A detailed log of the checks is saved in the file '~/.xmds/waf_configure/config.log'.  This can be used to identify issues with packages that XMDS2 is not recognised, but you think that you have successfully installed on your system.



