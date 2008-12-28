#!/usr/bin/env python
# encoding: utf-8

import TransformMultiplexer

import _NoTransform
import NoTransformMPI
_NoTransform._NoTransform.mpiCapableSubclass = NoTransformMPI.NoTransformMPI

import FourierTransformFFTW3
import FourierTransformFFTW3Threads
import FourierTransformFFTW3MPI

FourierTransformFFTW3.FourierTransformFFTW3.mpiCapableSubclass = FourierTransformFFTW3MPI.FourierTransformFFTW3MPI

import MMT
