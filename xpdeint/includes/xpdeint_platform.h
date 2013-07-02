/* *****************************************************************************
/
/ This file is a modified version of 'compilercompat.h' from Solirte.
/ This file is part of Solirte, a solenoid ion ray-tracing engine.
/ (c) 2008 Michael Brown.
/ michael.brown@anu.edu.au
/ Modified by Graham Dennis.
/
/ No platform is like any other. This file tries to get a (mostly) consistant
/ environment across all supported platforms.
/ *************************************************************************** */

#ifndef XPDEINT_PLATFORM_H
#define XPDEINT_PLATFORM_H

// -----------------------------------------------------------------------------
// Configuration constants.
// -----------------------------------------------------------------------------

#define CFG_COMPILER_MSVC 1
#define CFG_COMPILER_SUNCC 2
#define CFG_COMPILER_GCC 3
#define CFG_COMPILER_ICC 4

#define CFG_PLATFORM_WIN32 1
#define CFG_PLATFORM_LINUX 2
#define CFG_PLATFORM_SOLARIS 3
#define CFG_PLATFORM_CYGWIN 4
#define CFG_PLATFORM_OSX 5
#define CFG_PLATFORM_FREEBSD 6

#define CFG_ENDIAN_LITTLE 1234
#define CFG_ENDIAN_BIG 4321

#define CFG_OSAPI_WIN32 1
#define CFG_OSAPI_POSIX 2

#define CFG_THREADAPI_WIN32 1
#define CFG_THREADAPI_PTHREADS 2

// -----------------------------------------------------------------------------
// External compiler- and system-specific options.
// -----------------------------------------------------------------------------
#ifndef CFG_HAVE_COMPILER_CONFIG_H
  #define CFG_HAVE_COMPILER_CONFIG_H 0
#endif

#if CFG_HAVE_COMPILER_CONFIG_H == 1
  #include "compiler_config.h"
#endif

// -----------------------------------------------------------------------------
// Compiler identification.
// -----------------------------------------------------------------------------

#ifndef CFG_COMPILER
  #if defined(_MSC_VER)
    #define CFG_COMPILER CFG_COMPILER_MSVC
  #endif

  #if defined(__SUNPRO_C) || defined(__SUNPRO_CC)
    #define CFG_COMPILER CFG_COMPILER_SUNCC
  #endif

  #if defined(__GNUC__) && !defined(__INTEL_COMPILER)
    #define CFG_COMPILER CFG_COMPILER_GCC
  #endif

  #if defined(__INTEL_COMPILER)
    #define CFG_COMPILER CFG_COMPILER_ICC
  #endif

  #ifndef CFG_COMPILER
    #error Cannot detect compiler.
  #endif
#endif

// -----------------------------------------------------------------------------
// Platform identification.
// -----------------------------------------------------------------------------

#ifndef CFG_PLATFORM
  #if defined(_WIN32)
    #define CFG_PLATFORM CFG_PLATFORM_WIN32
  #endif

  #if defined(__linux__)
    #define CFG_PLATFORM CFG_PLATFORM_LINUX
  #endif

  #if defined(__CYGWIN__)
    #define CFG_PLATFORM CFG_PLATFORM_CYGWIN
  #endif

  #if defined(__SVR4) && defined(__sun)
    #define CFG_PLATFORM CFG_PLATFORM_SOLARIS
  #endif
  
  #if defined(__APPLE__)
    #define CFG_PLATFORM CFG_PLATFORM_OSX
  #endif
  
  #if defined(__FreeBSD__)
    #define CFG_PLATFORM CFG_PLATFORM_FREEBSD
  #endif

  #ifndef CFG_PLATFORM
    #error Cannot detect platform.
  #endif
#endif

// -----------------------------------------------------------------------------
// All the basic include files.
// -----------------------------------------------------------------------------
#if (CFG_PLATFORM == CFG_PLATFORM_LINUX) && (CFG_COMPILER == CFG_COMPILER_GCC)
  #ifndef CFG_COMPILER 
    #define _XOPEN_SOURCE 600
  #endif
#endif

#if CFG_COMPILER == CFG_COMPILER_MSVC
  // Stop MSVC from nerfing std::Vector performance.
  #define _SECURE_SCL 0

  // Needed for M_PI
  #define _USE_MATH_DEFINES
  #ifdef _DEBUG                   // Turn on heap tracing if we're debugging.
    #define CRTDBG_MAP_ALLOC
  #endif
