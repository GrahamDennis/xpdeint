.. _WorkedExamples:

Worked Examples
===============

   :ref:`NonLinearSchrodingerEquation` (partial differential equation)
   
   :ref:`Kubo` (stochastic differential equations)

.. _NonLinearSchrodingerEquation:

The nonlinear Schrodinger equation
----------------------------------

This worked example will show a range of new features that can be used in an **XMDS2** script, and we will also examine our first partial differential equation.  We will take the one dimensional nonlinear Schrodinger equation, which is a common nonlinear wave equation.  The equation describing this problem is

.. math::
    \frac{\partial \phi}{\partial \xi} = i \left[\frac{1}{2}\frac{\partial^2 \phi}{\partial \tau^2} + i\Gamma(\tau)\phi+|\phi|^2\right]

where :math:`\phi` is a complex-valued field, and :math:`\Gamma(\tau)` is a :math:`\tau`-dependent damping term.  Let us look at an XMDS2 script that integrates this equation, and then examine it in detail.

.. code-block:: xpdeint

    <simulation xmds-version="2">
      <name>nlse</name>
  
      <author>Joe Hope</author>
      <description>
        The nonlinear Schrodinger equation in one dimension, 
        which is a simple partial differential equation.  
        We introduce several new features in this script.
      </description>
  
      <features>
          <benchmark />
          <bing />
          <fftw plan="patient" />
          <openmp />
          <auto_vectorise />
          <globals>
              <![CDATA[
              const double energy = 4;
              const double vel = 0.3;
              const double hwhm = 1.0;
              ]]>
           </globals>
         </features>

      <geometry>
          <propagation_dimension> xi </propagation_dimension>
          <transverse_dimensions>
            <dimension name="tau" lattice="128"  domain="(-6, 6)" />
          </transverse_dimensions>
       </geometry>
  
      <vector name="wavefunction" type="complex">
        <components> phi </components>
        <initialisation>
          <![CDATA[
          const double w0 = hwhm*sqrt(2/log(2));
          const double amp = sqrt(energy/w0/sqrt(M_PI/2));
          phi = amp*exp(-tau*tau/w0/w0)*exp(i*vel*tau);
          ]]>
        </initialisation>
      </vector>
  
      <vector name="dampingVector" type="real">
        <components> Gamma </components>
        <initialisation>
          <![CDATA[
          Gamma=1.0*(1-exp(-pow(tau*tau/4.0/4.0,10)));
          ]]>
        </initialisation>
      </vector>

      <sequence>
        <integrate algorithm="ARK45" interval="20.0" tolerance="1e-7">
          <samples>10 100 10</samples>
          <operators>
            <integration_vectors>wavefunction</integration_vectors>
            <operator kind="ex" constant="yes">
              <operator_names>Ltt</operator_names>
              <![CDATA[
                Ltt = -i*ktau*ktau*0.5;
              ]]>
            </operator>
            <![CDATA[
            dphi_dxi = Ltt[phi] - phi*Gamma + i*mod2(phi)*phi;
            ]]>
            <dependencies>dampingVector</dependencies>
          </operators>
        </integrate>
      </sequence>
  
      <output format="binary" filename="nlse.xsil">
        <group>
          <sampling initial_sample="yes">
            <dimension name="tau" lattice="128" />
            <moments>density</moments>
            <dependencies>wavefunction</dependencies>
            <![CDATA[
              density = mod2(phi);
            ]]>
          </sampling>
        </group>

        <group>
          <sampling initial_sample="yes">
            <dimension name="tau" lattice="0" />
            <moments>normalisation</moments>
            <dependencies>wavefunction</dependencies>
            <![CDATA[
              normalisation = mod2(phi);
            ]]>
          </sampling>
        </group>

        <group>
          <sampling initial_sample="yes">
            <moments>densityK</moments>
            <dimension name="tau" fourier_space="yes" lattice="32" />
            <dependencies>wavefunction</dependencies>
            <![CDATA[
              densityK = mod2(phi);
            ]]>
          </sampling>
        </group>

      </output>
    </simulation>

Let us examine the new items in the ``<features>`` element that we have demonstrated here.  The existence of the ``<benchmark>`` element causes the simulation to be timed.  The ``<bing>`` element causes the computer to make a sound upon the conclusion of the simulation.  The ``<fftw>`` element is used to pass options to the `FFTW libraries for fast Fourier transforms <http://fftw.org>`_, which are needed to do spectral derivatives for the partial differential equation.  Here we used the option `plan="patient"`, which makes the simulation test carefully to find the fastest method for doing the FFTs.  More information on possible choices can be found in the `FFTW documentation <http://fftw.org>`_.

Finally, we use two tags to make the simulation run faster.  The ``<auto_vectorise>`` element switches on several loop optimisations that exist in later versions of the GCC compiler.  The ``<openmp>`` element turns on threaded parallel processing using the OPENMP standard where possible.  These options are not activated by default as they only exist on certain compilers.  If your code compiles with them on, then they are recommended.

