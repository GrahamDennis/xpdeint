News
-----

XMDS 2.2.0 "Out of cheese error" (January 13, 2014)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

XMDS 2.2.0 contains a number of new features, as well as bugfixes and updates. Specifically

* Separated IP operators.  This is a significant performance optimisation (~30%) for problems with two or more dimensions.  It requires separating IP operators of the form "f(kx) + g(ky)" (e.g. kinetic energy for quantum physics) into *two* IP operators and explicitly setting the dimensions="x" and dimensions="y" attributes on each.  See :ref:`Optimisation hints<OptimisationHints>` for details.
* Significant speed optimisations for adaptive integrators with IP operators (past IP operator calculations are re-used if the time-step hasn't changed).
* The "constant" attribute for IP/EX operators is now unnecessary and considered advanced usage.  If you don't know whether to specify constant="yes" or constant="no", don't specify either.
* The xsil2graphics2 data exporter now supports Matlab, Octave, Mathematica and Python in all output formats, as well as R (HDF5 only).  The Matlab/Octave scripts are now identical.  A script generated for one will work for the other.
* Bessel-Neumann transforms have been implemented.  Set transform="bessel-neumann" if you want a Bessel (Hankel) transform but have zero derivative at the boundary (Neumann boundary conditions) instead of zero function value (Dirichlet boundary conditions).  If you don't care about your boundary condition, stick with the "bessel" transform.
* A Bulirisch-Stoer integrator.  This can be useful for problems which are very smooth as you can use an arbitrarily high order algorithm.  Specify algorithm="RE" and extrapolations="5" to have a 10th order integrator.  Currently this is fixed-step only.
* "adaptive-mpi-multipath" driver.  This implements a load scheduler that better spreads the work across different CPUs when different paths can take very different amounts of time. Also useful in heterogeneous clusters.
* XMDS2 is currently undergoing acceptance into Debian linux and will soon be able to be installed via the package manager. In the meantime you can find it in the private APT repository at http://xmds.laboissiere.net.
* A number of bug fixes.
* Expanded and improved documentation.

Many thanks to all who contributed to this release!


XMDS 2.1.4 "Well if this isn't nice, I don't know what is" (September 27, 2013)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The XMDS 2.1.4 update contains many new improvements and bugfixes:

* *xsil2graphics2* now supports all output formats for MATLAB, Octave and Python.  The scripts generated for MATLAB/Octave are compatible with both.
* Fix a bug when :ref:`nonlocally<ReferencingNonlocal>` referencing a :ref:`dimension alias<DimensionAliases>` with subsampling in *sampling_group* blocks or in some situations when MPI is used.  This bug caused incorrect elements of the vector to be accessed.
* Correct the Fourier basis for dimensions using Hermite-Gauss transforms.  Previously 'kx' was effectively behaving as '-kx'.
* Improve the performance of 'nx' <--> 'kx' Hermite-Gauss transforms.
* Stochastic error checking with runtime noise generation now works correctly.  Previously different random numbers were generated for the full-step paths and the half-step paths.
* Documentation updates.

XMDS 2.1.3 "Happy Mollusc" (June 7, 2013)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The XMDS 2.1.3 update is a bugfix release that includes the following improvements:

* XMDS will work when MPI isn't installed (but only for single-process simulations).
* Support for GCC 4.8
* The number of paths used by the multi-path driver can now be specified at run-time (using *<validation kind="run-time">*)
* Other bug fixes

XMDS 2.1.2 "Happy Mollusc" (October 15, 2012)
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

XMDS 2.1 "Happy Mollusc" (June 14, 2012)
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


XMDS 2.0 "Shiny!" (September 13, 2010)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
