.. _FAQ:

Frequently Asked Questions
==========================

XMDS scripts look complicated! How do I start?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you're unfamiliar with XMDS2, writing a script from scratch might seem difficult. In most cases, however, the best approach is to take an existing script and modify it for your needs. At the most basic level, you can simply take a script from the /examples directory that is similar to what you want to do, change the name of the integration variable(s) and replace the line describing the differential equation to use your DE instead. That's all you need to do, and will ensure all the syntax is correct and all the required XML blocks are present.

You can then incrementally change things such as the number of output points, what quantities get output, number of grid points, and so on. Many XMDS2 users have never written a script from scratch, and just use their previous scripts and example scripts as a scaffold when they create a script for a new problem.


Where can I get help?
~~~~~~~~~~~~~~~~~~~~~

The documentation on this website is currently incomplete, but it still covers a fair bit and is worth reading. Similarly, the example scripts in the /examples directory cover most of the functionality of XMDS2, so it's worth looking looking through them to see if any of them do something similar to what you're trying to do.

You should also feel free to email questions to the XMDS users' mailing list at xmds-users@lists.sourceforge.net, where the developers and other users can assist you. You can join the mailing list by going to http://sourceforge.net/projects/xmds/ and clicking on "mailing lists." Also, if you look through the mailing list archives, your particular problem may already have been discussed.


How should I cite XMDS2?
~~~~~~~~~~~~~~~~~~~~~~~~
If you publish work that has involved XMDS2, please cite it as: `Comput. Phys. Commun. 184, 201-208 (2013) <http://dx.doi.org/10.1016/j.cpc.2012.08.016>`_.


I think I found a bug! Where should I report it?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Please report bugs to the developer mailing list at xmds-devel@lists.sourceforge.net. In your email, please include a description of the problem and attach the XMDS2 script that triggers the bug.


How do I put time dependence into my vectors?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Standard vectors can't have time dependence (or, more accurately, depend on the ``propagation_dimension`` variable), but computed vectors can. So, for example, if you have set your ``propagation_dimension`` as "t", you can simply use the variable "t" in your computed vector and it will work. 

Alternatively, you can explicitly use the ``propagation_dimension`` variable in your differential equation inside the ``<operators>`` block.  


Can I specify the range of my domain and number of grid points at run-time?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Yes, you can. In your script, specify the domain and number of grid points as arguments to be passed in at run-time, use those variables in your ``<geometry>`` block rather than explicitly specifying them, and use the ``<validation kind="run-time" />`` feature. See the :ref:`Validation <Validation>` entry in the Reference section for an example.

While the domain can always be specified in this way, specifying the lattice size at run-time is currently only allowed with the following transforms: 'dct', 'dst', 'dft' and 'none' (see :ref:`Transforms <Validation>` in the Reference section).

Also note that for some multi-dimensional spaces using different transforms, XMDS2 will sometimes optimise the code it generates based on the relative sizes of the dimensions. If one or more of the lattices are specified at run-time it is unable to do this and will have to make guesses. In some situations this may result in slightly slower code.


When can I use IP operators (and why should I) and when must I use EX operators?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

An :ref:`<operator><OperatorNamesElement>` that specifies named operators to be used in integration equations can have the ``kind="IP"`` or ``kind="EX"`` attribute, standing for 'interaction picture' and 'explicit' operators respectively.  Explicit operators can be used in all situations, and simply construct and calculate a new vector of the form in the square brackets.  IP operators use less memory and can improve speed by allowing larger timesteps, but have two important restrictions.  **Use of IP operators without understanding these restrictions can lead to incorrect code**.  

Some explanation is in order.  The IP algorithm applies the operator separately to the rest of the evolution.  The reason this can be so effective is that the separate evolution can be performed exactly.  The solution of the equation :math:`\frac{d \psi}{dt} = L \psi` is :math:`\psi(t+\Delta t) = exp(L \Delta t) \psi(t)` for arbitrarily large timestep :math:`\Delta t`.  For a diagonal linear ``L``, the matrix exponential is straightforward.  Also, when it is constant, then the exponential can be computed and stored prior to the integration, which makes the implementation of this operator very cheap.  Thus, when IP operators are defined, XMDS2 reads the equations as written by the user, and determines which operators to apply to which fields.  It then implements these operators separately, and the text describing the operator inside the equations (in this example, the ``L[psi]`` term) is replaced by the numeral zero.  

Therefore, the limitations of IP operators themselves means that they can only be applied to to named components of one of the integration vectors, and not functions of those components.  Furthermore, an IP operator acting on a component must only be used in the derivative for that particular component.  Secondly, due to the implementation of IP operators in XMDS2, it is not safe to use them in comments, or in conjunction with declared variables.  It is also not safe to multiply or divide them by any factors, functions or vectors.  They must turn up in a purely additive way when defining the derivative of a component of an integration vector.  The XMDS2 parser attempts to catch possible violations of these rules, and will produce warnings in some cases.


Visual Editors
~~~~~~~~~~~~~~

In this section goes stuff about how to set up TextMate (or other editors to highlight xpdeint scripts).
