Developer Documentation
=======================

Developers need to know more than users.  For example, they need to know about the test suite, and writing test cases.  They need to know how to perform a developer installation.  They need to know how to edit and compile this documentation.  They need a step-by-step release process.

.. _TestScripts:

Test scripts
============

Every time you add a new feature and/or fix a new and exciting bug, it is a great idea to make sure that the new feature works and/or the bug stays fixed.  Fortunately, it is pleasantly easy to add a test case to the testing suite.

1. Write normal XMDS script that behaves as you expect.
2. Add a ``<testing>`` element to your script.  You can read the description of this element and its contents below, and have a look at other testcases for examples, but the basic structure is simple:.

.. parsed-literal::

      <:ref:`testing <TestingElement>`> 
        <:ref:`command_line <CommandLineElement>`> <:ref:`/command_line <CommandLineElement>`>
        <:ref:`arguments <ArgumentsElement>`>
          <:ref:`argument <ArgumentElement>` />
          <:ref:`argument <ArgumentElement>` />
          ...
        <:ref:`/arguments <ArgumentsElement>`>
        <:ref:`input_xsil_file <InputXSILFileElement>` />
        <:ref:`xsil_file <XSILFileElement>`>
          <:ref:`moment_group <MomentGroupElement>` />
          <:ref:`moment_group <MomentGroupElement>` />
          ...
        <:ref:`/xsil_file <XSILFileElement>`>
      <:ref:`/testing <TestingElement>`>
      
3. Put into the appropriate ``testsuite/`` directory.
4. run ``./run_tests.py`` This will automatically generate your ``_expected`` files.
5. Commit the ``.xmds``, ``*_expected.xsil`` file and any ``*_expected*`` data files.
  
.. _TestingElement:

Testing element
---------------



.. _CommandLineElement:

command_line element
--------------------


.. _InputXSILFileElement:

input_xsil_file element
-----------------------


.. _XSILFileElement:

xsil_file element
-----------------


.. _MomentGroupElement:

moment_group element
--------------------



Steps to update ``XMDS`` script validator (XML schema)
======================================================

1. Modify ``xpdeint/support/xpdeint.rnc``. This is a RelaxNG compact file, which specifies the XML schema which is only used for issuing warnings to users about missing or extraneous XML tags / attributes.
2. Run ``make`` in ``xpdeint/support/`` to update ``xpdeint/support/xpdeint.rng``. This is the file which is actually used, which is in RelaxNG format, but RelaxNG compact is easier to read and edit.
3. Commit both ``xpdeint/support/xpdeint.rnc`` and ``xpdeint/support/xpdeint.rng``.


Directory layout
================

XMDS2's code and templates
--------------------------

All ``.tmpl`` files are Cheetah template files.  These are used to generate C++ code.  These templates are compiled as part of the XMDS2 build process to ``.py`` files of the same name.  Do not edit the generated ``.py`` files, always edit the ``.tmpl`` files and regenerate the corresponding ``.py`` files with ``make``.

* ``xpdeint/``: 
	* ``Features/``: Code for all ``<feature>`` elements, such as ``<globals>`` and ``<auto_vectorise>``
		* ``Transforms/``: Code for the Fourier and matrix-based transforms (including MPI variants).
	* ``Geometry/``: Code for describing the geometry of simulation dimensions and domains.  Includes code for ``Geometry``, ``Field`` and all ``DimensionRepresentation``s.
	* ``Operators/``: Code for all ``<operator>`` elements, including ``IP``, ``EX`` and the temporal derivative operator ``DeltaA``.
	* ``Segments/``: Code for all elements that can appear in a ``<segments>`` tag.  This includes ``<integrate>``, ``<filter>``, and ``<breakpoint>``.
		* ``Integrators``: Code for fixed and adaptive integration schemes, and all steppers (e.g. ``RK4``, ``RK45``, ``RK9``, etc.)
	* ``Stochastic/``: Code for all random number generators and the random variables derived from them.
		* ``Generators/``: Code for random number generators, includes ``dSFMT``, ``POSIX``, ``Solirte``.
		* ``RandomVariables/``: Code for the random variables derived from the random number generators.  These are the gaussian, poissonian and uniform random variables.
	* ``SimulationDrivers/``: Code for all ``<driver>`` elements.  In particular, this is where the location of MPI and multi-path code.
	* ``Vectors/``: Code for all ``<vector>`` elements, and their initialisation.  This includes normal ``<vector>`` elements as well as ``<computed_vector>`` and ``<noise_vector>`` elements.
	* ``includes/``: C++ header and sources files used by the generated simulations.
	* ``support/``: Support files
		* ``wscript``: ``waf`` build script for configuring and compiling generated simulations
		* ``xpdeint.rnc``: Compact RelaxNG XML validation for XMDS scripts.  This is the source file for the XML RelaxNG file ``xpdeint.rng``
		* ``xpdeint.rng``: RelaxNG XML validation for XMDS scripts.  To regenerate this file from ``xpdeint.rnc``, just run ``make`` in this directory.
	* ``waf/``: Our included version of the Python configuration and build tool ``waf``.
	* ``waf_extensions/``: ``waf`` tool for compiling Cheetah templates.
	* ``xsil2graphics2/``: Templates for the output formats supported by ``xsil2graphics2``.
	* ``wscript``: ``waf`` build script for XMDS2 itself.
	* ``CodeParser.py``: Minimally parses included C++ code for handling nonlocal dimension access, IP/EX operators and IP operator validation.
	* ``Configuration.py``: Manages configuration and building of generated simulations.
	* ``FriendlyPlusStyle.py``: Sphinx plug-in to improve formatting of XMDS scripts in user documentation.
	* This directory also contains code for the input script parser, code blocks, code indentation, and the root ``_ScriptElement`` class.


Support files
-------------

* ``admin/``: Documentation source, Linux installer and release scripts.
	* ``developer-doc-source/``: source for epydoc python class documentation (generated from python code).
	* ``userdoc-source/``: source for the user documentation (results visible at www.xmds.org and xmds2.readthedocs.org).
	* ``xpdeint.tmbundle/``: TextMate support bundle for Cheetah templates and XMDS scripts
* ``bin/``: Executable scripts to be installed as part of XMDS2 (includes ``xmds2`` and ``xsil2graphics2``).
* ``examples/``: Example XMDS2 input scripts demonstrating most of XMDS2's features.
* ``testsuite/``: Testsuite of XMDS2 scripts.  Run the testsuite by executing ``./run_tests.py``