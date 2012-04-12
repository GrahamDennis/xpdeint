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
