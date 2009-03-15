/* *****************************************************************************
/
/ This file is part of Solirte, a solenoid ion ray-tracing engine.
/ (c) 2008 Michael Brown.
/ michael.brown@anu.edu.au
/
/ A random number generator that can do various distributions.
/ *************************************************************************** */

#ifndef PRNG_H
#define PRNG_H

#include "randpool.h"
#include "ziggurat.h"
// #include <math.h>
#include <string>
#include <vector>

#ifndef CFG_TIMETRACK_DISABLE
#include "../platform/timetrack.h"
#endif

#if CFG_COMPILER == CFG_COMPILER_MSVC
// Shut up one of the more braindead MSVC warnings.
#pragma warning(push)
#pragma warning(disable: 4127)
#endif

template<class SFMTParams>
class CPRNG
{
  public:
    static const size_t BufSize = CRandPool<SFMTParams>::BufSize;
  private:
    #ifndef CFG_TIMETRACK_DISABLE
    static struct TMetrics
    {
      static THREADVAR uint32_t uniform_FP64_refill_count;
      static THREADVAR uint64_t uniform_FP64_refill_time;
      static THREADVAR uint32_t uniform_FP32_refill_count;
      static THREADVAR uint64_t uniform_FP32_refill_time;
      static THREADVAR uint32_t gaussiantail_FP64_refill_count;
      static THREADVAR uint64_t gaussiantail_FP64_refill_time;
      static THREADVAR uint32_t gaussian_FP64_refill_count;
      static THREADVAR uint64_t gaussian_FP64_refill_time;
      static THREADVAR uint64_t gaussian_FP64_numgen;
      static THREADVAR uint32_t exponential_FP64_refill_count;
      static THREADVAR uint64_t exponential_FP64_refill_time;
      static THREADVAR uint64_t exponential_FP64_numgen;
      static THREADVAR uint32_t exponential_FP32_refill_count;
      static THREADVAR uint64_t exponential_FP32_refill_time;
      static THREADVAR uint64_t exponential_FP32_numgen;

      TMetrics(void)
      {
        CPerfCounters::SetName(uniform_FP64_refill_count, "CPRNG<" + GenToString(SFMTParams::MEXP) + ">.uniform.FP64.refill.count");
        CPerfCounters::SetName(uniform_FP64_refill_time, "CPRNG<" + GenToString(SFMTParams::MEXP) + ">.uniform.FP64.refill.time");
        CPerfCounters::SetName(uniform_FP32_refill_count, "CPRNG<" + GenToString(SFMTParams::MEXP) + ">.uniform.FP32.refill.count");
        CPerfCounters::SetName(uniform_FP32_refill_time, "CPRNG<" + GenToString(SFMTParams::MEXP) + ">.uniform.FP32.refill.time");
        CPerfCounters::SetName(gaussiantail_FP64_refill_count, "CPRNG<" + GenToString(SFMTParams::MEXP) + ">.gaussiantail.FP64.refill.count");
        CPerfCounters::SetName(gaussiantail_FP64_refill_time, "CPRNG<" + GenToString(SFMTParams::MEXP) + ">.gaussiantail.FP64.refill.time");
        CPerfCounters::SetName(gaussian_FP64_refill_count, "CPRNG<" + GenToString(SFMTParams::MEXP) + ">.gaussian.FP64.refill.count");
        CPerfCounters::SetName(gaussian_FP64_refill_time, "CPRNG<" + GenToString(SFMTParams::MEXP) + ">.gaussian.FP64.refill.time");
        CPerfCounters::SetName(gaussian_FP64_numgen, "CPRNG<" + GenToString(SFMTParams::MEXP) + ">.gaussian.FP64.numgen");
        CPerfCounters::SetName(exponential_FP64_refill_count, "CPRNG<" + GenToString(SFMTParams::MEXP) + ">.exponential.FP64.refill.count");
        CPerfCounters::SetName(exponential_FP64_refill_time, "CPRNG<" + GenToString(SFMTParams::MEXP) + ">.exponential.FP64.refill.time");
        CPerfCounters::SetName(exponential_FP64_numgen, "CPRNG<" + GenToString(SFMTParams::MEXP) + ">.exponential.FP64.numgen");
        CPerfCounters::SetName(exponential_FP32_refill_count, "CPRNG<" + GenToString(SFMTParams::MEXP) + ">.exponential.FP32.refill.count");
        CPerfCounters::SetName(exponential_FP32_refill_time, "CPRNG<" + GenToString(SFMTParams::MEXP) + ">.exponential.FP32.refill.time");
        CPerfCounters::SetName(exponential_FP32_numgen, "CPRNG<" + GenToString(SFMTParams::MEXP) + ">.exponential.FP32.numgen");
      }

      void ForceConstruction(void) { }
    } Metrics;
    #endif
    
  private:
    // Uniform random doubles on [0,1)
    static const size_t FBufLen_uniform_FP64 = BufSize * 2;
    CDataBuffer<BufSize * 16> FBuffer_uniform_FP64;
    // Uniform random singles on [0,1)
    static const size_t FBufLen_uniform_FP32 = BufSize * 4;
    CDataBuffer<BufSize * 16> FBuffer_uniform_FP32;

    // Gaussian tail random doubles (for Ziggurat). Note 2:1 reduction ratio
    // (needs 2 u128's to generate 2 doubles).
    static const size_t FBufLen_gaussiantail_FP64 = (BufSize / 2) * 2;
    CDataBuffer<BufSize / 2 * 16> FBuffer_gaussiantail_FP64;
    // Gaussian random doubles.
    CDataBuffer<BufSize * 16> FBuffer_gaussian_FP64;
    // Exponential random doubles.
    CDataBuffer<BufSize * 16> FBuffer_exponential_FP64;
    // Exponential random singles.
    CDataBuffer<BufSize * 16> FBuffer_exponential_FP32;
    // Generic integer pool
    CDataBuffer<BufSize * 16> FBuffer_integer;
    // The randpool itself.
    CRandPool<SFMTParams> FRandPool;
    // Positions and lengths.
    size_t FBufPos_uniform_FP64;
    size_t FBufPos_uniform_FP32;
    size_t FBufPos_gaussiantail_FP64;
    size_t FBufLen_gaussian_FP64;
    size_t FBufPos_gaussian_FP64;
    size_t FBufLen_exponential_FP64;
    size_t FBufPos_exponential_FP64;
    size_t FBufLen_exponential_FP32;
    size_t FBufPos_exponential_FP32;
    double FScaleFactor_exponential_FP64;
    float FScaleFactor_exponential_FP32;
    size_t FBufPos_integer;
    int RefCount;
  protected:
    void RefillBuf_uniform_FP64(void);
    void RefillBuf_uniform_FP32(void);
    void RefillBuf_gaussiantail_FP64(void);
    void RefillBuf_gaussian_FP64(void);
    void RefillBuf_exponential_FP64(void);
    void RefillBuf_exponential_FP32(void);
    void RefillBuf_integer(void);
  public:
    static std::string GetIDString(void) { return CRandPool<SFMTParams>::GetIDString(); }

    void Seed(uint32_t seed)
    {
      FRandPool.init_gen_rand(seed);
      FBufPos_uniform_FP64 = BufSize * 2;
      FBufPos_uniform_FP32 = BufSize * 4;
      FBufPos_gaussiantail_FP64 = BufSize;
      FBufPos_gaussian_FP64 = 0;
      FBufLen_gaussian_FP64 = 0;
      FBufPos_exponential_FP64 = 0;
      FBufLen_exponential_FP64 = 0;
      FScaleFactor_exponential_FP64 = 0;
      FBufPos_exponential_FP32 = 0;
      FBufLen_exponential_FP32 = 0;
      FScaleFactor_exponential_FP32 = 0;
      FBufPos_integer = BufSize * 16;
    }

    CPRNG(uint32_t seed)
    {
      Seed(seed);
      RefCount = 1;
      #ifndef CFG_TIMETRACK_DISABLE
      Metrics.ForceConstruction();
      #endif
    }

    int AddRef(void) { return ++RefCount; }
    // Note: We can't do "delete this" in Release because of the thread-moving
    // capability. See CThreadRand::MovedThreads() for details.
    int Release(void) { return --RefCount; }
    int GetRefCount(void) { return RefCount; }

    double Random_uniform_FP64(void);
    float Random_uniform_FP32(void);
    double Random_gaussiantail_FP64(void);
    double Random_gaussian_FP64(void);
    double Random_exponential_FP64(void);
    float Random_exponential_FP32(void);
    uint32_t Random_u32(void);
    uint32_t Random_u32(uint32_t MaxVal);

    void Random_uniform_FP(float &x) { x = Random_uniform_FP32(); }
    void Random_uniform_FP(double &x) { x = Random_uniform_FP64(); }
    void Random_exponential_FP(double &x) { x = Random_exponential_FP64(); }
    void Random_exponential_FP(float &x) { x = Random_exponential_FP32(); }

    void RandFill_uniform_FP64(double *Buffer, size_t NumDoubles);
    void RandFill_uniform_FP32(float *Buffer, size_t NumFloats);
    void RandFill_gaussian_FP64(double *Buffer, size_t NumDoubles);
    void RandFill_gaussiantail_FP64(double *Buffer, size_t NumDoubles);
    void RandFill_exponential_FP64(double *Buffer, size_t NumDoubles);
    void RandFill_exponential_FP32(float *Buffer, size_t NumFloats);
    void RandFill_u32(uint32_t *Buffer, size_t NumU32s);

    typedef typename CRandPool<SFMTParams>::CRandomBlockPtr CRandomBlockPtr;
    CRandomBlockPtr GetRandomBlock(void) { return FRandPool.GetRandomBlock(); }

    static void *operator new(size_t size)
    {
      return _aligned_malloc(size, 16);
    }

    static void operator delete(void *p)
    {
      _aligned_free(p);
    }
};

