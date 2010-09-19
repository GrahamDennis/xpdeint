#!/usr/bin/env python
# encoding: utf-8

import Arguments
import AutoVectorise
import Benchmark
import Bing
import CFlags
import ChunkedOutput
import Diagnostics
import ErrorCheck
import Globals
import HaltNonFinite
import MaxIterations
import OpenMP
import Output
import Stochastic
import Transforms
import Validation

import OutputFormat
from BinaryFormat import BinaryFormat
from AsciiFormat import AsciiFormat
from HDF5Format import HDF5Format

formatMapping = [(f.name, f) for f in [BinaryFormat, AsciiFormat, HDF5Format]]
del BinaryFormat, AsciiFormat, HDF5Format

OutputFormat.OutputFormat.outputFormatClasses.update(formatMapping)

