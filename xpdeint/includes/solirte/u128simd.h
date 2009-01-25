/* *****************************************************************************
/
/ This file is part of Solirte, a solenoid ion ray-tracing engine.
/ (c) 2008 Michael Brown.
/ michael.brown@anu.edu.au
/
/ One nice this to have would be a generic 128-bit SIMD-like class so that
/ everything could be nicely ecapsulated, and SSE/AltiVec could be
/ transparently used. Unfortunately, there's no compiler that will consistantly
/ produce good code for such a type. So, things have to be done in a slightly
/ more ugly way: global operators on the basic intrinsic types. Even the simple
/ wrapping done here appears to be pushing the limit of code generation on
/ some compilers (eg: MSVC, GCC 3.x).
/
/ Note also that most compilers implode on the MMX implementation and produce
/ code that's worse than simple scalar code.
/
/ Finally, the unusual views-with-load/store concept for CDataBuffer is needed
/ to help GCC. Without this construct, gcc's aliasing rules are violated and the
/ compiler generates incorrect code.
/ *************************************************************************** */

#ifndef U128SIMD_H
#define U128SIMD_H

#include <iomanip>

// intrinsic = hardware SIMD implementation (fast)
// mmx = mmx (surprise!)
// scalar = software SIMD implementation (slow)
#define CFG_SIMD_INTRINSIC 1
#define CFG_SIMD_MMX 2
#define CFG_SIMD_SCALAR 3

#if (CFG_COMPILER == CFG_COMPILER_MSVC)
// Disable the "no EMMS instruction" warning - this is the responsibility of any
// function that calls these functions.
#pragma warning( push )
#pragma warning(disable : 4799)
#endif

// -----------------------------------------------------------------------------
// SIMD operations
// -----------------------------------------------------------------------------

#if (CFG_HAVE_SSE1 == 1)
inline __m128 SIMDOP_add(const __m128 LHS, const __m128 RHS)
{ return _mm_add_ps(LHS, RHS); }

inline __m128 SIMDOP_sub(const __m128 LHS, const __m128 RHS)
{ return _mm_sub_ps(LHS, RHS); }

inline __m128 SIMDOP_mul(const __m128 LHS, const __m128 RHS)
{ return _mm_mul_ps(LHS, RHS); }

inline __m128 SIMDOP_or(const __m128 LHS, const __m128 RHS)
{ return _mm_or_ps(LHS, RHS); }

inline __m128 SIMDOP_and(const __m128 LHS, const __m128 RHS)
{ return _mm_and_ps(LHS, RHS); }

inline __m128 SIMDOP_xor(const __m128 LHS, const __m128 RHS)
{ return _mm_xor_ps(LHS, RHS); }
#endif

#if (CFG_HAVE_SSE2 == 1)

inline __m128i SIMDOP_or(__m128i LHS, __m128i RHS)
{ return _mm_or_si128(LHS, RHS); }

inline __m128i SIMDOP_and(__m128i LHS, __m128i RHS)
{ return _mm_and_si128(LHS, RHS); }

inline __m128i SIMDOP_xor(__m128i LHS, __m128i RHS)
{ return _mm_xor_si128(LHS, RHS); }

#if (CFG_ONLY_INTEGER_SSE2 == 0)
inline __m128d SIMDOP_add(const __m128d LHS, const __m128d RHS)
{ return _mm_add_pd(LHS, RHS); }

inline __m128d SIMDOP_sub(const __m128d LHS, const __m128d RHS)
{ return _mm_sub_pd(LHS, RHS); }

inline __m128d SIMDOP_mul(const __m128d LHS, const __m128d RHS)
{ return _mm_mul_pd(LHS, RHS); }

inline __m128d SIMDOP_or(const __m128d LHS, const __m128d RHS)
{ return _mm_or_pd(LHS, RHS); }

inline __m128d SIMDOP_and(const __m128d LHS, const __m128d RHS)
{ return _mm_and_pd(LHS, RHS); }

inline __m128d SIMDOP_xor(const __m128d LHS, const __m128d RHS)
{ return _mm_xor_pd(LHS, RHS); }
#endif
#endif

// -----------------------------------------------------------------------------
// Common functions
// -----------------------------------------------------------------------------

template<uint32_t x, int NumBits>
struct lowestbit_u32
{
  static const uint32_t BitMask = (1 << (NumBits / 2)) - 1;
  static const uint32_t LowPart = x & BitMask;
  static const uint32_t HighPart = (x >> (NumBits / 2)) & BitMask;
  static const uint32_t CalcVal = (LowPart == 0) ?
    (lowestbit_u32<HighPart, NumBits / 2>::CalcVal << (NumBits / 2)) :
    lowestbit_u32<LowPart, NumBits / 2>::CalcVal;
};

template<uint32_t x>
struct lowestbit_u32<x, 1>
{
  static const uint32_t CalcVal = x;
};

template<uint32_t x0, uint32_t x1, uint32_t x2, uint32_t x3>
struct lowestbit_u128
{
  static const int y0 = lowestbit_u32<x0, 32>::CalcVal;
  static const int y1 = (y0 != 0) ? 0 : lowestbit_u32<x1, 32>::CalcVal;
  static const int y2 = ((y0 | y1) != 0) ? 0 : lowestbit_u32<x2, 32>::CalcVal;
  static const int y3 = ((y0 | y1 | y2) != 0) ? 0 : lowestbit_u32<x3, 32>::CalcVal;
};

template<int Bits> struct U64_Shr32Mask
{
  static const uint64_t SingleMask = 0xffffffff >> Bits;
  static const uint64_t Value = SingleMask | (SingleMask << 32);
};

template<int Bits> struct U64_Shl32Mask
{
  static const uint64_t SingleMask = (0xffffffff << Bits) & 0xffffffff;
  static const uint64_t Value = SingleMask | (SingleMask << 32);
};

#if CFG_HAVE_SSE2 == 1
  #if (CFG_COMPILER == CFG_COMPILER_MSVC) || ((CFG_COMPILER == CFG_COMPILER_GCC) && (__GNUC__ < 4))
    inline __m128 _mm_castsi128_ps(const __m128i &x) { return reinterpret_cast<const __m128 &>(x); } 
    inline __m128d _mm_castsi128_pd(const __m128i &x) { return reinterpret_cast<const __m128d &>(x); } 

    inline __m128i _mm_castps_si128(const __m128 &x) { return reinterpret_cast<const __m128i &>(x); }
    inline __m128d _mm_castps_pd(const __m128 &x) { return reinterpret_cast<const __m128d &>(x); }

    inline __m128i _mm_castpd_si128(const __m128d &x) { return reinterpret_cast<const __m128i &>(x); }
    inline __m128 _mm_castpd_ps(const __m128d &x) { return reinterpret_cast<const __m128 &>(x); }
  #endif
#endif

// -----------------------------------------------------------------------------
// 128-bit register
// -----------------------------------------------------------------------------

#if (CFG_HAVE_SSE2 == 1)
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// SSE2 implementation.
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#define CFG_HAVE_U128 CFG_SIMD_INTRINSIC