// -----------------------------------------------------------------------------
// Uniform random singles.
// PATHDEF UniformFP32
// -----------------------------------------------------------------------------
template<class SFMTParams>
NOINLINE void CPRNG<SFMTParams>::RefillBuf_uniform_FP32(void)
{
  #ifndef CFG_TIMETRACK_DISABLE
  CTimedScope ScopeTimer(Metrics.uniform_FP32_refill_time);
  Metrics.uniform_FP32_refill_count++;
  #endif

  typename CRandPool<SFMTParams>::CRandomBlockPtr RandomBlock = FRandPool.GetRandomBlock();
  // Don't need SIMDOps::EmptyForFP() here (handled per-path, since we've got an MMX path)

#if (CFG_HAVE_U128FP32 == CFG_SIMD_INTRINSIC)
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// FP32-intrinsic implementation
// PATHNAME u128fp32intrinsic
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  SIMDOps::EmptyForFP();
  CDataBuffer_ConstView<uint128fp32_t, BufSize * 16> SrcPtr = RandomBlock.template GetConstView<uint128fp32_t>();
  CDataBuffer_VarView<uint128fp32_t, BufSize * 16> DstPtr = FBuffer_uniform_FP32.template GetVarView<uint128fp32_t>();

  uint128fp32_t AndMask = SIMDOps::uint128fp32_t_const<0x007FFFFF, 0x007FFFFF, 0x007FFFFF, 0x007FFFFF>::Value();
  uint128fp32_t One = SIMDOps::uint128fp32_t_const<0x3F800000, 0x3F800000, 0x3F800000, 0x3F800000>::Value();

  size_t CopyLoop;
  for (CopyLoop = 0; CopyLoop < BufSize - (BufSize % 4); CopyLoop += 4)
  {
    DstPtr.Store(CopyLoop + 0, SIMDOP_sub(SIMDOP_or(SIMDOP_and(SrcPtr.Load(CopyLoop + 0), AndMask), One), One));
    DstPtr.Store(CopyLoop + 1, SIMDOP_sub(SIMDOP_or(SIMDOP_and(SrcPtr.Load(CopyLoop + 1), AndMask), One), One));
    DstPtr.Store(CopyLoop + 2, SIMDOP_sub(SIMDOP_or(SIMDOP_and(SrcPtr.Load(CopyLoop + 2), AndMask), One), One));
    DstPtr.Store(CopyLoop + 3, SIMDOP_sub(SIMDOP_or(SIMDOP_and(SrcPtr.Load(CopyLoop + 3), AndMask), One), One));
  }

  // Unrolling tail.
  if ((BufSize % 4) == 3)
  {
    DstPtr.Store(CopyLoop + 0, SIMDOP_sub(SIMDOP_or(SIMDOP_and(SrcPtr.Load(CopyLoop + 0), AndMask), One), One));
    DstPtr.Store(CopyLoop + 1, SIMDOP_sub(SIMDOP_or(SIMDOP_and(SrcPtr.Load(CopyLoop + 1), AndMask), One), One));
    DstPtr.Store(CopyLoop + 2, SIMDOP_sub(SIMDOP_or(SIMDOP_and(SrcPtr.Load(CopyLoop + 2), AndMask), One), One));
  }
  if ((BufSize % 4) == 2)
  {
    DstPtr.Store(CopyLoop + 0, SIMDOP_sub(SIMDOP_or(SIMDOP_and(SrcPtr.Load(CopyLoop + 0), AndMask), One), One));
    DstPtr.Store(CopyLoop + 1, SIMDOP_sub(SIMDOP_or(SIMDOP_and(SrcPtr.Load(CopyLoop + 1), AndMask), One), One));
  }
  if ((BufSize % 4) == 1)
  {
    DstPtr.Store(CopyLoop + 0, SIMDOP_sub(SIMDOP_or(SIMDOP_and(SrcPtr.Load(CopyLoop + 0), AndMask), One), One));
  }
#elif (CFG_HAVE_U128 == CFG_SIMD_INTRINSIC)
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// U128-intrinsic, fp32-scalar implementation
// PATHNAME u128intrinsic-fp32scalar
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  SIMDOps::EmptyForFP();
  CDataBuffer_ConstView<uint128_t, BufSize * 16> SrcPtr = RandomBlock.template GetConstView<uint128_t>();
  CDataBuffer_VarView<float, BufSize * 16> DstPtr = FBuffer_uniform_FP32.template GetVarView<float>();

  uint128_t AndMask = SIMDOps::uint128_t_const<0x007FFFFF, 0x007FFFFF, 0x007FFFFF, 0x007FFFFF>::Value();
  uint128_t OrMask = SIMDOps::uint128_t_const<0x3F800000, 0x3F800000, 0x3F800000, 0x3F800000>::Value();

  // Unrolled part
  union 
  {
    uint128_t AsU128;
    float AsFP32[4];
  } TempBuf[4];

  size_t CopyLoop;
  for (CopyLoop = 0; CopyLoop < BufSize - (BufSize % 4); CopyLoop += 4)
  {
    TempBuf[0].AsU128 = SIMDOP_or(SIMDOP_and(SrcPtr.Load(CopyLoop + 0), AndMask), OrMask);
    DstPtr.Store(CopyLoop * 4 + 0, TempBuf[0].AsFP32[0] - 1);
    DstPtr.Store(CopyLoop * 4 + 1, TempBuf[0].AsFP32[1] - 1);
    DstPtr.Store(CopyLoop * 4 + 2, TempBuf[0].AsFP32[2] - 1);
    DstPtr.Store(CopyLoop * 4 + 3, TempBuf[0].AsFP32[3] - 1);
    TempBuf[1].AsU128 = SIMDOP_or(SIMDOP_and(SrcPtr.Load(CopyLoop + 1), AndMask), OrMask);
    DstPtr.Store(CopyLoop * 4 + 4, TempBuf[1].AsFP32[0] - 1);
    DstPtr.Store(CopyLoop * 4 + 5, TempBuf[1].AsFP32[1] - 1);
    DstPtr.Store(CopyLoop * 4 + 6, TempBuf[1].AsFP32[2] - 1);
    DstPtr.Store(CopyLoop * 4 + 7, TempBuf[1].AsFP32[3] - 1);
    TempBuf[2].AsU128 = SIMDOP_or(SIMDOP_and(SrcPtr.Load(CopyLoop + 2), AndMask), OrMask);
    DstPtr.Store(CopyLoop * 4 + 8, TempBuf[2].AsFP32[0] - 1);
    DstPtr.Store(CopyLoop * 4 + 9, TempBuf[2].AsFP32[1] - 1);
    DstPtr.Store(CopyLoop * 4 + 10, TempBuf[2].AsFP32[2] - 1);
    DstPtr.Store(CopyLoop * 4 + 11, TempBuf[2].AsFP32[3] - 1);
    TempBuf[3].AsU128 = SIMDOP_or(SIMDOP_and(SrcPtr.Load(CopyLoop + 3), AndMask), OrMask);
    DstPtr.Store(CopyLoop * 4 + 12, TempBuf[3].AsFP32[0] - 1);
    DstPtr.Store(CopyLoop * 4 + 13, TempBuf[3].AsFP32[1] - 1);
    DstPtr.Store(CopyLoop * 4 + 14, TempBuf[3].AsFP32[2] - 1);
    DstPtr.Store(CopyLoop * 4 + 15, TempBuf[3].AsFP32[3] - 1);
  }

  // Unrolling tail.
  if ((BufSize % 4) == 3)
  {
    TempBuf[0].AsU128 = SIMDOP_or(SIMDOP_and(SrcPtr.Load(CopyLoop + 0), AndMask), OrMask);
    DstPtr.Store(CopyLoop * 4 + 0, TempBuf[0].AsFP32[0] - 1);
    DstPtr.Store(CopyLoop * 4 + 1, TempBuf[0].AsFP32[1] - 1);
    DstPtr.Store(CopyLoop * 4 + 2, TempBuf[0].AsFP32[2] - 1);
    DstPtr.Store(CopyLoop * 4 + 3, TempBuf[0].AsFP32[3] - 1);
    TempBuf[1].AsU128 = SIMDOP_or(SIMDOP_and(SrcPtr.Load(CopyLoop + 1), AndMask), OrMask);
    DstPtr.Store(CopyLoop * 4 + 4, TempBuf[1].AsFP32[0] - 1);
    DstPtr.Store(CopyLoop * 4 + 5, TempBuf[1].AsFP32[1] - 1);
    DstPtr.Store(CopyLoop * 4 + 6, TempBuf[1].AsFP32[2] - 1);
    DstPtr.Store(CopyLoop * 4 + 7, TempBuf[1].AsFP32[3] - 1);
    TempBuf[2].AsU128 = SIMDOP_or(SIMDOP_and(SrcPtr.Load(CopyLoop + 2), AndMask), OrMask);
    DstPtr.Store(CopyLoop * 4 + 8, TempBuf[2].AsFP32[0] - 1);
    DstPtr.Store(CopyLoop * 4 + 9, TempBuf[2].AsFP32[1] - 1);
    DstPtr.Store(CopyLoop * 4 + 10, TempBuf[2].AsFP32[2] - 1);
    DstPtr.Store(CopyLoop * 4 + 11, TempBuf[2].AsFP32[3] - 1);
  }
  if ((BufSize % 4) == 2)
  {
    TempBuf[0].AsU128 = SIMDOP_or(SIMDOP_and(SrcPtr.Load(CopyLoop + 0), AndMask), OrMask);
    DstPtr.Store(CopyLoop * 4 + 0, TempBuf[0].AsFP32[0] - 1);
    DstPtr.Store(CopyLoop * 4 + 1, TempBuf[0].AsFP32[1] - 1);
    DstPtr.Store(CopyLoop * 4 + 2, TempBuf[0].AsFP32[2] - 1);
    DstPtr.Store(CopyLoop * 4 + 3, TempBuf[0].AsFP32[3] - 1);
    TempBuf[1].AsU128 = SIMDOP_or(SIMDOP_and(SrcPtr.Load(CopyLoop + 1), AndMask), OrMask);
    DstPtr.Store(CopyLoop * 4 + 4, TempBuf[1].AsFP32[0] - 1);
    DstPtr.Store(CopyLoop * 4 + 5, TempBuf[1].AsFP32[1] - 1);
    DstPtr.Store(CopyLoop * 4 + 6, TempBuf[2].AsFP32[2] - 1);
    DstPtr.Store(CopyLoop * 4 + 7, TempBuf[2].AsFP32[3] - 1);
  }
  if ((BufSize % 4) == 1)
  {
    TempBuf[0].AsU128 = SIMDOP_or(SIMDOP_and(SrcPtr.Load(CopyLoop + 0), AndMask), OrMask);
    DstPtr.Store(CopyLoop * 4 + 0, TempBuf[0].AsFP32[0] - 1);
    DstPtr.Store(CopyLoop * 4 + 1, TempBuf[0].AsFP32[1] - 1);
    DstPtr.Store(CopyLoop * 4 + 2, TempBuf[0].AsFP32[2] - 1);
    DstPtr.Store(CopyLoop * 4 + 3, TempBuf[0].AsFP32[3] - 1);
  }
#elif (CFG_HAVE_U128 == CFG_SIMD_MMX)
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// U128-mmx, fp32-scalar two-pass implementation
// PATHNAME u128mmx-fp32scalar-2pass
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  {
    // Integer pass.
    CDataBuffer_ConstView<__m64, BufSize * 16> SrcPtr = RandomBlock.template GetConstView<__m64>();
    CDataBuffer_VarView<__m64, BufSize * 16> DstPtr = FBuffer_uniform_FP32.template GetVarView<__m64>();

    __m64 AndMask = SIMDOps::__m64_const<0x007FFFFF, 0x007FFFFF>::Value();
    __m64 OrMask = SIMDOps::__m64_const<0x3F800000, 0x3F800000>::Value();

    size_t CopyLoop;
    for (CopyLoop = 0; CopyLoop < BufSize - BufSize % 2; CopyLoop += 2)
    {
      DstPtr.Store(CopyLoop * 2 + 0, _mm_or_si64(_mm_and_si64(SrcPtr.Load(CopyLoop * 2 + 0), AndMask), OrMask));
      DstPtr.Store(CopyLoop * 2 + 1, _mm_or_si64(_mm_and_si64(SrcPtr.Load(CopyLoop * 2 + 1), AndMask), OrMask));
      DstPtr.Store(CopyLoop * 2 + 2, _mm_or_si64(_mm_and_si64(SrcPtr.Load(CopyLoop * 2 + 2), AndMask), OrMask));
      DstPtr.Store(CopyLoop * 2 + 3, _mm_or_si64(_mm_and_si64(SrcPtr.Load(CopyLoop * 2 + 3), AndMask), OrMask));
    }
    if ((BufSize % 2) == 1)
    {
      DstPtr.Store(CopyLoop * 2 + 0, _mm_or_si64(_mm_and_si64(SrcPtr.Load(CopyLoop * 2 + 0), AndMask), OrMask));
      DstPtr.Store(CopyLoop * 2 + 1, _mm_or_si64(_mm_and_si64(SrcPtr.Load(CopyLoop * 2 + 1), AndMask), OrMask));
    }

    SIMDOps::EmptyForFP();
  }
  {
    // Floating point pass.
    CDataBuffer_VarView<float, BufSize * 16> DstPtr = FBuffer_uniform_FP32.template GetVarView<float>();

    size_t CopyLoop;
    for (CopyLoop = 0; CopyLoop < BufSize - BufSize % 2; CopyLoop += 2)
    {
      DstPtr.Store(CopyLoop * 4 + 0, DstPtr.Load(CopyLoop * 4 + 0) - 1.0f);
      DstPtr.Store(CopyLoop * 4 + 1, DstPtr.Load(CopyLoop * 4 + 1) - 1.0f);
      DstPtr.Store(CopyLoop * 4 + 2, DstPtr.Load(CopyLoop * 4 + 2) - 1.0f);
      DstPtr.Store(CopyLoop * 4 + 3, DstPtr.Load(CopyLoop * 4 + 3) - 1.0f);
      DstPtr.Store(CopyLoop * 4 + 4, DstPtr.Load(CopyLoop * 4 + 4) - 1.0f);
      DstPtr.Store(CopyLoop * 4 + 5, DstPtr.Load(CopyLoop * 4 + 5) - 1.0f);
      DstPtr.Store(CopyLoop * 4 + 6, DstPtr.Load(CopyLoop * 4 + 6) - 1.0f);
      DstPtr.Store(CopyLoop * 4 + 7, DstPtr.Load(CopyLoop * 4 + 7) - 1.0f);
    }
    if ((BufSize % 2) == 1)
    {
      DstPtr.Store(CopyLoop * 4 + 0, DstPtr.Load(CopyLoop * 4 + 0) - 1.0f);
      DstPtr.Store(CopyLoop * 4 + 1, DstPtr.Load(CopyLoop * 4 + 1) - 1.0f);
      DstPtr.Store(CopyLoop * 4 + 2, DstPtr.Load(CopyLoop * 4 + 2) - 1.0f);
      DstPtr.Store(CopyLoop * 4 + 3, DstPtr.Load(CopyLoop * 4 + 3) - 1.0f);
    }
  }
#elif (CFG_BITS == 64)
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// U128-scalar, fp32-scalar 64-bit one-pass implementation
// PATHNAME u128scalar-fp32scalar-64bit
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  SIMDOps::EmptyForFP();
  CDataBuffer_ConstView<uint64_t, BufSize * 16> SrcPtr = RandomBlock.template GetConstView<uint64_t>();
  CDataBuffer_VarView<float, BufSize * 16> DstPtr = FBuffer_uniform_FP32.template GetVarView<float>();

  uint64_t AndMask = UINT64_C(0x007FFFFF007FFFFF);
  uint64_t OrMask = UINT64_C(0x3F8000003F800000);

  // The main conversion loop.
  union
  {
    uint64_t AsU64;
    float AsFP32[2];
  } FPConv[2];

  for (size_t CopyLoop = 0; CopyLoop < BufSize; CopyLoop++)
  {
    FPConv[0].AsU64 = (SrcPtr.Load(CopyLoop * 2 + 0) & AndMask) | OrMask;
    DstPtr.Store(CopyLoop * 4 + 0, FPConv[0].AsFP32[0] - 1.0f);
    DstPtr.Store(CopyLoop * 4 + 1, FPConv[0].AsFP32[1] - 1.0f);
    FPConv[1].AsU64 = (SrcPtr.Load(CopyLoop * 2 + 1) & AndMask) | OrMask;
    DstPtr.Store(CopyLoop * 4 + 2, FPConv[1].AsFP32[0] - 1.0f);
    DstPtr.Store(CopyLoop * 4 + 3, FPConv[1].AsFP32[1] - 1.0f);
  }
#else
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// U128-scalar, fp32-scalar 32-bit one-pass implementation
// PATHNAME u128scalar-fp32scalar-32bit
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  SIMDOps::EmptyForFP();
  CDataBuffer_ConstView<uint32_t, BufSize * 16> SrcPtr = RandomBlock.template GetConstView<uint32_t>();
  CDataBuffer_VarView<float, BufSize * 16> DstPtr = FBuffer_uniform_FP32.template GetVarView<float>();

  uint32_t AndMask = 0x007FFFFF;
  uint32_t OrMask = 0x3F800000;

  // The main conversion loop.
  union
  {
    uint32_t AsU32;
    float AsFP32;
  } FPConv[4];

  for (size_t CopyLoop = 0; CopyLoop < BufSize; CopyLoop++)
  {
    FPConv[0].AsU32 = (SrcPtr.Load(CopyLoop * 4 + 0) & AndMask) | OrMask;
    DstPtr.Store(CopyLoop * 4 + 0, FPConv[0].AsFP32 - 1.0f);
    FPConv[1].AsU32 = (SrcPtr.Load(CopyLoop * 4 + 1) & AndMask) | OrMask;
    DstPtr.Store(CopyLoop * 4 + 1, FPConv[1].AsFP32 - 1.0f);
    FPConv[2].AsU32 = (SrcPtr.Load(CopyLoop * 4 + 2) & AndMask) | OrMask;
    DstPtr.Store(CopyLoop * 4 + 2, FPConv[2].AsFP32 - 1.0f);
    FPConv[3].AsU32 = (SrcPtr.Load(CopyLoop * 4 + 3) & AndMask) | OrMask;
    DstPtr.Store(CopyLoop * 4 + 3, FPConv[3].AsFP32 - 1.0f);
  }
#endif
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// Common code.
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  FBufPos_uniform_FP32 = 0;
}

