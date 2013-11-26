#!/usr/bin/env python
# encoding: utf-8

import TransformMultiplexer
transformClasses = TransformMultiplexer.TransformMultiplexer.transformClasses

import _NoTransform
import NoTransformMPI
_NoTransform._NoTransform.mpiCapableSubclass = NoTransformMPI.NoTransformMPI
transformClasses['none'] = _NoTransform._NoTransform

import FourierTransformFFTW3
import FourierTransformFFTW3Threads
import FourierTransformFFTW3MPI
FourierTransformFFTW3.FourierTransformFFTW3.mpiCapableSubclass = FourierTransformFFTW3MPI.FourierTransformFFTW3MPI
transformClasses.update([(name, FourierTransformFFTW3.FourierTransformFFTW3) for name in ['dft', 'dct', 'dst', 'mpi']])

import BesselTransform
transformClasses.update([(name, BesselTransform.BesselTransform) for name in ['bessel', 'spherical-bessel']])
import BesselNeumannTransform
transformClasses['bessel-neumann'] = BesselNeumannTransform.BesselNeumannTransform

import HermiteGaussTransform
transformClasses['hermite-gauss'] = HermiteGaussTransform.HermiteGaussTransform

del transformClasses