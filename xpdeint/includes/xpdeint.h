/*
 * xpdeint.h
 * Copyright (C) 2008-2012 Graham Dennis (graham.dennis@anu.edu.au) and Joe Hope. All rights reserved.
 *
*/

#ifndef xpdeint_h
#define xpdeint_h

#ifndef xmds_malloc
  #define xmds_malloc(n) _aligned_malloc(n, 16)
#endif

#ifndef xmds_free
  #define xmds_free   _aligned_free
#endif

inline complex::value_type mod(const complex& _t) { return std::abs(_t); }
inline complex::value_type mod2(const complex& _t) { return std::norm(_t); }
inline complex cis(const real& _t) { return std::polar((real)1.0, _t); }

namespace std {
  inline Complex<float> operator*(const Complex<float>& a, const double b) { return a*float(b); }
  inline Complex<float> operator*(const double b, const Complex<float>& a) { return a*float(b); }
  inline Complex<float> operator/(const Complex<float>& a, const double b) { return a/float(b); }
  inline Complex<float> operator/(const double b, const Complex<float>& a) { return float(b)/a; }
  inline Complex<float> operator+(const Complex<float>& a, const double b) { return a + float(b); }
  inline Complex<float> operator+(const double b, const Complex<float>& a) { return a + float(b); }
  inline Complex<float> operator-(const Complex<float>& a, const double b) { return a - float(b); }
  inline Complex<float> operator-(const double b, const Complex<float>& a) { return float(b) - a; }

  inline complex operator*(const complex& a, const int b) { return a*complex::value_type(b); }
  inline complex operator*(const int b, const complex& a) { return a*complex::value_type(b); }
  inline complex operator/(const complex& a, const int b) { return a/complex::value_type(b); }
  inline complex operator/(const int b, const complex& a) { return complex::value_type(b)/a; }
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