#endif

#include <stdlib.h>
#if (CFG_PLATFORM == CFG_PLATFORM_WIN32)
  #include <malloc.h>
  #ifdef _DEBUG
  #include <crtdbg.h>
  #endif
#endif
#if (CFG_COMPILER != CFG_COMPILER_MSVC)
  // For endian/bits.
  #include <sys/param.h>
#endif

// -----------------------------------------------------------------------------
// Endian detection.
// -----------------------------------------------------------------------------
#ifndef CFG_ENDIAN
  #ifdef __BYTE_ORDER
    #if (__BYTE_ORDER == __LITTLE_ENDIAN)
      #define CFG_ENDIAN CFG_ENDIAN_LITTLE
    #endif
    #if (__BYTE_ORDER == __BIG_ENDIAN)
      #define CFG_ENDIAN CFG_ENDIAN_BIG
    #endif
  #endif
#endif

#ifndef CFG_ENDIAN
  #ifdef BYTE_ORDER
    #if (BYTE_ORDER == LITTLE_ENDIAN)
      #define CFG_ENDIAN CFG_ENDIAN_LITTLE
    #endif
    #if (BYTE_ORDER == BIG_ENDIAN)
      #define CFG_ENDIAN CFG_ENDIAN_BIG
    #endif
  #endif
#endif

#ifndef CFG_ENDIAN
  #ifdef _BIG_ENDIAN
    #define CFG_ENDIAN CFG_ENDIAN_BIG
  #endif
  #ifdef _LITTLE_ENDIAN
    #define CFG_ENDIAN CFG_ENDIAN_LITTLE
  #endif
#endif

#if CFG_COMPILER == CFG_COMPILER_MSVC
  #if defined(_M_X64) || defined(_M_IX86)
    #define CFG_ENDIAN CFG_ENDIAN_LITTLE
  #endif
#endif

#ifndef CFG_ENDIAN
  #error Cannot detect endian.
#endif

// -----------------------------------------------------------------------------
// 32/64 bit detection.
// -----------------------------------------------------------------------------
#ifndef CFG_BITS
  #if CFG_COMPILER == CFG_COMPILER_MSVC
    #ifdef _M_X64
      #define CFG_BITS 64
    #endif
    #ifdef _M_IX86
      #define CFG_BITS 32
    #endif
  #endif

  #if CFG_COMPILER == CFG_COMPILER_SUNCC
    #if defined(__amd64__) || defined(__sparc64__) || defined(__x86_64__)
      #define CFG_BITS 64
    #else
      #define CFG_BITS 32
    #endif
  #endif

  #if (CFG_COMPILER == CFG_COMPILER_GCC) || (CFG_COMPILER == CFG_COMPILER_ICC)
    #if defined(_LP64) || defined(_ILP64) || defined(__LP64__) || defined(__ILP64__) 
      #define CFG_BITS 64
    #else
      #define CFG_BITS 32
    #endif
  #endif
#endif

#ifndef CFG_BITS
  #error Cannot detect 32/64 bit mode.
#endif

// -----------------------------------------------------------------------------
// SSE detection.
// -----------------------------------------------------------------------------

#if CFG_COMPILER == CFG_COMPILER_MSVC
  // Processor settings.
  #ifdef _M_X64
    #ifdef CFG_HAVE_MMX
      #undef CFG_HAVE_MMX
    #endif
    #define CFG_HAVE_MMX 0
    #ifndef CFG_HAVE_SSE1
      #define CFG_HAVE_SSE1 1
    #endif
    #ifndef CFG_HAVE_SSE2
      #define CFG_HAVE_SSE2 1
    #endif
  #elif defined(_M_IX86)
    #if ((_M_IX86 >= 6) && !defined(CFG_HAVE_MMX))
      #define CFG_HAVE_MMX 1
    #endif
    #if ((_M_IX86_FP >= 1) && !defined(CFG_HAVE_SSE1))
      #define CFG_HAVE_SSE1 1
    #endif
    #if ((_M_IX86_FP >= 2) && !defined(CFG_HAVE_SSE2))
      #define CFG_HAVE_SSE2 1
    #endif
  #endif
#endif

#if (defined(__MMX__) && !defined(CFG_HAVE_MMX))
  #define CFG_HAVE_MMX 1
#endif

#if (defined(__SSE__) && !defined(CFG_HAVE_SSE1))
  #define CFG_HAVE_SSE1 1
#endif

