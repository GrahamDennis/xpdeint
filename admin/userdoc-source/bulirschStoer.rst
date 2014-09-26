.. index:: Modified midpoint method

.. _MMDetail:

Modified Midpoint Method
~~~~~~~~~~~~~~~~~~~~~~~~

Although the modified midpoint can be used standalone as an ordinary differential equation integrator, it is regarded as much more powerful when used as a stepper to complement the Bulirsch-Stoer technique.

The modified midpoint method advances a vector of dependent variables :math:`y(x)` from a point :math:`x`, to a point :math:`x + H` by a sequence of :math:`n` substeps, each of size :math:`h=H/n`.

The number of right-hand side evaluations required by the modified midpoint method is :math:`n+1`.  The formulas for the method are

.. math::
    z_0 &= y(x) \\
    z_1 &= z_0 + h f(x, z_0) \\
    z_{m+1} &= z_{m-1} + 2 h f(x + m h, z_m)\; \text{ for } m = 1, 2, \dots, n-1 \\
    y(x+H) \approx y_n &= \frac{1}{2} \left[ z_n + z_{n-1} + h f(x + H, z_n) \right]
    
The error of this, expressed as a power series in :math:`h`, the stepsize, contains only even powers of :math:`h`:

.. math::
    y_n - y(x + H) &= \sum_{i=1}^{\infty} \alpha_i h^{2i}

where :math:`H` is held constant, but :math:`h` changes :math:`y` by varing the :math:`n` in :math:`h = H/n`.

The importance of this even power series is that using Richardson Extrapolation to combine steps and knock out higher-order error terms gains us two orders at a time.

The modified midpoint method is a second-order method, but holds an advantage over second order Runge-Kutta, as it only requires one derivative evaluation per step, instead of the two evaluations that Runge-Kutta necessitates.

.. index:: Bulirsch-Stoer algorithm

.. _BSDetail:

Bulirsch-Stoer Algorithm
~~~~~~~~~~~~~~~~~~~~~~~~

The Bulirsch-Stoer algorithm utilizes three core concepts in its design.

First, the usage of Richardson Extrapolation.

.. image:: images/modifiedMidpoint/richardsonExtrapolation.*
    :align: center

Richardson Extrapolation considers the final answer of a numerical calculation as being an analytic function of an adjustable parameter such as the stepsize :math:`h`. That analytic function can be probed by performing the calculation with various values of :math:`h`, none of them being necessarily small enough to yield the accuracy that we desire. When we know enough about the function, we fit it to some analytic form and then evaluate it at the point where :math:`h = 0`.

Secondly, the usage of rational function extrapolation in Richardson-type applications. Rational function fits can remain good approximations to analytic functions even after the various terms in powers of :math:`h`, all have comparable magnitudes. In other words, :math:`h` can be so large as to make the whole notion of the “order” of the method meaningless — and the method can still work superbly.

The third idea is to use an integration method whose error function is strictly even, allowing the rational function or polynomial approximation to be in terms of the variable :math:`h^2` instead of just :math:`h`.

These three ideas give us the Bulirsch-Stoer method, where a single step takes us from :math:`x` to :math:`x + H`, where :math:`H` is supposed to be a significantly large distance. That single step consists of many substeps of the modified midpoint method, which is then extrapolated to zero stepsize.

(Excerpts derived from **Numerical Recipes: The Art of Scientific Computing**, Third Edition (2007), p1256; Cambridge University Press; ISBN-10: 0521880688, `<http://www.nr.com/>`_)


.. index:: Bulirsch-Stoer error scaling

.. _ErrorScaling:

Error Scaling Behaviour
~~~~~~~~~~~~~~~~~~~~~~~

.. image:: images/modifiedMidpoint/error_scaling.*
    :width: 800px
    :height: 600px
    :align: center

The graph above shows the error scaling behaviour for the Bulirsch-Stoer method. This was generated using data from XMDS2 for a simple problem whose analytical solution was known. For more information and to generate this plot yourself see the testsuite/integrators/richardson_extrapolation/error_scaling directory. There you will find the .xmds files for generating the data and a python script to generate the plot above (requires gnuplot).