typedef __m128i uint128_t;

namespace SIMDOps
{
  inline __m128i AndNot(__m128i LHS, __m128i RHS)
  { return _mm_andnot_si128(RHS, LHS); } // Note reversed order

  template<int NumBytes> inline __m128i Shr8(__m128i Src)
  { return _mm_srli_si128(Src, NumBytes); }

  template<int NumBytes> __m128i Shl8(__m128i Src)
  { return _mm_slli_si128(Src, NumBytes); }

  template<int NumBits> __m128i Shr_u32(__m128i Src)
  { return _mm_srli_epi32(Src, NumBits); }

  template<int NumBits> __m128i Shl_u32(__m128i Src)
  { return _mm_slli_epi32(Src, NumBits); }

  inline __m128i Parity(__m128i Src)
  {
    __m128i x = Src;
    x = _mm_xor_si128(_mm_slli_epi64(x, 1), x);
    x = _mm_xor_si128(_mm_slli_epi64(x, 2), x);
    x = _mm_xor_si128(_mm_slli_epi64(x, 4), x);
    x = _mm_xor_si128(_mm_slli_epi64(x, 8), x);
    x = _mm_xor_si128(_mm_slli_epi64(x, 16), x);
    x = _mm_xor_si128(_mm_slli_epi64(x, 32), x);
    x = _mm_xor_si128(_mm_shuffle_epi32(x, 0xFF), _mm_shuffle_epi32(x, 0x55));
    x = _mm_srai_epi32(x, 31);
    return x;
  }

  template<uint32_t x0, uint32_t x1, uint32_t x2, uint32_t x3> struct uint128_t_const
  {
    static inline __m128i Value(void)
    {
      static const union
      {
        uint32_t AsU32[4];
        __m128i AsM128I;
      } InitData = {{x0, x1, x2, x3}};
      return InitData.AsM128I;
    }
  };

  inline __m128i make_uint128_t(uint32_t x0, uint32_t x1, uint32_t x2, uint32_t x3)
  {
    union
    {
      uint32_t AsU32[4];
      __m128i AsM128I;
    } InitData = {{x0, x1, x2, x3}};
    return InitData.AsM128I;
  }

  inline void EmptyForFP(void) { }
}
#endif

#if (CFG_HAVE_MMX == 1) && !defined(CFG_HAVE_U128)
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// MMX implementation
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#define CFG_HAVE_U128 CFG_SIMD_MMX

struct uint128_t
{
  __m64 VecData[2];
};

inline uint128_t SIMDOP_or(const uint128_t &LHS, const uint128_t &RHS)
{
  uint128_t RetVal = {{_mm_or_si64(LHS.VecData[0], RHS.VecData[0]), _mm_or_si64(LHS.VecData[1], RHS.VecData[1])}};
  return RetVal;
}

inline uint128_t SIMDOP_and(const uint128_t &LHS, const uint128_t &RHS)
{
  uint128_t RetVal = {{_mm_and_si64(LHS.VecData[0], RHS.VecData[0]), _mm_and_si64(LHS.VecData[1], RHS.VecData[1])}};
  return RetVal;
}

inline uint128_t SIMDOP_xor(const uint128_t &LHS, const uint128_t &RHS)
{
  uint128_t RetVal = {{_mm_xor_si64(LHS.VecData[0], RHS.VecData[0]), _mm_xor_si64(LHS.VecData[1], RHS.VecData[1])}};
  return RetVal;
}

namespace SIMDOps
{
  inline __m64 AndNot(const __m64 LHS, const __m64 RHS)
  {
    // Note reversed order
    return _mm_andnot_si64(RHS, LHS);
  }

  inline uint128_t AndNot(const uint128_t &LHS, const uint128_t &RHS)
  {
    uint128_t RetVal = {{AndNot(LHS.VecData[0], RHS.VecData[0]), AndNot(LHS.VecData[1], RHS.VecData[1])}};
    return RetVal;
  }

  template<int NumBytes> inline uint128_t Shr8(const uint128_t &Src)
  {
    uint128_t RetVal = {{
      _mm_or_si64(_mm_srli_si64(Src.VecData[0], NumBytes * 8), _mm_slli_si64(Src.VecData[1], 64 - NumBytes * 8)),
      _mm_srli_si64(Src.VecData[1], NumBytes * 8)}};
    return RetVal;
  }

  template<int NumBytes> inline uint128_t Shl8(const uint128_t &Src)
  {
    uint128_t RetVal = {{
      _mm_slli_si64(Src.VecData[0], NumBytes * 8),
      _mm_or_si64(_mm_slli_si64(Src.VecData[1], NumBytes * 8),  _mm_srli_si64(Src.VecData[0], 64 - NumBytes * 8))}};
    return RetVal;
  }

  template<int NumBits> inline uint128_t Shr_u32(const uint128_t &Src)
  {
    uint128_t RetVal = {{
      _mm_srli_pi32(Src.VecData[0], NumBits),
      _mm_srli_pi32(Src.VecData[1], NumBits)}};
    return RetVal;
  }

  template<int NumBits> inline uint128_t Shl_u32(const uint128_t &Src)
  {
    uint128_t RetVal = {{
      _mm_slli_pi32(Src.VecData[0], NumBits),
      _mm_slli_pi32(Src.VecData[1], NumBits)}};
    return RetVal;
  }

  inline uint128_t Parity(const uint128_t &Src)
  {
    __m64 x = _mm_xor_si64(Src.VecData[0], Src.VecData[1]);
    x = _mm_xor_si64(_mm_slli_si64(x, 1), x);
    x = _mm_xor_si64(_mm_slli_si64(x, 2), x);
    x = _mm_xor_si64(_mm_slli_si64(x, 4), x);
    x = _mm_xor_si64(_mm_slli_si64(x, 8), x);
    x = _mm_xor_si64(_mm_slli_si64(x, 16), x);
    x = _mm_xor_si64(_mm_slli_si64(x, 32), x);
    x = _mm_unpackhi_pi32(x, x);
    x = _mm_srai_pi32(x, 31);
    uint128_t RetVal = {{x, x}};
    return RetVal;
  }

  template<uint32_t x0, uint32_t x1> struct __m64_const
  {
    static inline __m64 Value(void)
    {
      static const union
      {
        uint32_t AsU32[2];
        __m64 AsM64;
      } InitData = {{x0, x1}};
      return InitData.AsM64;
    }
  };

  template<uint32_t x0, uint32_t x1, uint32_t x2, uint32_t x3> struct uint128_t_const
  {
    static inline uint128_t Value(void)
    {
      static const union
      {
        uint32_t AsU32[4];
        uint128_t AsU128;
      } InitData = {{x0, x1, x2, x3}};
      return InitData.AsU128;
    }
  };

  inline uint128_t make_uint128_t(uint32_t x0, uint32_t x1, uint32_t x2, uint32_t x3)
  {
    union
    {
      uint32_t AsU32[4];
      uint128_t AsU128;
    } InitData = {{x0, x1, x2, x3}};
    return InitData.AsU128;
  }

