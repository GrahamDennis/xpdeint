.. raw:: html

  <style> .attributes-code {color:#0000BB; font-family:'monospace'; font-style:italic} </style>

.. raw:: html

  <style> .attributes-standard {color:#0000BB; font-family:'monospace'; font-style:italic; font-size:smaller} </style>

.. raw:: html

  <style> .smaller-font {font-size:smaller} </style>

.. role:: attributes-code
.. role:: attributes-standard
.. role:: smaller-font

.. _ReferenceElements:

*********************
XMDS2 script elements
*********************

This section outlines all the elements and options available in an XMDS2 script.  This is very much a **work in progress**, beginning with placeholders in most cases, as we have prioritised the tutorials for new users.  One of the most productive ways that non-developer veterans can contribute to the project is to help develop this documentation.




.. _SimulationElement:

Simulation element
==================

The ``<simulation>`` element is the single top level element in an XMDS2 simulation, and contains all the other elements.  All XMDS scripts must contain exactly one simulation element, and it must have the ``xmds-version="2"`` attribute defined.

Example syntax::

    <simulation xmds-version="2">
        <!-- Rest of simulation goes here -->
    </simulation>




.. _NameElement:

Name element
============

The name of your simulation. This element is optional, but recommended. If it is set, it will be the name of the executable file generated from this script. It will also be the name of the output file (with an appropriate extension) if the ``filename`` attribute is not given a value in the ``<output>`` element.

Example syntax::

    <name> funky_solver </name>


.. _AuthorElement:

Author element
==============

The author(s) of this script. This element is optional, but can be useful if you need to find the person who has written an incomprehensible script and thinks comments are for the weak.

Example syntax::

    <author> Ima Mollusc </author>


.. _DescriptionElement:

Description element
===================

A description of what the simulation does. Optional, but recommended, in case you (or someone else) has to revist the script at some distant point in the future.

Example syntax::

    <description>
      Calculate the 3D ground state of a Rubidium BEC in a harmonic magnetic trap assuming
      cylindrical symmetry about the z axis and reflection symmetry about z=0.
      This permits us to use the cylindrical Bessel functions to expand the solution transverse
      to z and a cosine series to expand the solution along z.
    </description>



.. _FeaturesElement:

Features Elements
=================


Features elements are where simulation-wide options are specified. The ``<features>`` element wraps one or more elements describing features. There are many possible feature elements. Currently, a full list of the features supported is:

    * :ref:`arguments <ArgumentsElement>`
    * :ref:`auto_vectorise <Autovectorise>`
    * :ref:`benchmark <Benchmark>`
    * :ref:`bing <Bing>`
    * :ref:`cflags <CFlags>`
    * :ref:`diagnostics <Diagnostics>`
    * :ref:`error_check <ErrorCheck>`
    * :ref:`halt_non_finite <HaltNonFinite>`
    * :ref:`fftw <FFTW>`
    * :ref:`globals <Globals>`
    * :ref:`OpenMP <OpenMP>`
    * :ref:`precision <Precision>`
    * :ref:`validation <Validation>`

Example syntax::

    <simulation xmds-version="2">
      <features>
        <bing />
        <precision> double </precision>
        ...
      </features>
    </simulation>


.. _ArgumentsElement:

Arguments Element
-----------------

The ``<arguments>`` element is optional, and allows defining variables that can be passed to the simulation at run time. These variables are then globally accessible throughout the simulation script. Each of the variables must be defined in an ``<argument>`` element (see below). The variables can then be passed to the simulation executable as options on the command line. For example, one could define the variables ``size``, ``number``, and ``pulse_shape`` ::

    <name> arguments_test </name>
    <features>
      <arguments>
        <argument name="size" type="real" default_value="20.0"/>
        <argument name="number" type="integer" default_value="7"/>
        <argument name="pulse_shape" type="string" default_value="gaussian"/>
      </arguments>
    </features>

When ``XMDS2`` is run on this script the executable ``arguments_test`` is created. The values of ``size``, ``number``, and ``pulse_shape`` can then be set to whatever is desired at runtime via

::

  ./arguments_test --size=1.3 --number=2 --pulse_shape=lorentzian

It is also possible to include an optional ``CDATA`` block inside the ``<arguments>`` block. This code will run after the arguments have been initialised with the values passed from the command line. This code block could be used, for example, to sanity check the parameters passed in, or for assigning values to global variables based on those parameters. For example, one could have the following ::

    <features>
      <globals>
        <![CDATA[
          real atom_kick;
        ]]>
      <globals>
      <arguments>
        <argument name="bragg_order" type="integer" default_value="2"/>
        <![CDATA[
          atom_kick = bragg_order * 2*M_PI / 780e-9;
        ]]>
      </arguments>
    </features>


.. _ArgumentElement:

Argument element
~~~~~~~~~~~~~~~~


Each ``<argument>`` element describes one variable that can be passed to the simulation at runtime via the command line. There are three mandatory attributes: ``name``, ``type``, and ``default_value``. ``name`` is the name by which you can refer to that variable later in the script, as well as the name of the command line parameter. ``type`` defines the data type of the variable, and ``default_value`` is the value to which the variable is set if it is not given a value on the command line.


.. _AutoVectorise:

Auto_vectorise element
----------------------

The ``<auto_vectorise />`` feature attempts to activate automatic vectorisation for large loops, if it is available in the compiler.  This should make some simulations go faster.


.. _Benchmark:

Benchmark
---------

The ``<benchmark />`` feature includes a timing routine in the generated code, so that it is possible to see how long the simulations take to run.


.. _Bing:

Bing
----

The ``<bing />`` feature causes the simulation to make an invigorating sound when the simulation finishes executing.


.. _CFlags:

C Flags
-------

The ``<cflags>`` feature allows extra flags to be passed to the compiler.  This can be useful for optimisation, and also using specific external libraries.  The extra options to be passed are defined with a 'CDATA' block.  The compile options can be made visible by running XMDS2 either with the "-v" (verbose) option, or the "-g" (debug) option.

Example syntax::

    <cflags>
        <![CDATA[
            -O4
        ]]>
    </cflags>



.. _Diagnostics:

Diagnostics
-----------

The ``<diagnostics />`` feature causes a simulation to output more information as it executes.  This should be useful when a simulation is dying / giving bad results to help diagnose the cause.  Currently, it largely outputs step error information.



.. _ErrorCheck:

Error Check
-----------


It's often important to know whether you've got errors.  This feature runs each integration twice: once with the specified error tolerance or defined lattice spacing in the propagation dimension, and then again with half the lattice spacing, or an equivalently lower error tolerance.  Each component of the output then shows the difference between these two integrations as an estimate of the error.  This feature is particularly useful when integrating stochastic equations, as it treats the noise generation correctly between the two runs, and thus makes a reasonable estimate of the strong convergence of the equations.

Example syntax::

    <simulation xmds-version="2">
        <features>
            <error_check />
        </features>
    </simulation>


.. _HaltNonFinite:

Halt_Non_Finite
---------------

The ``<halt_non_finite />`` feature is used to stop computations from continuing to run after the vectors stop having numerical values.  This can occur when a number is too large to represent numerically, or when an illegal operation occurs.  Processing variables with non-numerical values is usually much slower than normal processing, and the results are meaningless.  Of course, there is a small cost to introducing a run-time check, so this feature is optional.


.. _FFTW:

fftw element
------------

The ``<fftw \>`` feature can be used to pass options to the `Fast Fourier Transform library <http://fftw.org>`_ used by XMDS.  This library tests algorithms on each architecture to determine the fastest method of solving each problem.  Typically this costs very little overhead, as the results of all previous tests are stored in the directory "~/.xmds/wisdom".  The level of detail for the search can be specified using the ``plan`` attribute, which can take values of ``"estimate"``, ``"measure"``,``"patient"``, or ``"exhaustive"``, in order of the depth of the search.  The number of threads for threaded FFTs can be specified with the ``threads`` attribute, which must be a positive integer.

Example syntax::

    <fftw plan="patient" threads="3" />


.. _Globals:

Globals
-------

The globals feature places the contents of a 'CDATA' block near the top of the generated program.  Amongst other things, this is useful for defining variables that are then accessible throughout the entire program.

Example syntax::

    <globals>
      <![CDATA[
        const real omegaz = 2*M_PI*20;
        long Nparticles = 50000;

        /* offset constants */
        real frequency = omegaz/2/M_PI;
      ]]>
    </globals>


.. _OpenMP:

OpenMP
------

The ``<openmp />`` feature instructs compatible compilers to parallelise key loops using the `OpenMP API <http://www.openmp.org>`_ standard. 


.. _Precision:

Precision
-----------

This specifies the precision of the XMDS2 ``real`` and ``complex`` datatypes, as well as the precision used when computing transforms. Currently two values are accepted: ``single`` and ``double``. If this feature isn't specified, XMDS2 defaults to using double precision for its variables and internal calculations.

Single precision has approximately 7.2 decimal digits of accuracy, with a minimum value of 1.4×10\ :superscript:`-45` and a maximum of 3.8×10\ :superscript:`34`. Double precision has approximately 16 decimal digits of accuracy, a minimum value of 4.9×10\ :superscript:`-324` and a maximum value of 1.8×10\ :superscript:`308`.

Using single precision can be attractive, as it can be more than twice as fast, depending on whether a simulation is CPU bound, memory bandwidth bound, MPI bound or bottlenecked elsewhere, although in some situations you may see no speed-up at all. Caution should be exercised, however. Keep in mind how many timesteps your simulation requires, and take note of the tolerance you have set per step, to see if the result will lie within your acceptable total error - seven digit precision isn't a lot. Quite apart from the precision, the range of single precision can often be inadequate for many physical problems. In atomic physics, for example, intermediate values below 1.4×10\ :superscript:`-45` are easily obtained, and will be taken as zero. Similarly, values above 3.8×10\ :superscript:`34` will result in NaNs and make the simulation results invalid.

Also note that when using an adaptive step integrator, setting a tolerance close to limits of the precision can lead to very slow performance.

A further limitation is that not all the combinations of random number generators and probability distributions that are supported in double precision are supported in single precision. For example, the ``solirte`` generator does not support single precision gaussian distributions. ``dsfmt``, however, is one of the fastest generators, and does support single precision.

WARNING: Single precision mode has not been tested anywhere near as thoroughly as the default double precision mode, and there is a higher chance you will run into bugs.

Example syntax::

    <simulation xmds-version="2">
        <features>
            <precision> single </precision>
        </features>
    </simulation>


.. _Validation:

Validation
----------

XMDS makes a large number of checks in the code generation process to verify that the values for all parameters are safe choices.  Sometimes we wish to allow these parameters to be specified by variables.  This opens up many possibilities, but requires that any safety checks for parameters be performed during the execution of the program itself.  The ``<validation>`` feature activates that option, with allowable attributes being "run-time", "compile-time" and "none".

Example syntax::

    <simulation xmds-version="2">
        <features>
            <validation kind="run-time" />
        </features>
    </simulation>



.. _DriverElement:

Driver Element
==============

The driver element controls the overall management of the simulation, including how many paths of a stochastic simulation are to be averaged, and whether or not it is to be run using distributed memory parallelisation.  If it is not included, then the simulation is performed once without using MPI parallelisation.  If it is included, it must have a ``name`` attribute.

The ``name`` attribute can have values of "none" (which is equivalent to the default option of not specifying a driver), "distributed-mpi", "multi-path" or "mpi-multi-path".

Choosing the ``name="distributed-mpi"`` option allows a single integration over multiple processors.  The resulting executable can then be run according to your particular implementation of MPI.  The FFTW library only allows MPI processing of multidimensional vectors, as otherwise shared memory parallel processing requires too much inter-process communication to be efficient.  As noted in the worked example :ref:`WignerArguments`, it is wise to test the speed of the simulation using different numbers of processors.

The ``name="multi-path"`` option is used for stochastic simulations, which are typically run multiple times and averaged.  It requires a ``paths`` attribute with the number of iterations of the integration to be averaged.  The output will report the averages of the desired samples, and the standard error in those averages.  
The ``name="mpi-multi-path"`` option integrates separate paths on different processors, which is typically a highly efficient process.

Example syntax::

    <simulation xmds-version="2">
        <driver name="distributed-mpi" />
            <!-- or -->
        <driver name="multi-path" paths="10" />
            <!-- or -->
        <driver name="mpi-multi-path" paths="1000" />
    </simulation>

.. _GeometryElement:

Geometry Element
================

.. _PropagationDimensionElement:

The ``<geometry>`` element describes the dimensions used in your simulation, and is required.  The only required element inside is the ``<propagation_dimension>`` element, which defines the name of the dimension along which your simulation will integrate.  Nothing else about this dimension is specified, as requirements for the lattice along the integration dimension is specified by the ``<integrate>`` blocks themselves, as described in section :ref:`IntegrateElement`.

.. _TransverseDimensionsElement:

.. _DimensionElement:

If there are other dimensions in your problem, they are called "transverse dimensions", and are described in the ``<transverse_dimensions>`` element.  Each dimension is then described in its own ``<dimension>`` element.  A transverse dimension must have a unique name defined by a ``name`` attribute.  If it is not specified, the type of dimension will default to "real", otherwise it can be specified with the ``type`` attribute.  Allowable types (other than "real") are "long", "int", and "integer", which are actually all synonyms for an integer-valued dimension.

Each transverse dimension must specify how many points or modes it requires, and the range over which it is defined.  This is done by the ``lattice`` and ``domain`` attributes respectively.  The ``lattice`` attribute is an integer, and is optional for integer dimensions, where it can be defined implicitly by the domain.  The ``domain`` attribute is specified as a pair of numbers (e.g. ``domain="(-17,3)"``) defining the minimum and maximum of the grid.

Any dimension can have a number of aliases.  These act exactly like copies of that dimension, but must be included explicitly in the definition of subsequent vectors (i.e. they are not included in the default list of dimensions for a new vector).  The list of aliases for a dimension are included in an ``aliases`` attribute.  They are useful for non-local reference of variables.  See ``groundstate_gaussian.xmds`` and ``2DMultistateSE.xmds`` as examples.

Integrals over a dimension can be multiplied by a common prefactor, which is specified using the ``volume_prefactor`` attribute.  For example, this allows the automatic inclusion of a factor of two due to a reflection symmetry by adding the attribute ``volume_prefactor="2"``.

.. _Transforms:

Each transverse dimension can be associated with a transform.  This allows the simulation to manipulate vectors defined on that dimension in the transform space.  The default is Fourier space (with the associated transform being the discrete Fourier transform, or "dft"), but others can be specified with the ``transform`` attribute.  The other options are "none", "dst", "dct", "bessel", "spherical-bessel" and "hermite-gauss".  Using the right transform can dramatically improve the speed of a calculation.

An advanced feature discussed further in :ref:`DimensionAliases` are dimension aliases, which are specified by the ``aliases`` attribute.  This feature is useful for example, when calculating correlation functions.

Example syntax::

    <simulation xmds-version="2">
        <geometry>
            <propagation_dimension> t </propagation_dimension>
            <transverse_dimensions>
                <!-- A real-valued dimension from -1.5 to 1.5 -->
                <dimension name="x" lattice="128" domain="(-1.5, 1.5)" />
                
                <!-- An integer-valued dimension with the 6 values -2, -1, 0, 1, 2, 3 -->
                <dimension name="j"               domain="(-2,3)" type="integer" />
                
                <!-- A real-valued dimension using the bessel transform for a radial coordinate -->
                <dimension name="r" lattice="64" domain="(0, 5)"  transform="bessel" volume_prefactor="2.0*M_PI" />
            </transverse_dimensions>
        </geometry>
    </simulation>


.. _dft_Transform:

The "dft" transform
-------------------

The "dft" transform is performed using the the normal discrete Fourier transform, which means that it enforces periodic boundary conditions on vectors defined on that dimension.  Another implication is that it can only be used with complex-valued vectors.  The discrete Fourier transform is almost exactly the same as a standard Fourier transform.  The standard Fourier transform is

.. math::

    \mathcal{F}\left[f(x)\right](k) = \frac{1}{2\pi}\int_{x_\text{min}}^{x_\text{max}} f(x) e^{-i k x} dx

The discrete Fourier transform has no information about the domain of the lattice, so the XMDS2 transform is equivalent to

.. math::
    \tilde{\mathcal{F}}\left[f(x)\right](k) &= \frac{1}{2\pi}\int_{x_\text{min}}^{x_\text{max}} f(x) e^{-i k (x+ x_\text{min})} dx \\
    &= e^{-i x_\text{min} k} \mathcal{F}\left[f(x)\right](k)

The standard usage in an XMDS simulation involves moving to Fourier space, applying a transformation, and then moving back.  For this purpose, the two transformations are entirely equivalent as the extra phase factor cancels.  However, when fields are explicitly defined in Fourier space, care must be taken to include this phase factor explicitly.  See section :ref:`Convolutions` in the Advanced Topics section.

When a dimension uses the "dft" transform, then the Fourier space variable is defined as the name of the dimension prefixed with a "k".  For example, the dimensions "x", "y", "z" and "tau" will be referenced in Fourier space as "kx","ky", "kz" and "ktau".  

Fourier transforms allow easy calculation of derivatives, as the n\ :sup:`th` derivative of a field is proportional to the n\ :sup:`th` moment of the field in Fourier space:

.. math::
    \mathcal{F}\left[\frac{\partial^n f(x)}{\partial x^n}\right](k_x) = \left(i \;k_x\right)^n \mathcal{F}\left[f(x)\right](k_x)

This identity can be used to write the differential operator :math:`\mathcal{L} = \frac{\partial}{\partial x}` as an ``IP`` or ``EX`` operator as ``L = i*kx;`` (see :ref:`OperatorsElement` for more details).

Example syntax::

    <simulation xmds-version="2">
        <geometry>
            <propagation_dimension> t </propagation_dimension>
            <transverse_dimensions>
                <!-- transform="dft" is the default, omitting it wouldn't change anything -->
                <dimension name="x" lattice="128" domain="(-1.5, 1.5)" transform="dft" />
            </transverse_dimensions>
        </geometry>
    </simulation>


The "dct" transform
-------------------

The "dct" (discrete cosine transform) is a Fourier-based transform that implies different boundary conditions for associated vectors.  XMDS uses the type-II DCT, often called "the DCT", and its inverse, which is also called the type-III DCT.  This transform assumes that any vector using this dimension is both periodic, and also even around a specific point within each period.  The grid is therefore only defined across a half period in order to sample each unique point once, and can therefore be of any shape where all the odd derivatives are zero at each boundary.  This is a very different boundary condition compared to the DFT, which demands periodic boundary conditions, and is therefore suitable for different simulations.  For example, the DCT is a natural choice when implementing zero Neumann boundary conditions.

As the DCT transform can be defined on real data rather only complex data, it can also be superior to DFT-based spectral methods for simulations of real-valued fields where boundary conditions are artificial.

XMDS labels the cosine transform space variables the same as for :ref:`Fourier transforms<dft_Transform>` and all the even derivatives can be calculated the same way.  Odd moments of the cosine-space variables are in fact *not* related to the corresponding odd derivatives by an inverse cosine transform.

Discrete cosine transforms allow easy calculation of even-order derivatives, as the 2n\ :sup:`th` derivative of a field is proportional to the 2n\ :sup:`th` moment of the field in DCT-space:

.. math::
    \mathcal{F}_\text{DCT}\left[\frac{\partial^{2n} f(x)}{\partial x^{2n}}\right](k_x) = (-k_x^2)^{n}\; \mathcal{F}_\text{DCT}\left[f(x)\right](k_x)

This identity can be used to write the differential operator :math:`\mathcal{L} = \frac{\partial^2}{\partial x^2}` as an ``IP`` or ``EX`` operator as ``L = -kx*kx;`` (see :ref:`OperatorsElement` for more details).

For problems where you are defining the simulation domain over only half of the physical domain to take advantage of reflection symmetry, consider using ``volume_prefactor="2.0"`` so that all volume integrals are over the entire physical domain, not just the simulation domain. i.e. integrals would be over -1 to 1 instead of 0 to 1 if the domain was specified as ``domain="(0,1)"``.


Example syntax::

    <simulation xmds-version="2">
        <geometry>
            <propagation_dimension> t </propagation_dimension>
            <transverse_dimensions>
                <dimension name="x" lattice="128" domain="(-1.5, 1.5)" transform="dct" />
                    <!-- Or to cause volume integrals to be multiplied by 2 -->
                <dimension name="y" lattice="128" domain="(0, 1)" transform="dct" volume_prefactor="2.0" />
            </transverse_dimensions>
        </geometry>
    </simulation>


The "dst" transform
-------------------

The "dst" (discrete sine transform) is a counterpart to the DCT transform.  XMDS uses the type-II DST and its inverse, which is also called the type-III DST.  This transform assumes that fields are periodic in this dimension, but also that they are also odd around a specific point within each period.  The grid is therefore only defined across a half period in order to sample each unique point once, and can therefore be of any shape where all the even derivatives are zero at each boundary.  

The DST transform can be defined on real-valued vectors.  As odd-valued functions are zero at the boundaries, this is a natural transform to use when implementing zero Dirichlet boundary conditions.

XMDS labels the sine transform space variables the same as for :ref:`Fourier transforms<dft_Transform>` and all the even derivatives can be calculated the same way.  Odd moments of the sine-space variables are in fact *not* related to the corresponding odd derivatives by an inverse sine transform.

Discrete sine transforms allow easy calculation of even-order derivatives, as the 2n\ :sup:`th` derivative of a field is proportional to the 2n\ :sup:`th` moment of the field in DST-space:

.. math::
    \mathcal{F}_\text{DST}\left[\frac{\partial^{2n} f(x)}{\partial x^{2n}}\right](k_x) = (-k_x^2)^{n}\; \mathcal{F}_\text{DST}\left[f(x)\right](k_x)

This identity can be used to write the differential operator :math:`\mathcal{L} = \frac{\partial^2}{\partial x^2}` as an ``IP`` or ``EX`` operator as ``L = -kx*kx;`` (see :ref:`OperatorsElement` for more details).


Example syntax::

    <simulation xmds-version="2">
        <geometry>
            <propagation_dimension> t </propagation_dimension>
            <transverse_dimensions>
                <dimension name="x" lattice="128" domain="(0, 1.5)" transform="dst" />
            </transverse_dimensions>
        </geometry>
    </simulation>


The "bessel" transform
----------------------

Just as the Fourier basis is useful for finding derivatives in Euclidean geometry, the basis of Bessel functions is useful for finding certain common operators in cylindrical co-ordinates.  In particular, we use the Bessel functions of the first kind, :math:`J_m(u)`.  The relevant transform is the Hankel transform:

.. math::
    F_m(k) = \mathcal{H}_m \left[f\right](k) = \int_0^\infty r f(r) J_m(k r) dr
    
which has the inverse transform:

.. math::
    f(r) = \mathcal{H}^{-1}_m \left[F_m\right](r) = \int_0^\infty k F_m(k) J_m(k r) dk
    
This transform pair has the useful property that the Laplacian in cylindrical co-ordinates is diagonal in this basis:

.. math::
    \nabla^2 \left(f(r) e^{i m \theta}\right) &= \left(\frac{\partial^2 f}{\partial r^2} +\frac{1}{r}\frac{\partial f}{\partial r} -\frac{m^2}{r^2} f \right) e^{i m \theta} = \left\{\mathcal{H}^{-1}_m \left[(-k^2) F_m(k)\right](r) \right\} e^{i m \theta}
    
XMDS labels the variables in the transformed space with a prefix of 'k', just as for :ref:`Fourier transforms<dft_Transform>`.  The order :math:`m` of the transform is defined by the ``order`` attribute in the ``<dimension>`` element, which must be assigned as a non-negative integer.  If the order is not specified, it defaults to zero which corresponds to the solution being independent of the angular coordinate :math:`\theta`.  

It can often be useful to have a different sampling in normal space and Hankel space.  Reducing the number of modes in either space dramatically speeds simulations.  To set the number of lattice points in Hankel space to be different to the number of lattice points for the field in its original space, use the attribute ``spectral_lattice``.  The Bessel space lattice is chosen such that the boundary condition at the edge of the domain is zero.  This ensures that all of the Bessel modes are orthogonal.  The spatial lattice is also chosen in a non-uniform manner so that Gaussian quadrature methods can be usedfor spectrally accurate transforms.

Hankel transforms allow easy calculation of the Laplacian of fields with cylindrical symmetry.  Applying the operator ``L = -kr*kr`` in Hankel space is therefore equivalent to applying the operator

.. math::
    \mathcal{L} = \left(\frac{\partial^2}{\partial r^2} +\frac{1}{r}\frac{\partial}{\partial r} -\frac{m^2}{r^2} \right)
    
in coordinate space.

In non-Euclidean co-ordinates, integrals have non-unit volume elements.  For example, in cylindrical co-ordinates with a radial co-ordinate 'r', integrals over this dimension have a volume element :math:`r dr`.  When performing integrals along a dimension specified by the "bessel" transform, the factor of the radius is included implicitly.  If you are using a geometry with some symmetry, it is common to have prefactors in your integration.  For example, for a two-dimensional volume in cylindrical symmetry, all integrals would have a volume element of :math:`2\pi r dr`.  This extra factor of :math:`2 \pi` can be included for all integrals by specifying the attribute ``volume_prefactor="2*M_PI"``.  See the example ``bessel_cosine_groundstate.xmds`` for a demonstration.

Example syntax::

    <simulation xmds-version="2">
        <geometry>
            <propagation_dimension> t </propagation_dimension>
            <transverse_dimensions>
                <dimension name="r" lattice="128" domain="(0, 3)" transform="bessel" volume_prefactor="2*M_PI" />
            </transverse_dimensions>
        </geometry>
    </simulation>



The "spherical-bessel" transform
--------------------------------

When working in spherical coordinates, it is often useful to use the spherical Bessel functions :math:`j_l(x)=\sqrt{\frac{\pi}{2x}}J_{l+\frac{1}{2}}(x)` as a basis.  These are eigenfunctions of the radial component of Laplace's equation in spherical coordinates:

.. math::
    \nabla^2 \left[j_l(k r)\; Y^m_l(\theta, \phi)\right] &= \left[\frac{\partial^2 }{\partial r^2} +\frac{2}{r}\frac{\partial }{\partial r} -\frac{l(l+1)}{r^2}\right] j_l(k r) \; Y^m_l(\theta, \phi) = -k^2 j_l(k r)\; Y^m_l(\theta, \phi)

Just as the Bessel basis above, the transformed dimensions are prefixed with a 'k', and it is possible (and usually wise) to use the ``spectral_lattice`` attribute to specify a different lattice size in the transformed space.  Also, the spacing of these lattices are again chosen in a non-uniform manner to Gaussian quadrature methods for spectrally accurate transforms.  Finally, the ``order`` attribute can be used to specify the order :math:`l` of the spherical Bessel functions used.  

If we denote the transformation to and from this basis by :math:`\mathcal{SH}`, then we can write the useful property:

.. math::
    \frac{\partial^2 f}{\partial r^2} +\frac{2}{r}\frac{\partial f}{\partial r} -\frac{l (l+1)}{r^2} = \mathcal{SH}^{-1}_l \left[(-k^2) F_l(k)\right](r)

Spherical Bessel transforms allow easy calculation of the Laplacian of fields with spherical symmetry. Applying the operator ``L = -kr*kr`` in Spherical Bessel space is therefore equivalent to applying the operator

.. math::
    \mathcal{L} = \left( \frac{\partial^2}{\partial r^2} +\frac{2}{r}\frac{\partial}{\partial r} -\frac{l (l+1)}{r^2} \right)
    
in coordinate space.  

In non-Euclidean co-ordinates, integrals have non-unit volume elements.  For example, in spherical co-ordinates with a radial co-ordinate 'r', integrals over this dimension have a volume element :math:`r^2 dr`.  When performing integrals along a dimension specified by the "spherical-bessel" transform, the factor of the square of the radius is included implicitly.  If you are using a geometry with some symmetry, it is common to have prefactors in your integration.  For example, for a three-dimensional volume in spherical symmetry, all integrals would have a volume element of :math:`4\pi r^2 dr`.  This extra factor of :math:`4 \pi` can be included for all integrals by specifying the attribute ``volume_prefactor="4*M_PI"``.  This is demonstrated in the example bessel_transform.xmds.

Example syntax::

    <simulation xmds-version="2">
        <geometry>
            <propagation_dimension> t </propagation_dimension>
            <transverse_dimensions>
                <dimension name="r" lattice="128" domain="(0, 3)" transform="spherical-bessel" volume_prefactor="4*M_PI" />
            </transverse_dimensions>
        </geometry>
    </simulation>



The "hermite-gauss" transform
-----------------------------

The "hermite-gauss" transform allows transformations to and from the basis of Hermite functions :math:`\psi_n(x)`:

.. math::
    \psi_n(x) = \left(2^n n! \sigma \sqrt{\pi}\right)^{-1/2} e^{-x^2/2\sigma^2} H_n(\sigma x)
    
where the functions :math:`H_n(x)` are the Hermite polynomials:

.. math::
    H_n(x) &= (-1)^n e^{x^2} \frac{d^n}{dx^n} \left(e^{-x^2}\right)
    
which are eigenfunctions of the Schroedinger equation for a harmonic oscillator:

.. math::
    - \frac{\hbar^2}{2 m} \frac{\partial^2 \psi_n}{\partial x^2} + \frac{1}{2} m \omega^2 x^2 \psi_n(x) = \hbar \omega\left(n+\frac{1}{2}\right) \psi_n(x),

with :math:`\sigma = \sqrt{\frac{\hbar}{m \omega}}`.
    
This transform is different to the others in that it requires a ``length_scale`` attribute rather than a ``domain`` attribute, as the range of the lattice will depend on the number of basis functions used. The ``length_scale`` attribute defines the scale of the domain as the standard deviation :math:`\sigma` of the lowest order Hermite function :math:`\psi_0(x)`:

.. math::
    \psi_0(x) = (\sigma^2 \pi)^{-1/4} e^{-x^2/2 \sigma^2}

When a dimension uses the "hermite-gauss" transform, then the variable indexing the basis functions is defined as the name of the dimension prefixed with an "n".  For example, when referencing the basis function indices for the dimensions "x", "y", "z" and "tau", use the variable "nx", "ny", "nz" and "ntau".  

Applying the operator ``L = nx + 0.5`` in Hermite space is therefore equivalent to applying the operator

.. math::
   \mathcal{L} = \left(- \frac{\sigma^2}{2}\frac{\partial^2}{\partial x^2} + \frac{1}{2 \sigma^2} x^2 \right)
    
in coordinate space.  

The Hermite-Gauss transform permits one to work in energy-space for the harmonic oscillator.  The normal Fourier transform of "hermite-gauss" dimensions can also be referenced using the dimension name prefixed with a "k".  See the examples ``hermitegauss_transform.xmds`` and ``hermitegauss_groundstate.xmds`` for examples.


Example syntax::

    <simulation xmds-version="2">
        <geometry>
            <propagation_dimension> t </propagation_dimension>
            <transverse_dimensions>
                <dimension name="r" lattice="128" length_scale="1.0" transform="hermite-gauss" />
            </transverse_dimensions>
        </geometry>
    </simulation>




.. _VectorElement:

Vector Element
==============

Vectors are arrays of data, defined over any subset of the transverse dimensions defined in your :ref:`GeometryElement`.  These dimensions are listed in the attribute ``dimensions``, which can be an empty string if you wish the vector to not be defined on any dimensions.  If you do not include a ``dimensions`` attribute then the vector defaults to being a function of all transverse dimensions, not including any aliases.  Vectors are used to store static or dynamic variables, but you do not have to specify their purpose when they are defined.  They can then be referenced and/or changed by sequence elements, as described below.

Each ``<vector>`` element has a unique name, defined by a ``name`` attribute.  It is either complex-valued (the default) or real-valued, which can be specified using the ``type="real"`` attribute.

.. _ComponentsElement:

A vector contains a list of variables, each defined by name in the ``<components>`` element.  The name of each component is the name used to reference it later in the simulation.

Vectors are initialised at the beginning of a simulation, either from code or from an input file.  The basis choice for this initialisation defaults to the normal space as defined in the ``<geometry>`` element, but any transverse dimension can be initialised in their transform basis by specifying them in an ``initial_basis`` attribute.  The ``initial_basis`` attribute lists dimensions either by their name as defined by the ``<geometry>`` element, or by their transformed name.  For example, to initialise a two-dimensional vector defined with ``dimensions="x y"`` in Fourier space for the y-dimension, we would include the attribute ``initial_basis="x ky"``, or just ``initial_basis="ky"``.  

.. _InitialisationElement:

When initialising the vector within the XMDS script, the appropriate code is placed in a 'CDATA' block inside an ``<initialisation>`` element.  This code is in standard C-syntax, and should reference the components of the vector by name.  XMDS defines a few useful :ref:`shorthand macros<XMDSCSyntax>` for this C-code.  If you wish to initialise all the components of the vector as zeros, then it suffices simply to add the attribute ``kind="zero"`` or to omit the ``<initialisation>`` element entirely.  
    
.. _ReferencingNonlocal:

While the default XMDS behaviour is to reference all variables locally, any vector can be referenced non-locally.  The notation for referencing the value of a vector 'phi' with a dimension 'j' at a value of 'j=jk' is ``phi(j => jk)``.  Multiple non-local dimensions are addressed by adding the references in a list, e.g. ``phi(j => jk, x => y)``.  See ``2DMultistateSE.xmds`` for an example.

.. _FilenameElement:

If you wish to initialise from a file, then you can choose to initialise from an hdf5 file using ``kind="hdf5"`` in the ``<initialisation>`` element, and then supply the name of the input file with the ``filename`` element.  This is a standard data format which can be generated from XMDS, or from another program.  An example for generating a file in another program for input into XMDS is detailed in the Advanced topic: :ref:`Importing`.

When initialising from a file, the default is to require the lattice of the transverse dimensions to exactly match the lattice defined by XMDS.  There is an option to import data defined on a subset or superset of the lattice points.  Obviously, the dimensionality of the imported field still has to be correct.  This option is activated by defining the attribute ``geometry_matching_mode="loose"``.  The default option is defined as ``geometry_matching_mode="strict"``.  A requirement of the initialisation geometry is that the lattice points of the input file are spaced identically to those of the simulation grid.  This allows expanding or contracting a domain between simulations.  If used in Fourier space, this feature can be used for coarsening or refining a simulation grid.  See :ref:`LooseGeometryMatchingMode` for details.

Example syntax::

    <simulation xmds-version="2">
        <geometry>
            <propagation_dimension> t </propagation_dimension>
            <transverse_dimensions>
                <dimension name="x" lattice="128" domain="(-1, 1)" />
            </transverse_dimensions>
        </geometry>
    
        <!-- A one-dimensional vector with dimension 'x' -->
        <vector name="wavefunction" initial_basis="x" type="complex">
            <components> phi </components>
            <initialisation>
                <![CDATA[
                    // 'cis(x)' is cos(x) + i * sin(x)
                    phi = exp(-0.5 * x * x) * cis(40 * x);
                ]]>
            </initialisation>
        </vector>
        
        <!-- A zero-dimensional real vector with components u and v -->
        <vector name="zero_dim" dimensions="" type="real">
            <components>
                u v
            </components>
            <initialisation kind="hdf5">
                <filename>data.h5</filename>
            </initialisation>
        </vector>
    </simulation>



.. _Dependencies:

The dependencies element
------------------------

Often a vector, computed vector, filter, integration operator or output group will reference the values in one or more other vectors, computed vectors or noise vectors.  These dependencies are defined via a ``<dependencies>`` element, which lists the names of the vectors.  The components of those vectors will then be available for use in the 'CDATA' block, and can be referenced by their name.  

For a vector, the basis of the dependent vectors, and therefore the basis of the dimensions available in the 'CDATA' block, are defined by the ``initial_basis`` of the vector.  For a ``<computed_vector>``, ``<filter>`` ``<integration_vector>``, or moment group vector, the basis of the dependencies can be specified by a ``basis`` attribute in the ``<dependencies>`` element.  For example, ``basis="x ny kz"``.

Any transverse dimensions that appear in the ``<dependencies>`` element that do not appear in the ``dimensions`` attribute of the vector are integrated out.  For integer dimensions, this is simply an implicit sum over the dimension.  For real-valued dimensions, this is an implicit integral over the range of that dimension.

Example syntax::

    <simulation xmds-version="2">
        <geometry>
            <propagation_dimension> t </propagation_dimension>
            <transverse_dimensions>
                <dimension name="x" lattice="128" domain="(-1, 1)" />
                <dimension name="y" lattice="10" domain="(-3, 2)" transform="dct" />
            </transverse_dimensions>
        </geometry>
    
        <!-- A one-dimensional vector with dimension 'x' -->
        <vector name="wavefunction" dimensions="x" initial_basis="x" type="complex">
            <components> phi </components>
            <initialisation>
                <!-- 
                    The initialisation of the vector 'wavefunction' depends on information
                    in the 'two_dim' vector.  The vector two_dim is DCT-transformed into the
                    (x, ky) basis, and the ky dimension is implicitly integrated over in the
                    following initialisation code
                  -->
                <dependencies basis="x ky">two_dim</dependencies>
                <![CDATA[
                    // 'cis(x)' is cos(x) + i * sin(x)
                    phi = exp(-0.5 * x * x + v) * cis(u * x);
                ]]>
            </initialisation>
        </vector>
        
        <!-- A two-dimensional real vector with components u and v -->
        <vector name="two_dim" type="real">
            <components>
                u v
            </components>
            <initialisation kind="hdf5">
                <filename>data.h5</filename>
            </initialisation>
        </vector>
    </simulation>



.. _ComputedVectorElement:

Computed Vector Element
=======================

.. _EvaluationElement:

Computed vectors are arrays of data much like normal ``<vector>`` elements, but they are always calculated as they are referenced, so they cannot be initialised from file.  It is defined with a ``<computed_vector>`` element, which has a ``name`` attribute, optional ``dimensions`` and ``type`` attributes, and a ``<components>`` element, just like a ``<vector>`` element.  Instead of an <:ref:`initialisation<InitialisationElement>`> element, it has an ``<evaluation>`` element that serves the same purpose.  The ``<evaluation>`` element contains a ``<dependencies>`` element (see ``above<Dependencies>``), and a 'CDATA' block containing the code that defines it.

As it is not being stored, a ``<computed_vector>`` does not have or require an ``initial_basis`` attribute, as it will be transformed into an appropriate basis for the element that references it.  The basis for its evaluation will be determined entirely by the ``basis`` attribute of the ``<dependencies>`` element.

Example syntax::

    <simulation xmds-version="2">
        <geometry>
            <propagation_dimension> t </propagation_dimension>
            <transverse_dimensions>
                <dimension name="x" lattice="128" domain="(-1, 1)" />
            </transverse_dimensions>
        </geometry>
    
        <!-- A one-dimensional vector with dimension 'x' -->
        <vector name="wavefunction" type="complex">
            <components> phi </components>
            <initialisation>
                <![CDATA[
                    // 'cis(x)' is cos(x) + i * sin(x)
                    phi = exp(-0.5 * x * x) * cis(40 * x);
                ]]>
            </initialisation>
        </vector>
        
        <!-- A zero-dimensional real computed vector with components Ncalc -->
        <computed_vector name="zero_dim" dimensions="" type="real">
            <components>
                Ncalc
            </components>
            <evaluation>
                <dependencies>wavefunction</dependencies>
                <![CDATA[
                    // Implicitly integrating over the dimension 'x'
                    Ncalc = mod2(phi);
                ]]>
            </evaluation>
        </vector>
    </simulation>



.. _NoiseVectorElement:

Noise Vector Element
====================

Noise vectors are used like computed vectors, but when they are evaluated they generate arrays of random numbers of various kinds.  They do not depend on other vectors, and are not initialised by code.  They are defined by a ``<noise_vector>`` element, which has a ``name`` attribute, and optional ``dimensions``, ``initial_basis`` and ``type`` attributes, which work identically as for normal vectors.  

The choice of pseudo-random number generator (RNG) can be specified with the ``method`` attribute, which has options "posix" (the default), "mkl", "solirte" and "dsfmt".  It is only possible to use any particular method if that library is available.

The random number generators can be provided with a seed using the ``seed`` attribute, which should typically consist of a list of three integers.  All RNGs require positive integers as seeds.  It is possible to use the :ref:`<validation kind="run-time"/><Validation>` feature to use passed variables as seeds.  It is advantageous to used fixed seeds rather than timer-based seeds, as the :ref:`<error_check><ErrorCheck>` element can test for strong convergence if the same seeds are used for both integrations.  If the ``seed`` attribute is not specified, then fixed seeds will be generated as the code is generated.

The different types of noise vectors are defined by a mandatory ``kind`` attribute, which must take the value of 'gauss', 'gaussian', 'wiener', 'poissonian','jump' or 'uniform'.  

Example syntax::

    <simulation xmds-version="2">
        <geometry>
            <propagation_dimension> t </propagation_dimension>
            <transverse_dimensions>
                <dimension name="x" lattice="128" domain="(-1, 1)" />
            </transverse_dimensions>
        </geometry>
    
        <!-- 
            A one-dimensional complex wiener noise vector.
            This noise is appropriate for using in the complex
            random-walk equation of motion:
                dz_dt = eta;
        -->
        <noise_vector name="noise" kind="wiener">
            <components>
                eta
            </components>
        </vector>
    </simulation>


.. _uniformNoise:

Uniform noise
-------------

Uniform noises defined over any transverse dimensions are simply uniformly distributed random numbers between zero and one.  This noise is an example of a "static" noise, i.e. one suitable for initial conditions of a field.  If it were included in the equations of motion for a field, then the effect of the noise would depend on the lattice spacing of the propagation dimension.  XMDS therefore does not allow this noise type to be used in integration elements.

Example syntax::

    <simulation xmds-version="2">
        <noise_vector name="drivingNoise" dimensions="x" kind="uniform" type="complex" method="dsfmt" seed="314 159 276">
          <components>Eta</components>
        </noise_vector>
    </simulation>


.. _gaussianNoise:

Gaussian noise
--------------

Noise generated with the "gaussian" method is gaussian distributed with zero mean.  For a real-valued noise vector, the variance at each point is the inverse of the volume element of the transverse dimensions in the vector.  This volume element for a single transverse dimension is that used to perform integrals over that dimension.  For example, it would include a factor of :math:`r^2` for a dimension "r" defined with a ``spherical-bessel`` transform.  It can be non-uniform for dimensions based on non-Fourier transforms, and will include the product of the ``volume_prefactor`` attribute as specified in the :ref:`Geometry<GeometryElement>` element.  The volume element for an integer-type dimension is unity (i.e. where the integral is just an unweighted sum).  The volume element for a ``noise_vector`` with multiple dimensions is simply the product of the volume elements of the individual dimensions.

This lattice-dependent variance is typical in most applications of partial differential equations with stochastic initial conditions, as the physical quantity is the variance of the field over some finite volume, which does not change if the variance at each lattice site varies as described above.

For complex-valued noise vector, the real and imaginary parts of the noise are independent, and each have half the variance of a real-valued noise.  This means that the modulus squared of a complex-valued noise vector has the same variance as a real-valued noise vector at each point.

Gaussian noise vectors are an example of a "static" noise, i.e. one suitable for initial conditions of a field.  If they were included in the equations of motion for a field, then the effect of the noise would depend on the lattice spacing of the propagation dimension.  XMDS therefore does not allow this noise type to be used in integration elements.

Example syntax::

    <simulation xmds-version="2">
        <noise_vector name="initialNoise" dimensions="x" kind="gauss" type="real" method="posix" seed="314 159 276">
          <components>fuzz</components>
        </noise_vector>
    </simulation>


.. _wienerNoise:

Wiener noise
------------

Noise generated with the "wiener" method is gaussian distributed with zero mean and the same variance as the static "gaussian" noise defined above, multiplied by a factor of the lattice step in the propagation dimension.  This means that these noise vectors can be used to define Wiener noises for standard stochastic ordinary or partial differential equations.  Most integrators in XMDS effectively interpret these noises as Stratonovich increments.

As a dynamic noise, a Wiener process is not well-defined except in an ``integrate`` element.

Example syntax::

    <simulation xmds-version="2">
        <noise_vector name="diffusion" dimensions="x" kind="wiener" type="real" method="solirte" seed="314 159 276">
          <components>dW</components>
        </noise_vector>
    </simulation>


.. _poissionianNoise:

Poissonian noise
----------------

A noise vector using the "poissonian" method generates a random variable from a Poissonian distribution.  While the the Poisson distribution is integer-valued, the variable will be cast as a real number.  The rate of the Poissonian distribution is defined by the ``mean`` or ``mean-density`` attributes.  These are are synonyms, and must be defined as positive real numbers.  For Poissonian noises defined over real-valued transverse dimensions, the rate is given by the product of this ``mean-density`` attribute and the volume element at that point, taking into account all transverse dimensions, including their ``volume_prefactor`` attributes.  The result is that the integral over each volume in space is a sample from a Poissonian distribution of that rate.

Poissonian noise vectors are an example of a "static" noise, i.e. one suitable for initial conditions of a field.  If they were included in the equations of motion for a field, then the effect of the noise would depend on the lattice spacing of the propagation dimension.  XMDS therefore does not allow this noise type to be used in integration elements.

Example syntax::

    <simulation xmds-version="2">
        <noise_vector name="initialDistribution" dimensions="x" kind="poissonian" type="real" mean-density="2.7" method="solirte" seed="314 159 276">
          <components>Pdist</components>
        </noise_vector>
    </simulation>


.. _jumpNoise:

Jump noise
----------

A noise vector using the "jump" method is the dynamic version of the poissonian noise method, and must have the ``mean-rate`` attribute specified as a positive real number.  The variable at each point is chosen from a Poissonian distribution with a mean equal to the product of three variables: the ``mean-rate`` attribute; the volume of the element as defined by its transverse dimensions (including their ``volume_prefactor`` attributes); and the step size in the propagation dimension.  Normally defined in the limit where the noise value is zero almost always, with a few occurrences where it is unity, and none of any higher value, this type of noise is commonly used in differential equations with a Poissonian jump process.

It is common to wish to vary the mean rate of a jump process, which means that the ``mean-rate`` attribute must be a variable or a piece of code.  These cannot be verified to be a positive real number at compile time, so they must be used with the :ref:`<validation><Validation>` feature with either the ``kind="none"`` or ``kind="run-time"`` attributes.

As a dynamic noise, a jump process is not well-defined except in an ``integrate`` element.

Example syntax::

    <simulation xmds-version="2">
        <noise_vector name="initialDistribution" dimensions="" kind="jump" type="real" mean-rate="2.7" method="solirte" seed="314 159 276">
          <components>dN</components>
        </noise_vector>
    </simulation>



.. _SequenceElement:

Sequence Element
================

All processing of vectors happens in sequence elements.  Each simulation must have exactly one main sequence element, but it can then contain any number of nested sequence elements.  A sequence element can contain any number of ``<sequence>``, :ref:`<filter><FilterElement>`, :ref:`<integrate><IntegrateElement>` and/or :ref:`<breakpoint><BreakpointElement>` elements, which are executed in the order they are written.  A sequence can be repeated a number of times by using the ``cycles`` attribute.  For example, ``<sequence cycles="10">`` will execute the elements in that sequence 10 times.
    
Example syntax::

    <simulation xmds-version="2">
        <sequence cycles="2">
            <sequence>  ... </sequence>
            <filter> ... </filter>
            <integrate> ...</integrate>
        </sequence>
    </simulation>    

.. _FilterElement:

Filter element
==============

A ``<filter>`` element can be placed inside a ``<sequence>`` element or an :ref:`<integrate><IntegrateElement>` element.  It contains a 'CDATA' block and an optional :ref:`<dependencies><Dependencies>` element, which may give access to variables in other ``<vector>``, ``<computed_vector>`` or ``<noise_vector>`` elements.  The code inside the 'CDATA' block is executed over the combined tensor product space of the dependencies, or simply once if there is no dependencies element.  This element therefore allows arbitrary execution of C-code.
    
One of the common uses of a filter element is to apply discontinuous changes to the vectors and variables of the simulation.

Example syntax::

    <sequence>
        <filter>
           <dependencies>normalisation wavefunction</dependencies>
           <![CDATA[
             phi *= sqrt(Nparticles/Ncalc);
           ]]>
        </filter>
    </sequence>


.. _IntegrateElement:

Integrate element
=================

The ``<integrate>`` element is at the heart of most XMDS simulations.  It is used to integrate a set of (potentially stochastic) first-order differential equations for one or more of the vectors defined using the ``<vector>`` element along the propagation dimension.  At the beginning of the simulation, the value of the propagation dimension is set to zero, and the vectors are initialised as defined in the :ref:`<vector><VectorElement>` element.  As successive sequence elements change these variables, each integrate element simply integrates onward from the current values.
    
The length of the integration is defined by the ``interval`` attribute, which must be a positive real number.  An ``<integrate>`` element must have an ``algorithm`` attribute defined, which defines the integration method.  Current methods include :ref:`SI <SI>`, :ref:`SIC <SI>`, :ref:`RK4 <RK4>`, :ref:`RK9 <RK4>`, :ref:`ARK45 <ARK45>`, and :ref:`ARK89 <ARK45>`.  Fixed step algorithms require a ``steps`` attribute, which must be a positive integer that defines the number of (evenly spaced) integration steps.  Adaptive stepsize algorithms require a ``tolerance`` attribute that must be a positive real number much smaller than one, which defines the allowable relative error per integration step.  If the ``steps`` attribute is specified for an adaptive stepsize algorithm, then it is used to generate the initial stepsize estimate.

.. _SamplesElement:

The optional ``<samples>`` element is used to track the evolution of one or more vectors or variables during an integration.  This element must contain a non-negative integer for each :ref:`<group><GroupElement>` element defined in the simulation's :ref:`<output><OutputElement>` element.  The list of integers then defines the number of times that the moments defined in those groups will be sampled.  For a fixed step algorithm, each non-zero number of samples must be a factor of the total number of steps. 
    
The vectors to be integrated and the form of the differential equations are defined in the :ref:`<operators><OperatorsElement>` element (or elements).  Filters to be applied each step can be defined with optional :ref:`<filters><FiltersElement>` elements.  
    
Computed vectors can be defined with the ``<computed_vector>`` element.  These act exactly like a globally defined :ref:`ComputedVectorElement`, but are only available within the single ``<integrate>`` element.

Example syntax::

    <integrate algorithm="ARK89" interval="1e-4" steps="10000" tolerance="1e-8">
      <samples>20</samples>
      <filters>
        <filter>
          <dependencies>wavefunction normalisation</dependencies>
          <![CDATA[
            phi *= sqrt(Nparticles/Ncalc);   // Correct normalisation of the wavefunction
          ]]>
        </filter>
      </filters>
      <operators>
        <operator kind="ip" constant="yes">
          <operator_names>T</operator_names>
          <![CDATA[
            T = -0.5*hbar/M*ky*ky;
          ]]>
        </operator>
        <dependencies>potential</dependencies>
        <![CDATA[
          dphi_dt = T[phi] - (V1 + Uint/hbar*mod2(phi))*phi;
        ]]>
        <integration_vectors>wavefunction</integration_vectors>
      </operators>
    </integrate>

.. _OperatorsElement:

Operators and operator elements
-------------------------------

An :ref:`<integrate><IntegrateElement>` element must contain one or more ``<operators>`` elements, which define both which vectors are to be integrated, and their derivative in the propagation dimension.  When all vectors to be integrated have the same dimensionality, they can all be defined within a single ``<operators>`` element, and when vectors with different dimension are to be integrated, each set of vectors with the same dimensionality should be placed in separate ``<operators>`` elements.  
    
.. _IntegrationVectorsElement:

Within each ``<operators>`` element, the vectors that are to be integrated are listed by name in the ``<integration_vectors>`` element, and the differential equations are written in a 'CDATA' block.   The derivative of each component of the integration vectors must be defined along the propagation dimension.  For example, if the integration vectors have components 'phi' and 'beta', and the propagation dimension is labelled 'tau', then the 'CDATA' block must define the variables 'dphi_dtau' and 'dbeta_dtau'.  These derivatives can be any function of the available variables, including any components from other vectors, computed vectors or noise vectors that are listed in the optional :ref:`<dependencies><Dependencies>` element.  These dependent vectors must be defined on a subset of the dimensions of the integration vectors.  
    
When noise vectors are referenced, equations with both Wiener should be written as though the equations are in differential form, as described in the worked examples :ref:`Kubo` and :ref:`Fibre`.  Jump-based Poisson noises will also be written in an equivalent form, as modelled by the example 'photodetector.xmds`.
    
By default, the name of each component references the local value of the vector, but :ref:`nonlocal variables<ReferencingNonlocal>` can be accessed using the standard syntax.  However, typically the most common (and most efficient) method of referencing nonlocal variables is to reference variables that are local in the :ref:`transformed space<Transforms>` for a given transverse dimension.  This is done using ``<operator>`` elements.
    
.. _OperatorElement:

There are three kinds of ``<operator>`` elements.  The first is denoted with a ``kind="functions"`` attribute, and contains a 'CDATA' block that will be executed in the order that it is defined.  This is useful when you wish to calculate functions that do not depend on the transverse dimensions.  Defining these along with the main equations of motion causes them to be recalculated separately for each point.  The second kind of ``<operator>`` element is used to define an operation in a transformed space.  This is often an efficient method of calculating common nonlocal terms such as derivatives.  The third kind is used to define integration of one or more vectors along a transverse dimension.

Example syntax::

    <operator kind="functions">
      <![CDATA[
      f = cos(t);
      ]]>
    </operator>
    
.. _OperatorNamesElement:

The second kind of operator element defines a list of operators in an ``<operator_names>`` element.  The basis of these operators defaults to the transform space unless a different basis is specified using the ``basis`` attribute.  These operators must then be defined in a 'CDATA' block, using any :ref:`dependencies<Dependencies>` as normal.  If the operators constant across the integration, then the attribute ``constant="yes"`` should be set, otherwise the ``constant="no"`` attribute ensures that the operator is recalculated each step.  The operators defined in these elements can then be used in the 'CDATA' block that defines the equations of motion.  The application of operator 'L' to vector 'psi' is denoted ``L[psi]``.  Operators can be applied to functions of vectors using the same notation, such as ``L[psi*psi]``.  Aside from the example above, many examples can be found in the examples folder, and the :ref:`WorkedExamples` section of the documentation.

Operators of this second kind have the ``kind="IP"`` or ``kind="EX"`` attribute, standing for 'interaction picture' and 'explicit' operators respectively.  Explicit operators can be used in all situations, and simply construct and calculate a new vector of the form in the square brackets.  IP operators use less memory and can improve speed by allowing larger timesteps, but have two important restrictions.  **Use of IP operators without understanding these restrictions can lead to incorrect code**.  The first restriction is that IP operators can only be applied to named components of one of the integration vectors, and not functions of those components.  The second restriction is that the equations of motion must be written such that the term with the operator is not multiplied by any quantity or used inside a function.  (For those interested, the reason for this is that the IP algorithm applies the operator separately to the rest of the evolution, and therefore the actual text of the ``L[psi]`` term is replaced by the numeral zero.)  If you must break either of those rules, then you need to use the EX algorithm.

Example syntax::

    <operator kind="ex" constant="yes">
      <operator_names>T</operator_names>
      <![CDATA[
        T = -0.5*hbar/M*ky*ky;
      ]]>
    </operator>

The third kind of operator element is used to define an integration along a transverse dimension.  This kind of evolution is called "cross-propagation", and is described briefly in the examples 'tla.xmds', 'tla_sic.xmds' and 'sine_cross.xmds'.  This class of equations have a subset of vectors that have an initial condition on one side of a transverse dimension, and a differential equation defined in that dimension, and as such, this kind of operator element has much of the structure of an entire :ref:`<integrate><IntegrateElement>` element.  
    
An operator element with the ``kind="cross_propagation"`` attribute must specify the transverse dimension along which the integration would proceed with the ``propagation_dimension`` attribute.  It must also specify its own :ref:`<integration_vectors><IntegrationVectorsElement>` element, its own ``<operators>`` elements (of the second kind), and may define an optional :ref:`<dependencies><Dependencies>` element.  The algorithm to be used for the transverse integration is specified by the ``algorithm`` attribute, with options being ``algorithm="SI"`` and ``algorithm="RK4"``.  The derivatives in the cross propagation direction are defined in a 'CDATA' block, just as for a normal ``<integrate>`` element.  
    
.. _BoundaryConditionElement:

The boundary conditions are specified by a ``<boundary_conditions>`` element, which requires the ``kind="left"`` or ``kind="right"`` attribute to specify on which side of the grid that the boundary conditions are specified.  The boundary conditions for the ``<integration_vectors>`` are then specified in a 'CDATA' block, which may refer to vectors in an optional :ref:`<dependencies><Dependencies>` element that can be contained in the ``<boundary_conditions>`` element.

Example syntax::

    <operator kind="cross_propagation" algorithm="RK4" propagation_dimension="t">
      <integration_vectors>cross</integration_vectors>
      <dependencies>constants</dependencies>
      <boundary_condition kind="left">
        <![CDATA[
          v = 1.0;
          w = 1.0;
        ]]>
      </boundary_condition>
  
      <operator kind="ip" constant="yes">
        <operator_names>L</operator_names>
        <![CDATA[
          L = i;
        ]]>
      </operator>
  
      <![CDATA[
        dv_dt = i*v;
        dw_dt = L[w]; 
      ]]>
    </operator>


.. _Algorithms:

Algorithms
----------

The stability, efficiency and even convergence of a numerical integration can depend on the method.  Due to the varying properties of different sets of equations, it is impossible to define the best method for all equations, so XMDS provides an option to use different algorithms.  These include fixed step algorithms, which divide the integration region into equal steps, and adaptive stepsize algorithms, which attempt to estimate the error in the simulation in order to choose an appropriate size for the next step.  As a first guess, a good method for a deterministic integration would be :ref:`ARK89<ARK45>`, and a good guess for a stochastic method would be the :ref:`SI`.

For the purposes of the descriptions below, we will assume that we are considering the following set of coupled differential equations for the vector of variables :math:`\mathbf{x}(t)`:

.. math::

    \frac{d x_j}{dt} = f_j(\mathbf{x}(t),t)

.. _SI:

SI and SIC algorithms
~~~~~~~~~~~~~~~~~~~~~

The SI algorithm is a semi-implicit fixed-step algorithm that finds the increment of the vector by solving

.. math::

    x_j(t+\Delta t) = x_j(t) + f_j\left(\mathbf{x}(t+\frac{\Delta t}{2}),t+\frac{\Delta t}{2}\right) \;\Delta t

using a simple iteration to find the values of the vector at the midpoint of the step self-consistently.  The number of iterations can be set using the ``iterations`` attribute, and it defaults to ``iterations="3"``.  The choice of ``iterations="1"`` is therefore fully equivalent to the Euler algorithm, where

.. math::

    x_j(t+\Delta t) = x_j(t) + f_j\left(\mathbf{x}(t),t\right) \;\Delta t.

The Euler algorithm is the only safe algorithm for direct integration of :ref:`jump-based Poisson processes<jumpNoise>`.  Efficient numerical solution of those types of equations is best done via a process of triggered filters, which will be described in the :ref:`AdvancedTopics` section.
    
When SI integration is used in conjunction with SI cross-propagation, a slight variant of the SI algorithm can be employed where the integration in both directions is contained within the iteration process.  This is activated by using ``algorithm="SIC"`` rather than ``algorithm="SI"``.

The SI algorithm is correct to second order in the step-size for deterministic equations, and first order in the step-size for Stratonovich stochastic equations with Wiener noises.  This makes it the highest order stochastic algorithm in XMDS, although there are many sets of equations that integrate more efficiently with lower order algorithms.

.. _RK4:

Runge-Kutta algorithms
~~~~~~~~~~~~~~~~~~~~~~

Runge-Kutta algorithms are the workhorse of numerical integration, and XMDS employs two fixed step versions: ``algorithm="RK4"``, which is correct to fourth-order in the step size, and ``algorithm="RK9"``, which is correct to ninth order in the step size.  It must be strongly noted that a higher order of convergence does not automatically mean a superior algorithm.  RK9 requires several times the memory of the RK4 algorithm, and each step requires significantly more computation.

All Runge-Kutta algorithms are convergent for Stratonovich stochastic equations at the order of the square root of the step-size.  This 'half-order' convergence may seem very weak, but for some classes of stochastic equation this improves up to one half of the deterministic order of convergence.  Also, the convergence of some stochastic equations is limited by the 'deterministic part', which can be improved dramatically by using a higher order Runge-Kutta method.


.. _ARK45:

Adaptive Runge-Kutta algorithms
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Fixed step integrators can encounter two issues.  First, as the equations or parameters of a simulation are changed, the minimum number of steps required to integrate it may change.  This means that the convergence must be re-tested multiple times for each set of parameters, as overestimating the number of steps required to perform an integration to a specified error tolerance can be very inefficient. Second, even if the minimum acceptable number of steps required is known for a given simulation, it may be that there are regions of integration that are of wildly varying difficulty.  For a fixed step integrator, this means that the step-size must be small enough to handle the most difficult region, and is therefore inefficiently small for the easier regions.  Adaptive step-size
algorithms get around this problem by testing the convergence during the integration, and adjusting the step-size until it reaches some target tolerance.

XMDS employs two adaptive step-size algorithms based on 'embedded Runge-Kutta' methods.  These are Runge-Kutta methods that can output multiple variables that have different convergence.  The difference between the higher-order and the lower-order solutions gives an estimate of the error in each step, which can then be used to estimate an appropriate size for the next step.  We use ``algorthim="ARK45"``, which contains fourth and fifth order solutions, and ``algorthim=ARK89``, which contains eighth and ninth order solutions.  Each algorithm converges with the order of the lowest order solution (fourth and eighth order respectively).  The overheads involved in estimating the error and step-size make the adaptive algorithms slower than fixed step integration using the same step-size, but overall there is typically a significant performance gain from being able to avoid doing this optimisation manually.

All adaptive stepsize algorithms require a ``tolerance`` attribute, which must be a positive real number that defines the allowable error per step.  It is also possible to specify a ``max_iterations`` attribute, which is a positive integer that stops the integrator from trying too many times to find an acceptable stepsize.  The integrator will abort with an error if the number of attempts for a single step exceeds the maximum specified with this attribute.

As all Runge-Kutta solutions have equal order of convergence for stochastic equations, *if the step-size is limited by the stochastic term then the step-size estimation is entirely unreliable*.  Adaptive Runge-Kutta algorithms are therefore not appropriate for stochastic equations.


.. _FiltersElement:

Filters element
---------------

:ref:`Filter elements<FilterElement>` are used inside :ref:`sequence elements<SequenceElement>` to execute arbitrary code, or make discontinuous changes in the vectors.  Sometimes it is desirable to perform a filter element at the beginning or end of each step in an integration.  This can be done by placing ``<filter>`` elements in a ``<filters>`` element within the ``<integrate>`` element.  The ``<filters>`` element specifies whether the filters are to be executed at the end of each step or the beginning of each step with the ``where="step end"`` and ``where="step start"`` attributes respectively.  Each filter
is then executed in the order found in the ``<filters>`` element.

Example syntax::

    <integrate algorithm="ARK45" interval="100000.0" steps="10000000" tolerance="1e-8">
      <samples>5000 100</samples>
      <filters where="step end">
        <filter>
            <dependencies>vector1 vector2</dependencies>
            <![CDATA[
                x = 1;
                y *= ynorm;
                ]]>
        </filter>
      </filters>

      <operators>
        <integration_vectors>vector1</integration_vectors>
        <![CDATA[
        dx_dt = alpha;
        dy_dt = beta*y;
        ]]>
      </operators>
    </integrate>


.. _BreakpointElement:

Breakpoint element
==================

The ``<breakpoint>`` element is used to output the full state of one or more vectors.  Unlike sampled output, it executes immediately rather than at the end of a program, and can therefore be used to examine the current state of an ongoing simulation.  The vectors to be output are defined via a :ref:`<dependencies><Dependencies>` element, and the basis is chosen by the ``basis`` attribute supplied to that ``<dependencies>`` element, as usual.  A single ``<breakpoint>`` element must only contain vectors of equal dimension.  The data format is specified by the ``format`` attribute, with current options being "ascii", "binary" and the recommended: "hdf5".  The filename for the output can be specified by a ``filename`` attribute, in which case the same filename will be used each time the element is executed.  If the ``filename`` attribute is not specified, then the first output will default to "1.xsil", and subsequent executions of the same breakpoint will increment the number by one.

Example syntax::

    <breakpoint filename="groundstate_break.xsil" format="hdf5">
      <dependencies basis="ky">wavefunction</dependencies>
    </breakpoint>

.. _OutputElement:

Output element
==============

The ``<output>`` element describes the output of the program.  It is often inefficient to output the complete state of all vectors at all times during a large simulation, so the purpose of this function is to define subsets of the information required for output.  Each different format of information is described in a different ``<group>`` element inside the output element.  The ``<output>`` element may contain any number of ``<group>`` elements.  The format of the output data can be specified by the optional ``format`` attribute, which may take values of "ascii", "binary", and "hdf5" (the default).  The filename can be specified with the optional ``filename`` element, which otherwise defaults to the simulation name with the '.xsil' suffix.

The ``<samples>`` inside ``<integrate>`` elements defines a string of integers, with exactly one for each ``<group>`` element.  During that integration, the variables described in each ``<group>`` element will be sampled and stored that number of times.  


.. _GroupElement:

Group (Sampling) Element
------------------------

A ``<group>`` element defines a set of variables that we wish to output, typically they are functions of some subset of vectors.  It must contain a ``<sampling>`` element, which contains all of the following elements.  The names of the desired variables are listed in a ``<moments>`` element, just like the ``<components>`` element of a vector.  They are defined with a ':ref:`CDATA<XMDSCSyntax>`' block, accessing any components of vectors and computed vectors that are defined in a :ref:`<dependencies><Dependencies>` element, also just like a vector.  :ref:`Computed vectors<ComputedVectorElement>` and :ref:`<operator><OperatorElement>` elements can be defined and used in the definition, just like in an :ref:`<integrate><IntegrateElement>` element.
    
The basis of the output is specified by the ``basis`` attribute in the ``<sampling>`` element.  This overrides any basis specification in the ``<dependencies>`` element.  Because we often wish to calculate these vectors on a finer grid than we wish to output, it is possible to specify that the output on a subset of the points defined for any transverse dimension.  This is done by adding a number in parentheses after that dimension in the basis string, e.g. ``basis="x y(32) kz(64)"``.  If the number is zero, then that dimension is integrated out.  If that number is one or more, then that dimension will be sampled on a subset of points in that space.
    
The ``initial_sample`` attribute, which must be "yes" or "no", determines whether the moment group will be sampled before any integration occurs.

Example syntax::

    <output format="hdf5" filename="SimOutput.xsil">
      <group>
          <sampling basis="x y" initial_sample="yes">
            <computed_vector name="filter3" dimensions="" type="complex">
              <components>sparemomentagain</components>
              <evaluation>
                <dependencies basis="kx ky">integrated_u main</dependencies>
                <![CDATA[
                  sparemomentagain = mod2(u);
                ]]>
              </evaluation>
            </computed_vector>
            <operator kind="ex" constant="no">
              <operator_names>L</operator_names>
              <![CDATA[
                L = -T*kx*kx/mu;
              ]]>
            </operator>
            <moments>amp ke</moments>
            <dependencies>main filter1</dependencies>
            <![CDATA[
              amp = mod2(u + moment);
              ke = mod2(L[u]);
            ]]>
          </sampling>
 
      <group>
        <sampling basis="kx(0) ky(64)" initial_sample="yes">
          <moments>Dens_P </moments>
          <dependencies>fields </dependencies>
          <![CDATA[
            Dens_P = mod2(psi);
          ]]>
        </sampling>
     </group>
    </output>


.. _XMDSCSyntax:

XMDS-specific C syntax
======================

There are some handy shortcuts included, and we should list them all.