template<class SFMTParams>
inline float CPRNG<SFMTParams>::Random_uniform_FP32(void)
{
  if (FBufPos_uniform_FP32 == FBufLen_uniform_FP32) RefillBuf_uniform_FP32();
  return FBuffer_uniform_FP32.LoadFP32(EndianFix<2>(FBufPos_uniform_FP32++));
}

template<class SFMTParams>
inline void CPRNG<SFMTParams>::RandFill_uniform_FP32(float *Buffer, size_t NumFloats)
{
  size_t NumToGo = NumFloats;
  while (NumToGo > 0)
  {
    // Round up to the next 128-bit boundary.
    FBufPos_uniform_FP32 = (FBufPos_uniform_FP32 + 3) & ~3;

    // Make sure there's something to copy from.
    while (FBufLen_uniform_FP32 == FBufPos_uniform_FP32)
      RefillBuf_uniform_FP32();

    // See how many to do.
    size_t NumInBuf = FBufLen_uniform_FP32 - FBufPos_uniform_FP32;
    size_t NumToDo = (NumToGo > NumInBuf) ? NumInBuf : NumToGo;

    // Copy.
    memcpy(Buffer, FBuffer_uniform_FP32.GetPointerFP32() + FBufPos_uniform_FP32, NumToDo * sizeof(float));

    // Update pointers, etc.
    Buffer += NumToDo;
    NumToGo -= NumToDo;
    FBufPos_uniform_FP32 += NumToDo;
  }
}

// -----------------------------------------------------------------------------
// Uniform random doubles.
// PATHDEF UniformFP64
// -----------------------------------------------------------------------------
template<class SFMTParams>
NOINLINE void CPRNG<SFMTParams>::RefillBuf_uniform_FP64(void)
{
  #ifndef CFG_TIMETRACK_DISABLE
  CTimedScope ScopeTimer(Metrics.uniform_FP64_refill_time);
  Metrics.uniform_FP64_refill_count++;
  #endif

  typename CRandPool<SFMTParams>::CRandomBlockPtr RandomBlock = FRandPool.GetRandomBlock();
  // Don't need SIMDOps::EmptyForFP() here (handled per-path, since we've got an MMX path)

#if (CFG_HAVE_U128FP64 == CFG_SIMD_INTRINSIC)
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// FP64-intrinsic implementation
// PATHNAME u128fp64intrinsic
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  SIMDOps::EmptyForFP();
  CDataBuffer_ConstView<uint128fp64_t, BufSize * 16> SrcPtr = RandomBlock.template GetConstView<uint128fp64_t>();
  CDataBuffer_VarView<uint128fp64_t, BufSize * 16> DstPtr = FBuffer_uniform_FP64.template GetVarView<uint128fp64_t>();

  uint128fp64_t AndMask = SIMDOps::uint128fp64_t_const<0xFFFFFFFF, 0x000FFFFF, 0xFFFFFFFF, 0x000FFFFF>::Value();
  uint128fp64_t One = SIMDOps::uint128fp64_t_const<0x00000000, 0x3FF00000, 0x00000000, 0x3FF00000>::Value();

  size_t CopyLoop;
  for (CopyLoop = 0; CopyLoop < BufSize - (BufSize % 4); CopyLoop += 4)
  {
    DstPtr.Store(CopyLoop + 0, SIMDOP_sub(SIMDOP_or(SIMDOP_and(SrcPtr.Load(CopyLoop + 0), AndMask), One), One));
    DstPtr.Store(CopyLoop + 1, SIMDOP_sub(SIMDOP_or(SIMDOP_and(SrcPtr.Load(CopyLoop + 1), AndMask), One), One));
    DstPtr.Store(CopyLoop + 2, SIMDOP_sub(SIMDOP_or(SIMDOP_and(SrcPtr.Load(CopyLoop + 2), AndMask), One), One));
    DstPtr.Store(CopyLoop + 3, SIMDOP_sub(SIMDOP_or(SIMDOP_and(SrcPtr.Load(CopyLoop + 3), AndMask), One), One));
  }

  // Unrolling tail.
  if ((BufSize % 4) == 3)
  {
    DstPtr.Store(CopyLoop + 0, SIMDOP_sub(SIMDOP_or(SIMDOP_and(SrcPtr.Load(CopyLoop + 0), AndMask), One), One));
    DstPtr.Store(CopyLoop + 1, SIMDOP_sub(SIMDOP_or(SIMDOP_and(SrcPtr.Load(CopyLoop + 1), AndMask), One), One));
    DstPtr.Store(CopyLoop + 2, SIMDOP_sub(SIMDOP_or(SIMDOP_and(SrcPtr.Load(CopyLoop + 2), AndMask), One), One));
  }
  if ((BufSize % 4) == 2)
  {
    DstPtr.Store(CopyLoop + 0, SIMDOP_sub(SIMDOP_or(SIMDOP_and(SrcPtr.Load(CopyLoop + 0), AndMask), One), One));
    DstPtr.Store(CopyLoop + 1, SIMDOP_sub(SIMDOP_or(SIMDOP_and(SrcPtr.Load(CopyLoop + 1), AndMask), One), One));
  }
  if ((BufSize % 4) == 1)
  {
    DstPtr.Store(CopyLoop + 0, SIMDOP_sub(SIMDOP_or(SIMDOP_and(SrcPtr.Load(CopyLoop + 0), AndMask), One), One));
  }
#elif (CFG_HAVE_U128 == CFG_SIMD_INTRINSIC)
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// U128-intrinsic, fp64-scalar implementation
// PATHNAME u128intrinsic-fp64scalar
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  SIMDOps::EmptyForFP();
  CDataBuffer_ConstView<uint128_t, BufSize * 16> SrcPtr = RandomBlock.template GetConstView<uint128_t>();
  CDataBuffer_VarView<double, BufSize * 16> DstPtr = FBuffer_uniform_FP64.template GetVarView<double>();

  uint128_t AndMask = SIMDOps::uint128_t_const<0xFFFFFFFF, 0x000FFFFF, 0xFFFFFFFF, 0x000FFFFF>::Value();
  uint128_t OrMask = SIMDOps::uint128_t_const<0x00000000, 0x3FF00000, 0x00000000, 0x3FF00000>::Value();

  // Unrolled part
  union 
  {
    uint128_t AsU128;
    double AsFP64[2];
  } TempBuf[4];

  size_t CopyLoop;
  for (CopyLoop = 0; CopyLoop < BufSize - (BufSize % 4); CopyLoop += 4)
  {
    TempBuf[0].AsU128 = SIMDOP_or(SIMDOP_and(SrcPtr.Load(CopyLoop + 0), AndMask), OrMask);
    DstPtr.Store(CopyLoop * 2 + 0, TempBuf[0].AsFP64[0] - 1.0);
    DstPtr.Store(CopyLoop * 2 + 1, TempBuf[0].AsFP64[1] - 1.0);
    TempBuf[1].AsU128 = SIMDOP_or(SIMDOP_and(SrcPtr.Load(CopyLoop + 1), AndMask), OrMask);
    DstPtr.Store(CopyLoop * 2 + 2, TempBuf[1].AsFP64[0] - 1.0);
    DstPtr.Store(CopyLoop * 2 + 3, TempBuf[1].AsFP64[1] - 1.0);
    TempBuf[2].AsU128 = SIMDOP_or(SIMDOP_and(SrcPtr.Load(CopyLoop + 2), AndMask), OrMask);
    DstPtr.Store(CopyLoop * 2 + 4, TempBuf[2].AsFP64[0] - 1.0);
    DstPtr.Store(CopyLoop * 2 + 5, TempBuf[2].AsFP64[1] - 1.0);
    TempBuf[3].AsU128 = SIMDOP_or(SIMDOP_and(SrcPtr.Load(CopyLoop + 3), AndMask), OrMask);
    DstPtr.Store(CopyLoop * 2 + 6, TempBuf[3].AsFP64[0] - 1.0);
    DstPtr.Store(CopyLoop * 2 + 7, TempBuf[3].AsFP64[1] - 1.0);
  }

  // Unrolling tail.
  if ((BufSize % 4) == 3)
  {
    TempBuf[0].AsU128 = SIMDOP_or(SIMDOP_and(SrcPtr.Load(CopyLoop + 0), AndMask), OrMask);
    DstPtr.Store(CopyLoop * 2 + 0, TempBuf[0].AsFP64[0] - 1.0);
    DstPtr.Store(CopyLoop * 2 + 1, TempBuf[0].AsFP64[1] - 1.0);
    TempBuf[1].AsU128 = SIMDOP_or(SIMDOP_and(SrcPtr.Load(CopyLoop + 1), AndMask), OrMask);
    DstPtr.Store(CopyLoop * 2 + 2, TempBuf[1].AsFP64[0] - 1.0);
    DstPtr.Store(CopyLoop * 2 + 3, TempBuf[1].AsFP64[1] - 1.0);
    TempBuf[2].AsU128 = SIMDOP_or(SIMDOP_and(SrcPtr.Load(CopyLoop + 2), AndMask), OrMask);
    DstPtr.Store(CopyLoop * 2 + 4, TempBuf[2].AsFP64[0] - 1.0);
    DstPtr.Store(CopyLoop * 2 + 5, TempBuf[2].AsFP64[1] - 1.0);
  }
  if ((BufSize % 4) == 2)
  {
    TempBuf[0].AsU128 = SIMDOP_or(SIMDOP_and(SrcPtr.Load(CopyLoop + 0), AndMask), OrMask);
    DstPtr.Store(CopyLoop * 2 + 0, TempBuf[0].AsFP64[0] - 1.0);
    DstPtr.Store(CopyLoop * 2 + 1, TempBuf[0].AsFP64[1] - 1.0);
    TempBuf[1].AsU128 = SIMDOP_or(SIMDOP_and(SrcPtr.Load(CopyLoop + 1), AndMask), OrMask);
    DstPtr.Store(CopyLoop * 2 + 2, TempBuf[1].AsFP64[0] - 1.0);
    DstPtr.Store(CopyLoop * 2 + 3, TempBuf[1].AsFP64[1] - 1.0);
  }
  if ((BufSize % 4) == 1)
  {
    TempBuf[0].AsU128 = SIMDOP_or(SIMDOP_and(SrcPtr.Load(CopyLoop + 0), AndMask), OrMask);
    DstPtr.Store(CopyLoop * 2 + 0, TempBuf[0].AsFP64[0] - 1.0);
    DstPtr.Store(CopyLoop * 2 + 1, TempBuf[0].AsFP64[1] - 1.0);
  }
#elif (CFG_HAVE_U128 == CFG_SIMD_MMX)
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// U128-mmx, fp64-scalar two-pass implementation
// PATHNAME u128mmx-fp64scalar-2pass
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  {
    // Integer pass.
    CDataBuffer_ConstView<__m64, BufSize * 16> SrcPtr = RandomBlock.template GetConstView<__m64>();
    CDataBuffer_VarView<__m64, BufSize * 16> DstPtr = FBuffer_uniform_FP64.template GetVarView<__m64>();

    __m64 AndMask = SIMDOps::__m64_const<0xFFFFFFFF, 0x000FFFFF>::Value();
    __m64 OrMask = SIMDOps::__m64_const<0x00000000, 0x3FF00000>::Value();

    size_t CopyLoop;
    for (CopyLoop = 0; CopyLoop < BufSize - BufSize % 2; CopyLoop += 2)
    {
      DstPtr.Store(CopyLoop * 2 + 0, _mm_or_si64(_mm_and_si64(SrcPtr.Load(CopyLoop * 2 + 0), AndMask), OrMask));
      DstPtr.Store(CopyLoop * 2 + 1, _mm_or_si64(_mm_and_si64(SrcPtr.Load(CopyLoop * 2 + 1), AndMask), OrMask));
      DstPtr.Store(CopyLoop * 2 + 2, _mm_or_si64(_mm_and_si64(SrcPtr.Load(CopyLoop * 2 + 2), AndMask), OrMask));
      DstPtr.Store(CopyLoop * 2 + 3, _mm_or_si64(_mm_and_si64(SrcPtr.Load(CopyLoop * 2 + 3), AndMask), OrMask));
    }
    if ((BufSize % 2) == 1)
    {
      DstPtr.Store(CopyLoop * 2 + 0, _mm_or_si64(_mm_and_si64(SrcPtr.Load(CopyLoop * 2 + 0), AndMask), OrMask));
      DstPtr.Store(CopyLoop * 2 + 1, _mm_or_si64(_mm_and_si64(SrcPtr.Load(CopyLoop * 2 + 1), AndMask), OrMask));
    }

    SIMDOps::EmptyForFP();
  }
  {
    // Floating point pass.
    CDataBuffer_VarView<double, BufSize * 16> DstPtr = FBuffer_uniform_FP64.template GetVarView<double>();

    size_t CopyLoop;
    for (CopyLoop = 0; CopyLoop < BufSize - BufSize % 2; CopyLoop += 2)
    {
      DstPtr.Store(CopyLoop * 2 + 0, DstPtr.Load(CopyLoop * 2 + 0) - 1.0);
      DstPtr.Store(CopyLoop * 2 + 1, DstPtr.Load(CopyLoop * 2 + 1) - 1.0);
      DstPtr.Store(CopyLoop * 2 + 2, DstPtr.Load(CopyLoop * 2 + 2) - 1.0);
      DstPtr.Store(CopyLoop * 2 + 3, DstPtr.Load(CopyLoop * 2 + 3) - 1.0);
    }
    if ((BufSize % 2) == 1)
    {
      DstPtr.Store(CopyLoop * 2 + 0, DstPtr.Load(CopyLoop * 2 + 0) - 1.0);
      DstPtr.Store(CopyLoop * 2 + 1, DstPtr.Load(CopyLoop * 2 + 1) - 1.0);
    }
  }
#elif (CFG_BITS == 64)
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// U128-scalar, fp64-scalar 64-bit one-pass implementation
// PATHNAME u128scalar-fp64scalar-64bit
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  SIMDOps::EmptyForFP();
  CDataBuffer_ConstView<uint64_t, BufSize * 16> SrcPtr = RandomBlock.template GetConstView<uint64_t>();
  CDataBuffer_VarView<double, BufSize * 16> DstPtr = FBuffer_uniform_FP64.template GetVarView<double>();

  uint64_t AndMask = UINT64_C(0x000FFFFFFFFFFFFF);
  uint64_t OrMask = UINT64_C(0x3FF0000000000000);

  // The main conversion loop.
  union
  {
    uint64_t AsU64;
    double AsFP64;
  } FPConv[2];

  for (size_t CopyLoop = 0; CopyLoop < 2 * BufSize; CopyLoop += 2)
  {
    FPConv[0].AsU64 = (SrcPtr.Load(CopyLoop + 0) & AndMask) | OrMask;
    DstPtr.Store(CopyLoop + 0, FPConv[0].AsFP64 - 1.0);
    FPConv[1].AsU64 = (SrcPtr.Load(CopyLoop + 1) & AndMask) | OrMask;
    DstPtr.Store(CopyLoop + 1, FPConv[1].AsFP64 - 1.0);
  }
#else
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// U128-scalar, fp64-scalar 32-bit one-pass implementation
// PATHNAME u128scalar-fp64scalar-32bit
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  SIMDOps::EmptyForFP();
  CDataBuffer_ConstView<uint32_t, BufSize * 16> SrcPtr = RandomBlock.template GetConstView<uint32_t>();
  CDataBuffer_VarView<double, BufSize * 16> DstPtr = FBuffer_uniform_FP64.template GetVarView<double>();

  uint32_t AndMask = 0x000FFFFF;
  uint32_t OrMask = 0x3FF00000;

  // The main conversion loop.
  union
  {
    uint32_t AsU32[2];
    double AsFP64;
  } FPConv[2];

  for (size_t CopyLoop = 0; CopyLoop < BufSize; CopyLoop++)
  {
    FPConv[0].AsU32[EndianFix_static<1, 1>::Value] = (SrcPtr.Load(CopyLoop * 4 + EndianFix_static<2, 1>::Value) & AndMask) | OrMask;
    FPConv[0].AsU32[EndianFix_static<1, 0>::Value] = SrcPtr.Load(CopyLoop * 4 + EndianFix_static<2, 0>::Value);
    DstPtr.Store(CopyLoop * 2 + EndianFix_static<1, 0>::Value, FPConv[0].AsFP64 - 1.0);
    FPConv[1].AsU32[EndianFix_static<1, 1>::Value] = (SrcPtr.Load((CopyLoop) * 4 + EndianFix_static<2, 3>::Value) & AndMask) | OrMask;
    FPConv[1].AsU32[EndianFix_static<1, 0>::Value] = SrcPtr.Load((CopyLoop) * 4 + EndianFix_static<2, 2>::Value);
    DstPtr.Store(CopyLoop * 2 + EndianFix_static<1, 1>::Value, FPConv[1].AsFP64 - 1.0);
  }
#endif
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// Common code.
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  FBufPos_uniform_FP64 = 0;
}