  #if CFG_SUNCC_BROKEN_MM_EMPTY == 1
  inline void EmptyForFP(void) { _mm_empty_sun(); }
  #else
  inline void EmptyForFP(void) { _mm_empty(); }
  #endif
}

#endif

#if !defined(CFG_HAVE_U128)
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// Scalar implementation
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#define CFG_HAVE_U128 CFG_SIMD_SCALAR

#if CFG_BITS == 64
// 64-bit implementation
struct uint128_t
{
  int64_t VecData[2];
  template<size_t Idx> inline uint64_t GetU64(void)
  { return VecData[EndianFix_static<1, Idx>::Value]; }
  template<size_t Idx> inline void SetU64(uint64_t x)
  { VecData[EndianFix_static<1, Idx>::Value] = x; }
};

inline uint128_t SIMDOP_or(const uint128_t &LHS, const uint128_t &RHS)
{
  uint128_t RetVal = {{LHS.VecData[0] | RHS.VecData[0], LHS.VecData[1] | RHS.VecData[1]}};
  return RetVal;
}

inline uint128_t SIMDOP_and(const uint128_t &LHS, const uint128_t &RHS)
{
  uint128_t RetVal = {{LHS.VecData[0] & RHS.VecData[0], LHS.VecData[1] & RHS.VecData[1]}};
  return RetVal;
}

inline uint128_t SIMDOP_xor(const uint128_t &LHS, const uint128_t &RHS)
{
  uint128_t RetVal = {{LHS.VecData[0] ^ RHS.VecData[0], LHS.VecData[1] ^ RHS.VecData[1]}};
  return RetVal;
}

namespace SIMDOps
{
  inline uint64_t AndNot(const uint64_t LHS, const uint64_t RHS)
  {
    return LHS & !RHS;
  }

  inline uint128_t AndNot(const uint128_t &LHS, const uint128_t &RHS)
  {
    uint128_t RetVal = {{AndNot(LHS.VecData[0], RHS.VecData[0]), AndNot(LHS.VecData[1], RHS.VecData[1])}};
    return RetVal;
  }

  template<int NumBits, int Idx, int SrcIdx> inline uint64_t Shr128_sub(uint64_t Src)
  {
    // Low bit of SrcIdx ends up at SrcIdx * 64 - NumBits.
    // Get position relative to the low bit of Idx (= Idx * 64).
    static const int SrcLow = SrcIdx * 64 - NumBits - Idx * 64;
    static const int UseLeftShift = ((SrcLow > 0) && (SrcLow < 64)) ? 1 : 0;
    static const int UseRightShift = ((SrcLow < 0) && (SrcLow > -64)) ? 1 : 0;
    static const int UseNoShift = (SrcLow == 0) ? 1 : 0;
    static const int LShiftBits = (UseLeftShift == 1) ? SrcLow : 0;
    static const int RShiftBits = (UseRightShift == 1) ? -SrcLow : 0;
    if (UseLeftShift == 1) return Src << LShiftBits;
    if (UseRightShift == 1) return Src >> RShiftBits;
    if (UseNoShift == 1) return Src;
    return 0;
  }

  template<int NumBytes> inline uint128_t Shr8(const uint128_t &Src)
  {
    uint128_t RetVal = {{
      Shr128_sub<NumBytes * 8, EndianFix_static_int<1, 0>::Value, EndianFix_static_int<1, 0>::Value>(Src.VecData[0]) |
      Shr128_sub<NumBytes * 8, EndianFix_static_int<1, 0>::Value, EndianFix_static_int<1, 1>::Value>(Src.VecData[1]),
      Shr128_sub<NumBytes * 8, EndianFix_static_int<1, 1>::Value, EndianFix_static_int<1, 0>::Value>(Src.VecData[0]) |
      Shr128_sub<NumBytes * 8, EndianFix_static_int<1, 1>::Value, EndianFix_static_int<1, 1>::Value>(Src.VecData[1])}};
    return RetVal;
  }

  template<int NumBytes> inline uint128_t Shl8(const uint128_t &Src)
  {
    uint128_t RetVal = {{
      Shr128_sub<-NumBytes * 8, EndianFix_static_int<1, 0>::Value, EndianFix_static_int<1, 0>::Value>(Src.VecData[0]) |
      Shr128_sub<-NumBytes * 8, EndianFix_static_int<1, 0>::Value, EndianFix_static_int<1, 1>::Value>(Src.VecData[1]),
      Shr128_sub<-NumBytes * 8, EndianFix_static_int<1, 1>::Value, EndianFix_static_int<1, 0>::Value>(Src.VecData[0]) |
      Shr128_sub<-NumBytes * 8, EndianFix_static_int<1, 1>::Value, EndianFix_static_int<1, 1>::Value>(Src.VecData[1])}};
    return RetVal;
  }

  template<int NumBits> inline uint128_t Shr_u32(const uint128_t &Src)
  {
    uint128_t RetVal = {{
      (Src.VecData[0] >> NumBits) & U64_Shr32Mask<NumBits>::Value,
      (Src.VecData[1] >> NumBits) & U64_Shr32Mask<NumBits>::Value}};
    return RetVal;
  }

  template<int NumBits> inline uint128_t Shl_u32(const uint128_t &Src)
  {
    uint128_t RetVal = {{
      (Src.VecData[0] << NumBits) & U64_Shr32Mask<NumBits>::Value,
      (Src.VecData[1] << NumBits) & U64_Shr32Mask<NumBits>::Value}};
    return RetVal;
  }

  inline uint128_t Parity(const uint128_t &Src)
  {
    uint64_t x = Src.VecData[0] ^ Src.VecData[1];
    x ^= x << 1;
    x ^= x << 2;
    x ^= x << 4;
    x ^= x << 8;
    x ^= x << 16;
    x ^= x << 32;
    x = static_cast<uint64_t>(static_cast<int64_t>(x) >> 63);
    uint128_t RetVal = {{x, x}};
    return RetVal;
  }

  inline uint128_t make_uint128_t(uint32_t x0, uint32_t x1, uint32_t x2, uint32_t x3)
  {
    #if CFG_ENDIAN == CFG_ENDIAN_LITTLE
    uint128_t RetVal = {{
      static_cast<uint64_t>(x0) | (static_cast<uint64_t>(x1) << 32),
      static_cast<uint64_t>(x2) | (static_cast<uint64_t>(x3) << 32)}};
    #else
    uint128_t RetVal = {{
      static_cast<uint64_t>(x2) | (static_cast<uint64_t>(x3) << 32),
      static_cast<uint64_t>(x0) | (static_cast<uint64_t>(x1) << 32)}};
    #endif
    return RetVal;
  }

  template<uint32_t x0, uint32_t x1, uint32_t x2, uint32_t x3> struct uint128_t_const
  {
    static inline uint128_t Value(void)
    {
      return make_uint128_t(x0, x1, x2, x3);
    }
  };

  inline void EmptyForFP(void) { }
}
#else
// 32-bit implementation
struct uint128_t
{
  uint32_t VecData[4];
};

