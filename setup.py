#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name="xpdeint",
      version="0.6",
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
      install_requires = ['Cheetah>=2.0.1', 'Pygments'],
      
      package_data = {
        '': ['includes/*.c', 'includes/*.h', 'includes/*.cc', 'examples/*.xmds', 'support/xpdeint.rng']
      },
      
      # We aren't zip safe because we will require access to
      # *.c and *.h files inside the distributed egg
      zip_safe = False,
      
      entry_points = '''
      [pygments.lexers]
      XMDSScriptLexer = xpdeint.XMDSScriptLexer:XMDSScriptLexer
      
      [pygments.styles]
      friendly_plus = xpdeint.FriendlyPlusStyle:FriendlyPlusStyle
      '''
)

setup(name="xsil2graphics",
      version="0.1",
      description="Post-processor for XSIL data files output by xpdeint/xmds",
      url="http://xmds.sourceforge.net",
      license="GPL2",
      keywords="scientific/engineering simulation, visualiation",
      platforms="OS Independent",
      
      # I think it's fair to say I have little idea what I'm doing here.
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
      
      scripts = ['bin/xsil2graphics2'],
      
      exclude_package_data = {'': ['README', 'TODO']},
      
      # Project requires Cheetah for all of the templates
      install_requires = ['Cheetah>=2.0.1', 'Pygments'],
      
      package_data = {
        '': ['includes/*.c', 'includes/*.h', 'includes/*.cc', 'examples/*.xmds', 'support/xpdeint.rng']
      },
      
      # We aren't zip safe because we will require access to
      # *.c and *.h files inside the distributed egg
      zip_safe = False,
      
      entry_points = '''
      [pygments.lexers]
      XMDSScriptLexer = xpdeint.XMDSScriptLexer:XMDSScriptLexer
      
      [pygments.styles]
      friendly_plus = xpdeint.FriendlyPlusStyle:FriendlyPlusStyle
      '''
)
