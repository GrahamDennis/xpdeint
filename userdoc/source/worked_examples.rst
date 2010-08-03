.. _WorkedExamples:

Worked Examples
===============

One of the best ways to learn XMDS2 is to see several illustrative examples.  Here are a set of example scripts and explanations of the code, which will be a good way to get started.  As an instructional aid, they are meant to be read sequentially, but the adventurous could try starting with one that looked like a simulation they wanted to run, and adapt for their own purposes.

   :ref:`NonLinearSchrodingerEquation` (partial differential equation)
   
   :ref:`Kubo` (stochastic differential equations)

.. _NonLinearSchrodingerEquation:

The nonlinear Schrodinger equation
----------------------------------

This worked example will show a range of new features that can be used in an **XMDS2** script, and we will also examine our first partial differential equation.  We will take the one dimensional nonlinear Schrodinger equation, which is a common nonlinear wave equation.  The equation describing this problem is:

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
  
      <vector name="wavefunction" type="complex" dimensions="tau">
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

Two vector elements have been defined in this simulation.  One defines the complex-valued wavefunction "phi" that we wish to evolve.  We define the transverse dimensions over which this vector is defined by the ``dimensions`` tag in the description.  By default, it is defined over all of the transverse dimensions in the ``<geometry>`` element, so even though we have omitted this tag for the second vector, it also assumes that the vector is defined over all of tau.  

The second vector element contains the component "Gamma" which is a function of the transverse variable tau, as specified in the equation of motion for the field.  This second vector could have been avoided in two ways.  First, the function could have been written explicitly in the integrate block where it is required, but calculating it once and then recalling it from memory is far more efficient.  Second, it could have been included in the "wavefunction" vector as another component, but then it would have been unnecessarily complex-valued, it would have needed an explicit derivative in the equations of motion (presumably "dGamma_dxi = 0;"), and it would have been Fourier transformed whenever the phi component was transformed.  So separating it as its own vector is far more efficient.

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

This example demonstrates the integration of a stochastic differential equation.  We examine the Kubo oscillator, which is a complex variable whose phase is evolving according to a Wiener noise.  In a suitable rotating frame, the equation of motion for the variable is

.. math::
    dz = i z dW

where we can interpret this as a Stratonovich or Ito differential equation, depending on the choice of rotating frame.  This equation is solved by the following XMDS2 script:

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
  
      <driver name="multi-path" paths="10000" />
  
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

The first new item in this script is the ``<driver>`` element.  This element enables us to change top level management of the simulation.  Without this element, XMDS2 will integrate the stochastic equation as described.  With this element and the option ``name="multi-path"``, it will integrate it multiple times, using different random numbers each time.  The output will then contain the mean values and standard errors of your output variables.  The number of integrations included in the averages is set with the ``paths`` variable.

In the ``<features>`` element we have included the ``<error_check>`` element.  This performs the integration first with the specified number of steps (or with the specified tolerance), and then with twice the number of steps (or equivalently reduced tolerance).  The output then includes the difference between the output variables on the coarse and the fine grids as the 'error' in the output variables.  This error is particularly useful for stochastic integrations, where algorithms with adaptive step-sizes are less safe, so the number of integration steps must be user-specified.

We define the stochastic elements in a simulation with the ``<noise_vector>`` element.  

.. code-block:: xpdeint

    <noise_vector name="drivingNoise" dimensions="" kind="wiener" type="real" method="dsfmt" seed="314 159 276">
     <components>dW</components>
    </noise_vector>
  
This defines a vector that is used like any other, but it will be randomly generated with particular statistics and characteristics rather than initialised.  The name, dimensions and type tags are defined just as for normal vectors.  The names of the components are also defined in the same way.  The noise is defined as a Wiener noise here (``kind = "wiener"``), which is a zero-mean Gaussian random noise with an average variance equal to the discretisation volume (here it is just the step size in the propagation dimension, as it is not defined over transverse dimensions).  Other noise types are possible, including uniform and Poissonian noises, but we will not describe them in detail here.  

We may also define a noise method to choose a non-default pseudo random number generator, and a seed for the random number generator.  Using a seed can be very useful when debugging the behaviour of a simulation, and many compilers have pseudo-random number generators that are superior to the default option (posix).

The integrate block is using the semi-implicit algorithm (``algorithm="SI"``), which is a good default choice for stochastic problems, even though it is only second order convergent for deterministic equations.  More will be said about algorithm choice later, but for now we should note that adaptive algorithms based on Runge-Kutta methods are not guaranteed to converge safely for stochastic equations.  This can be particularly deceptive as they often succeed, particularly for almost any problem for which there is a known analytic solution.  

We include elements from the noise vector in the equation of motion just as we do for any other vector.  The default SI and Runge-Kutta algorithms converge to the *Stratonovich* integral.  Ito stochastic equations can be converted to Stratonovich form and vice versa.

Executing the generated program 'kubo' gives slightly different output due to the "multi-path" driver.

.. code-block:: none

            $ ./kubo
            Beginning full step integration ...
            Starting path 1
            Starting path 2

            ... many lines omitted ...

            Starting path 9999
            Starting path 10000
            Beginning half step integration ...
            Starting path 1
            Starting path 2

            ... many lines omitted ...

            Starting path 9999
            Starting path 10000
            Generating output for kubo
            Maximum step error in moment group 1 was 4.942549e-04
            Time elapsed for simulation is: 2.71 seconds

The maximum step error in each moment group is given in absolute terms.  This is the largest difference between the full step integration and the half step integration.  While a single path might be very stochastic:

.. figure:: images/kuboSingle.*
    :align: center
    
    The mean value of the real and imaginary components of the z variable for a single path of the simulation.
    
The average over multiple paths can be increasingly smooth.  

.. figure:: images/kubo10000.*
    :align: center

    The mean and standard error of the z variable averaged over 10000 paths, as given by this simulation.  It agrees within the standard error with the expected result of :math:`\exp(-t/2)`.

