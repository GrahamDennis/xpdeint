Optimisation Hints
===================

There are a variety of things you can do to make your simulations run faster.

Geometry and transform-based tricks
-----------------------------------

Simpler simulation geometries
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Consider symmetry, can you use ``dct`` transforms or ``bessel`` transforms? Do you really need that many points? How big does your grid need to be? Could absorbing boundary conditions help?

Tricks for Bessel and Hermite-Gauss transforms
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Mention that dimensions using matrix transforms should be first for performance reasons.

Reduce code complexity
----------------------
Avoid transcendental functions like :math:`\sin(x)` or :math:`\exp(x)` in inner loops. Not all operations are made equal, use multiplication over division.

Use the Interaction Picture (IP) operator
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Just do it. Only use the EX operator when you have to. If you must use the EX operator, consider making it ``constant="no"``. It uses less memory.

Consider writing the evolution in spectral basis
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The basis that makes most sense will be the one which is the 'hardest' to integrate.

Don't recalculate things you don't have to
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Use ``computed_vectors`` appropriately.


Compiler and library tricks
---------------------------

Faster compiler
^^^^^^^^^^^^^^^
If you're using an Intel CPU, then you should consider using their compiler, icc. They made the silicon, and they also made a compiler that understands how their chips work significantly better than the more-portable GCC.

Faster libraries
^^^^^^^^^^^^^^^^
Intel MKL is faster than ATLAS, which is faster than GSL CBLAS. If you have a Mac, then Apple's vecLib is plenty fast.

Auto-vectorisation
^^^^^^^^^^^^^^^^^^
Auto-vectorisation is a compiler feature that makes compilers generate more efficient code that can execute the same operation on multiple pieces of data simultaneously. To use this feature, you need to add the following to the ``<features>`` block at the start of your simulation:

.. code-block:: xpdeint
    
    <auto_vectorise />

This will make xpdeint generate code that is more friendly to compiler's auto-vectorisation features so that more code can be vectorised. It will also add the appropriate compiler options to turn on your compiler's auto-vectorisation features. For auto-vectorisation to increase the speed of your simulations, you will need a compiler that supports it such as gcc 4.2 or later, or Intel's C compiler, ``icc``.

OpenMP
^^^^^^
`OpenMP <http://openmp.org>`_ is a set of compiler directives to make it easier to use threads (different execution contexts) in programs. Using threads in your simulation does occur some overhead, so for the speedup to outweigh the overhead, you must have a reasonably large simulation grid. To add these compiler directives to the generated simulations, add the tag ``<openmp />`` in the ``<features>`` block. This can be used in combination with the auto-vectorisation feature above. Note that if you are using gcc, make sure you check that your simulations are faster by using this as gcc's OpenMP implementation isn't as good as icc's.

If you are using the OpenMP feature and are using `FFTW <http://www.fftw.org>`_-based transforms (Discrete Fourier/Cosine/Sine Transforms), you should consider using threads with your FFT's by adding the following to the ``<features>`` block at the start of your simulation:

.. code-block:: xpdeint
    
    <fftw threads="2" />

Replace the number of threads in the above code by the number of threads that you want to use.

Parallelisation with MPI
^^^^^^^^^^^^^^^^^^^^^^^^
Some simulations are so large or take so much time that it is not reasonable to run them on a single CPU on a single machine. Fortunately, the `Message Passing Interface <http://www.mpi-forum.org/>`_ was developed to enable different computers working on the same program to exchange data. You will need a MPI package installed to be abel to use this feature with your simulations. One popular implementation of MPI is `OpenMPI <http://www.open-mpi.org>`_.

Atom-optics-specific hints
--------------------------

Separate out imaginary-time calculation code
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When doing simulations that require the calculation of the groundstate (typically via the imaginary time algorithm), typically the groundstate itself does not need to be changed frequently as it is usually the dynamics of the simulation that have the interesting physics. In this case, you can save having to re-calculate groundstate every time by having one script (call it ``groundstate.xmds``) that saves the calculated groundstate to a file using a breakpoint, and a second simulation that loads this calculated groundstate and then performs the evolution. More often than not, you won't need to re-run the groundstate finder.

The file format used in this example is `HDF5 <http://www.hdfgroup.org/HDF5/>`_, and you will need the HDF5 libraries installed to use this example. The alternative is to use the deprecated ``binary`` format, however to load ``binary`` format data ``xmds``, the predecessor to ``xpdeint`` must be installed. Anyone who has done this before will tell you that installing it isn't a pleasant experience, and so HDF5 is the recommended file format.

If your wavefunction vector is called ``'wavefunction'``, then to save the groundstate to the file ``groundstate_break.h5`` in the HDF5 format, put the following code immediately after the integrate block that calculates your groundstate:

.. code-block:: xpdeint

    <breakpoint filename="groundstate_break" format="hdf5">
      <dependencies>wavefunction</dependencies>
    </breakpoint>

In addition to the ``groundstate_break.h5`` file, an XSIL wrapper ``groundstate_break.xsil`` will also be created for use with :ref:`xsil2graphics2`.

To load this groundstate into your evolution script, the declaration of your ``'wavefunction'`` vector in your evolution script should look something like

.. code-block:: xpdeint

    <vector name="wavefunction">
      <components>phi1 phi2</components>
      <initialisation kind="hdf5">
        <filename>groundstate_break.h5</filename>
      </initialisation>
    </vector>

Note that the groundstate-finder doesn't need to have all of the components that the evolution script needs. For example, if you are considering the evolution of a two-component BEC where only one component has a population in the groundstate, then your groundstate script can contain only the ``phi1`` component, while your evolution script can contain both the ``phi1`` component and the ``phi2`` component. Note that the geometry of the script generating the groundstate and the evolution script must be the same.

Use an energy or momentum offset
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This is just the interaction picture with a constant term in the Hamiltonian. If your state is going to rotate like :math:`e^{i(\omega + \delta\omega)t}`, then transform your equations to remove the :math:`e^{i \omega t}` term. Likewise for spatial rotations, if one mode will be moving on average with momentum :math:`\hbar k`, then transform your equations to remove that term. This way, you may be able to reduce the density of points you need in that dimension. Warning: don't forget to consider this when looking at your results. I (Graham Dennis) have been tripped up on multiple occasions when making this optimisation.
