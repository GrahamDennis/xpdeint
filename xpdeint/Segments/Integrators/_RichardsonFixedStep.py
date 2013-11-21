#!/usr/bin/env python
# encoding: utf-8
"""
_RichardsonFixedStep.py

Created by Graham Dennis on 2013-11-21.

Copyright (c) 2013, Graham Dennis

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""

from xpdeint.Segments.Integrators.FixedStep import FixedStep


class _RichardsonFixedStep(FixedStep):
  
  extrapolations = 4
  
  def preflight(self):
    super(_RichardsonFixedStep, self).preflight()
    
    self.extraIntegrationArrayNames.extend(['rerow_T%i_%i' % (i, j) for j in range(self.extrapolations) for i in range(2)])
    self.extraIntegrationArrayNames.append('re_reset')
  