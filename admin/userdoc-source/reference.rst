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

.. code-block:: bash

    $ xmds2 --configure --include-path /path/to/include --lib-path /path/to/lib 

Running XMDS2 with the '--configure' option also searches for packages that have been installed since you last installed or configured XMDS2.  If you wish to run 'xmds2 --configure' with the same extra options as last time, simply use the command:

.. code-block:: bash

    $ xmds2 --reconfigure

A detailed log of the checks is saved in the file '~/.xmds/waf_configure/config.log'.  This can be used to identify issues with packages that XMDS2 is not recognised, but you think that you have successfully installed on your system.


.. _UsefulXMLSyntax:

Useful XML Syntax
=================

Standard XML placeholders can be used to simplify some scripts.  For example, the following (abbreviated) code ensures that the limits of a domain are symmetric.

.. code-block:: xmds2

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

Example syntax::

    <simulation xmds-version="2">
        <!-- Rest of simulation goes here -->
    </simulation>


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

Example syntax::

    <simulation xmds-version="2">
        <features>
            <error_check />
        </features>
    </simulation>


.. _Precision:

Precision
-----------

This specifies the precision of the XMDS2 ``real`` and ``complex`` datatypes, as well as the precision used when computing transforms. Currently two values are accepted: ``single`` and ``double``. If this feature isn't specified, XMDS2 defaults to using double precision for its variables and internal calculations.

Single precision has approximately 7.2 decimal digits of accuracy, with a minimum value of 1.4×10\ :superscript:`-45` and a maximum of 3.8×10\ :superscript:`34`. Double precision has approximately 16 decimal digits of accuracy, a minimum value of 4.9×10\ :superscript:`-324` and a maximum value of 1.8×10\ :superscript:`308`.

Using single precision can be attractive, as it can be more than twice as fast, depending on whether a simulation is CPU bound, memory bandwidth bound, MPI bound or bottlenecked elsewhere. Caution should be exercised, however. Keep in mind how many timesteps your simulation requires, and take note of the tolerance you have set per step, to see if the result will lie within your acceptable total error - seven digit precision isn't a lot. Quite apart from the precision, the range of single precision can often be inadequate for many physical problems. In atomic physics, for example, intermediate values below 1.4×10\ :superscript:`-45` are easily obtained, and will be taken as zero. Similarly, values above 3.8×10\ :superscript:`34` will result in NaNs and make the simulation results invalid.

A further limitation is that not all the combinations of random number generators and probability distributions that are supported in double precision are supported in single precision. For example, neither the ``solirte`` nor ``dsfmt`` generators support single precision gaussian distributions. The ``posix`` generator will always work, but may be very slow.

Example syntax::

    <simulation xmds-version="2">
        <features>
            <precision> single </precision>
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

The ``<geometry>`` element describes the dimensions used in your simulation, and is required.  The only required element inside is the ``<propagation_dimension>`` element, which defines the name of the dimension along which your simulation will integrate.  Nothing else about this dimension is specified, as requirements for the lattice along the integration dimension is specified by the ``<integrate>`` blocks themselves, as described in section :ref:`IntegrateElement`.

If there are other dimensions in your problem, they are called "transverse dimensions", and are described in the ``<transverse_dimensions>`` element.  Each dimension is then described in its own ``<dimension>`` element.  A transverse dimension must have a unique name defined by a ``name`` attribute.  If it is not specified, the type of dimension will default to "real", otherwise it can be specified with the ``type`` attribute.  Allowable types (other than "real") are "long", "int", and "integer", which are actually all synonyms for an integer-valued dimension.

Each transverse dimension must specify how many points or modes it requires, and the range over which it is defined.  This is done by the ``lattice`` and ``domain`` attributes respectively.  The ``lattice`` attribute is an integer, and is optional for integer dimensions, where it can be defined implicitly by the domain.  The ``domain`` attribute is specified as a pair of numbers (e.g. ``domain="(-17,3)"``) defining the minimum and maximum of the grid.

Any dimension can have a number of aliases.  These act exactly like copies of that dimension, but must be included explicitly in the definition of subsequent vectors (i.e. they are not included in the default list of dimensions for a new vector).  The list of aliases for a dimension are included in an ``aliases`` attribute.  They are useful for non-local reference of variables.  See ``groundstate_gaussian.xmds`` and ``2DMultistateSE.xmds`` as examples.

Integrals over a dimension can be multiplied by a common prefactor, which is specified using the ``volume_prefactor`` attribute.  For example, this allows the automatic inclusion of a factor of two due to a reflection symmetry by adding the attribute ``volume_prefactor="2"``.

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