#if (defined(__SSE2__) && !defined(CFG_HAVE_SSE2))
  #define CFG_HAVE_SSE2 1
#endif

#if (defined(__SSE3__) && !defined(CFG_HAVE_SSE3))
  #define CFG_HAVE_SSE3 1
#endif

#if (defined(__ALTIVEC__) && !defined(CFG_HAVE_ALTIVEC))
  #define CFG_HAVE_ALTIVEC 1
#endif

#ifndef CFG_HAVE_MMX
  #define CFG_HAVE_MMX 0
#endif

#ifndef CFG_HAVE_SSE1
  #define CFG_HAVE_SSE1 0
#endif

#ifndef CFG_HAVE_SSE2
  #define CFG_HAVE_SSE2 0
#endif

#ifndef CFG_HAVE_SSE3
  #define CFG_HAVE_SSE3 0
#endif

#ifndef CFG_HAVE_ALTIVEC
  #define CFG_HAVE_ALTIVEC 0
#endif

// -----------------------------------------------------------------------------
// Cache size (SMP performance tweak).
// -----------------------------------------------------------------------------

#ifndef CFG_CACHELINE
  #define CFG_CACHELINE 128
#endif

// -----------------------------------------------------------------------------
// Compiler-specific configuration/fixes.
// -----------------------------------------------------------------------------

// Define UNREFERENCED_PARAMETER if it's not already done.
#ifndef UNREFERENCED_PARAMETER
  #ifndef _MSC_VER
    #define UNREFERENCED_PARAMETER(P) (void)(P)
  #endif
#endif

#if (CFG_PLATFORM == CFG_PLATFORM_OSX) || (CFG_PLATFORM == CFG_PLATFORM_FREEBSD)
  inline void *_aligned_malloc(size_t size, size_t alignment)
  {
    UNREFERENCED_PARAMETER(alignment);
    return malloc(size);
  }

  inline void _aligned_free(void *memblock)
  {
    free(memblock);
  }
#elif (CFG_PLATFORM == CFG_PLATFORM_SOLARIS)
  inline void *_aligned_malloc(size_t size, size_t alignment)
  {
    return memalign(alignment, size);
  }

  inline void _aligned_free(void *memblock)
  {
    free(memblock);
  }
#elif (CFG_PLATFORM == CFG_PLATFORM_LINUX)
  inline void *_aligned_malloc(size_t size, size_t alignment)
  {
    void *RetVal = NULL;
    
    // Need to collect the result of the posix_memalign call otherwise
    // we get a "warn_unused_result" warning. We don't actually need to
    // check the result, since on failure (i != 0) RetVal will be null.
    int i = posix_memalign(&RetVal, alignment, size);
    return RetVal;
  }

  inline void _aligned_free(void *memblock)
  {
    free(memblock);
  }
#elif (CFG_PLATFORM == CFG_PLATFORM_WIN32)
  // _aligned_malloc and _aligned_free are native.
#else
  #warning No aligned malloc support. Please implement.
#endif

// Choose compiler-specific fixes.
#if CFG_COMPILER == CFG_COMPILER_MSVC
  // Replacement for stdint.h
  typedef __int8 int8_t;
  typedef __int16 int16_t;
  typedef __int32 int32_t;
  typedef __int64 int64_t;
  typedef unsigned __int8 uint8_t;
  typedef unsigned __int16 uint16_t;
  typedef unsigned __int32 uint32_t;
  typedef unsigned __int64 uint64_t;

  // Fix up nonstandard case-insensitive compare naming
  #include <string.h>
  inline int strcasecmp(const char *s1, const char *s2)
  { return _stricmp(s1, s2); }

  // Note what's supported
  #define THREADVAR __declspec(thread)

  #define CFG_HAVE_TCHAR_H 1
  #define CFG_HAVE_SECURECRT 1

  #define ALIGN_8(atype, avar) __declspec(align(8)) atype avar
  #define ALIGN_16(atype, avar) __declspec(align(16)) atype avar
  #define ALIGN_CACHE(atype, avar) __declspec(align(CFG_CACHELINE)) atype avar

  #define NOINLINE __declspec(noinline)
  #define FORCEINLINE __forceinline
#endif

