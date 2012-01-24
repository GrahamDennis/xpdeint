.. _Reference:

***************
XMDS2 Reference
***************

This section outlines all the elements and options available in an XMDS2 script.  This is very much a **work in progress**, beginning with placeholders in most cases, as we have prioritised the tutorials for new users.  One of the most productive ways that non-developer veterans can contribute to the project is to help develop this documentation.

.. _InstallationConfigurationRuntime:

Installation, Configuration and Runtime options
===============================================

Running the 'xmds2' program with the option '--help', gives several options that can change its behaviour at runtime.  These include:
  * '-g', which gives debug information, including the actual compile line, 
  * '-o', which overrides the name of the output file to be generated, and 
  * '-n', which generates the C code for the simulation, but does not try to compile it.

It also has commands to configure XMDS2 and recheck the installation.  If your program requires extra paths to compile, you can configure XMDS2 to include those paths by default.  Simply use the command

.. code-block:: none

    $ xmds2 --configure --include-path /path/to/include --lib-path /path/to/lib 

Running XMDS2 with the '--configure' option also searches for packages that have been installed since you last installed or configured XMDS2.  If you wish to run 'xmds2 --configure' with the same extra options as last time, simply use the command:

.. code-block:: none

    $ xmds2 --reconfigure

A detailed log of the checks is saved in the file '~/.xmds/waf_configure/config.log'.  This can be used to identify issues with packages that XMDS2 is not recognised, but you think that you have successfully installed on your system.


.. _UsefulXMLSyntax:

Useful XML Syntax
=================

Standard XML placeholders can be used to simplify some scripts.  For example, the following (abbreviated) code ensures that the limits of a domain are symmetric.

.. code-block:: none

    <?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE simulation [
    <!ENTITY Npts    "64">
    <!ENTITY L      "3.0e-5">
    ]>
      <simulation xmds-version="2">
      
        . . .
        
        <geometry>
            <propagation_dimension> t </propagation_dimension>
            <transverse_dimensions>
              <dimension name="x" lattice="&Npts;"  domain="(-&L;, &L;)" />
            </transverse_dimensions>
         </geometry>


.. _SimulationElement:

Simulation Element
==================

The ``<simulation>`` element is the single top level element in an XMDS2 simulation, and contains all the other elements.  All XMDS scripts must contain exactly one simulation element.




.. _FeaturesElement:

Features Element
================

Features elements are where simulation-wide options are specified.  There are many possible features elements.  We will give a full list here, and then describe each one.

    * :ref:`ErrorCheck`

.. _ErrorCheck:

Error Check
-----------

It's often important to know whether you've got errors.


.. _DriverElement:

Driver Element
==============

The driver element controls the overall management of the simulation, including how many paths of a stochastic simulation are to be averaged, and whether or not it is to be run using distributed memory parallelisation.




.. _GeometryElement:

Geometry Element
================

The `<geometry>` element describes the dimensions used in your simulation.  Not all arrays are defined on all dimensions.



.. _VectorElement:

Vector Element
==============

Vectors are arrays of data, defined over any subset of the transverse dimensions defined in your :ref:`GeometryElement`.  They are initialised at the beginning of a simulation, either from code or from an input file.  They can then be referenced and/or changed by sequence elements.  Variants of the vector elements are 


.. _ComputedVectorElement:

Computed Vector Element
=======================

Computed vectors are arrays of data much like normal ``vector`` elements, but they are always calculated as they are referenced.  



.. _NoiseVectorElement:

Noise Vector Element
====================

Noise vectors used like computed vectors, but when they are evaluated they generate arrays of random numbers of various kinds. 



.. _SequenceElement:

Sequence Element
================


.. _FilterElement:

Filter Element
--------------


.. _IntegrateElement:

Integrate Element
-----------------

.. _BreakpointElement:

Breakpoint Element
------------------

.. _OutputElement:

Output Element
==============

The ``<output>`` element describes the output of the program.  It is often inefficient to output the complete state of all vectors at all times during a large simulation, so the purpose of this function is to define subsets of the information required for output.  Each different format of information is described in a different ``<group>`` element inside the output element.  The ``<output>`` element may contain any number of ``<group>`` elements.

The ``<samples>`` inside ``<integrate>`` elements defines a string of integers, with exactly one for each ``<group>`` element.  During that integration, the variables described in each ``<group>`` element will be sampled and stored that number of times 

.. _GroupElement:

Group Element
-------------

The group elements

Further details will be forthcoming, but for now, try looking at the :ref:`workedExamples`, and a search of the /examples folder.