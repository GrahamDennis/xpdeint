#!/usr/bin/env python

from setuptools import setup, find_packages

import os
if not os.path.exists('xpdeint'):
    raise Exception("setup.py must be run from the xpdeint main directory.")

packages = []
skip_dirs = set(['.svn', 'waf_build'])
for root, dirs, files in os.walk('xpdeint'):
    for d in skip_dirs.intersection(dirs):
        dirs.remove(d)
    if not '__init__.py' in files:
        del dirs[:]
    else:
        packages.append(root.replace(os.sep, '.'))

setup(name="xpdeint",
      version="0.7",
      description="Stochastic ODE/PDE integrator",
      url="http://xmds.sourceforge.net",
      license="GPL2",
      keywords="scientific/engineering simulation",
      platforms="OS Independent",
      packages = packages,
      
      scripts = ['bin/xpdeint', 'bin/xsil2graphics2'],
      
      exclude_package_data = {'': ['README', 'TODO']},
      
      # Project requires Cheetah for all of the templates
      install_requires = ['Cheetah>=2.0.1', 'pyparsing'],
      
      package_data = {
        'xpdeint': ['examples/*.xmds',
                    'includes/*.c',
                    'includes/*.h',
                    'includes/dSFMT/*',
                    'includes/solirte/*',
                    'support/xpdeint.rng',
                    'support/wscript'
                   ]
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