template<class SFMTParams>
inline double CPRNG<SFMTParams>::Random_uniform_FP64(void)
{
  if (FBufPos_uniform_FP64 == FBufLen_uniform_FP64) RefillBuf_uniform_FP64();
  return FBuffer_uniform_FP64.LoadFP64(EndianFix<1>(FBufPos_uniform_FP64++));
}

template<class SFMTParams>
inline void CPRNG<SFMTParams>::RandFill_uniform_FP64(double *Buffer, size_t NumDoubles)
{
  size_t NumToGo = NumDoubles;
  while (NumToGo > 0)
  {
    // Round up to the next 128-bit boundary.
    FBufPos_uniform_FP64 = (FBufPos_uniform_FP64 + 1) & ~1;

    // Make sure there's something to copy from.
    while (FBufLen_uniform_FP64 == FBufPos_uniform_FP64)
      RefillBuf_uniform_FP64();

    // See how many to do.
    size_t NumInBuf = FBufLen_uniform_FP64 - FBufPos_uniform_FP64;
    size_t NumToDo = (NumToGo > NumInBuf) ? NumInBuf : NumToGo;

    // Copy.
    memcpy(Buffer, FBuffer_uniform_FP64.GetPointerFP64() + FBufPos_uniform_FP64, NumToDo * sizeof(double));

    // Update pointers, etc.
    Buffer += NumToDo;
    NumToGo -= NumToDo;
    FBufPos_uniform_FP64 += NumToDo;
  }
}

