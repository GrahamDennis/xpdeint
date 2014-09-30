/*
 * xpdeint.h
 * Copyright (C) 2008-2012 Graham Dennis (graham.dennis@anu.edu.au) and Joe Hope. All rights reserved.
 *
*/

#ifndef xpdeint_h
#define xpdeint_h

#ifndef _xmds_malloc
  #define _xmds_malloc(n) _aligned_malloc(n, 16)
#endif

#ifndef xmds_free
  #define xmds_free   _aligned_free
#endif

inline XMDSComplexType::value_type mod(const XMDSComplexType& _t) { return std::abs(_t); }
inline XMDSComplexType::value_type mod2(const XMDSComplexType& _t) { return std::norm(_t); }
inline XMDSComplexType cis(const real& _t) { return std::polar((real)1.0, _t); }

namespace std {
  inline complex<float> operator*(const complex<float>& a, const double b) { return a*float(b); }
  inline complex<float> operator*(const double b, const complex<float>& a) { return a*float(b); }
  inline complex<float> operator/(const complex<float>& a, const double b) { return a/float(b); }
  inline complex<float> operator/(const double b, const complex<float>& a) { return float(b)/a; }
  inline complex<float> operator+(const complex<float>& a, const double b) { return a + float(b); }
  inline complex<float> operator+(const double b, const complex<float>& a) { return a + float(b); }
  inline complex<float> operator-(const complex<float>& a, const double b) { return a - float(b); }
  inline complex<float> operator-(const double b, const complex<float>& a) { return float(b) - a; }
};

inline XMDSComplexType operator*(const XMDSComplexType& a, const int b) { return a*XMDSComplexType::value_type(b); }
inline XMDSComplexType operator*(const int b, const XMDSComplexType& a) { return a*XMDSComplexType::value_type(b); }
inline XMDSComplexType operator/(const XMDSComplexType& a, const int b) { return a/XMDSComplexType::value_type(b); }
inline XMDSComplexType operator/(const int b, const XMDSComplexType& a) { return XMDSComplexType::value_type(b)/a; }
inline XMDSComplexType operator+(const XMDSComplexType& a, const int b) { return a + XMDSComplexType::value_type(b); }
inline XMDSComplexType operator+(const int b, const XMDSComplexType& a) { return a + XMDSComplexType::value_type(b); }
inline XMDSComplexType operator-(const XMDSComplexType& a, const int b) { return a - XMDSComplexType::value_type(b); }
inline XMDSComplexType operator-(const int b, const XMDSComplexType& a) { return XMDSComplexType::value_type(b) - a; }


extern bool initialiseFieldFromXSILFile(const char *filename,
   const char *mgName, unsigned long dimension, char **dimNames,
   char **componentNames,
   // output variables
   char**binaryDataFilename, int *unsignedLongSize,
   bool *dataEncodingIsNative, bool *isPrecisionDouble,
   unsigned long *nDataComponents, unsigned long **inputLattice,
   int **componentIndicesPtr);

#endif // xpdeint_h