Let us examine the ``<geometry>`` element.

.. code-block:: xpdeint

      <geometry>
          <propagation_dimension> xi </propagation_dimension>
          <transverse_dimensions>
            <dimension name="tau" lattice="128"  domain="(-6, 6)" />
          </transverse_dimensions>
       </geometry>

This is the first example that includes a transverse dimension.  We have only one dimension, and we have labelled it "tau".  It is a continuous dimension, but only defined on a grid containing 128 points (defined with the lattice variable), and on a domain from -6 to 6.  The default is that transforms in continuous dimensions are fast Fourier transforms, which means that this dimension is effectively defined on a loop, and the "tau=-6" and "tau=6" positions are in fact the same.  Other transforms are possible, as are discrete dimensions such as an integer-valued index, but we will leave these advanced possibilities to later examples.

Two vector elements have been defined in this simulation.  One defines the complex-valued wavefunction "phi" that we wish to evolve, and the other contains the component "Gamma" which is a function of the transverse variable tau, as specified in the equation of motion for the field.  This second vector could have been avoided in two ways.  First, the function could have been written explicitly in the integrate block where it is required, but calculating it once and then recalling it from memory is far more efficient.  Second, it could have been included in the "wavefunction" vector as another component, but then it would have been unnecessarily complex-valued, it would have needed an explicit derivative in the equations of motion (presumably "dGamma_dxi = 0;"), and it would have been Fourier transformed whenever the phi component was transformed.  So separating it as its own vector is far more efficient.

The ``<integrate>`` element for a partial differential equation has some new features:

.. code-block:: xpdeint

        <integrate algorithm="ARK45" interval="20.0" tolerance="1e-7">
          <samples>10 100 10</samples>
          <operators>
            <integration_vectors>wavefunction</integration_vectors>
            <operator kind="ex" constant="yes">
              <operator_names>Ltt</operator_names>
              <![CDATA[
                Ltt = -i*ktau*ktau*0.5;
              ]]>
            </operator>
            <![CDATA[
            dphi_dxi = Ltt[phi] - phi*Gamma + i*mod2(phi)*phi;
            ]]>
            <dependencies>dampingVector</dependencies>
          </operators>
        </integrate>

There are some trivial changes from the tutorial script, such as the fact that we are using the ARK45 algorithm rather than ARK89.  Higher order algorithms are often better, but not always.  Also, since this script has multiple output groups, we have to specify how many times each of these output groups are sampled in the ``<samples>`` element, so there are three numbers there.  Besides the vectors that are to be integrated, we also specify that we want to use the vector "dampingVector" during this integration.  This is achieved by including the ``<dependencies>`` element inside the ``<operators>`` element.

The equation of motion as written in the CDATA block looks almost identical to our desired equation of motion, except for the term based on the second derivative, which introduces an important new concept.  Inside the ``<operators>`` element, we can define any number of operators.  Operators are used to define functions in the transformed space of each dimension, which in this case is Fourier space.  The derivative of a function is equivalent to multiplying by :math:`-i*k` in Fourier space, so the :math:`\frac{i}{2}\frac{\partial^2 \phi}{\partial \tau^2}` term in our equation of motion is equivalent to multiplying by :math:`-\frac{i}{2}k_\tau^2` in Fourier space.  In this example we define "Ltt" as an operator of exactly that form, and in the equation of motion it is applied to the field "phi".  

Operators can be explicit (``kind="ex"``) or in the interaction picture (``kind="ip"``).  The interaction picture can be more efficient, but it restricts the possible syntax of the equation of motion.  Safe utilisation of interaction picture operators will be described later, but for now let us emphasise that **explicit operators should be used** unless the user is clear what they are doing.  The ``constant="yes"`` option in the operator block means that the operator is not a function of the propagation dimension "xi", and therefore only needs to be calculated once at the start of the simulation.

The output of a partial differential equation offers more possibilities than an ordinary differential equation, and we examine some in this example.

For vectors with transverse dimensions, we can sample functions of the vectors on the full lattice or a subset of the points.  For each of the transverse dimensions we include a ``<dimension>`` element that specifies how many lattice points are to be sampled.  This must be a factor of the lattice size for that dimension.  If the dimension is specified without the lattice, the entire lattice will be sampled.  If the dimension is not described at all, then the output will only sample a single lattice point on that dimension.  

.. code-block:: xpdeint

        <group>
          <sampling initial_sample="yes">
            <dimension name="tau" lattice="128" />
            <moments>density</moments>
            <dependencies>wavefunction</dependencies>
            <![CDATA[
              density = mod2(phi);
            ]]>
          </sampling>
        </group>

The first output group samples the mod square of the vector "phi" over the full lattice of 128 points.

If the lattice parameter is set to zero, then the corresponding dimension is integrated.