inline uint128_t SIMDOP_or(const uint128_t &LHS, const uint128_t &RHS)
{
  uint128_t RetVal = {{
    LHS.VecData[0] | RHS.VecData[0], LHS.VecData[1] | RHS.VecData[1],
    LHS.VecData[2] | RHS.VecData[2], LHS.VecData[3] | RHS.VecData[3]}};
  return RetVal;
}

inline uint128_t SIMDOP_and(const uint128_t &LHS, const uint128_t &RHS)
{
  uint128_t RetVal = {{
    LHS.VecData[0] & RHS.VecData[0], LHS.VecData[1] & RHS.VecData[1],
    LHS.VecData[2] & RHS.VecData[2], LHS.VecData[3] & RHS.VecData[3]}};
  return RetVal;
}

inline uint128_t SIMDOP_xor(const uint128_t &LHS, const uint128_t &RHS)
{
  uint128_t RetVal = {{
    LHS.VecData[0] ^ RHS.VecData[0], LHS.VecData[1] ^ RHS.VecData[1],
    LHS.VecData[2] ^ RHS.VecData[2], LHS.VecData[3] ^ RHS.VecData[3]}};
  return RetVal;
}

namespace SIMDOps
{
  inline uint32_t AndNot(const uint32_t LHS, const uint32_t RHS)
  {
    return LHS & !RHS;
  }

  inline uint128_t AndNot(const uint128_t &LHS, const uint128_t &RHS)
  {
    uint128_t RetVal = {{
      AndNot(LHS.VecData[0], RHS.VecData[0]), AndNot(LHS.VecData[1], RHS.VecData[1]),
      AndNot(LHS.VecData[2], RHS.VecData[2]), AndNot(LHS.VecData[3], RHS.VecData[3])}};
    return RetVal;
  }

  template<int NumBits, int Idx, int SrcIdx> inline uint32_t Shr128_sub(uint32_t Src)
  {
    // Low bit of SrcIdx ends up at SrcIdx * 32 - NumBits.
    // Get position relative to the low bit of Idx (= Idx * 32).
    static const int SrcLow = SrcIdx * 32 - NumBits - Idx * 32;
    static const int UseLeftShift = ((SrcLow > 0) && (SrcLow < 32)) ? 1 : 0;
    static const int UseRightShift = ((SrcLow < 0) && (SrcLow > -32)) ? 1 : 0;
    static const int UseNoShift = (SrcLow == 0) ? 1 : 0;
    static const int LShiftBits = (UseLeftShift == 1) ? SrcLow : 0;
    static const int RShiftBits = (UseRightShift == 1) ? -SrcLow : 0;
    if (UseLeftShift == 1) return Src << LShiftBits;
    if (UseRightShift == 1) return Src >> RShiftBits;
    if (UseNoShift == 1) return Src;
    return 0;
  }

  template<int NumBytes> inline uint128_t Shr8(const uint128_t &Src)
  {
    uint128_t RetVal = {{
      Shr128_sub<NumBytes * 8, EndianFix_static_int<2, 0>::Value, EndianFix_static_int<2, 0>::Value>(Src.VecData[0]) |
      Shr128_sub<NumBytes * 8, EndianFix_static_int<2, 0>::Value, EndianFix_static_int<2, 1>::Value>(Src.VecData[1]) |
      Shr128_sub<NumBytes * 8, EndianFix_static_int<2, 0>::Value, EndianFix_static_int<2, 2>::Value>(Src.VecData[2]) |
      Shr128_sub<NumBytes * 8, EndianFix_static_int<2, 0>::Value, EndianFix_static_int<2, 3>::Value>(Src.VecData[3]),
      Shr128_sub<NumBytes * 8, EndianFix_static_int<2, 1>::Value, EndianFix_static_int<2, 0>::Value>(Src.VecData[0]) |
      Shr128_sub<NumBytes * 8, EndianFix_static_int<2, 1>::Value, EndianFix_static_int<2, 1>::Value>(Src.VecData[1]) |
      Shr128_sub<NumBytes * 8, EndianFix_static_int<2, 1>::Value, EndianFix_static_int<2, 2>::Value>(Src.VecData[2]) |
      Shr128_sub<NumBytes * 8, EndianFix_static_int<2, 1>::Value, EndianFix_static_int<2, 3>::Value>(Src.VecData[3]),
      Shr128_sub<NumBytes * 8, EndianFix_static_int<2, 2>::Value, EndianFix_static_int<2, 0>::Value>(Src.VecData[0]) |
      Shr128_sub<NumBytes * 8, EndianFix_static_int<2, 2>::Value, EndianFix_static_int<2, 1>::Value>(Src.VecData[1]) |
      Shr128_sub<NumBytes * 8, EndianFix_static_int<2, 2>::Value, EndianFix_static_int<2, 2>::Value>(Src.VecData[2]) |
      Shr128_sub<NumBytes * 8, EndianFix_static_int<2, 2>::Value, EndianFix_static_int<2, 3>::Value>(Src.VecData[3]),
      Shr128_sub<NumBytes * 8, EndianFix_static_int<2, 3>::Value, EndianFix_static_int<2, 0>::Value>(Src.VecData[0]) |
      Shr128_sub<NumBytes * 8, EndianFix_static_int<2, 3>::Value, EndianFix_static_int<2, 1>::Value>(Src.VecData[1]) |
      Shr128_sub<NumBytes * 8, EndianFix_static_int<2, 3>::Value, EndianFix_static_int<2, 2>::Value>(Src.VecData[2]) |
      Shr128_sub<NumBytes * 8, EndianFix_static_int<2, 3>::Value, EndianFix_static_int<2, 3>::Value>(Src.VecData[3])}};
    return RetVal;
  }