// -----------------------------------------------------------------------------
// Gaussian tail random numbers.
// PATHDEF GaussianTailFP64
// -----------------------------------------------------------------------------
template<class SFMTParams>
NOINLINE void CPRNG<SFMTParams>::RefillBuf_gaussiantail_FP64(void)
{
  #ifndef CFG_TIMETRACK_DISABLE
  CTimedScope ScopeTimer(Metrics.gaussiantail_FP64_refill_time);
  Metrics.gaussiantail_FP64_refill_count++;
  #endif

  typename CRandPool<SFMTParams>::CRandomBlockPtr RandomBlock = FRandPool.GetRandomBlock();
  SIMDOps::EmptyForFP();

#if (CFG_HAVE_U128 == CFG_SIMD_INTRINSIC) && (CFG_HAVE_U128FP64 == CFG_SIMD_INTRINSIC)
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// U128-intrinsic, fp64-intrinsic implementation
// PATHNAME u128fp64intrinsic
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  // Some constants.
  uint128fp64_t SignAndMask = SIMDOps::uint128fp64_t_const<0x00000000, 0x80000000, 0x00000000, 0x80000000>::Value();
  uint128fp64_t FPAndMask = SIMDOps::uint128fp64_t_const<0xFFFFFFFF, 0x000FFFFF, 0xFFFFFFFF, 0x000FFFFF>::Value();
  uint128fp64_t FPOrMask = SIMDOps::uint128fp64_t_const<0x00000000, 0x3FF00000, 0x00000000, 0x3FF00000>::Value();

  double a = CZigguratGaussian_FP64::Bins[1].XScale;
  double a2 = a * a;
  uint128fp64_t a128 = SIMDOps::make_uint128fp64_t(a, a);

  // Process each of the values.
  CDataBuffer_ConstView<uint128fp64_t, BufSize * 16> SrcPtr = RandomBlock.template GetConstView<uint128fp64_t>();
  CDataBuffer_VarView<uint128fp64_t, BufSize / 2 * 16> DstPtr = FBuffer_gaussiantail_FP64.template GetVarView<uint128fp64_t>();

  for (size_t SrcIdx = 0; SrcIdx < FBufLen_gaussiantail_FP64 / 2; SrcIdx++)
  {
    // From the first uint128_t, extract two fp64's (and two signs later).
    uint128fp64_t Src = SrcPtr.Load(SrcIdx * 2);
    uint128fp64_t u1 = SIMDOP_sub(SIMDOP_or(SIMDOP_and(Src, FPAndMask), FPOrMask), FPOrMask);
    uint128fp64_t SignBit = SIMDOP_and(Src, SignAndMask);

    // Transform u1
    union
    {
      uint128fp64_t AsU128;
      double AsFP64[2];
    } Test = {u1};
    Test.AsFP64[0] = sqrt(a2 - 2 * log(Test.AsFP64[0]));
    Test.AsFP64[1] = sqrt(a2 - 2 * log(Test.AsFP64[1]));

    // Calculate the compare result (u2 < a / Test) ie: Test * u2 < a
    // Accept if Test * u2 < a
    uint128fp64_t u2 = SIMDOP_sub(SIMDOP_or(SIMDOP_and(SrcPtr.Load(SrcIdx * 2 + 1), FPAndMask), FPOrMask), FPOrMask);
    uint128fp64_t CompareResult = SIMDOps::CmpGE(SIMDOP_mul(Test.AsU128, u2), a128);

    // Store the transformed u1.
    DstPtr.Store(SrcIdx, SIMDOP_or(SIMDOP_or(Test.AsU128, SignBit), CompareResult));
  }
#elif (CFG_HAVE_U128 == CFG_SIMD_INTRINSIC) // Note: No mmx due to emms overhead.
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// U128-intrinsic, fp64-scalar implementation
// PATHNAME u128intrinsic-fp64scalar
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  // Some constants.
  uint128_t SignAndMask = SIMDOps::uint128_t_const<0x00000000, 0x80000000, 0x00000000, 0x80000000>::Value();
  uint128_t FPAndMask = SIMDOps::uint128_t_const<0xFFFFFFFF, 0x000FFFFF, 0xFFFFFFFF, 0x000FFFFF>::Value();
  uint128_t FPOrMask = SIMDOps::uint128_t_const<0x00000000, 0x3FF00000, 0x00000000, 0x3FF00000>::Value();

  double a = CZigguratGaussian_FP64::Bins[1].XScale;
  double a2 = a * a;

  // Process each of the values.
  CDataBuffer_ConstView<uint128_t, BufSize * 16> SrcPtr = RandomBlock.template GetConstView<uint128_t>();
  CDataBuffer_VarView<uint128_t, BufSize / 2 * 16> DstPtr = FBuffer_gaussiantail_FP64.template GetVarView<uint128_t>();

  union
  {
    uint128_t AsU128;
    double AsFP64[2];
  } u1;

  union
  {
    uint128_t AsU128;
    double AsFP64[2];
  } u2;

  for (size_t SrcIdx = 0; SrcIdx < FBufLen_gaussiantail_FP64 / 2; SrcIdx++)
  {
    // Extract (u1 + 1) and the sign bit.
    uint128_t TempSrc = SrcPtr.Load(SrcIdx * 2);
    u1.AsU128 = SIMDOP_or(SIMDOP_and(TempSrc, FPAndMask), FPOrMask);
    uint128_t SignBit = SIMDOP_and(TempSrc, SignAndMask);

    // Extract (u2 + 1).
    u2.AsU128 = SIMDOP_or(SIMDOP_and(SrcPtr.Load(SrcIdx * 2 + 1), FPAndMask), FPOrMask);

    // Transform u1.
    double Test0 = sqrt(a2 - 2 * log(u1.AsFP64[0] - 1.0));
    double Test1 = sqrt(a2 - 2 * log(u1.AsFP64[1] - 1.0));
    union
    {
      double AsFP64[2];
      uint128_t AsU128;
    } Test = {{Test0, Test1}};

    // Calculate the compare results (u2 < a / Test) ie: Test * u2 < a
    // Accept if Test * u2 < a
    #if (CFG_BITS == 64)
    uint64_t Compare0 = ((Test0 * (u2.AsFP64[0] - 1.0)) >= a) ? UINT64_C(0xFFFFFFFFFFFFFFFF) : 0;
    uint64_t Compare1 = ((Test1 * (u2.AsFP64[1] - 1.0)) >= a) ? UINT64_C(0xFFFFFFFFFFFFFFFF) : 0;
    union
    {
      uint64_t AsU64[2];
      uint128_t AsU128;
    } CompareResult = {{Compare0, Compare1}};
    #else
    uint32_t Compare0 = ((Test0 * (u2.AsFP64[0] - 1.0)) >= a) ? 0xFFFFFFFF : 0;
    uint32_t Compare1 = ((Test1 * (u2.AsFP64[1] - 1.0)) >= a) ? 0xFFFFFFFF : 0;
    union
    {
      uint32_t AsU32[4];
      uint128_t AsU128;
    } CompareResult = {{Compare0, Compare0, Compare1, Compare1}};
    #endif

    // Store the transformed u1.
    DstPtr.Store(SrcIdx, SIMDOP_or(SIMDOP_or(Test.AsU128, SignBit), CompareResult.AsU128));
  }
#elif (CFG_BITS == 64)
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// U128-scalar, fp64-scalar 64-bit implementation
// PATHNAME u128scalar-fp64scalar-64bit
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  // Some constants.
  const uint64_t FPAndMask = UINT64_C(0x000FFFFFFFFFFFFF);
  const uint64_t FPOrMask = UINT64_C(0x3FF0000000000000);
  const uint64_t SignAndMask = UINT64_C(0x8000000000000000);

  double a = CZigguratGaussian_FP64::Bins[1].XScale;
  double a2 = a * a;

  // Process each of the values.
  CDataBuffer_ConstView<uint64_t, BufSize * 16> SrcPtr = RandomBlock.template GetConstView<uint64_t>();
  CDataBuffer_VarView<uint64_t, BufSize / 2 * 16> DstPtr = FBuffer_gaussiantail_FP64.template GetVarView<uint64_t>();

  union
  {
    uint64_t AsU64;
    double AsFP64;
  } u1;

  union
  {
    uint64_t AsU64;
    double AsFP64;
  } u2;

  for (size_t SrcIdx = 0; SrcIdx < FBufLen_gaussiantail_FP64 * 2; SrcIdx++)
  {
    // Extract (u1 + 1) and the sign bit.
    uint64_t TmpSrc = SrcPtr.Load(SrcIdx);
    u1.AsU64 = (TmpSrc & FPAndMask) | FPOrMask;
    uint64_t SignBit = TmpSrc & SignAndMask;

    // Extract (u2 + 1).
    u2.AsU64 = (SrcPtr.Load(SrcIdx + 2) & FPAndMask) | FPOrMask;

    // Calculate Test = sqrt(a * a - 2 * log(u1))
    // Reuse the u1 structure to convert to a u64.
    double Test = sqrt(a2 - 2 * log(u1.AsFP64 - 1.0));
    u1.AsFP64 = Test;

    // Calculate the destination index.
    size_t DstIdx = (SrcIdx & 1) + (SrcIdx / 4 * 2);

    // Calculate the compare result (u2 < a / Test) ie: Test * u2 < a
    // Accept if Test * u2 < a
    uint64_t OrMask = ((Test * (u2.AsFP64 - 1.0)) >= a) ? UINT64_C(0xFFFFFFFFFFFFFFFF) : 0;

    DstPtr.Store(DstIdx, u1.AsU64 | OrMask | SignBit);

    // Special counting up: we want the loop index to go 0, 1, 4, 5, 8, 9, ...
    // since the values inbetween are used for the second random number u2.
    SrcIdx += 2 * (SrcIdx & 1);
  }
#else
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// U128-scalar, fp64-scalar 32-bit implementation
// PATHNAME u128scalar-fp64scalar-32bit
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  // Some constants.
  const uint32_t FPAndMask = 0x000FFFFF;
  const uint32_t FPOrMask = 0x3FF00000;
  const uint32_t SignAndMask = 0x80000000;

  double a = CZigguratGaussian_FP64::Bins[1].XScale;
  double a2 = a * a;

  // Process each of the values.
  CDataBuffer_ConstView<uint32_t, BufSize * 16> SrcPtr = RandomBlock.template GetConstView<uint32_t>();
  CDataBuffer_VarView<uint32_t, BufSize / 2 * 16> DstPtr = FBuffer_gaussiantail_FP64.template GetVarView<uint32_t>();

  union
  {
    uint32_t AsU32[2];
    double AsFP64;
  } u1;

  union
  {
    uint32_t AsU32[2];
    double AsFP64;
  } u2;

  for (size_t SrcIdx = 0; SrcIdx < FBufLen_gaussiantail_FP64 * 2; SrcIdx++)
  {
    // Extract (u1 + 1) and the sign bit.
    u1.AsU32[EndianFix_static<1, 0>::Value] = SrcPtr.Load(SrcIdx * 2 + EndianFix_static<1, 0>::Value);
    uint32_t TmpSrc = SrcPtr.Load(SrcIdx * 2 + EndianFix_static<1, 1>::Value);
    u1.AsU32[EndianFix_static<1, 1>::Value] = (TmpSrc & FPAndMask) | FPOrMask;
    uint32_t SignBit = TmpSrc & SignAndMask;

    // Extract (u2 + 1).
    u2.AsU32[EndianFix_static<1, 0>::Value] = SrcPtr.Load((SrcIdx + 2) * 2 + EndianFix_static<1, 0>::Value);
    u2.AsU32[EndianFix_static<1, 1>::Value] = (SrcPtr.Load((SrcIdx + 2) * 2 + EndianFix_static<1, 1>::Value) & FPAndMask) | FPOrMask;

    // Calculate Test = sqrt(a * a - 2 * log(u1))
    // Reuse the u1 structure to convert to two u32's.
    double Test = sqrt(a2 - 2 * log(u1.AsFP64 - 1.0));
    u1.AsFP64 = Test;

    // Calculate the destination index.
    size_t DstIdx = (SrcIdx & 1) + (SrcIdx / 4 * 2);

    // Calculate the compare result (u2 < a / Test) ie: Test * u2 < a
    // Accept if Test * u2 < a
    uint32_t OrMask = ((Test * (u2.AsFP64 - 1.0)) >= a) ? 0xFFFFFFFF : 0;

    DstPtr.Store(DstIdx * 2 + EndianFix_static<1, 0>::Value, u1.AsU32[EndianFix_static<1, 0>::Value] | OrMask);
    DstPtr.Store(DstIdx * 2 + EndianFix_static<1, 1>::Value, u1.AsU32[EndianFix_static<1, 1>::Value] | OrMask | SignBit);

    // Special counting up: we want the loop index to go 0, 1, 4, 5, 8, 9, ...
    // since the values inbetween are used for the second random number u2.
    SrcIdx += 2 * (SrcIdx & 1);
  }
#endif
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// Common code.
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  FBufPos_gaussiantail_FP64 = 0;
}

template<class SFMTParams>
inline double CPRNG<SFMTParams>::Random_gaussiantail_FP64(void)
{
  for (;;)
  {
    while (FBufPos_gaussiantail_FP64 < FBufLen_gaussiantail_FP64)
    {
      size_t SrcIdx = EndianFix<1>(FBufPos_gaussiantail_FP64++);
      // If the upper 32 bits is 0xffffffff then it's a NaN so skip.
      if (FBuffer_gaussiantail_FP64.LoadU32(SrcIdx * 2 + EndianFix_static<1, 1>::Value) != 0xffffffff)
        return FBuffer_gaussiantail_FP64.LoadFP64(SrcIdx);
    }
    RefillBuf_gaussiantail_FP64();
  }
}

template<class SFMTParams>
inline void CPRNG<SFMTParams>::RandFill_gaussiantail_FP64(double *Buffer, size_t NumDoubles)
{
  size_t NumDone = 0;
  for(;;)
  {
    // Copy.
    for (size_t CopyLoop = FBufPos_gaussiantail_FP64; CopyLoop < FBufLen_gaussiantail_FP64; CopyLoop++)
    {
      size_t SrcIdx = EndianFix<1>(CopyLoop);
      if (FBuffer_gaussiantail_FP64.LoadU32(SrcIdx * 2 + EndianFix_static<1, 1>::Value) != 0xffffffff)
      {
        Buffer[NumDone++] = FBuffer_gaussiantail_FP64.LoadFP64(SrcIdx);
        if (NumDone == NumDoubles)
        {
          FBufPos_gaussiantail_FP64 = CopyLoop + 1;
          return;
        }
      }
    }

    // The only way to get here is if the buffer is empty. Refill it.
    RefillBuf_gaussiantail_FP64();    
  }
}

