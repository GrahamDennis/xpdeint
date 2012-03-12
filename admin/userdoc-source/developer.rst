Developer Documentation
=======================

Developers need to know more than users.  For example, they need to know about the test suite, and writing test cases.  They need to know how to perform a developer installation.  They need to know how to edit and compile this documentation.  They need a step-by-step release process.

Steps to create a test case
---------------------------

1. Write normal XMDS script for testcase.
2. Add a ``<testing>`` block.  See other testcases for examples.
3. Put into the appropriate ``testsuite/`` directory.
4. run ``./run_tests.py`` This will automatically generate your ``_expected`` files.
5. Commit the ``.xmds``, ``*_expected.xsil`` file and any ``*_expected*`` data files.

Steps to update ``XMDS`` script validator (XML schema)
------------------------------------------------------

1. Modify ``xpdeint/support/xpdeint.rnc``. This is a RelaxNG compact file, which specifies the XML schema which is only used for issuing warnings to users about missing or extraneous XML tags / attributes.
2. Run ``make`` in ``xpdeint/support/`` to update ``xpdeint/support/xpdeint.rng``. This is the file which is actually used, which is in RelaxNG format, but RelaxNG compact is easier to read and edit.
3. Commit both ``xpdeint/support/xpdeint.rnc`` and ``xpdeint/support/xpdeint.rng``.