  template<int NumBytes> inline uint128_t Shl8(const uint128_t &Src)
  {
    uint128_t RetVal = {{
      Shr128_sub<-NumBytes * 8, EndianFix_static_int<2, 0>::Value, EndianFix_static_int<2, 0>::Value>(Src.VecData[0]) |
      Shr128_sub<-NumBytes * 8, EndianFix_static_int<2, 0>::Value, EndianFix_static_int<2, 1>::Value>(Src.VecData[1]) |
      Shr128_sub<-NumBytes * 8, EndianFix_static_int<2, 0>::Value, EndianFix_static_int<2, 2>::Value>(Src.VecData[2]) |
      Shr128_sub<-NumBytes * 8, EndianFix_static_int<2, 0>::Value, EndianFix_static_int<2, 3>::Value>(Src.VecData[3]),
      Shr128_sub<-NumBytes * 8, EndianFix_static_int<2, 1>::Value, EndianFix_static_int<2, 0>::Value>(Src.VecData[0]) |
      Shr128_sub<-NumBytes * 8, EndianFix_static_int<2, 1>::Value, EndianFix_static_int<2, 1>::Value>(Src.VecData[1]) |
      Shr128_sub<-NumBytes * 8, EndianFix_static_int<2, 1>::Value, EndianFix_static_int<2, 2>::Value>(Src.VecData[2]) |
      Shr128_sub<-NumBytes * 8, EndianFix_static_int<2, 1>::Value, EndianFix_static_int<2, 3>::Value>(Src.VecData[3]),
      Shr128_sub<-NumBytes * 8, EndianFix_static_int<2, 2>::Value, EndianFix_static_int<2, 0>::Value>(Src.VecData[0]) |
      Shr128_sub<-NumBytes * 8, EndianFix_static_int<2, 2>::Value, EndianFix_static_int<2, 1>::Value>(Src.VecData[1]) |
      Shr128_sub<-NumBytes * 8, EndianFix_static_int<2, 2>::Value, EndianFix_static_int<2, 2>::Value>(Src.VecData[2]) |
      Shr128_sub<-NumBytes * 8, EndianFix_static_int<2, 2>::Value, EndianFix_static_int<2, 3>::Value>(Src.VecData[3]),
      Shr128_sub<-NumBytes * 8, EndianFix_static_int<2, 3>::Value, EndianFix_static_int<2, 0>::Value>(Src.VecData[0]) |
      Shr128_sub<-NumBytes * 8, EndianFix_static_int<2, 3>::Value, EndianFix_static_int<2, 1>::Value>(Src.VecData[1]) |
      Shr128_sub<-NumBytes * 8, EndianFix_static_int<2, 3>::Value, EndianFix_static_int<2, 2>::Value>(Src.VecData[2]) |
      Shr128_sub<-NumBytes * 8, EndianFix_static_int<2, 3>::Value, EndianFix_static_int<2, 3>::Value>(Src.VecData[3])}};
    return RetVal;
  }

  template<int NumBits> inline uint128_t Shr_u32(const uint128_t &Src)
  {
    uint128_t RetVal = {{
      Src.VecData[0] >> NumBits, Src.VecData[1] >> NumBits,
      Src.VecData[2] >> NumBits, Src.VecData[3] >> NumBits}};
    return RetVal;
  }

  template<int NumBits> inline uint128_t Shl_u32(const uint128_t &Src)
  {
    uint128_t RetVal = {{
      Src.VecData[0] << NumBits, Src.VecData[1] << NumBits,
      Src.VecData[2] << NumBits, Src.VecData[3] << NumBits}};
    return RetVal;
  }

  inline uint128_t Parity(const uint128_t &Src)
  {
    uint32_t x = Src.VecData[0] ^ Src.VecData[1] ^ Src.VecData[2] ^ Src.VecData[3];
    x ^= x << 1;
    x ^= x << 2;
    x ^= x << 4;
    x ^= x << 8;
    x ^= x << 16;
    x = static_cast<uint32_t>(static_cast<int32_t>(x) >> 31);
    uint128_t RetVal = {{x, x, x, x}};
    return RetVal;
  }

  inline uint128_t make_uint128_t(uint32_t x0, uint32_t x1, uint32_t x2, uint32_t x3)
  {
    #if CFG_ENDIAN == CFG_ENDIAN_LITTLE
    uint128_t RetVal = {{x0, x1, x2, x3}};
    #else
    uint128_t RetVal = {{x3, x2, x1, x0}};
    #endif
    return RetVal;
  }

  template<uint32_t x0, uint32_t x1, uint32_t x2, uint32_t x3> struct uint128_t_const
  {
    static inline uint128_t Value(void)
    {
      return make_uint128_t(x0, x1, x2, x3);
    }
  };

  inline void EmptyForFP(void) { }
}
#endif

#endif

// -----------------------------------------------------------------------------
// A vector of 4 FP32's.
// -----------------------------------------------------------------------------

#if (CFG_HAVE_SSE1 == 1) && !defined(CFG_HAVE_U128FP32)
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// SSE1 implementation.
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#define CFG_HAVE_U128FP32 CFG_SIMD_INTRINSIC

typedef __m128 uint128fp32_t;

namespace SIMDOps
{
  #if (CFG_HAVE_U128 == CFG_SIMD_INTRINSIC)
  inline __m128 simdcast_fp32(const uint128_t Src)
  { return _mm_castsi128_ps(Src); }
  #elif (CFG_HAVE_U128 == CFG_SIMD_MMX)
  inline __m128 simdcast_fp32(const uint128_t &Src)
  {
    static const union
    {
      __m64 AsMMX[2];
      __m128 AsM128;
    } InitData = {{Src.VecData[0], Src.VecData[1]}};
    return InitData.AsM128;
  }
  #elif CFG_BITS == 64
  inline __m128 simdcast_fp32(const uint128_t &Src)
  {
    static const union
    {
      uint64_t AsU64[2];
      __m128 AsM128;
    } InitData = {{Src.VecData[0], Src.VecData[1]}};
    return InitData.AsM128;
  }
  #else
  inline __m128 simdcast_fp32(const uint128_t &Src)
  {
    static const union
    {
      uint64_t AsU32[4];
      __m128 AsM128;
    } InitData = {{Src.VecData[0], Src.VecData[1], Src.VecData[2], Src.VecData[3]}};
    return InitData.AsM128;
  }
  #endif

  template<uint32_t x0, uint32_t x1, uint32_t x2, uint32_t x3> struct uint128fp32_t_const
  {
    static __m128 Value(void)
    {
      static const union
      {
        uint32_t AsU32[4];
        __m128 AsM128;
      } InitData = {{x0, x1, x2, x3}};
      return InitData.AsM128;
    }
  };
}
#endif

#if !defined(CFG_HAVE_U128FP32)
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// Scalar implementation.
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#define CFG_HAVE_U128FP32 CFG_SIMD_SCALAR

struct uint128fp32_t
{
  float VecData[4];
};

inline uint128fp32_t SIMDOP_add(const uint128fp32_t &LHS, const uint128fp32_t &RHS)
{
  uint128fp32_t RetVal = {{
    LHS.VecData[0] + RHS.VecData[0], LHS.VecData[1] + RHS.VecData[1],
    LHS.VecData[2] + RHS.VecData[2], LHS.VecData[3] + RHS.VecData[3]}};
  return RetVal;
}

inline uint128fp32_t SIMDOP_sub(const uint128fp32_t &LHS, const uint128fp32_t &RHS)
{
  uint128fp32_t RetVal = {{
    LHS.VecData[0] - RHS.VecData[0], LHS.VecData[1] - RHS.VecData[1],
    LHS.VecData[2] - RHS.VecData[2], LHS.VecData[3] - RHS.VecData[3]}};
  return RetVal;
}

inline uint128fp32_t SIMDOP_mul(const uint128fp32_t &LHS, const uint128fp32_t &RHS)
{
  uint128fp32_t RetVal = {{
    LHS.VecData[0] * RHS.VecData[0], LHS.VecData[1] * RHS.VecData[1],
    LHS.VecData[2] * RHS.VecData[2], LHS.VecData[3] * RHS.VecData[3]}};
  return RetVal;
}

