#!/usr/bin/env python

from distutils.core import setup

a=setup(name="xpdeint",
      version="0.0.1",
      description="Stochastic ODE/PDE integrator",
      author="Graham Dennis",
      author_email="grahamdennis@users.sourceforge.net",
      maintainer="Graham Dennis",
      maintainer_email="grahamdennis@users.sourceforge.net",
      url="http://xmds.sourceforge.net",
      license="GPL",
      keywords="scientific/engineering simulation",
      platforms="OS Independent",
      packages=['xmds2'],
)
