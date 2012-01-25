.. _Reference:

***************
XMDS2 Reference
***************

This section outlines all the elements and options available in an XMDS2 script.  This is very much a **work in progress**, beginning with placeholders in most cases, as we have prioritised the tutorials for new users.  One of the most productive ways that non-developer veterans can contribute to the project is to help develop this documentation.

.. _InstallationConfigurationRuntime:

Installation, Configuration and Runtime options
===============================================

Running the 'xmds2' program with the option '--help', gives several options that can change its behaviour at runtime.  These include:
  * '-o', which overrides the name of the output file to be generated
  * '-n', which generates the C code for the simulation, but does not try to compile it
  * '-v', which gives verbose output about compilation flags.
  * '-g', which compiles the simulation in debug mode (compilation errors refer to lines in the source, not the .xmds file). This option implies '-v'. This option is mostly useful when debugging XMDS code generation.

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

The ``<simulation>`` element is the single top level element in an XMDS2 simulation, and contains all the other elements.  All XMDS scripts must contain exactly one simulation element, and it must have the ``xmds-version="2"`` attribute defined.




.. _FeaturesElement:

Features Elements
=================

Features elements are where simulation-wide options are specified.  There are many possible features elements.  We will give a full list here, and then describe each one.

    * :ref:`ErrorCheck`
    * :ref:`Precision`

.. _ErrorCheck:

Error Check
-----------

It's often important to know whether you've got errors.

.. _Precision:

Precision
-----------

This specifies the precision of the XMDS2 ``real`` and ``complex`` datatypes, as well as the precision used when computing transforms. Currently two values are accepted: ``single`` and ``double``. If this feature isn't specified, XMDS2 defaults to using double precision for its variables and internal calculations.

Single precision has approximately 7.2 decimal digits of accuracy, with a minimum value of 1.4×10\ :superscript:`-45` and a maximum of 3.8×10\ :superscript:`34`. Double precision has approximately 16 decimal digits of accuracy, a minimum value of 4.9×10\ :superscript:`-324` and a maximum value of 1.8×10\ :superscript:`308`.

Using single precision can be attractive, as it can be more than twice as fast, depending on whether a simulation is CPU bound, memory bandwidth bound, MPI bound or bottlenecked elsewhere. Caution should be exercised, however. Keep in mind how many timesteps your simulation requires, and take note of the tolerance you have set per step, to see if the result will lie within your acceptable total error - seven digit precision isn't a lot. Quite apart from the precision, the range of single precision can often be inadequate for many physical problems. In atomic physics, for example, intermediate values below 1.4×10\ :superscript:`-45` are easily obtained, and will be taken as zero. Similarly, values above 3.8×10\ :superscript:`34` will result in NaNs and make the simulation results invalid.

A further limitation is that not all the combinations of random number generators and probability distributions that are supported in double precision are supported in single precision. For example, neither the solirte nor dsfmt generators support single precision gaussian distributions. The posix generator will always work, but may be very slow.

Example syntax: ``<precision> single </precision>``

.. _DriverElement:

Driver Element
==============

The driver element controls the overall management of the simulation, including how many paths of a stochastic simulation are to be averaged, and whether or not it is to be run using distributed memory parallelisation.  If it is not included, then the simulation is performed once without using MPI parallelisation.  If it is included, it must have a ``name`` attribute.

The ``name`` attribute can have values of "none" (which is equivalent to the default option of not specifying a driver), "distributed-mpi", "multi=path" or "mpi-multi-path".

Choosing the ``name="distributed-mpi"`` option allows a single integration over multiple processors.  The resulting executable can then be run according to your particular implementation of MPI.  The FFTW library only allows MPI processing of multidimensional vectors, as otherwise shared memory parallel processing requires too much inter-process communication to be efficient.  As noted in the worked example :ref:`WignerArguments`, it is wise to test the speed of the simulation using different numbers of processors.

The ``name="multi-path"`` option is used for stochastic simulations, which are typically run multiple times and averaged.  It requires a ``paths`` attribute with the number of iterations of the integration to be averaged.  The output will report the averages of the desired samples, and the standard error in those averages.  
The ``name="mpi-multi-path"`` option integrates separate paths on different processors, which is typically a highly efficient process.


.. _GeometryElement:

Geometry Element
================

The ``<geometry>`` element describes the dimensions used in your simulation, and is required.  The only required element inside is the ``<propagation_dimension>`` element, which defines the name of the dimension along which your simulation will integrate.  Nothing else about this dimension is specified, as requirements for the lattice along the integration dimension is specified by the ``<integrate>`` blocks themselves, as described in section :ref:`IntegrateElement`.

If there are other dimensions in your problem, they are called "transverse dimensions", and are described in the ``<transverse_dimensions>`` element.  Each dimension is then described in its own ``<dimension>`` element.  A transverse dimension must have a unique name defined by a ``name`` attribute.  If it is not specified, the type of dimension will default to "real", otherwise it can be specified with the ``type`` attribute.  Allowable types (other than "real") are "long", "int", and "integer", which are actually all synonyms for an integer-valued dimension.

Each transverse dimension must specify a domain.

Not all arrays are defined on all dimensions.



.. _VectorElement:

Vector Element
==============

Vectors are arrays of data, defined over any subset of the transverse dimensions defined in your :ref:`GeometryElement`.  They are initialised at the beginning of a simulation, either from code or from an input file.  They can then be referenced and/or changed by sequence elements.  Variants of the vector elements are 


.. _ComputedVectorElement:

Computed Vector Element
=======================

Computed vectors are arrays of data much like normal ``<vector>`` elements, but they are always calculated as they are referenced.  



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