#if (CFG_COMPILER == CFG_COMPILER_GCC) || (CFG_COMPILER == CFG_COMPILER_ICC)
  #include <stdint.h>
  
  #define CFG_HAVE_LRINT 1
  #define CFG_HAVE_LRINTF 1
  #define CFG_HAVE_NAN 1

  #define ALIGN_8(atype, avar) atype __attribute__((aligned(8))) avar
  #define ALIGN_16(atype, avar) atype avar __attribute__((aligned(16)))
  #define ALIGN_CACHE(atype, avar) atype avar __attribute__((aligned(CFG_CACHELINE)))

  #define NOINLINE __attribute__ ((noinline))
  #define FORCEINLINE __attribute__ ((always_inline))
#endif

#if CFG_COMPILER == CFG_COMPILER_SUNCC
  #include <stdint.h>

  // Note what's supported
  #define CFG_HAVE_LRINT 1
  #define CFG_HAVE_LRINTF 1
  #define CFG_HAVE_NAN 1

  #if __SUNPRO_CC >= 0x590
    #define NOINLINE __attribute__ ((noinline))
    #define FORCEINLINE __attribute__ ((always_inline))

    #define ALIGN_8(atype, avar) atype __attribute__((aligned(8))) avar
    #define ALIGN_16(atype, avar) atype __attribute__((aligned(16))) avar
    #define ALIGN_CACHE(atype, avar) atype __attribute__((aligned(CFG_CACHELINE))) avar
  #else
    // Sun C prior to 5.9 only has integer SSE2 and MMX support.
    #define CFG_ONLY_INTEGER_SSE2 1
    #ifdef CFG_HAVE_SSE1
      #undef CFG_HAVE_SSE1
      #define CFG_HAVE_SSE1 0
    #endif
    #ifdef CFG_HAVE_SSE3
      #undef CFG_HAVE_SSE3
      #define CFG_HAVE_SSE3 0
    #endif
  #endif
#endif

#ifndef NOINLINE
  #define NOINLINE
#endif

#ifndef FORCEINLINE
  #define FORCEINLINE inline
#endif

// -----------------------------------------------------------------------------
// Include SSE1/SSE2 headers.
// -----------------------------------------------------------------------------

#if CFG_COMPILER == CFG_COMPILER_SUNCC
  #include <sunmedia_intrin.h>
#else
  #if CFG_HAVE_MMX == 1
    #include <mmintrin.h>
  #endif

  #if CFG_HAVE_SSE1 == 1
    #include <xmmintrin.h>
  #endif

  #if CFG_HAVE_SSE2 == 1
    #include <emmintrin.h>
  #endif

  #if CFG_HAVE_SSE3 == 1
    #include <pmmintrin.h>
  #endif

  #if CFG_HAVE_ALTIVEC == 1
    #if !defined(__APPLE__)
      #include <altivec.h>
    #endif

    // Fix up GCC's mess
    #if !defined(__APPLE_ALTIVEC__)
      #undef vector
      #undef bool
      #undef pixel
    #endif
  #endif
#endif

// -----------------------------------------------------------------------------
// Platform-specific configuration/fixes.
// -----------------------------------------------------------------------------

// Threading and OS API selection
#ifndef CFG_OSAPI
  #if CFG_PLATFORM == CFG_PLATFORM_WIN32
    #define CFG_OSAPI CFG_OSAPI_WIN32
  #elif CFG_PLATFORM == CFG_PLATFORM_LINUX
    #define CFG_OSAPI CFG_OSAPI_POSIX
  #elif CFG_PLATFORM == CFG_PLATFORM_CYGWIN
    #define CFG_OSAPI CFG_OSAPI_POSIX
  #elif CFG_PLATFORM == CFG_PLATFORM_SOLARIS
    #define CFG_OSAPI CFG_OSAPI_POSIX
  #elif CFG_PLATFORM == CFG_PLATFORM_OSX
    #define CFG_OSAPI CFG_OSAPI_POSIX
  #elif CFG_PLATFORM == CFG_PLATFORM_FREEBSD
    #define CFG_OSAPI CFG_OSAPI_POSIX
  #else
    #error Cannot detect OS API.
  #endif
#endif