// -----------------------------------------------------------------------------
// Gaussian random numbers.
// PATHDEF GaussianFP64
// -----------------------------------------------------------------------------
template<class SFMTParams>
NOINLINE void CPRNG<SFMTParams>::RefillBuf_gaussian_FP64(void)
{
  #ifndef CFG_TIMETRACK_DISABLE
  CTimedScope ScopeTimer(Metrics.gaussian_FP64_refill_time);
  Metrics.gaussian_FP64_refill_count++;
  #endif

  typename CRandPool<SFMTParams>::CRandomBlockPtr RandomBlock = FRandPool.GetRandomBlock();
  SIMDOps::EmptyForFP();
  size_t DstPos = 0;

#if (CFG_HAVE_U128 == CFG_SIMD_INTRINSIC) && (CFG_HAVE_U128FP64 == CFG_SIMD_INTRINSIC)
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// U128-intrinsic, fp64-intrinsic implementation
// PATHNAME u128fp64intrinsic
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  CDataBuffer_ConstView<uint128_t, BufSize * 16> SrcPtr = RandomBlock.template GetConstView<uint128_t>();
  CDataBuffer_VarView<double, BufSize * 16> DstPtr = FBuffer_gaussian_FP64.template GetVarView<double>();

  // Load a few constants.
  uint128_t FPAndMask = SIMDOps::uint128_t_const<0xFFFFFFFF, 0x000FFFFF, 0xFFFFFFFF, 0x000FFFFF>::Value();
  uint128fp64_t FPSignMask = SIMDOps::uint128fp64_t_const<0x00000000, 0x80000000, 0x00000000, 0x80000000>::Value();
  uint128fp64_t FPOrMask = SIMDOps::uint128fp64_t_const<0x00000000, 0x3FF00000, 0x00000000, 0x3FF00000>::Value();
  uint128_t BinAndMask = SIMDOps::uint128_t_const<0x00000000, 0x07F00000, 0x00000000, 0x07F00000>::Value();

  union
  {
    uint128_t AsU128;
    uint64_t AsU64[2];
  } BinPos;

  union
  {
    uint128_t AsU128;
    uint32_t AsU32[4];
  } BinIndex;

  union
  {
    double AsFP64[2];
    uint128fp64_t AsU128;
  } FPScale;

  for (size_t SrcPos = 0; SrcPos < BufSize; SrcPos++)
  {
    // Get a random number, uniform over (1, 1). Note that there is a slight
    // defect in that the "zero" bin will have twice as many elements as it
    // should (due to +/- 0). It's small enough to be irrelevant though.
    // Also get the integer representation.
    uint128_t SrcU128 = SrcPtr.Load(SrcPos);
    uint128_t TempRes = SIMDOP_and(SrcU128, FPAndMask);
    uint128fp64_t FPTemp = SIMDOP_or(
      SIMDOP_sub(SIMDOP_or(SIMDOps::simdcast_fp64(TempRes), FPOrMask), FPOrMask),
      SIMDOP_and(SIMDOps::simdcast_fp64(SrcU128), FPSignMask));

    BinPos.AsU128 = TempRes;

    // Get the bin number. Bin 0 is in EndianFix<2>(1), Bin 1 is in
    // EndianFix<2>(1) + 2.
    BinIndex.AsU128 = SIMDOps::Shr_u32<20>(SIMDOP_and(SrcU128, BinAndMask));

    // Pack the two multiplies together.
    FPScale.AsFP64[0] = CZigguratGaussian_FP64::Bins[BinIndex.AsU32[EndianFix_static<1, 1>::Value + 0]].XScale;
    FPScale.AsFP64[1] = CZigguratGaussian_FP64::Bins[BinIndex.AsU32[EndianFix_static<1, 1>::Value + 2]].XScale;
    
    FPScale.AsU128 = SIMDOP_mul(FPScale.AsU128, FPTemp);

    // Handle the first result
    uint32_t CurBinIndex = BinIndex.AsU32[EndianFix_static<2, 1>::Value];
    double CurFPResult = FPScale.AsFP64[EndianFix_static<1, 0>::Value];

    if (BinPos.AsU64[EndianFix_static<1, 0>::Value] < CZigguratGaussian_FP64::Bins[CurBinIndex].THold)
    {
      // Accept.
      DstPtr.Store(DstPos++, CurFPResult);
    }
    else
    {
      if (CurBinIndex == 0)
      {
        // Sample from the tail.
        DstPtr.Store(DstPos++, Random_gaussiantail_FP64());
      }
      else
      {
        // Intermediate region.
        double yval = exp(-CurFPResult * CurFPResult * 0.5);
        double ysample = CZigguratGaussian_FP64::Bins[CurBinIndex].YOffset + CZigguratGaussian_FP64::Bins[CurBinIndex].YScale * Random_uniform_FP64();
        if (ysample < yval)
        {
          // Accept.
          DstPtr.Store(DstPos++, CurFPResult);
        }
      }
    }

    // Handle the second result
    CurBinIndex = BinIndex.AsU32[EndianFix_static<2, 3>::Value];
    CurFPResult = FPScale.AsFP64[EndianFix_static<1, 1>::Value];

    if (BinPos.AsU64[EndianFix_static<1, 1>::Value] < CZigguratGaussian_FP64::Bins[CurBinIndex].THold)
    {
      // Accept.
      DstPtr.Store(DstPos++, CurFPResult);
    }
    else
    {
      if (CurBinIndex == 0)
      {
        // Sample from the tail.
        DstPtr.Store(DstPos++, Random_gaussiantail_FP64());
      }
      else
      {
        // Intermediate region.
        double yval = exp(-CurFPResult * CurFPResult * 0.5);
        double ysample = CZigguratGaussian_FP64::Bins[CurBinIndex].YOffset + CZigguratGaussian_FP64::Bins[CurBinIndex].YScale * Random_uniform_FP64();
        if (ysample < yval)
        {
          // Accept.
          DstPtr.Store(DstPos++, CurFPResult);
        }
      }
    }
  }
#else
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// U128-scalar, fp64-scalar 32/64-bit implementation
// PATHNAME u128scalar-fp64scalar
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  CDataBuffer_ConstView<uint64_t, BufSize * 16> SrcPtr = RandomBlock.template GetConstView<uint64_t>();
  CDataBuffer_VarView<uint64_t, BufSize * 16> DstPtr = FBuffer_gaussian_FP64.template GetVarView<uint64_t>();

  // Load a few constants.
  const uint64_t FPAndMask = UINT64_C(0x000FFFFFFFFFFFFF);
  const uint64_t FPSignMask = UINT64_C(0x8000000000000000);
  const uint64_t FPOrMask = UINT64_C(0x3FF0000000000000);
  const uint32_t BinAndMask = 0x0000007F;

  union
  {
    uint64_t AsU64;
    double AsFP64;
  } FPConv;

  for (size_t SrcPos = 0; SrcPos < BufSize * 2; SrcPos++)
  {
    // Get a random number, uniform over (1, 1). Note that there is a slight
    // defect in that the "zero" bin will have twice as many elements as it
    // should (due to +/- 0). It's small enough to be irrelevant though.
    // Also get the integer representation.
    uint64_t TmpSrc = SrcPtr.Load(EndianFix<1>(SrcPos));
    uint64_t IntBinPos = (TmpSrc & FPAndMask);
    FPConv.AsU64 = IntBinPos | FPOrMask;

    // Get the bin number.
    uint32_t BinIdx = static_cast<uint32_t>((TmpSrc >> 52) & BinAndMask);

    // Scale
    double FPResult = (FPConv.AsFP64 - 1.0) * CZigguratGaussian_FP64::Bins[BinIdx].XScale;
    FPConv.AsFP64 = FPResult;

    // Handle the result.
    if (IntBinPos < CZigguratGaussian_FP64::Bins[BinIdx].THold)
    {
      // Accept.
      FBuffer_gaussian_FP64.StoreU64(DstPos++, FPConv.AsU64 | (TmpSrc & FPSignMask));
    }
    else
    {
      if (BinIdx == 0)
      {
        // Sample from the tail.
        FBuffer_gaussian_FP64.StoreFP64(DstPos++, Random_gaussiantail_FP64());
      }
      else
      {
        // Intermediate region.
        double yval = exp(-FPResult * FPResult * 0.5);
        double ysample = CZigguratGaussian_FP64::Bins[BinIdx].YOffset + CZigguratGaussian_FP64::Bins[BinIdx].YScale * Random_uniform_FP64();
        if (ysample < yval)
        {
          // Accept.
          FBuffer_gaussian_FP64.StoreU64(DstPos++, FPConv.AsU64 | (TmpSrc & FPSignMask));
        }
      }
    }
  }
#endif
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// Common code
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  // Store the number of numbers we actually generated.
  FBufLen_gaussian_FP64 = DstPos;
  FBufPos_gaussian_FP64 = 0;
  #ifndef CFG_TIMETRACK_DISABLE
  Metrics.gaussian_FP64_numgen += DstPos;
  #endif
}

template<class SFMTParams>
inline double CPRNG<SFMTParams>::Random_gaussian_FP64(void)
{
  CDataBuffer_ConstView<double, BufSize * 16> SrcView = FBuffer_gaussian_FP64.template GetConstView<double>();
  for (;;)
  {
    if (FBufPos_gaussian_FP64 < FBufLen_gaussian_FP64)
      return SrcView.Load(EndianFix<1>(FBufPos_gaussian_FP64++));
    RefillBuf_gaussian_FP64();
  }
}

template<class SFMTParams>
inline void CPRNG<SFMTParams>::RandFill_gaussian_FP64(double *Buffer, size_t NumDoubles)
{
  CDataBuffer_ConstView<double, BufSize * 16> SrcView = FBuffer_gaussian_FP64.template GetConstView<double>();

  // Round the source offset up to the next 128-bit boundary.
  size_t BufPos128 = (FBufPos_gaussian_FP64 + 1) / 2;
  size_t NumToGo128 = NumDoubles / 2;

  while (NumToGo128 > 0)
  {
    // Make sure there's something to copy from.
    if (BufPos128 >= FBufLen_gaussian_FP64 / 2)
    {
      RefillBuf_gaussian_FP64();
      BufPos128 = 0;
    }

    // See how many to do.
    size_t NumInBuf128 = (FBufLen_gaussian_FP64 / 2) - BufPos128;
    size_t NumToDo128 = (NumToGo128 > NumInBuf128) ? NumInBuf128 : NumToGo128;

    // Copy.
    memcpy(Buffer, SrcView.GetPointer() + BufPos128 * 2, NumToDo128 * 16);

    // Update pointers, etc.
    Buffer += NumToDo128 * 2;
    NumToGo128 -= NumToDo128;
    BufPos128 += NumToDo128;
  }

  // Store the position back.
  FBufPos_gaussian_FP64 = BufPos128 * 2;

  // If there's one left, transfer it by itself.
  if (NumDoubles % 2 == 1) *Buffer = Random_gaussian_FP64();
}

// -----------------------------------------------------------------------------
// Integers
// -----------------------------------------------------------------------------

template<class SFMTParams>
inline void CPRNG<SFMTParams>::RefillBuf_integer(void)
{
  typename CRandPool<SFMTParams>::CRandomBlockPtr RandomBlock = FRandPool.GetRandomBlock();
  SIMDOps::EmptyForFP();
  memcpy(FBuffer_integer.GetPointerU8(), RandomBlock.GetDataPointer(), BufSize * 16);
  FBufPos_integer = 0;
}

template<class SFMTParams>
inline uint32_t CPRNG<SFMTParams>::Random_u32(void)
{
  // Round the source offset up to the next 32-bit boundary.
  size_t BufPos32 = (FBufPos_integer + 3) / 4;

  // Refill the buffer if need be.
  if (BufPos32 == BufSize * 4)
  {
    RefillBuf_integer();
    BufPos32 = 0;
  }

  // Get the value.
  CDataBuffer_ConstView<uint32_t, BufSize * 16> SrcView = FBuffer_integer.template GetConstView<uint32_t>();
  uint32_t RetVal = SrcView.Load(EndianFix<2>(BufPos32));
  FBufPos_integer = (BufPos32 + 1) * 4;
  return RetVal;
}

template<class SFMTParams>
inline uint32_t CPRNG<SFMTParams>::Random_u32(uint32_t MaxVal)
{
  if (MaxVal == 0x0FFFFFFFF) return Random_u32();

  uint32_t MaxOK = 0x0FFFFFFFF - (0x0FFFFFFFF % (MaxVal + 1)) - 1;
  uint32_t TestVal = Random_u32();
  while (TestVal > MaxOK) TestVal = Random_u32();
  return TestVal % (MaxVal + 1);
}

template<class SFMTParams>
inline void CPRNG<SFMTParams>::RandFill_u32(uint32_t *Buffer, size_t NumU32s)
{
  uint32_t *SrcPtr = FBuffer_integer.GetPointerU32();

  // Round the source offset up to the next 128-bit boundary.
  size_t BufPos128 = (FBufPos_integer + 15) / 16;
  size_t NumToGo128 = NumU32s / 4;

  while (NumToGo128 > 0)
  {
    // Make sure there's something to copy from.
    if (BufPos128 == BufSize)
    {
      RefillBuf_integer();
      BufPos128 = 0;
    }

    // See how many to do.
    size_t NumInBuf128 = BufSize - BufPos128;
    size_t NumToDo128 = (NumToGo128 > NumInBuf128) ? NumInBuf128 : NumToGo128;

    // Copy.
    memcpy(Buffer, SrcPtr + BufPos128 * 4, NumToDo128 * 16);

    // Update pointers, etc.
    Buffer += NumToDo128 * 4;
    NumToGo128 -= NumToDo128;
    BufPos128 += NumToDo128;
  }

  // Store the position back.
  FBufPos_integer = BufPos128 * 16;

  // Handle any remaining elements.
  switch(NumU32s % 4)
  {
    case 3:
      Buffer[0] = Random_u32();
      Buffer[1] = Random_u32();
      Buffer[2] = Random_u32();
      break;
    case 2:
      Buffer[0] = Random_u32();
      Buffer[1] = Random_u32();
      break;
    case 1:
      Buffer[0] = Random_u32();
      break;
  }
}