.. code-block:: xpdeint

        <group>
          <sampling initial_sample="yes">
            <dimension name="tau" lattice="0" />
            <moments>normalisation</moments>
            <dependencies>wavefunction</dependencies>
            <![CDATA[
              normalisation = mod2(phi);
            ]]>
          </sampling>
        </group>

This second output group samples the normalisation of the wavefunction :math:`\int d\tau |\phi(\tau)|^2` over the domain of :math:`\tau`.  This output requires only a single real number per sample, so we have sampled it many more times than the vectors themselves.

Finally, functions of the vectors can be sampled with their dimensions in Fourier space.

.. code-block:: xpdeint

        <group>
          <sampling initial_sample="yes">
            <moments>densityK</moments>
            <dimension name="tau" fourier_space="yes" lattice="32" />
            <dependencies>wavefunction</dependencies>
            <![CDATA[
              densityK = mod2(phi);
            ]]>
          </sampling>
        </group>

The final output group above samples the mod square of the Fourier-space wavefunction phi on a sample of 32 points.


.. _Kubo:

Kubo Oscillator
---------------

This example demonstrates the integration of a stochastic differential equation.  We examine the Kubo oscillator.

.. math::
    \frac{dx}{dt} &= \sigma (y - x)\\
    \frac{dy}{dt} &= x (\rho - z) - y\\
    \frac{dz}{dt} &= xy - \beta z

where we will solve with the parameters :math:`\sigma=10`, :math:`\rho=28`, :math:`\beta = \frac{8}{3}` and the initial condition :math:`x(0) = y(0) = z(0) = 1`.

Below is a minimal script that solves this problem. Don't worry if it doesn't make sense yet, soon we'll break it down into easily digestible parts.

.. code-block:: xpdeint

    <simulation xmds-version="2">
      <name>kubo</name>
      <author>Graham Dennis and Joe Hope</author>
      <description>
        Example Kubo oscillator simulation
      </description>
  
      <geometry>
        <propagation_dimension> t </propagation_dimension>
      </geometry>
  
      <driver name="multi-path" paths="1" />
  
      <features>
        <error_check />
        <benchmark />
      </features>

      <noise_vector name="drivingNoise" dimensions="" kind="wiener" type="real" method="dsfmt" seed="314 159 276">
        <components>dW</components>
      </noise_vector>
  
      <vector name="main" type="complex">
        <components> z </components>
        <initialisation noises="">
          <![CDATA[
            z = 1.0;
          ]]>
        </initialisation>
      </vector>
  
      <sequence>
        <integrate algorithm="SI" interval="10" steps="1000">
          <samples>100</samples>
          <operators>
            <integration_vectors>main</integration_vectors>
            <dependencies>drivingNoise</dependencies>
            <![CDATA[
              dz_dt = i*z*dW;
            ]]>
          </operators>
        </integrate>
      </sequence>

      <output format="ascii" filename="kubo.xsil">
        <group>
          <sampling initial_sample="yes">
            <moments>zR zI</moments>
            <dependencies>main</dependencies>
            <![CDATA[
              zR = z.Re();
              zI = z.Im();
            ]]>
          </sampling>
        </group>
      </output>
    </simulation>






You can compile and run this script with **xpdeint**. To compile the script, just pass the name of the script as an argument to **xpdeint**.

.. code-block:: none

    $ xpdeint lorenz.xmds
    g++ -o 'lorenz' 'lorenz.cc' -O3 -ffast-math -funroll-all-loops 
    -fomit-frame-pointer -lxmds -I"/Users/graham/Developer/xmds/xpdeint/xpdeint/includes" 

Now we can execute the generated program 'lorenz'.

.. code-block:: none

    $ ./lorenz
    Current timestep: 4.476617e-02
    Sampled field (for moment group #1) at t = 1.000000e-01
    Current timestep: 3.272028e-02
    Sampled field (for moment group #1) at t = 2.000000e-01
    Current timestep: 2.076453e-02
    Sampled field (for moment group #1) at t = 3.000000e-01
    Current timestep: 2.046119e-02
    Sampled field (for moment group #1) at t = 4.000000e-01
            ... many lines omitted ...
    Current timestep: 3.534532e-02
    Sampled field (for moment group #1) at t = 9.800000e+00
    Current timestep: 3.402670e-02
    Sampled field (for moment group #1) at t = 9.900000e+00
    Current timestep: 4.084675e-02
    Sampled field (for moment group #1) at t = 1.000000e+01
    Current timestep: 1.724322e-02
    Segment 1: minimum timestep: 1.324010e-02 maximum timestep: 1.000000e-01
      Attempted 314 steps, 0.96% steps failed.
    Generating output for lorenz


From this point on the plan is to break the above simulation to bits and describe each part separately. In each part the plan was to briefly mention the other kinds of things that can be done in a given part of the code, but not to go into the details. For example, when discussing the geometry element state that this is where you add additional dimensions to the problem but instead of stating how, simply say that this will be discussed in a later example. In the future we can link to the appropriate part of the documentation.