This identity can be used to write the differential operator :math:`\mathcal{L} = \frac{\partial}{\partial x}` as an ``IP`` or ``EX`` operator as ``L = i*kx;`` (see :ref:`OperatorElement` for more details).

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

This identity can be used to write the differential operator :math:`\mathcal{L} = \frac{\partial^2}{\partial x^2}` as an ``IP`` or ``EX`` operator as ``L = -kx*kx;`` (see :ref:`OperatorElement` for more details).

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

This identity can be used to write the differential operator :math:`\mathcal{L} = \frac{\partial^2}{\partial x^2}` as an ``IP`` or ``EX`` operator as ``L = -kx*kx;`` (see :ref:`OperatorElement` for more details).


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

It can often be useful to have a different sampling in normal space and Hankel space.  Reducing the number of modes in either space dramatically speeds simulations.  To set the number of lattice points in Hankel space to be different to the number of lattice points for the field in its original space, use the attribute ``spectral_lattice``.  All of these lattices are chosen in a non-uniform manner using Gaussian quadrature methods for spectrally accurate transforms.

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

A vector can be a group of variables, each defined by name in the ``<components>`` attribute.  The name of each component is the name used to reference it later in the simulation.

Vectors are initialised at the beginning of a simulation, either from code or from an input file.  The basis choice for this initialisation defaults to the normal space as defined in the ``<geometry>`` element, but any transverse dimension can be initialised in their transform basis by specifying them in an ``initial_basis`` attribute.  The ``initial_basis`` attribute lists dimensions either by their name as defined by the ``<geometry>`` element, or by their transformed name.  For example, to initialise a two-dimensional vector defined with ``dimensions="x y"`` in Fourier space for the y-dimension, we would include the attribute ``initial_basis="x ky"``, or just ``initial_basis="ky"``.  

When initialising the vector within the XMDS script, the appropriate code is placed in a 'CDATA' block inside an ``<initialisation>`` element.  This code is in standard C-syntax, and should reference the components of the vector by name.  If you wish to initialise all the components of the vector as zeros, then it suffices to simply add the attribute ``kind="zero"`` or to omit the ``<initialisation>`` element entirely.  

If you wish to initialise from a file, then you can choose to initialise from a hdf5 file using ``kind="hdf5"``, and then supply the name of the input file with a ``filename`` element.  These are standard data formats, both of which can be generated from XMDS, or from another program.  An example for generating a file in another program for input into XMDS is detailed in the Advanced topic: :ref:`Importing`.

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

.. _ReferencingNonlocal:

Referencing variables non-locally
---------------------------------

While the default XMDS behaviour is to reference all variables locally, any vector can be referenced non-locally.  The notation for referencing the value of a vector 'phi' with a dimension 'j' at a value of 'j=jk' is ``phi(j => jk)``.  Multiple non-local dimensions are addressed by adding the references in a list, e.g. ``phi(j => jk, x => y)``.  See ``2DMultistateSE.xmds`` for an example.




.. _ComputedVectorElement:

Computed Vector Element
=======================

Computed vectors are arrays of data much like normal ``<vector>`` elements, but they are always calculated as they are referenced, so they cannot be initialised from file.  It is defined with a ``<computed_vector>`` element, which has a ``name`` attribute, optional ``dimensions`` and ``type`` attributes, and a ``<components>`` attribute, just like a ``<vector>`` element.  Instead of an ``<initialisation>`` element, it has an ``<evaluation>`` element that serves the same purpose.  The ``<evaluation>`` element contains a ``<dependencies>`` element (see ``above<Dependencies>``), and a 'CDATA' block containing the code that defines it.

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

Noise vectors are used like computed vectors, but when they are evaluated they generate arrays of random numbers of various kinds.  They do not depend on other vectors, and are not initialised by code.  They are defined by a ``<noise_vector>`` element, which has a ``name`` attribute, and optional ``dimensions``, ``initial_basis`` and ``type`` attributes, which work identically as for normal vectors.  The different types of noise vectors are defined by a mandatory ``kind`` attribute, which must take the value of 'gauss', 'gaussian', 'wiener', 'poissonian','jump' or 'uniform'.  

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



.. _gaussianNoise:

Gaussian noise
--------------

.. _wienerNoise:

Wiener noise
------------

.. _poissionianNoise:

Poissonian noise
----------------

.. _jumpNoise:

Jump noise
----------




kind, method, seed



.. _SequenceElement:

Sequence Element
================


.. _FilterElement:

Filter Element
--------------


.. _IntegrateElement:

Integrate Element
-----------------

.. _OperatorElement:

Operator Element
~~~~~~~~~~~~~~~~

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

.. _XMDSCSyntax:

XMDS-specific C syntax
======================

There are some handy shortcuts included, and we should list them all.
