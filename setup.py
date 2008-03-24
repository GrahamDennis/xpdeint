#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name="xpdeint",
      version="0.2",
      description="Stochastic ODE/PDE integrator",
      url="http://xmds.sourceforge.net",
      license="GPL2",
      keywords="scientific/engineering simulation",
      platforms="OS Independent",
      packages = ['xpdeint',
                  'xpdeint.SimulationDrivers',
                  'xpdeint.Geometry',
                  'xpdeint.Vectors',
                  'xpdeint.Segments',
                  'xpdeint.Segments.Integrators',
                  'xpdeint.Operators',
                  'xpdeint.Features',
                  'xpdeint.Features.Noises',
                  'xpdeint.Features.Noises.DSFMT',
                  'xpdeint.Features.Noises.MKL',
                  'xpdeint.Features.Noises.POSIX',
                  ],
      
      scripts = ['bin/xpdeint'],
      
      exclude_package_data = {'': ['README', 'TODO']},
      
      # Project requires Cheetah for all of the templates
      install_requires = ['Cheetah>=2.0.1'],
      
      package_data = {
        '': ['includes/*.c', 'includes/*.h', 'includes/*.cc', 'examples/*.xmds']
      },
      
      # We aren't zip safe because we will require access to
      # *.c and *.h files inside the distributed egg
      zip_safe = False,
      
)