// -----------------------------------------------------------------------------
// Exponential random doubles.
// PATHDEF ExponentialFP64
// -----------------------------------------------------------------------------
template<class SFMTParams>
NOINLINE void CPRNG<SFMTParams>::RefillBuf_exponential_FP64(void)
{
  #ifndef CFG_TIMETRACK_DISABLE
  CTimedScope ScopeTimer(Metrics.exponential_FP64_refill_time);
  Metrics.exponential_FP64_refill_count++;
  #endif

  typename CRandPool<SFMTParams>::CRandomBlockPtr RandomBlock = FRandPool.GetRandomBlock();
  SIMDOps::EmptyForFP();

  double ScaleFactor = FScaleFactor_exponential_FP64;
  size_t DstPos = 0;

#if (CFG_HAVE_U128 == CFG_SIMD_INTRINSIC) && (CFG_HAVE_U128FP64 == CFG_SIMD_INTRINSIC)
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// U128-intrinsic, fp64-intrinsic implementation
// PATHNAME u128fp64intrinsic
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  CDataBuffer_ConstView<uint128_t, BufSize * 16> SrcPtr = RandomBlock.template GetConstView<uint128_t>();
  CDataBuffer_VarView<double, BufSize * 16> DstPtr = FBuffer_exponential_FP64.template GetVarView<double>();

  // Load a few constants.
  uint128_t FPAndMask = SIMDOps::uint128_t_const<0xFFFFFFFF, 0x000FFFFF, 0xFFFFFFFF, 0x000FFFFF>::Value();
  uint128fp64_t FPOrMask = SIMDOps::uint128fp64_t_const<0x00000000, 0x3FF00000, 0x00000000, 0x3FF00000>::Value();
  uint128_t BinAndMask = SIMDOps::uint128_t_const<0x00000000, 0x07F00000, 0x00000000, 0x07F00000>::Value();

  for (size_t SrcPos = 0; SrcPos < BufSize; SrcPos++)
  {
    // Get a random number, uniform over [0, 1). Also get the integer representation.
    uint128_t SrcU128 = SrcPtr.Load(SrcPos);
    uint128_t TempRes = SIMDOP_and(SrcU128, FPAndMask);
    uint128fp64_t FPTemp = SIMDOP_sub(SIMDOP_or(SIMDOps::simdcast_fp64(TempRes), FPOrMask), FPOrMask);

    union
    {
      uint128_t AsU128;
      uint64_t AsU64[2];
    } BinPos = {TempRes};

    // Get the bin number. Bin 0 is in EndianFix<2>(1), Bin 1 is in
    // EndianFix<2>(1) + 2.
    union
    {
      uint128_t AsU128;
      uint32_t AsU32[4];
    } BinIndex = {SIMDOps::Shr_u32<20>(SIMDOP_and(SrcU128, BinAndMask))};

    // Pack the two multiplies together.
    union
    {
      double AsFP64[2];
      uint128fp64_t AsU128;
    } FPScale = {{
      CZigguratExponential_FP64::Bins[BinIndex.AsU32[EndianFix_static<1, 1>::Value + 0]].XScale,
      CZigguratExponential_FP64::Bins[BinIndex.AsU32[EndianFix_static<1, 1>::Value + 2]].XScale}};

    union
    {
      uint128fp64_t AsU128;
      double AsFP64[2];
    } FPResult = {SIMDOP_mul(FPTemp, FPScale.AsU128)};

    // Handle the first result
    uint32_t CurBinIndex = BinIndex.AsU32[EndianFix_static<2, 1>::Value];
    double CurFPResult = FPResult.AsFP64[EndianFix_static<1, 0>::Value];

    if (BinPos.AsU64[EndianFix_static<1, 0>::Value] < CZigguratExponential_FP64::Bins[CurBinIndex].THold)
    {
      // Accept.
      DstPtr.Store(DstPos++, CurFPResult + ScaleFactor);
      ScaleFactor = 0;
    }
    else
    {
      if (CurBinIndex == 0)
      {
        // Sample from the tail. Actually, this is just another sample with a scalefactor!
        ScaleFactor += CZigguratExponential_FP64::Bins[1].XScale;
      }
      else
      {
        // Intermediate region.
        double yval = exp(-CurFPResult);
        double ysample = CZigguratExponential_FP64::Bins[CurBinIndex].YOffset + CZigguratExponential_FP64::Bins[CurBinIndex].YScale * Random_uniform_FP64();
        if (ysample < yval)
        {
          // Accept.
          DstPtr.Store(DstPos++, CurFPResult + ScaleFactor);
          ScaleFactor = 0;
        }
      }
    }

    // Handle the second result
    CurBinIndex = BinIndex.AsU32[EndianFix_static<2, 3>::Value];
    CurFPResult = FPResult.AsFP64[EndianFix_static<1, 1>::Value];

    if (BinPos.AsU64[EndianFix_static<1, 1>::Value] < CZigguratExponential_FP64::Bins[CurBinIndex].THold)
    {
      // Accept.
      DstPtr.Store(DstPos++, CurFPResult + ScaleFactor);
      ScaleFactor = 0;
    }
    else
    {
      if (CurBinIndex == 0)
      {
        // Sample from the tail. Actually, this is just another sample with a scalefactor!
        ScaleFactor += CZigguratExponential_FP64::Bins[1].XScale;
      }
      else
      {
        // Intermediate region.
        double yval = exp(-CurFPResult);
        double ysample = CZigguratExponential_FP64::Bins[CurBinIndex].YOffset + CZigguratExponential_FP64::Bins[CurBinIndex].YScale * Random_uniform_FP64();
        if (ysample < yval)
        {
          // Accept.
          DstPtr.Store(DstPos++, CurFPResult + ScaleFactor + ScaleFactor);
          ScaleFactor = 0;
        }
      }
    }
  }
#else
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// U128-scalar, fp64-scalar 32/64-bit implementation
// PATHNAME u128scalar-fp64scalar
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  CDataBuffer_ConstView<uint64_t, BufSize * 16> SrcPtr = RandomBlock.template GetConstView<uint64_t>();
  CDataBuffer_VarView<double, BufSize * 16> DstPtr = FBuffer_exponential_FP64.template GetVarView<double>();

  // Load a few constants.
  const uint64_t FPAndMask = UINT64_C(0x000FFFFFFFFFFFFF);
  const uint64_t FPOrMask = UINT64_C(0x3FF0000000000000);
  const uint32_t BinAndMask = 0x0000007F;

  union
  {
    uint64_t AsU64;
    double AsFP64;
  } u1;

  for (size_t SrcPos = 0; SrcPos < BufSize * 2; SrcPos++)
  {
    // Get a random number, uniform over [1, 2). Also get the integer representation.
    uint64_t TmpSrc = SrcPtr.Load(EndianFix<1>(SrcPos));
    uint64_t IntBinPos = (TmpSrc & FPAndMask);
    u1.AsU64 = IntBinPos | FPOrMask;

    // Get the bin number.
    uint32_t BinIdx = static_cast<uint32_t>((TmpSrc >> 52) & BinAndMask);

    // Scale
    double FPResult = (u1.AsFP64 - 1.0) * CZigguratExponential_FP64::Bins[BinIdx].XScale;

    // Handle the result.
    if (IntBinPos < CZigguratExponential_FP64::Bins[BinIdx].THold)
    {
      // Accept.
      DstPtr.Store(DstPos++, FPResult + ScaleFactor);
      ScaleFactor = 0;
    }
    else
    {
      if (BinIdx == 0)
      {
        // Sample from the tail. Actually, this is just another sample with a scalefactor!
        ScaleFactor += CZigguratExponential_FP64::Bins[1].XScale;
      }
      else
      {
        // Intermediate region.
        double yval = exp(-FPResult);
        double ysample = CZigguratExponential_FP64::Bins[BinIdx].YOffset + CZigguratExponential_FP64::Bins[BinIdx].YScale * Random_uniform_FP64();
        if (ysample < yval)
        {
          // Accept.
          DstPtr.Store(DstPos++, FPResult + ScaleFactor);
          ScaleFactor = 0;
        }
      }
    }
  }
#endif
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// Common code
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  // Store the number of numbers we actually generated.
  FBufLen_exponential_FP64 = DstPos;
  FBufPos_exponential_FP64 = 0;
  FScaleFactor_exponential_FP64 = ScaleFactor;
  #ifndef CFG_TIMETRACK_DISABLE
  Metrics.exponential_FP64_numgen += DstPos;
  #endif
}

template<class SFMTParams>
inline double CPRNG<SFMTParams>::Random_exponential_FP64(void)
{
  CDataBuffer_ConstView<double, BufSize * 16> SrcView = FBuffer_exponential_FP64.template GetConstView<double>();
  for (;;)
  {
    if (FBufPos_exponential_FP64 < FBufLen_exponential_FP64)
      return SrcView.Load(EndianFix<1>(FBufPos_exponential_FP64++));
    RefillBuf_exponential_FP64();
  }
}

template<class SFMTParams>
inline void CPRNG<SFMTParams>::RandFill_exponential_FP64(double *Buffer, size_t NumDoubles)
{
  CDataBuffer_ConstView<double, BufSize * 16> SrcView = FBuffer_exponential_FP64.template GetConstView<double>();

  // Round the source offset up to the next 128-bit boundary.
  size_t BufPos128 = (FBufPos_exponential_FP64 + 1) / 2;
  size_t NumToGo128 = NumDoubles / 2;

  while (NumToGo128 > 0)
  {
    // Make sure there's something to copy from.
    if (BufPos128 >= FBufLen_exponential_FP64 / 2)
    {
      RefillBuf_exponential_FP64();
      BufPos128 = 0;
    }


    // See how many to do.
    size_t NumInBuf128 = (FBufLen_exponential_FP64 / 2) - BufPos128;
    size_t NumToDo128 = (NumToGo128 > NumInBuf128) ? NumInBuf128 : NumToGo128;

    // Copy.
    memcpy(Buffer, SrcView.GetPointer() + BufPos128 * 2, NumToDo128 * 16);

    // Update pointers, etc.
    Buffer += NumToDo128 * 2;
    NumToGo128 -= NumToDo128;
    BufPos128 += NumToDo128;
  }

  // Store the position back.
  FBufPos_exponential_FP64 = BufPos128 * 2;

  // If there's one left, transfer it by itself.
  if (NumDoubles % 2 == 1) *Buffer = Random_exponential_FP64();
}

