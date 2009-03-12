/*
 * xpdeint.h
 * Copyright (C) 2008-2009 Graham Dennis (graham.dennis@anu.edu.au). All rights reserved.
 *
*/

#ifndef xpdeint_h
#define xpdeint_h

#ifdef FFTW3_H
#define xmds_malloc fftw_malloc
#define xmds_free   fftw_free
#else
#define xmds_malloc(n) _aligned_malloc(n, 16)
#define xmds_free   _aligned_free
#endif //FFTW3_H

inline complex::value_type mod(const complex& _t) { return std::abs(_t); }
inline complex::value_type mod2(const complex& _t) { return std::norm(_t); }

namespace std {
  inline complex operator*(const complex& a, const int b) { return a*complex::value_type(b); }
  inline complex operator*(const int b, const complex& a) { return a*complex::value_type(b); }
  inline complex operator+(const complex& a, const int b) { return a + complex::value_type(b); }
  inline complex operator+(const int b, const complex& a) { return a + complex::value_type(b); }
  inline complex operator-(const complex& a, const int b) { return a - complex::value_type(b); }
  inline complex operator-(const int b, const complex& a) { return complex::value_type(b) - a; }
};

extern bool initialiseFieldFromXSILFile(const char *filename,
   const char *mgName, unsigned long dimension, char **dimNames,
   char **componentNames,
   // output variables
   char**binaryDataFilename, int *unsignedLongSize,
   bool *dataEncodingIsNative, bool *isPrecisionDouble,
   unsigned long *nDataComponents, unsigned long **inputLattice,
   int **componentIndicesPtr);

#endif // xpdeint_h

