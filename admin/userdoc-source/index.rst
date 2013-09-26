.. xpdeint documentation master file, created by sphinx-quickstart on Tue Nov 18 15:10:03 2008.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to XMDS2!
=================

This website provides the documentation for XMDS2 (an all-new version of :ref:`XMDS<XMDSHistory>`), a software package that allows the fast and easy solution of sets of ordinary, partial and stochastic differential equations, using a variety of efficient numerical algorithms.

If you publish work that has involved XMDS2, please cite it as `Comput. Phys. Commun. 184, 201-208 (2013) <http://dx.doi.org/10.1016/j.cpc.2012.08.016>`_.

Documentation
-------------

To get started, take a look at our :ref:`documentation<Documentation>`.

News
-----

September 27, 2013: XMDS 2.1.4 "Well if this isn't nice, I don't know what is"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The XMDS 2.1.4 update contains many new improvements and bugfixes:

* *xsil2graphics2* now supports all output formats for MATLAB, Octave and Python.  The scripts generated for MATLAB/Octave are compatible with both.
* Fix a bug when :ref:`nonlocally<ReferencingNonlocal>` referencing a :ref:`dimension alias<DimensionAliases>` with subsampling in *sampling_group* blocks or in some situations when MPI is used.  This bug caused incorrect elements of the vector to be accessed.
* Correct the Fourier basis for dimensions using Hermite-Gauss transforms.  Previously 'kx' was effectively behaving as '-kx'.
* Improve the performance of 'nx' <--> 'kx' Hermite-Gauss transforms.
* Stochastic error checking with runtime noise generation now works correctly.  Previously different random numbers were generated for the full-step paths and the half-step paths.
* Documentation updates.

June 7, 2013: XMDS 2.1.3 "Happy Mollusc"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The XMDS 2.1.3 update is a bugfix release that includes the following improvements:

* XMDS will work when MPI isn't installed (but only for single-process simulations).
* Support for GCC 4.8
* The number of paths used by the multi-path driver can now be specified at run-time (using *<validation kind="run-time">*)
* Other bug fixes

October 15, 2012: XMDS 2.1.2 "Happy Mollusc"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The XMDS 2.1.2 update has many improvements:

* Named filters.  You can now specify a name for a filter block and call it like a function if you need to execute it conditionally.  See the documentation for the *<filter>* block for more information.
* New *chunked_output* feature.  XMDS can now output simulation results as it goes, reducing the memory requirement for simulations that generate significant amounts of output.  See the documentation for more details.
* Improved OpenMP support
* The EX operator is now faster in the common case (but you should still prefer IP when possible)
* If seeds are not provided for a *noise_vector*, they are now generated at simulation run-time, so different executions will give different results.  The generated noises can still be found in the output .xsil files enabling results to be reproduced if desired.
* Advanced feature: Dimensions can be accessed non-locally with the index of the lattice point.  This removes the need in hacks to manually access XMDS's underlying C arrays.  This is an advanced feature and requires a little knowledge of XMDS's internal grid representation.  See the advanced topics documentation for further details.
* Fixed adaptive integrator order when noises were used in vector initialisation
* Fix the Spherical Bessel basis.  There were errors in the definition of this basis which made it previously unreliable.
* Other bug fixes

June 14, 2012: XMDS 2.1 "Happy Mollusc"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

XMDS 2.1 is a significant upgrade with many improvements and bug fixes since 2.0. We also now have installers for Linux and Mac OS X, so you no longer have to build XMDS from source! See :ref:`here<Installation>` for details about the installers.

Existing users should note that this release introduces a more concise syntax for moment groups.  You can now use::

    <sampling_group initial_sample="yes" basis="x y z">
        ...
    </sampling_group>

Instead of::

    <group>
        <sampling initial_sample="yes" basis="x y z">
            ...
        </sampling>
    </group>

Another syntax change is that the initial basis of a vector should be specified with *initial_basis* instead of *initial_space*.

In both cases, although the old syntax is not described in the documentation, it is still supported, so existing scripts will work without any changes.


Other changes in XMDS 2.1 include:

* The *lattice* attribute for dimensions can now be specified at run-time.  Previously only the minimum and maximum values of the domain could be specified at run-time.  See :ref:`here<Validation>` for details.
* *noise_vectors* can now be used in non-uniform dimensions (e.g. dimensions using the Bessel transform for cylindrical symmetry).
* "loose" *geometry_matching_mode* for HDF5 vector initialisation.  This enables extending the simulation grid from one simulation to the next, or coarsening or refining a grid when importing.
* *vectors* can now be initialised by integrating over dimensions of other vectors.  *computed_vectors* always supported this, now *vectors* do too.
* Update to latest version of waf, which is used for compiling simulations and detecting FFTW, HDF5, etc. This should lead to fewer waf-related problems.
* Bug fixes.


September 13, 2010: XMDS 2.0 "Shiny!"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

XMDS 2.0 is a major upgrade which has been rewritten from the ground up to make it easier for us to apply new features. And there are many. XMDS 2.0 is faster and far more versatile than previous versions, allowing the efficient integration of almost any initial value problem on regular domains.

The feature list includes:

* Quantities of different dimensionalities. So you can have a 1D potential and a 3D wavefunction.
* Integrate more than one vector (in more than one geometry), so you can now simultaneously integrate a PDE and a coupled ODE (or coupled PDEs of different dimensions).
* Non-Fourier transformations including the Bessel basis, Spherical Bessel basis and the Hermite-Gauss (harmonic oscillator) basis.
* The ability to have more than one kind of noise (gaussian, poissonian, etc) in a simulation.
* Integer-valued dimensions with non-local access. You can have an array of variables and access different elements of that array.
* Significantly better error reporting. When errors are found when compiling the script they will almost always be reported with the corresponding line of your script, instead of the generated source.
* *IP*/*EX* operators are separate from the integration algorithm, so you can have both *IP* and *EX* operators in a single integrate block. Also, *EX* operators can act on arbitrary code, not just vector components. (e.g. *L[phi*phi]*).
* Cross propagation in the increasing direction of a given dimension or in the decreasing dimension. And you can have more than one cross-propagator in a given integrator (going in different directions or dimensions).
* Faster Gaussian noises.
* The ability to calculate spatial correlation functions.
* OpenMP support.
* MPI support.
* Output moment groups use less memory when there isn't a *post_processing* element.
* Generated source is indented correctly.
* An *xmds1*-like script file format.
* *xmds1*-like generated source.
* All of the integrators from *xmds1* (*SI*, *RK4*, *ARK45*, *RK9*, *ARK89*).