#ifndef CFG_THREADAPI
  #if CFG_PLATFORM == CFG_PLATFORM_WIN32
    #define CFG_THREADAPI CFG_THREADAPI_WIN32
  #elif CFG_PLATFORM == CFG_PLATFORM_LINUX
    #define CFG_THREADAPI CFG_THREADAPI_PTHREADS
  #elif CFG_PLATFORM == CFG_PLATFORM_CYGWIN
    #define CFG_THREADAPI CFG_THREADAPI_WIN32
  #elif CFG_PLATFORM == CFG_PLATFORM_SOLARIS
    #define CFG_THREADAPI CFG_THREADAPI_PTHREADS
  #elif CFG_PLATFORM == CFG_PLATFORM_OSX
    #define CFG_THREADAPI CFG_THREADAPI_PTHREADS
  #elif CFG_PLATFORM == CFG_PLATFORM_FREEBSD
    #define CFG_THREADAPI CFG_THREADAPI_PTHREADS
  #else
    #error Cannot detect threading API.
  #endif
#endif

#if CFG_OSAPI == CFG_OSAPI_WIN32
  #define NOMINMAX
  #include <windows.h>
#endif

#if CFG_OSAPI == CFG_OSAPI_POSIX
  #include <unistd.h>
#endif

#if CFG_THREADAPI == CFG_THREADAPI_WIN32
  #include <process.h>
#endif

#if CFG_THREADAPI == CFG_THREADAPI_PTHREADS
  #include <pthread.h>
#endif

// -----------------------------------------------------------------------------
// General fixes.
// -----------------------------------------------------------------------------

// Emulate NaN()
#if CFG_HAVE_NAN == 0
  inline double nan(char *StrRep)
  {
    UNREFERENCED_PARAMETER(StrRep);

    static const union
    {
      uint32_t nan_u32[2];
      double nan_double;
    } NANVal =
    #if CFG_ENDIAN == CFG_ENDIAN_LITTLE
      {{0xffffffff, 0x7fffffff}};
    #else
      {{0x7fffffff, 0xffffffff}};
    #endif
    return NANVal.nan_double;
  }
#endif

// Define UINT64_C for 64-bit constants
#ifndef UINT64_C
  #if (CFG_COMPILER == CFG_COMPILER_GCC) || (CFG_COMPILER == CFG_COMPILER_SUNCC) || (CFG_COMPILER == CFG_COMPILER_ICC)
    #define UINT64_C(x) (x ## ULL)
    #define INT64_C(x) (x ## LL)
  #elif CFG_COMPILER == CFG_COMPILER_MSVC
    #define UINT64_C(x) (x ## UI64)
    #define INT64_C(x) (x ## I64)
  #else
    #error Could not define UINT64_C. Need a compiler-specific fix.
  #endif
#endif

  template<typename fp_type> union FP_UNION;

  template<> union FP_UNION<double>
  {
      uint64_t as_int;
      double as_value;
  };

  template<> union FP_UNION<float>
  {
      uint32_t as_int;
      float as_value;
  };

  template<typename fp_type> inline FP_UNION<fp_type> _xmds_nan_mask();

  template<> inline FP_UNION<double> _xmds_nan_mask<double>()
  {
      static const FP_UNION<double> NANVal = {UINT64_C(0x7ff0000000000000)};
      return NANVal;
  }

  template<> inline FP_UNION<float> _xmds_nan_mask<float>()
  {
      static const FP_UNION<float> NANVal = {0x7f800000};
      return NANVal;
  }

  template<typename fp_type> inline bool _xmds_isnonfinite(fp_type value)
  {
      FP_UNION<fp_type> x, NANMask = _xmds_nan_mask<fp_type>();
      x.as_value = value;
      return (x.as_int & NANMask.as_int) == NANMask.as_int;
  }

// Floating point casting.
#if (CFG_HAVE_LRINT == 1) || (CFG_HAVE_LRINTF == 1)
  // Enable ISO C functions on platforms that support them.
  #define	_ISOC9X_SOURCE	1
	#define _ISOC99_SOURCE	1
	#define	__USE_ISOC9X	1
	#define	__USE_ISOC99	1
#endif

#if (CFG_COMPILER == CFG_COMPILER_MSVC) && defined(_M_X64)
  // MS killed inline assembly in x64 so have to go the slow way or the SSE(2)
  // way. Note that since we're checking that we're using MSVC and in 64-bit
  // mode, we know we have a LLP64 model (so long = 32 bits). The following is
  // NOT correct in a LP64 model, where long is 64 bits.
  #if (CFG_HAVE_LRINT == 0) && (CFG_HAVE_SSE2 == 1)
    inline long int lrint(double x) { return _mm_cvtsd_si32(_mm_load_sd(&x)); }
    #undef CFG_HAVE_LRINT
    #define CFG_HAVE_LRINT 1
  #endif

  #if (CFG_HAVE_LRINTF == 0) && (CFG_HAVE_SSE1 == 1)
    inline long int lrint(float x) { return _mm_cvtss_si32(_mm_load_ss(&x)); }
    #undef CFG_HAVE_LRINTF
    #define CFG_HAVE_LRINTF 1
  #endif
