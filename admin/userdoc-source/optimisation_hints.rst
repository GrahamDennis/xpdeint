.. _OptimisationHints:

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
Dimensions using matrix transforms should be first for performance reasons.  Unless you're using MPI, in which case XMDS can work it out for the first two dimensions.  Ideally, XMDS would sort it out in all cases, but it's not that smart yet.

Reduce code complexity
----------------------
Avoid transcendental functions like :math:`\sin(x)` or :math:`\exp(x)` in inner loops. Not all operations are made equal, use multiplication over division.

.. _OptimisingIPOperators:

Optimising with the Interaction Picture (IP) operator
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
You should use the IP operator when you can. Only use the EX operator when you have to. If you must use the EX operator, consider making it ``constant="no"``. It uses less memory.
When you use the IP operator, make sure you know what it's doing.  Do not pre- or post-multiply that term in your equations, XMDS will do a fairly thorough check to see you aren't using the IP operator improperly, but it is possible to confuse XMDS's check.

If your simulation uses two or more dimensions, check to see if your IP operator is separable, i.e. can be written in the form :math:`f(kx) + g(ky)` (this is frequently possible in atom-optics simulations). If your IP operator is separable, create separate IP operators for each dimension.  This provides a significant speedup (~30%) for simulations using an adaptive integrator.  For example, instead of using the IP operator:

.. code-block:: xpdeint

  <operator kind="ip">
    <operator_names>T</operator_names>
    <![CDATA[
      T = -i*0.5*hbar/M*(kx*kx + ky*ky);
    ]]>
  </operator>
  <![CDATA[
    dpsi_dt = T[psi] + /* other terms */
  ]]>

replace it with the pair of IP operators:

.. code-block:: xpdeint

  <operator kind="ip" dimensions="x">
    <operator_names>Tx</operator_names>
    <![CDATA[
      Tx = -i*0.5*hbar/M*kx*kx;
    ]]>
  </operator>
  <operator kind="ip" dimensions="y">
    <operator_names>Ty</operator_names>
    <![CDATA[
      Ty = -i*0.5*hbar/M*ky*ky;
    ]]>
  </operator>
  <![CDATA[
    dpsi_dt = Tx[psi] + Ty[psi] + /* other terms */
  ]]>

When using the IP operator, check if your operator is purely real or purely imaginary.  If real, (e.g. ``L = -0.5*kx * kx;``), then add the attribute ``type="real"`` to the ``<operator kind="ip">`` tag.  If purely imaginary, use ``type="imaginary"``.  This optimisation saves performing the part of the complex exponential that is unnecessary.

Consider writing the evolution in spectral basis
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Evolution equations do not need to be written in the position basis.  If your equations are diagonal in the spectral basis, then it makes more sense to compute the time derivative terms in that basis.  For example, if you have the system

.. math::
    \frac{d\psi_1(x)}{dt} &= i \frac{\hbar}{2M} \frac{d^2\psi_1(x)}{dx^2} - i \Omega \psi_2(x)\\
    \frac{d\psi_2(x)}{dt} &= i \frac{\hbar}{2M} \frac{d^2\psi_2(x)}{dx^2} - i \Omega \psi_1(x)

then this is diagonal in the Fourier basis where it takes the form

.. math::
    \frac{d\psi_1(k_x)}{dt} &= -i \frac{\hbar k_x^2}{2M} \psi_1(k_x) - i \Omega \psi_2(k_x)\\
    \frac{d\psi_2(k_x)}{dt} &= -i \frac{\hbar k_x^2}{2M} \psi_2(k_x) - i \Omega \psi_1(k_x)


The first term in each evolution equation can be solved exactly with an IP operator, and the second term is diagonal in Fourier space.  This can be written in XMDS as:

.. code-block:: xpdeint

    <operators>
      <integration_vectors basis="kx">wavefunction</integration_vectors>
      <operator kind="ip" type="imaginary" >
        <operator_names>Lxx</operator_names>
        <![CDATA[
          Lxx = -i*0.5*hbar_M*(kx*kx);
        ]]>
      </operator>
      <![CDATA[

        dpsi0_dt = Lxx[psi0] - i*Omega*psi1;
        dpsi1_dt = Lxx[psi1] - i*Omega*psi0;
          
      ]]>
    </operators>

Although the ``dpsi0_dt`` code reads the same in position and Fourier space, it is the ``basis=kx`` attribute on ``<integration_vectors>`` that causes the evolution code to be executed in Fourier space.  

A final optimisation is to cause the integration code itself to operate in Fourier space.  By default, all time stepping (i.e. :math:`f(t + \Delta t) = f(t) + f'(t) \Delta t` for forward-Euler integration) occurs in the position space.  As the derivative terms can be computed in Fourier space, it is faster to also to the time stepping in Fourier space too.  This then means that no Fourier transforms will be needed at all during this integrate block (except as needed by sampling).  To cause time-stepping to happen in Fourier space, we add the ``home_space="k"`` attribute to the surrounding ``<integrate>`` block.  By default, ``home_space`` has the value ``"x"`` which means position space, even if you don't have an ``x`` dimension.

The fully optimised code then reads:

.. code-block:: xpdeint

    <integrate algorithm="ARK45" interval="1" tolerance="1e-6" home_space="k">
      <samples> 10 </samples>
      <operators>
        <integration_vectors basis="kx">wavefunction</integration_vectors>
        <operator kind="ip" type="imaginary" >
          <operator_names>Lxx</operator_names>
          <![CDATA[
            Lxx = -i*0.5*hbar_M*(kx*kx);
          ]]>
        </operator>
        <![CDATA[

          dpsi0_dt = Lxx[psi0] - i*Omega*psi1;
          dpsi1_dt = Lxx[psi1] - i*Omega*psi0;
          
        ]]>
      </operators>
    </integrate>

This code will not use any Fourier transforms during an ordinary time-stepping, and will be much faster than if the code were written without the ``home_space`` and ``basis`` attributes.

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

**Note for Linux users**

If you used the linux installer, and are using Ubuntu or Debian, the version of the ATLAS package that gets installed is the generic version in the repositories. This version lacks architecture and CPU-specific optimizations. 

Creating an ATLAS package locally tuned for your specific machine will result in a faster linear algebra implementation, which can significantly speed up problems utilizing matrix based transforms (bessel, hermite-gauss etc). Some simple tests using a cylindrically symmetric problem with one bessel transform dimension and one FFT transform dimension showed speed increases from 5% - 100% over the default ATLAS package, depending on the number of grid points.

To create and install an ATLAS package optimized for your machine, carry out the following procedure:

Using your favourite package manager (e.g. Synaptic) to remove any current ATLAS libraries (probably libatlas3gf-base, libatlas-dev, libatlas-base-dev). Then create an empty directory whose path doesn't include any spaces. In this directory, do

.. code-block:: xpdeint

  apt-get source atlas
  apt-get build-dep atlas
  apt-get install devscripts dpkg-dev

  cd atlas-*
  sudo fakeroot debian/rules custom
  cd ..
  ls libatlas*.deb

Then, for each of the .deb packages listed by the ls command, install via:

.. code-block:: xpdeint

  sudo dpkg -i <filename here>.deb

This procedure was tested on Ubuntu 12.04 LTS, but an identical or very similar procedure should work for other Ubuntu/Debian versions. 

Finally, note that the "sudo fakeroot debian/rules custom" package creation step carries out an exhaustive series of tests to optimize for your architecture, SSE support, cache hierarchy and so on, and can take a long time. Be patient.


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