inline uint128fp32_t SIMDOP_or(const uint128fp32_t &LHS, const uint128fp32_t &RHS)
{
  union
  {
    uint128fp32_t AsU128FP32[2];
    uint128_t AsU128[2];
  } ConvData;
  ConvData.AsU128FP32[0] = LHS; ConvData.AsU128FP32[1] = RHS;
  ConvData.AsU128[0] = SIMDOP_or(ConvData.AsU128[0], ConvData.AsU128[1]);
  return ConvData.AsU128FP32[0];
}

inline uint128fp32_t SIMDOP_and(const uint128fp32_t &LHS, const uint128fp32_t &RHS)
{
  union
  {
    uint128fp32_t AsU128FP32[2];
    uint128_t AsU128[2];
  } ConvData;
  ConvData.AsU128FP32[0] = LHS; ConvData.AsU128FP32[1] = RHS;
  ConvData.AsU128[0] = SIMDOP_and(ConvData.AsU128[0], ConvData.AsU128[1]);
  return ConvData.AsU128FP32[0];
}

inline uint128fp32_t SIMDOP_xor(const uint128fp32_t &LHS, const uint128fp32_t &RHS)
{
  union
  {
    uint128fp32_t AsU128FP32[2];
    uint128_t AsU128[2];
  } ConvData;
  ConvData.AsU128FP32[0] = LHS; ConvData.AsU128FP32[1] = RHS;
  ConvData.AsU128[0] = SIMDOP_xor(ConvData.AsU128[0], ConvData.AsU128[1]);
  return ConvData.AsU128FP32[0];
}

namespace SIMDOps
{
  inline uint128fp32_t simdcast_fp32(const uint128_t &Src)
  {
    union
    {
      uint128_t AsU128;
      uint128fp32_t AsU128FP32;
    } ConvData;
    ConvData.AsU128 = Src;
    return ConvData.AsU128FP32;
  }

  template<uint32_t x0, uint32_t x1, uint32_t x2, uint32_t x3> struct uint128fp32_t_const
  {
    static uint128fp32_t Value(void)
    {
      static const union
      {
        uint32_t AsU32[4];
        uint128fp32_t AsU128FP32;
      } InitData =
      #if CFG_ENDIAN == CFG_ENDIAN_LITTLE
        {{x0, x1, x2, x3}};
      #else
        {{x3, x2, x1, x0}};
      #endif
      return InitData.AsU128FP32;
    }
  };
}
#endif

// -----------------------------------------------------------------------------
// A vector of 2 FP64's.
// -----------------------------------------------------------------------------

#if (CFG_HAVE_SSE2 == 1) && (CFG_ONLY_INTEGER_SSE2 == 0)
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// SSE2 implementation.
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#define CFG_HAVE_U128FP64 CFG_SIMD_INTRINSIC

typedef __m128d uint128fp64_t;

namespace SIMDOps
{
  inline __m128d CmpLT(__m128d LHS, __m128d RHS)
  { return _mm_cmplt_pd(LHS, RHS); }

  inline __m128d CmpGE(__m128d LHS, __m128d RHS)
  { return _mm_cmpge_pd(LHS, RHS); }

  inline __m128d simdcast_fp64(const uint128_t &Src)
  { return _mm_castsi128_pd(Src); }

  template<uint32_t x0, uint32_t x1, uint32_t x2, uint32_t x3> struct uint128fp64_t_const
  {
    static __m128d Value(void)
    {
      static const union
      {
        uint32_t AsU32[4];
        __m128d AsM128D;
      } InitData = {{x0, x1, x2, x3}};
      return InitData.AsM128D;
    }
  };

  inline __m128d make_uint128fp64_t(double x0, double x1)
  {
    union
    {
      double AsFP64[2];
      __m128d AsM128D;
    } InitData = {{x0, x1}};
    return InitData.AsM128D;
  }

  // Approximate reciprocal.
  inline __m128d recip_a(__m128d x)
  {
    return _mm_cvtps_pd(_mm_rcp_ps(_mm_cvtpd_ps(x)));
  }
}

#endif

#if !defined(CFG_HAVE_U128FP64)
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// Scalar implementation
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#define CFG_HAVE_U128FP64 CFG_SIMD_SCALAR

struct uint128fp64_t
{
  double VecData[2];
};

inline uint128fp64_t SIMDOP_add(const uint128fp64_t &LHS, const uint128fp64_t &RHS)
{
  uint128fp64_t RetVal = {{
    LHS.VecData[0] + RHS.VecData[0], LHS.VecData[1] + RHS.VecData[1]}};
  return RetVal;
}

inline uint128fp64_t SIMDOP_sub(const uint128fp64_t &LHS, const uint128fp64_t &RHS)
{
  uint128fp64_t RetVal = {{
    LHS.VecData[0] - RHS.VecData[0], LHS.VecData[1] - RHS.VecData[1]}};
  return RetVal;
}

inline uint128fp64_t SIMDOP_mul(const uint128fp64_t &LHS, const uint128fp64_t &RHS)
{
  uint128fp64_t RetVal = {{
    LHS.VecData[0] * RHS.VecData[0], LHS.VecData[1] * RHS.VecData[1]}};
  return RetVal;
}

inline uint128fp64_t SIMDOP_or(const uint128fp64_t &LHS, const uint128fp64_t &RHS)
{
  union
  {
    uint128fp64_t AsU128FP64[2];
    uint128_t AsU128[2];
  } ConvData;
  ConvData.AsU128FP64[0] = LHS; ConvData.AsU128FP64[1] = RHS;
  ConvData.AsU128[0] = SIMDOP_or(ConvData.AsU128[0], ConvData.AsU128[1]);
  return ConvData.AsU128FP64[0];
}

inline uint128fp64_t SIMDOP_and(const uint128fp64_t &LHS, const uint128fp64_t &RHS)
{
  union
  {
    uint128fp64_t AsU128FP64[2];
    uint128_t AsU128[2];
  } ConvData;
  ConvData.AsU128FP64[0] = LHS; ConvData.AsU128FP64[1] = RHS;
  ConvData.AsU128[0] = SIMDOP_and(ConvData.AsU128[0], ConvData.AsU128[1]);
  return ConvData.AsU128FP64[0];
}

inline uint128fp64_t SIMDOP_xor(const uint128fp64_t &LHS, const uint128fp64_t &RHS)
{
  union
  {
    uint128fp64_t AsU128FP64[2];
    uint128_t AsU128[2];
  } ConvData;
  ConvData.AsU128FP64[0] = LHS; ConvData.AsU128FP64[1] = RHS;
  ConvData.AsU128[0] = SIMDOP_xor(ConvData.AsU128[0], ConvData.AsU128[1]);
  return ConvData.AsU128FP64[0];
}

namespace SIMDOps
{
  inline uint128fp64_t simdcast_fp64(const uint128_t &Src)
  {
    union
    {
      uint128_t AsU128;
      uint128fp64_t AsU128FP64;
    } ConvData;
    ConvData.AsU128 = Src;
    return ConvData.AsU128FP64;
  }