#endif

#if (CFG_COMPILER == CFG_COMPILER_MSVC) && defined(_M_IX86) && !defined(_M_X64)
  // We can use inline assembler.
  #if (CFG_HAVE_LRINT == 0)
    inline long int lrint(double x)
    {
      long int RetVal;

	    __asm
	    {
        fld     x
        fistp   RetVal
		  };
  			
	    return RetVal;
    } 
    #undef CFG_HAVE_LRINT
    #define CFG_HAVE_LRINT 1
  #endif
	
  #if (CFG_HAVE_LRINTF == 0)
    inline long int lrintf(float x)
    {
      long int RetVal;

	    __asm
	    {
        fld     x
		    fistp   RetVal
		  };
  			
	    return RetVal;
    }
    #undef CFG_HAVE_LRINTF
    #define CFG_HAVE_LRINTF 1
  #endif
#endif

#if (CFG_HAVE_LRINT == 0)
  #if CFG_COMPILER == CFG_COMPILER_GCC
    #warning lrint() not natively supported, replacing with slow alternative.
  #elif CFG_COMPILER == CFG_COMPILER_MSVC
    #pragma message("Warning: lrint() not natively supported, replacing with slow alternative.")
  #endif
  // #include <math.h>
  inline long int lrint(double x) { return static_cast<long int>(floor(x + 0.5)); }
#endif

#if (CFG_HAVE_LRINTF == 0)
  #if CFG_COMPILER == CFG_COMPILER_GCC
    #warning lrintf() not natively supported, replacing with slow alternative.
  #elif CFG_COMPILER == CFG_COMPILER_MSVC
    #pragma message("Warning: lrintf() not natively supported, replacing with slow alternative.")
  #endif
  // #include <math.h>
  inline long int lrintf(float x) { return static_cast<long int>(floorf(x + 0.5f)); }
#endif

// -----------------------------------------------------------------------------
// Endian correction.
// -----------------------------------------------------------------------------

template<int Bits> inline size_t EndianFix(size_t LittleEndianIndex)
{
  #if CFG_ENDIAN == CFG_ENDIAN_BIG
  size_t FlipMask = (((size_t)1) << Bits) - 1;
  return
    (LittleEndianIndex & ~FlipMask) +
    (FlipMask - (LittleEndianIndex & FlipMask));
  #else
  return LittleEndianIndex;
  #endif
}

template<> size_t inline EndianFix<1>(size_t LittleEndianIndex)
{
  #if CFG_ENDIAN == CFG_ENDIAN_BIG
  return (LittleEndianIndex ^ 1);
  #else
  return LittleEndianIndex;
  #endif
}

template<int Bits> inline int EndianFix(int LittleEndianIndex)
{
  #if CFG_ENDIAN == CFG_ENDIAN_BIG
  size_t FlipMask = (((int)1) << Bits) - 1;
  return
    (LittleEndianIndex & ~FlipMask) +
    (FlipMask - (LittleEndianIndex & FlipMask));
  #else
  return LittleEndianIndex;
  #endif
}

template<> int inline EndianFix<1>(int LittleEndianIndex)
{
  #if CFG_ENDIAN == CFG_ENDIAN_BIG
  return (LittleEndianIndex ^ 1);
  #else
  return LittleEndianIndex;
  #endif
}

template<int Bits, size_t LittleEndianIndex> struct EndianFix_static
{
  #if CFG_ENDIAN == CFG_ENDIAN_BIG
  static const size_t FlipMask = (static_cast<size_t>(1) << Bits) - 1;
  static const size_t Value = (LittleEndianIndex & ~FlipMask) + (FlipMask - (LittleEndianIndex & FlipMask));
  #else
  static const size_t Value = LittleEndianIndex;
  #endif
};

template<int Bits, int LittleEndianIndex> struct EndianFix_static_int
{
  #if CFG_ENDIAN == CFG_ENDIAN_BIG
  static const int FlipMask = (static_cast<int>(1) << Bits) - 1;
  static const int Value = (LittleEndianIndex & ~FlipMask) + (FlipMask - (LittleEndianIndex & FlipMask));
  #else
  static const int Value = LittleEndianIndex;
  #endif
};

#endif