// -----------------------------------------------------------------------------
// Exponential random singles.
// PATHDEF ExponentialFP32
// -----------------------------------------------------------------------------
template<class SFMTParams>
NOINLINE void CPRNG<SFMTParams>::RefillBuf_exponential_FP32(void)
{
  #ifndef CFG_TIMETRACK_DISABLE
  CTimedScope ScopeTimer(Metrics.exponential_FP32_refill_time);
  Metrics.exponential_FP32_refill_count++;
  #endif

  typename CRandPool<SFMTParams>::CRandomBlockPtr RandomBlock = FRandPool.GetRandomBlock();
  SIMDOps::EmptyForFP();

  float ScaleFactor = FScaleFactor_exponential_FP32;
  size_t DstPos = 0;

#if (CFG_HAVE_U128 == CFG_SIMD_INTRINSIC) && (CFG_HAVE_U128FP32 == CFG_SIMD_INTRINSIC)
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// U128-intrinsic, fp32-intrinsic implementation
// PATHNAME u128fp32intrinsic
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  CDataBuffer_ConstView<uint128_t, BufSize * 16> SrcPtr = RandomBlock.template GetConstView<uint128_t>();
  CDataBuffer_VarView<float, BufSize * 16> DstPtr = FBuffer_exponential_FP32.template GetVarView<float>();

  // Load a few constants.
  uint128_t FPAndMask = SIMDOps::uint128_t_const<0x007FFFFF, 0x007FFFFF, 0x007FFFFF, 0x007FFFFF>::Value();
  uint128fp32_t FPOrMask = SIMDOps::uint128fp32_t_const<0x3F800000, 0x3F800000, 0x3F800000, 0x3F800000>::Value();
  uint128_t BinAndMask = SIMDOps::uint128_t_const<0x7F800000, 0x7F800000, 0x7F800000, 0x7F800000>::Value();

  for (size_t SrcPos = 0; SrcPos < BufSize; SrcPos++)
  {
    // Get a random number, uniform over [0, 1). Also get the integer representation.
    uint128_t SrcU128 = SrcPtr.Load(SrcPos);
    uint128_t TempRes = SIMDOP_and(SrcU128, FPAndMask);
    uint128fp32_t FPTemp = SIMDOP_sub(SIMDOP_or(SIMDOps::simdcast_fp32(TempRes), FPOrMask), FPOrMask);

    union
    {
      uint128_t AsU128;
      uint32_t AsU32[4];
    } BinPos = {TempRes};

    // Get the bin number.
    union
    {
      uint128_t AsU128;
      uint32_t AsU32[4];
    } BinIndex = {SIMDOps::Shr_u32<23>(SIMDOP_and(SrcU128, BinAndMask))};

    // Pack the four multiplies together.
    union
    {
      float AsFP32[4];
      uint128fp32_t AsU128;
    } FPScale = {{
      CZigguratExponential_FP32::Bins[BinIndex.AsU32[0]].XScale,
      CZigguratExponential_FP32::Bins[BinIndex.AsU32[1]].XScale,
      CZigguratExponential_FP32::Bins[BinIndex.AsU32[2]].XScale,
      CZigguratExponential_FP32::Bins[BinIndex.AsU32[3]].XScale}};

    union
    {
      uint128fp32_t AsU128;
      float AsFP32[4];
    } FPResult = {SIMDOP_mul(FPTemp, FPScale.AsU128)};

    // Handle the first result
    uint32_t CurBinIndex = BinIndex.AsU32[EndianFix_static<2, 0>::Value];
    float CurFPResult = FPResult.AsFP32[EndianFix_static<2, 0>::Value];

    if (BinPos.AsU32[EndianFix_static<2, 0>::Value] < CZigguratExponential_FP32::Bins[CurBinIndex].THold)
    {
      // Accept.
      DstPtr.Store(DstPos++, CurFPResult + ScaleFactor);
      ScaleFactor = 0;
    }
    else
    {
      if (CurBinIndex == 0)
      {
        // Sample from the tail. Actually, this is just another sample with a scalefactor!
        ScaleFactor += CZigguratExponential_FP32::Bins[1].XScale;
      }
      else
      {
        // Intermediate region.
        float yval = exp(-CurFPResult);
        float ysample = CZigguratExponential_FP32::Bins[CurBinIndex].YOffset + CZigguratExponential_FP32::Bins[CurBinIndex].YScale * Random_uniform_FP32();
        if (ysample < yval)
        {
          // Accept.
          DstPtr.Store(DstPos++, CurFPResult + ScaleFactor);
          ScaleFactor = 0;
        }
      }
    }

    // Handle the second result
    CurBinIndex = BinIndex.AsU32[EndianFix_static<2, 1>::Value];
    CurFPResult = FPResult.AsFP32[EndianFix_static<2, 1>::Value];

    if (BinPos.AsU32[EndianFix_static<2, 1>::Value] < CZigguratExponential_FP32::Bins[CurBinIndex].THold)
    {
      // Accept.
      DstPtr.Store(DstPos++, CurFPResult + ScaleFactor);
      ScaleFactor = 0;
    }
    else
    {
      if (CurBinIndex == 0)
      {
        // Sample from the tail. Actually, this is just another sample with a scalefactor!
        ScaleFactor += CZigguratExponential_FP32::Bins[1].XScale;
      }
      else
      {
        // Intermediate region.
        float yval = exp(-CurFPResult);
        float ysample = CZigguratExponential_FP32::Bins[CurBinIndex].YOffset + CZigguratExponential_FP32::Bins[CurBinIndex].YScale * Random_uniform_FP32();
        if (ysample < yval)
        {
          // Accept.
          DstPtr.Store(DstPos++, CurFPResult + ScaleFactor);
          ScaleFactor = 0;
        }
      }
    }

    // Handle the third result
    CurBinIndex = BinIndex.AsU32[EndianFix_static<2, 2>::Value];
    CurFPResult = FPResult.AsFP32[EndianFix_static<2, 2>::Value];

    if (BinPos.AsU32[EndianFix_static<2, 2>::Value] < CZigguratExponential_FP32::Bins[CurBinIndex].THold)
    {
      // Accept.
      DstPtr.Store(DstPos++, CurFPResult + ScaleFactor);
      ScaleFactor = 0;
    }
    else
    {
      if (CurBinIndex == 0)
      {
        // Sample from the tail. Actually, this is just another sample with a scalefactor!
        ScaleFactor += CZigguratExponential_FP32::Bins[1].XScale;
      }
      else
      {
        // Intermediate region.
        float yval = exp(-CurFPResult);
        float ysample = CZigguratExponential_FP32::Bins[CurBinIndex].YOffset + CZigguratExponential_FP32::Bins[CurBinIndex].YScale * Random_uniform_FP32();
        if (ysample < yval)
        {
          // Accept.
          DstPtr.Store(DstPos++, CurFPResult + ScaleFactor);
          ScaleFactor = 0;
        }
      }
    }

    // Handle the fourth result
    CurBinIndex = BinIndex.AsU32[EndianFix_static<2, 3>::Value];
    CurFPResult = FPResult.AsFP32[EndianFix_static<2, 3>::Value];

    if (BinPos.AsU32[EndianFix_static<2, 3>::Value] < CZigguratExponential_FP32::Bins[CurBinIndex].THold)
    {
      // Accept.
      DstPtr.Store(DstPos++, CurFPResult + ScaleFactor);
      ScaleFactor = 0;
    }
    else
    {
      if (CurBinIndex == 0)
      {
        // Sample from the tail. Actually, this is just another sample with a scalefactor!
        ScaleFactor += CZigguratExponential_FP32::Bins[1].XScale;
      }
      else
      {
        // Intermediate region.
        float yval = exp(-CurFPResult);
        float ysample = CZigguratExponential_FP32::Bins[CurBinIndex].YOffset + CZigguratExponential_FP32::Bins[CurBinIndex].YScale * Random_uniform_FP32();
        if (ysample < yval)
        {
          // Accept.
          DstPtr.Store(DstPos++, CurFPResult + ScaleFactor);
          ScaleFactor = 0;
        }
      }
    }
  }
#else
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// U128-scalar, fp32-scalar 32/64-bit implementation
// PATHNAME u128scalar-fp32scalar
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  CDataBuffer_ConstView<uint64_t, BufSize * 16> SrcPtr = RandomBlock.template GetConstView<uint64_t>();
  CDataBuffer_VarView<float, BufSize * 16> DstPtr = FBuffer_exponential_FP32.template GetVarView<float>();

  // Load a few constants.
  const uint64_t FPAndMask = UINT64_C(0x007FFFFF007FFFFF);
  const uint64_t FPOrMask = UINT64_C(0x3F8000003F800000);
  const uint32_t BinAndMask = 0x000000FF;

  union
  {
    uint64_t AsU64;
    float AsFP32[2];
  } u1;

  for (size_t SrcPos = 0; SrcPos < BufSize * 2; SrcPos++)
  {
    // Get a random number, uniform over [1, 2). Also get the integer representation.
    uint64_t TmpSrc = SrcPtr.Load(EndianFix<1>(SrcPos));
    uint64_t IntBinPos64 = (TmpSrc & FPAndMask);
    u1.AsU64 = IntBinPos64 | FPOrMask;

    // Handle the first result.
    // Get the bin number and position.
    uint32_t BinIdx = static_cast<uint32_t>(TmpSrc >> 23) & BinAndMask;

    // Scale
    float FPResult = (u1.AsFP32[EndianFix_static<1, 0>::Value] - 1.0f) * CZigguratExponential_FP32::Bins[BinIdx].XScale;

    // Store if we should.
    uint32_t IntBinPos = static_cast<uint32_t>(IntBinPos64);
    if (IntBinPos < CZigguratExponential_FP32::Bins[BinIdx].THold)
    {
      // Accept.
      DstPtr.Store(DstPos++, FPResult + ScaleFactor);
      ScaleFactor = 0;
    }
    else
    {
      if (BinIdx == 0)
      {
        // Sample from the tail. Actually, this is just another sample with a scalefactor!
        ScaleFactor += CZigguratExponential_FP32::Bins[1].XScale;
      }
      else
      {
        // Intermediate region.
        float yval = expf(-FPResult);
        float ysample = CZigguratExponential_FP32::Bins[BinIdx].YOffset + CZigguratExponential_FP32::Bins[BinIdx].YScale * Random_uniform_FP32();
        if (ysample < yval)
        {
          // Accept.
          DstPtr.Store(DstPos++, FPResult + ScaleFactor);
          ScaleFactor = 0;
        }
      }
    }

    // Handle the second result.
    // Get the bin number and position.
    BinIdx = static_cast<uint32_t>(TmpSrc >> (23 + 32)) & BinAndMask;

    // Scale
    FPResult = (u1.AsFP32[EndianFix_static<1, 1>::Value] - 1.0f) * CZigguratExponential_FP32::Bins[BinIdx].XScale;

    // Store if we should.
    IntBinPos = static_cast<uint32_t>(IntBinPos64 >> 32);
    if (IntBinPos < CZigguratExponential_FP32::Bins[BinIdx].THold)
    {
      // Accept.
      DstPtr.Store(DstPos++, FPResult + ScaleFactor);
      ScaleFactor = 0;
    }
    else
    {
      if (BinIdx == 0)
      {
        // Sample from the tail. Actually, this is just another sample with a scalefactor!
        ScaleFactor += CZigguratExponential_FP32::Bins[1].XScale;
      }
      else
      {
        // Intermediate region.
        float yval = expf(-FPResult);
        float ysample = CZigguratExponential_FP32::Bins[BinIdx].YOffset + CZigguratExponential_FP32::Bins[BinIdx].YScale * Random_uniform_FP32();
        if (ysample < yval)
        {
          // Accept.
          DstPtr.Store(DstPos++, FPResult + ScaleFactor);
          ScaleFactor = 0;
        }
      }
    }
  }
#endif
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// Common code
// - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  // Store the number of numbers we actually generated.
  FBufLen_exponential_FP32 = DstPos;
  FBufPos_exponential_FP32 = 0;
  FScaleFactor_exponential_FP32 = ScaleFactor;
  #ifndef CFG_TIMETRACK_DISABLE
  Metrics.exponential_FP32_numgen += DstPos;
  #endif
}

template<class SFMTParams>
inline float CPRNG<SFMTParams>::Random_exponential_FP32(void)
{
  CDataBuffer_ConstView<float, BufSize * 16> SrcView = FBuffer_exponential_FP32.template GetConstView<float>();
  for (;;)
  {
    if (FBufPos_exponential_FP32 < FBufLen_exponential_FP32)
      return SrcView.Load(EndianFix<2>(FBufPos_exponential_FP32++));
    RefillBuf_exponential_FP32();
  }
}

template<class SFMTParams>
inline void CPRNG<SFMTParams>::RandFill_exponential_FP32(float *Buffer, size_t NumFloats)
{
  CDataBuffer_ConstView<float, BufSize * 16> SrcView = FBuffer_exponential_FP32.template GetConstView<float>();

  // Round the source offset up to the next 128-bit boundary.
  size_t BufPos128 = (FBufPos_exponential_FP32 + 3) / 4;
  size_t NumToGo128 = NumFloats / 4;

  while (NumToGo128 > 0)
  {
    // Make sure there's something to copy from.
    if (BufPos128 >= FBufLen_exponential_FP32 / 4)
    {
      RefillBuf_exponential_FP32();
      BufPos128 = 0;
    }

    // See how many to do.
    size_t NumInBuf128 = (FBufLen_exponential_FP32 / 4) - BufPos128;
    size_t NumToDo128 = (NumToGo128 > NumInBuf128) ? NumInBuf128 : NumToGo128;

    // Copy.
    memcpy(Buffer, SrcView.GetPointer() + BufPos128 * 4, NumToDo128 * 16);

    // Update pointers, etc.
    Buffer += NumToDo128 * 4;
    NumToGo128 -= NumToDo128;
    BufPos128 += NumToDo128;
  }

  // Store the position back.
  FBufPos_exponential_FP32 = BufPos128 * 4;

  // If there's one left, transfer it by itself.
  switch(NumFloats % 4)
  {
    case 3:
      *(Buffer++) = Random_exponential_FP32();
    case 2:
      *(Buffer++) = Random_exponential_FP32();
    case 1:
      *(Buffer++) = Random_exponential_FP32();
    case 0:
      // Do nothing.
      break;
  }
}

#ifndef CFG_TIMETRACK_DISABLE
template<class SFMTParams> typename CPRNG<SFMTParams>::TMetrics CPRNG<SFMTParams>::Metrics;
template<class SFMTParams> THREADVAR uint32_t CPRNG<SFMTParams>::TMetrics::uniform_FP64_refill_count = 0;
template<class SFMTParams> THREADVAR uint64_t CPRNG<SFMTParams>::TMetrics::uniform_FP64_refill_time = 0;
template<class SFMTParams> THREADVAR uint32_t CPRNG<SFMTParams>::TMetrics::uniform_FP32_refill_count = 0;
template<class SFMTParams> THREADVAR uint64_t CPRNG<SFMTParams>::TMetrics::uniform_FP32_refill_time = 0;
template<class SFMTParams> THREADVAR uint32_t CPRNG<SFMTParams>::TMetrics::gaussiantail_FP64_refill_count = 0;
template<class SFMTParams> THREADVAR uint64_t CPRNG<SFMTParams>::TMetrics::gaussiantail_FP64_refill_time = 0;
template<class SFMTParams> THREADVAR uint32_t CPRNG<SFMTParams>::TMetrics::gaussian_FP64_refill_count = 0;
template<class SFMTParams> THREADVAR uint64_t CPRNG<SFMTParams>::TMetrics::gaussian_FP64_refill_time = 0;
template<class SFMTParams> THREADVAR uint64_t CPRNG<SFMTParams>::TMetrics::gaussian_FP64_numgen = 0;
template<class SFMTParams> THREADVAR uint32_t CPRNG<SFMTParams>::TMetrics::exponential_FP64_refill_count = 0;
template<class SFMTParams> THREADVAR uint64_t CPRNG<SFMTParams>::TMetrics::exponential_FP64_refill_time = 0;
template<class SFMTParams> THREADVAR uint64_t CPRNG<SFMTParams>::TMetrics::exponential_FP64_numgen = 0;
template<class SFMTParams> THREADVAR uint32_t CPRNG<SFMTParams>::TMetrics::exponential_FP32_refill_count = 0;
template<class SFMTParams> THREADVAR uint64_t CPRNG<SFMTParams>::TMetrics::exponential_FP32_refill_time = 0;
template<class SFMTParams> THREADVAR uint64_t CPRNG<SFMTParams>::TMetrics::exponential_FP32_numgen = 0;
#endif

#endif