  template<uint32_t x0, uint32_t x1, uint32_t x2, uint32_t x3> struct uint128fp64_t_const
  {
    static uint128fp64_t Value(void)
    {
      static const union
      {
        uint32_t AsU32[4];
        uint128fp64_t AsU128FP64;
      } InitData =
      #if CFG_ENDIAN == CFG_ENDIAN_LITTLE
        {{x0, x1, x2, x3}};
      #else
        {{x3, x2, x1, x0}};
      #endif
      return InitData.AsU128FP64;
    }
  };
}
#endif

// -----------------------------------------------------------------------------
// Generic buffer type.
// -----------------------------------------------------------------------------

// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// The views of the main class.
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

template<int NumBytes> class CDataBuffer;

template<class ElementType, int NumBytes> class CDataBuffer_ConstView
{
  private:
    CDataBuffer_ConstView(void);
};

template<class ElementType, int NumBytes> class CDataBuffer_VarView
{
  private:
    CDataBuffer_VarView(void);
};

// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// Template implementations.
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

#define BUFVIEWIMPL2(ElementType, Suffix, StoreType)                                              \
template<int NumBytes> class CDataBuffer_ConstView<ElementType, NumBytes>                         \
{                                                                                                 \
  private:                                                                                        \
    const CDataBuffer<NumBytes> &FDataBuffer;                                                     \
    CDataBuffer_ConstView<ElementType, NumBytes> &operator=(const CDataBuffer_ConstView<ElementType, NumBytes> &Src);\
  public:                                                                                         \
    inline CDataBuffer_ConstView(const CDataBuffer<NumBytes> &DataBuffer) : FDataBuffer(DataBuffer) { } \
    inline CDataBuffer_ConstView(const CDataBuffer_ConstView<ElementType, NumBytes> &Src) : FDataBuffer(Src.FDataBuffer) { } \
    inline ElementType Load(size_t Idx) const { return FDataBuffer.Load##Suffix(Idx); }           \
    inline const ElementType *GetPointer(void) const { return FDataBuffer.GetPointer##Suffix(); } \
};                                                                                                \
                                                                                                  \
template<int NumBytes> class CDataBuffer_VarView<ElementType, NumBytes>                           \
{                                                                                                 \
  private:                                                                                        \
    CDataBuffer<NumBytes> &FDataBuffer;                                                           \
    CDataBuffer_VarView<ElementType, NumBytes> &operator=(const CDataBuffer_VarView<ElementType, NumBytes> &Src);\
  public:                                                                                         \
    inline CDataBuffer_VarView(CDataBuffer<NumBytes> &DataBuffer) : FDataBuffer(DataBuffer) { }   \
    inline CDataBuffer_VarView(const CDataBuffer_VarView<ElementType, NumBytes> &Src) : FDataBuffer(Src.FDataBuffer) { } \
    inline ElementType Load(size_t Idx) const { return FDataBuffer.Load##Suffix(Idx); }           \
    inline void Store(size_t Idx, const StoreType Src) { FDataBuffer.Store##Suffix(Idx, Src); }   \
    inline ElementType *GetPointer(void) { return FDataBuffer.GetPointer##Suffix(); }             \
};

#define BUFVIEWIMPL(ElementType, Suffix) BUFVIEWIMPL2(ElementType, Suffix, ElementType)

BUFVIEWIMPL( uint8_t, U8)
BUFVIEWIMPL(  int8_t, I8)
BUFVIEWIMPL(uint16_t, U16)
BUFVIEWIMPL( int16_t, I16)
BUFVIEWIMPL(uint32_t, U32)
BUFVIEWIMPL( int32_t, I32)
BUFVIEWIMPL(uint64_t, U64)
BUFVIEWIMPL( int64_t, I64)
BUFVIEWIMPL(double, FP64)
BUFVIEWIMPL(float, FP32)
BUFVIEWIMPL2(uint128_t, U128, uint128_t &)
BUFVIEWIMPL2(uint128fp32_t, U128FP32, uint128fp32_t &)
BUFVIEWIMPL2(uint128fp64_t, U128FP64, uint128fp64_t &)

#if (CFG_HAVE_MMX == 1)
  BUFVIEWIMPL(   __m64, M64)
#endif
/*
#if (CFG_HAVE_SSE1 == 1)
  BUFVIEWIMPL(  __m128, M128)
#endif
#if (CFG_HAVE_SSE2 == 1)
  BUFVIEWIMPL( __m128i, M128I)
  BUFVIEWIMPL( __m128d, M128D)
#endif
*/
#undef BUFVIEWIMPL
#undef BUFVIEWIMPL2

// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// The main class
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

#if (CFG_COMPILER == CFG_COMPILER_MSVC)
// MSVC emits spurious C4328 errors on CDataBuffer, so squish them.
#pragma warning(disable : 4328)
#endif

template<int NumBytes> class CDataBuffer
{
  private:
    union TAllData
    {
      #if (CFG_HAVE_SSE2 == 1)
      __m128i     AsM128I[NumBytes / 16];
      #if (CFG_ONLY_INTEGER_SSE2 == 0)
      __m128d     AsM128D[NumBytes / 16];
      #endif
      #endif
      #if (CFG_HAVE_SSE1 == 1)
      __m128    AsM128[NumBytes / 16];
      #endif
      #if (CFG_HAVE_MMX == 1)
      __m64     AsM64[NumBytes / 8];
      #endif
       uint8_t  AsU8 [NumBytes    ];
        int8_t  AsI8 [NumBytes    ];
      uint16_t  AsU16[NumBytes / 2];
       int16_t  AsI16[NumBytes / 2];
      uint32_t  AsU32[NumBytes / 4];
       int32_t  AsI32[NumBytes / 4];
      uint64_t  AsU64[NumBytes / 8];
       int64_t  AsI64[NumBytes / 8];
      double    AsFP64[NumBytes / 8];
      float     AsFP32[NumBytes / 4];
      uint128_t AsU128[NumBytes / 16];
      uint128fp32_t AsU128FP32[NumBytes / 16];
      uint128fp64_t AsU128FP64[NumBytes / 16];
    };
    ALIGN_16(TAllData, FVecData);
  public:
      inline uint8_t LoadU8(size_t Idx) const { return FVecData.AsU8[Idx]; }
      inline void StoreU8(size_t Idx, const uint8_t Src) { FVecData.AsU8[Idx] = Src; }
      inline int8_t LoadI8(size_t Idx) const { return FVecData.AsI8[Idx]; }
      inline void StoreI8(size_t Idx, const int8_t Src) { FVecData.AsI8[Idx] = Src; }

      inline uint16_t LoadU16(size_t Idx) const { return FVecData.AsU16[Idx]; }
      inline void StoreU16(size_t Idx, const uint16_t Src) { FVecData.AsU16[Idx] = Src; }
      inline int16_t LoadI16(size_t Idx) const { return FVecData.AsI16[Idx]; }
      inline void StoreI16(size_t Idx, const int16_t Src) { FVecData.AsI16[Idx] = Src; }

      inline uint32_t LoadU32(size_t Idx) const { return FVecData.AsU32[Idx]; }
      inline void StoreU32(size_t Idx, const uint32_t Src) { FVecData.AsU32[Idx] = Src; }
      inline int32_t LoadI32(size_t Idx) const { return FVecData.AsI32[Idx]; }
      inline void StoreI32(size_t Idx, const int32_t Src) { FVecData.AsI32[Idx] = Src; }

      inline uint64_t LoadU64(size_t Idx) const { return FVecData.AsU64[Idx]; }
      inline void StoreU64(size_t Idx, const uint64_t Src) { FVecData.AsU64[Idx] = Src; }
      inline int64_t LoadI64(size_t Idx) const { return FVecData.AsI64[Idx]; }
      inline void StoreI64(size_t Idx, const int64_t Src) { FVecData.AsI64[Idx] = Src; }

      inline float LoadFP32(size_t Idx) const { return FVecData.AsFP32[Idx]; }
      inline void StoreFP32(size_t Idx, const float Src) { FVecData.AsFP32[Idx] = Src; }

      inline double LoadFP64(size_t Idx) const { return FVecData.AsFP64[Idx]; }
      inline void StoreFP64(size_t Idx, const double Src) { FVecData.AsFP64[Idx] = Src; }

      inline uint128_t LoadU128(size_t Idx) const { return FVecData.AsU128[Idx]; }
      inline void StoreU128(size_t Idx, const uint128_t &Src) { FVecData.AsU128[Idx] = Src; }

      inline uint128fp32_t LoadU128FP32(size_t Idx) const { return FVecData.AsU128FP32[Idx]; }
      inline void StoreU128FP32(size_t Idx, const uint128fp32_t &Src) { FVecData.AsU128FP32[Idx] = Src; }

      inline uint128fp64_t LoadU128FP64(size_t Idx) const { return FVecData.AsU128FP64[Idx]; }
      inline void StoreU128FP64(size_t Idx, const uint128fp64_t &Src) { FVecData.AsU128FP64[Idx] = Src; }

      #if (CFG_HAVE_MMX == 1)
      inline __m64 LoadM64(size_t Idx) const { return FVecData.AsM64[Idx]; }
      inline void StoreM64(size_t Idx, const __m64 Src) { FVecData.AsM64[Idx] = Src; }
      #endif

      #if (CFG_HAVE_SSE1 == 1)
      inline __m128 LoadM128(size_t Idx) const { return FVecData.AsM128[Idx]; }
      inline void StoreM128(size_t Idx, const __m128 Src) { FVecData.AsM128[Idx] = Src; }
      #endif

      #if (CFG_HAVE_SSE2 == 1)
      inline __m128i LoadM128I(size_t Idx) const { return FVecData.AsM128I[Idx]; }
      inline void StoreM128I(size_t Idx, const __m128i Src) { FVecData.AsM128I[Idx] = Src; }
      #if (CFG_ONLY_INTEGER_SSE2 == 0)
      inline __m128d LoadM128D(size_t Idx) const { return FVecData.AsM128D[Idx]; }
      inline void StoreM128D(size_t Idx, const __m128d Src) { FVecData.AsM128D[Idx] = Src; }
      #endif
      #endif

      inline void *GetPointerVoid(void) { return FVecData.AsU8; }
      inline const void *GetPointerVoid(void) const { return FVecData.AsU8; }

      inline uint8_t *GetPointerU8(void) { return FVecData.AsU8; }
      inline const uint8_t *GetPointerU8(void) const { return FVecData.AsU8; }
      inline int8_t *GetPointerI8(void) { return FVecData.AsI8; }
      inline const int8_t *GetPointerI8(void) const { return FVecData.AsI8; }

      inline uint16_t *GetPointerU16(void) { return FVecData.AsU16; }
      inline const uint16_t *GetPointerU16(void) const { return FVecData.AsU16; };
      inline int16_t *GetPointerI16(void) { return FVecData.AsI16; };
      inline const int16_t *GetPointerI16(void) const { return FVecData.AsI16; };

      inline uint32_t *GetPointerU32(void) { return FVecData.AsU32; };
      inline const uint32_t *GetPointerU32(void) const { return FVecData.AsU32; };
      inline int32_t *GetPointerI32(void) { return FVecData.AsI32; };
      inline const int32_t *GetPointerI32(void) const { return FVecData.AsI32; };

      inline uint64_t *GetPointerU64(void) { return FVecData.AsU64; };
      inline const uint64_t *GetPointerU64(void) const { return FVecData.AsU64; };
      inline int64_t *GetPointerI64(void) { return FVecData.AsI64; };
      inline const int64_t *GetPointerI64(void) const { return FVecData.AsI64; };

      inline double *GetPointerFP64(void) { return FVecData.AsFP64; };
      inline const double *GetPointerFP64(void) const { return FVecData.AsFP64; };

      inline float *GetPointerFP32(void) { return FVecData.AsFP32; };
      inline const float *GetPointerFP32(void) const { return FVecData.AsFP32; };

      #if (CFG_HAVE_MMX == 1)
      inline __m64 *GetPointerM64(void) { return FVecData.AsM64; };
      inline const __m64 *GetPointerM64(void) const { return FVecData.AsM64; };
      #endif

      #if (CFG_HAVE_SSE1 == 1)
      inline __m128 *GetPointerM128(void) { return FVecData.AsM128; };
      inline const __m128 *GetPointerM128(void) const { return FVecData.AsM128; };
      #endif

      #if (CFG_HAVE_SSE2 == 1)
      inline __m128i *GetPointerM128I(void) { return FVecData.AsM128I; };
      inline const __m128i *GetPointerM128I(void) const { return FVecData.AsM128I; };
      #if (CFG_ONLY_INTEGER_SSE2 == 0)
      inline __m128d *GetPointerM128D(void) { return FVecData.AsM128D; };
      inline const __m128d *GetPointerM128D(void) const { return FVecData.AsM128D; };
      #endif
      #endif

      inline uint128_t *GetPointerU128(void) { return FVecData.AsU128; };
      inline const uint128_t *GetPointerU128(void) const { return FVecData.AsU128; };

      inline uint128fp32_t *GetPointerU128FP32(void) { return FVecData.AsU128FP32; };
      inline const uint128fp32_t *GetPointerU128FP32(void) const { return FVecData.AsU128FP32; };

      inline uint128fp64_t *GetPointerU128FP64(void) { return FVecData.AsU128FP64; };
      inline const uint128fp64_t *GetPointerU128FP64(void) const { return FVecData.AsU128FP64; };

      template<class ElementType> inline CDataBuffer_ConstView<ElementType, NumBytes> GetConstView(void) const
      { return CDataBuffer_ConstView<ElementType, NumBytes>(*this); }
      template<class ElementType> inline CDataBuffer_VarView<ElementType, NumBytes> GetVarView(void)
      { return CDataBuffer_VarView<ElementType, NumBytes>(*this); }
};

#if CFG_COMPILER == CFG_COMPILER_MSVC
#pragma warning(pop)
#endif

#endif
