/*
 * xpdeint.h
 * Copyright (C) 2008 Graham Dennis (graham.dennis@anu.edu.au). All rights reserved.
 *
*/

#ifndef xpdeint_h
#define xpdeint_h

#include <xpdeint_complex.h>

extern bool initialiseFieldFromXSILFile(const char *filename,
   const char *mgName, unsigned long dimension, char **dimNames,
   char **componentNames,
   // output variables
   char**binaryDataFilename, int *unsignedLongSize,
   bool *dataEncodingIsNative, bool *isPrecisionDouble,
   unsigned long *nDataComponents, unsigned long **inputLattice,
   int **componentIndicesPtr);

#endif // xpdeint_h

