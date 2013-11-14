/* *****************************************************************************
/
/ This file is part of Solirte, a solenoid ion ray-tracing engine.
/ (c) 2008 Michael Brown.
/ michael.brown@anu.edu.au
/
/ An object that hands out blocks of random data.
/ *************************************************************************** */

#ifndef RANDPOOL_H
#define RANDPOOL_H

#include <iostream>
#include <iomanip>
#include <string>
#include <sstream>
#include <string.h>

#include "u128simd.h"

#ifndef CFG_TIMETRACK_DISABLE
#include "../platform/timetrack.h"
#endif

#define CFG_RANDPOOL_IMPL_SSE2 1
#define CFG_RANDPOOL_IMPL_ALTIVEC 2
#define CFG_RANDPOOL_IMPL_64BIT 3
#define CFG_RANDPOOL_IMPL_32BITSLOW 4
#define CFG_RANDPOOL_IMPL_MMX 5

#if (CFG_HAVE_SSE2 == 1)
  #define CFG_RANDPOOL_IMPL CFG_RANDPOOL_IMPL_SSE2
#endif
#if ((CFG_BITS == 64) && !defined(CFG_RANDPOOL_IMPL))
  #define CFG_RANDPOOL_IMPL CFG_RANDPOOL_IMPL_64BIT
#endif
#if ((CFG_HAVE_MMX == 1) && !defined(CFG_RANDPOOL_IMPL))
  #define CFG_RANDPOOL_IMPL CFG_RANDPOOL_IMPL_MMX
#endif
#if (!defined(CFG_RANDPOOL_IMPL))
  #define CFG_RANDPOOL_IMPL CFG_RANDPOOL_IMPL_32BITSLOW
#endif

#if (CFG_RANDPOOL_IMPL == CFG_RANDPOOL_IMPL_MMX)
  #include "sfmt_mmx.h"
#endif

#if CFG_COMPILER == CFG_COMPILER_MSVC
// Shut up one of the more braindead MSVC warnings.
#pragma warning(push)
#pragma warning(disable: 4127)
#endif

template <class SFMTConsts>
class CRandPool
{
  public:
    static const size_t N = SFMTConsts::MEXP / 128 + 1;
    static const size_t N32 = N * 4;

    #ifndef CFG_TIMETRACK_DISABLE
    static struct TMetrics
    {
      static THREADVAR uint32_t poolmoves;
      static THREADVAR uint32_t gen_rand_all_count;
      static THREADVAR uint64_t gen_rand_all_time;
      TMetrics(void)
      {
        CPerfCounters::SetName(poolmoves, "CRandPool<" + GenToString(SFMTConsts::MEXP) + ">.poolmoves");
        CPerfCounters::SetName(gen_rand_all_count, "CPRNG<" + GenToString(SFMTConsts::MEXP) + ">.gen_rand_all.count");
        CPerfCounters::SetName(gen_rand_all_time, "CPRNG<" + GenToString(SFMTConsts::MEXP) + ">.gen_rand_all.time");
      }

      void ForceConstruction(void) { }
    } Metrics;
    #endif

    typedef CDataBuffer_ConstView<uint32_t, N * 16> TPoolConstViewU32;
    typedef CDataBuffer_VarView<uint32_t, N * 16> TPoolVarViewU32;
    typedef CDataBuffer_ConstView<uint64_t, N * 16> TPoolConstViewU64;
    typedef CDataBuffer_VarView<uint64_t, N * 16> TPoolVarViewU64;
    #if CFG_HAVE_U128 == CFG_SIMD_INTRINSIC
    typedef CDataBuffer_ConstView<uint128_t, N * 16> TPoolViewConstU128;
    typedef CDataBuffer_VarView<uint128_t, N * 16> TPoolViewVarU128;
    #endif
    #if CFG_HAVE_U128FP64 == CFG_SIMD_INTRINSIC
    typedef CDataBuffer_ConstView<uint128fp64_t, N * 16> TPoolConstViewU128FP64;
    typedef CDataBuffer_VarView<uint128fp64_t, N * 16> TPoolVarViewU128FP64;
    #endif

    class CRandomBlock
    {
      private:
        CDataBuffer<N * 16> FPool;
        int FRefCount;
      protected:
      public:
        CRandomBlock(void) { FRefCount = 1; }
        int AddRef(void) { return ++FRefCount; }
        int GetRefCount(void) { return FRefCount; }
        int Release(void)
        {
          if (--FRefCount == 0)
          {
            delete this;
            return 0;
          }
          return FRefCount;
        }

        template<class ElementType> inline CDataBuffer_ConstView<ElementType, N * 16> GetConstView(void)
        { return FPool.template GetConstView<ElementType>(); }
        template<class ElementType> inline CDataBuffer_VarView<ElementType, N * 16> GetVarView(void)
        { return FPool.template GetVarView<ElementType>(); }

        void *GetDataPointer(void) { return &FPool; }

        static void *operator new(size_t size) { return _aligned_malloc(size, 16); }
        static void operator delete(void *p) { _aligned_free(p); }
    };

    class CRandomBlockPtr
    {
      private:
        CRandomBlock *FBlock;
      protected:
      public:
        CRandomBlockPtr(void) { FBlock = new CRandomBlock(); }
        CRandomBlockPtr(CRandomBlock *Src) : FBlock(Src) { /* No AddRef */ }
        CRandomBlockPtr(const CRandomBlockPtr &Src) : FBlock(Src.FBlock) { FBlock->AddRef(); }
        ~CRandomBlockPtr(void) { FBlock->Release(); }
        int GetRefCount(void) { return FBlock->GetRefCount(); }

        template<class ElementType> inline CDataBuffer_ConstView<ElementType, N * 16> GetConstView(void)
        { return FBlock->template GetConstView<ElementType>(); }
        template<class ElementType> inline CDataBuffer_VarView<ElementType, N * 16> GetVarView(void)
        { return FBlock->template GetVarView<ElementType>(); }

        void *GetDataPointer(void) { return FBlock->GetDataPointer(); }

        void MakeUnique(void)
        {
          if (GetRefCount() != 1)
          {
            #ifndef CFG_TIMETRACK_DISABLE
            Metrics.poolmoves++;
            #endif
            CRandomBlock *NewBlock = new CRandomBlock;
            memcpy(NewBlock->GetDataPointer(), FBlock->GetDataPointer(), N * sizeof(uint128_t));
            FBlock->Release();
            FBlock = NewBlock;
          }
        }
    };
  protected:
    // The 128-bit internal state array
    CRandomBlockPtr FPool;
  private:
    // A function used in the initialization (init_by_array).
    static inline uint32_t func1(uint32_t x)
    {
      return (x ^ (x >> 27)) * (uint32_t)1664525UL;
    }

    // A function used in the initialization (init_by_array).
    static inline uint32_t func2(uint32_t x)
    {
      return (x ^ (x >> 27)) * (uint32_t)1566083941UL;
    }

    // A function used in the initialization (init_gen_rand).
    static inline uint32_t func3(uint32_t x, uint32_t i)
    {
      return 1812433253UL * (x ^ (x >> 30)) + i;
    }

    // This function corrects for byte ordering on big endian machines. Note
    // that this function does slow things down a bit so should be avoided where
    // performance is important.
    static inline size_t IdxOf32(size_t LittleEndianIdx)
    {
      return EndianFix<2>(LittleEndianIdx);
    }

    #if (CFG_RANDPOOL_IMPL == CFG_RANDPOOL_IMPL_32BITSLOW)
    // -------------------------------------------------------------------------
    // Implementation for register-challenged 32-bit architectures. In other
    // words, x86. There simply isn't enough register to go around to buffer the
    // C and D values, so we have to pull them from memory (hopefully the cache)
    // instead. Note that this is really only needed if the compiler is not
    // supported by the inline assembler MMX version, which is faster.
    // 
    // This also serves a double duty as the "default" implementation in case we
    // don't have anything better to use. There's currently two architectures
    // that are not fully optimal (and use this implementation): 32-bit SPARC,
    // and 32-bit PPC systems that don't support AltiVec (such as POWER). There
    // should be a register-buffering 32-bit implementation for these
    // architectures.
    // -------------------------------------------------------------------------

    static std::string GetRandpoolImpl(void) { return "32bitslow"; }

    // Emulation of 128-bit shifts using 32-bit integer operations.
    template<int NumBits, int Idx, int SrcIdx> static inline uint32_t Shr128_sub(uint32_t *SrcPtr)
    {
      // Low bit of SrcIdx ends up at SrcIdx * 32 - NumBits.
      // Get position relative to the low bit of Idx (= Idx * 32).
      static const int SrcLow = SrcIdx * 32 - NumBits - Idx * 32;
      static const int UseLeftShift = ((SrcLow > 0) && (SrcLow < 32)) ? 1 : 0;
      static const int UseRightShift = ((SrcLow < 0) && (SrcLow > -32)) ? 1 : 0;
      static const int UseNoShift = (SrcLow == 0) ? 1 : 0;
      static const int LShiftBits = (UseLeftShift == 1) ? SrcLow : 0;
      static const int RShiftBits = (UseRightShift == 1) ? -SrcLow : 0;
      if (UseLeftShift == 1) return SrcPtr[EndianFix_static_int<2, SrcIdx>::Value] << LShiftBits;
      if (UseRightShift == 1) return SrcPtr[EndianFix_static_int<2, SrcIdx>::Value] >> RShiftBits;
      if (UseNoShift == 1) return SrcPtr[EndianFix_static_int<2, SrcIdx>::Value];
      return 0;
    }

    template<int NumBits, int Idx, int SrcIdx> static inline uint32_t Shl128_sub(uint32_t *SrcPtr)
    {
      return Shr128_sub<-NumBits, Idx, SrcIdx>(SrcPtr);
    }

    template<int NumBits, int Idx> static uint32_t inline Shr128Xor(uint32_t x, uint32_t *Y128Ptr)
    {
      return x ^
        Shr128_sub<NumBits, Idx, 0>(Y128Ptr) ^ Shr128_sub<NumBits, Idx, 1>(Y128Ptr) ^
        Shr128_sub<NumBits, Idx, 2>(Y128Ptr) ^ Shr128_sub<NumBits, Idx, 3>(Y128Ptr);
    }

    template<int NumBits, int Idx> static uint32_t inline Shl128Xor(uint32_t x, uint32_t *Y128Ptr)
    {
      return x ^
        Shl128_sub<NumBits, Idx, 0>(Y128Ptr) ^ Shl128_sub<NumBits, Idx, 1>(Y128Ptr) ^
        Shl128_sub<NumBits, Idx, 2>(Y128Ptr) ^ Shl128_sub<NumBits, Idx, 3>(Y128Ptr);
    }

    // The recursion function for 32-bit architectures with high register
    // pressure (ie: x86). Zero registers are used for caching.
    template<int COffset, int DOffset>
    static void inline mm_recursion_32_0(uint32_t *BufA, uint32_t *BufB)
    {
      uint32_t A0Res;
      A0Res = Shl128Xor<SFMTConsts::SL2 * 8, 0>(BufA[EndianFix_static_int<2, 0>::Value], BufA);
      A0Res ^= (BufB[EndianFix_static_int<2, 0>::Value] >> SFMTConsts::SR1) & SFMTConsts::MSK1;
      A0Res = Shr128Xor<SFMTConsts::SR2 * 8, 0>(A0Res, BufA + COffset * 4);
      A0Res ^= BufA[EndianFix_static_int<2, 0>::Value + DOffset * 4] << SFMTConsts::SL1;
      if (SFMTConsts::SL2 == 0) BufA[EndianFix_static_int<2, 0>::Value] = A0Res;

      uint32_t A1Res;
      A1Res = Shl128Xor<SFMTConsts::SL2 * 8, 1>(BufA[EndianFix_static_int<2, 1>::Value], BufA);
      A1Res ^= (BufB[EndianFix_static_int<2, 1>::Value] >> SFMTConsts::SR1) & SFMTConsts::MSK2;
      A1Res = Shr128Xor<SFMTConsts::SR2 * 8, 1>(A1Res, BufA + COffset * 4);
      A1Res ^= BufA[EndianFix_static_int<2, 1>::Value + DOffset * 4] << SFMTConsts::SL1;
      if ((SFMTConsts::SL2 > 0) && (SFMTConsts::SL2 <= 32)) BufA[EndianFix_static_int<2, 0>::Value] = A0Res;
      if (SFMTConsts::SL2 == 0) BufA[EndianFix_static_int<2, 1>::Value] = A1Res;

      uint32_t A2Res;
      A2Res = Shl128Xor<SFMTConsts::SL2 * 8, 2>(BufA[EndianFix_static_int<2, 2>::Value], BufA);
      A2Res ^= (BufB[EndianFix_static_int<2, 2>::Value] >> SFMTConsts::SR1) & SFMTConsts::MSK3;
      A2Res = Shr128Xor<SFMTConsts::SR2 * 8, 2>(A2Res, BufA + COffset * 4);
      A2Res ^= BufA[EndianFix_static_int<2, 2>::Value + DOffset * 4] << SFMTConsts::SL1;
      if ((SFMTConsts::SL2 > 32) && (SFMTConsts::SL2 <= 64)) BufA[EndianFix_static_int<2, 0>::Value] = A0Res;
      if ((SFMTConsts::SL2 > 0) && (SFMTConsts::SL2 <= 32)) BufA[EndianFix_static_int<2, 1>::Value] = A1Res;
      if (SFMTConsts::SL2 == 0) BufA[EndianFix_static_int<2, 2>::Value] = A2Res;

      uint32_t A3Res;
      A3Res = Shl128Xor<SFMTConsts::SL2 * 8, 3>(BufA[EndianFix_static_int<2, 3>::Value], BufA);
      A3Res ^= (BufB[EndianFix_static_int<2, 3>::Value] >> SFMTConsts::SR1) & SFMTConsts::MSK4;
      A3Res = Shr128Xor<SFMTConsts::SR2 * 8, 3>(A3Res, BufA + COffset * 4);
      A3Res ^= BufA[EndianFix_static_int<2, 3>::Value + DOffset * 4] << SFMTConsts::SL1;
      if (SFMTConsts::SL2 > 64) BufA[EndianFix_static_int<2, 0>::Value] = A0Res;
      if (SFMTConsts::SL2 > 32) BufA[EndianFix_static_int<2, 1>::Value] = A1Res;
      if (SFMTConsts::SL2 > 0) BufA[EndianFix_static_int<2, 2>::Value] = A2Res;
      BufA[EndianFix_static_int<2, 3>::Value] = A3Res;
    }

    NOINLINE void gen_rand_all(void)
    {
      #ifndef CFG_TIMETRACK_DISABLE
      CTimedScope ScopeTimer(Metrics.gen_rand_all_time);
      Metrics.gen_rand_all_count++;
      #endif

      uint32_t *APtr = FPool.template GetVarView<uint32_t>().GetPointer();
      uint32_t *BPtr = APtr + SFMTConsts::POS1 * 4;

      // The two initial loops (unusual C and D offsets).
      mm_recursion_32_0<N - 2, N - 1>(APtr, BPtr);
      mm_recursion_32_0<N - 2, -1>(APtr + 4, BPtr + 4);

      int NumLoops = N - SFMTConsts::POS1 - 2;
      APtr += (NumLoops + 2) * 4;
      BPtr += (NumLoops + 2) * 4;

      // The main loop. No unrolling.
      int RepLoop = 0;
      for (;;)
      {
        for (int MainLoop = -NumLoops; MainLoop != 0; MainLoop++)
          mm_recursion_32_0<-2, -1>(APtr + MainLoop * 4, BPtr + MainLoop * 4);
        if (RepLoop == 0)
        {
          // Need to adjust BPtr to handle wrapping of the buffer.
          RepLoop = 1;
          NumLoops = SFMTConsts::POS1;
          APtr += NumLoops * 4;
          BPtr += (NumLoops - N) * 4;
        }
        else
          break;
      }
    }
    #endif

    #if (CFG_RANDPOOL_IMPL == CFG_RANDPOOL_IMPL_MMX)
    // -------------------------------------------------------------------------
    // MMX implementation. Since current compilers can't handle the register
    // pressure for this implementation, it has to be done via assembler (inline
    // if we're using MSVC, external if we're using something else). All we do
    // is bounce out to the correct function.
    // -------------------------------------------------------------------------
    static std::string GetRandpoolImpl(void) { return "mmx"; }
    NOINLINE void gen_rand_all(void)
    {
      #ifndef CFG_TIMETRACK_DISABLE
      CTimedScope ScopeTimer(Metrics.gen_rand_all_time);
      Metrics.gen_rand_all_count++;
      #endif

      SFMT_recursion_mmx<SFMTConsts>::SFMT_recursion(FPool.GetDataPointer());
    }
    #endif

    #if (CFG_RANDPOOL_IMPL == CFG_RANDPOOL_IMPL_64BIT)
    // -------------------------------------------------------------------------
    // Implementation for 64 bit architectures. Here, we buffer C and D in
    // registers. It is assumed that there are sufficient registers that this
    // can be done. In every 64-bit platform of relevance (x86-64, SPARC, PPC,
    // and IA64) this is the case. Note that in the case of x86-64 we'd probably
    // be using SSE2 anyhow.
    // -------------------------------------------------------------------------

    static std::string GetRandpoolImpl(void) { return "64bit"; }

    // Emulation of 128-bit shifts using 64-bit integer operations.
    template<int NumBits, int Idx, int SrcIdx> FORCEINLINE uint64_t Shr128_sub(uint64_t YVal)
    {
      // Low bit of SrcIdx ends up at SrcIdx * 64 - NumBits.
      // Get position relative to the low bit of Idx (= Idx * 64).
      static const int SrcLow = SrcIdx * 64 - NumBits - Idx * 64;
      static const int UseLeftShift = ((SrcLow > 0) && (SrcLow < 64)) ? 1 : 0;
      static const int UseRightShift = ((SrcLow < 0) && (SrcLow > -64)) ? 1 : 0;
      static const int UseNoShift = (SrcLow == 0) ? 1 : 0;
      static const int LShiftBits = (UseLeftShift == 1) ? SrcLow : 0;
      static const int RShiftBits = (UseRightShift == 1) ? -SrcLow : 0;
      if (UseLeftShift == 1) return YVal << LShiftBits;
      if (UseRightShift == 1) return YVal >> RShiftBits;
      if (UseNoShift == 1) return YVal;
      return 0;
    }

    template<int NumBits, int Idx, int SrcIdx> FORCEINLINE uint64_t Shl128_sub(uint64_t YVal)
    {
      return Shr128_sub<-NumBits, Idx, SrcIdx>(YVal);
    }

    template<int NumBits, int Idx> uint64_t FORCEINLINE Shr128Xor(uint64_t x, uint64_t YLow, uint64_t YHigh)
    {
      return x ^ Shr128_sub<NumBits, Idx, 0>(YLow) ^ Shr128_sub<NumBits, Idx, 1>(YHigh);
    }

    template<int NumBits, int Idx> uint64_t FORCEINLINE Shl128Xor(uint64_t x, uint64_t YLow, uint64_t YHigh)
    {
      return x ^ Shl128_sub<NumBits, Idx, 0>(YLow) ^ Shl128_sub<NumBits, Idx, 1>(YHigh);
    }

    // The recursion function for 64-bit architectures. It's assumed that there
    // are enough registers, which is true for any architecture worth worrying
    // about (x86-64, SPARC, IA64, PPC).
    void FORCEINLINE mm_recursion(uint128_t *BufA, uint128_t *BufB, uint64_t &ALowOut, uint64_t &AHighOut,
      uint64_t CLow, uint64_t CHigh, uint64_t DLow, uint64_t DHigh)
    {
      uint64_t ALowIn = BufA->GetU64<0>();
      uint64_t AHighIn = BufA->GetU64<1>();

      uint64_t A0Res;
      A0Res = Shl128Xor<SFMTConsts::SL2 * 8, 0>(ALowIn, ALowIn, AHighIn);
      A0Res ^= (BufB->GetU64<0>() >> SFMTConsts::SR1) &
        (static_cast<uint64_t>(SFMTConsts::MSK1) | (static_cast<uint64_t>(SFMTConsts::MSK2) << 32)) &
        U64_Shr32Mask<SFMTConsts::SR1>::Value;
      A0Res = Shr128Xor<SFMTConsts::SR2 * 8, 0>(A0Res, CLow, CHigh);
      A0Res ^= (DLow << SFMTConsts::SL1) & U64_Shl32Mask<SFMTConsts::SL1>::Value;
      if (SFMTConsts::SL2 == 0) { ALowOut = A0Res; BufA->SetU64<0>(A0Res); }

      uint64_t A1Res;
      A1Res = Shl128Xor<SFMTConsts::SL2 * 8, 1>(AHighIn, ALowIn, AHighIn);
      A1Res ^= (BufB->GetU64<1>() >> SFMTConsts::SR1) &
        (static_cast<uint64_t>(SFMTConsts::MSK3) | (static_cast<uint64_t>(SFMTConsts::MSK4) << 32)) &
        U64_Shr32Mask<SFMTConsts::SR1>::Value;
      A1Res = Shr128Xor<SFMTConsts::SR2 * 8, 1>(A1Res, CLow, CHigh);
      A1Res ^= (DHigh << SFMTConsts::SL1) & U64_Shl32Mask<SFMTConsts::SL1>::Value;
      if (SFMTConsts::SL2 > 0) { ALowOut = A0Res; BufA->SetU64<0>(A0Res); }
      AHighOut = A1Res; BufA->SetU64<1>(A1Res);
    }
    #endif

    #if (CFG_RANDPOOL_IMPL == CFG_RANDPOOL_IMPL_SSE2)
    // -------------------------------------------------------------------------
    // This is the SSE2 implementation. Implementing AltiVec in u128simd.h
    // should allow this to work fine for AltiVec as well.
    // -------------------------------------------------------------------------

    static std::string GetRandpoolImpl(void) { return "sse2"; }

    // The main recursion function.
    uint128_t FORCEINLINE mm_recursion(uint128_t *BufA, uint128_t *BufB,
      uint128_t ValC, uint128_t ValD, uint128_t Mask)
    {
      uint128_t ValA = *BufA;
      
      ValA = SIMDOP_xor(SIMDOP_xor(SIMDOP_xor(SIMDOP_xor(
        ValA,
        SIMDOps::Shl8<SFMTConsts::SL2>(ValA)),
        SIMDOP_and(SIMDOps::Shr_u32<SFMTConsts::SR1>(BufB[0]), Mask)),
        SIMDOps::Shr8<SFMTConsts::SR2>(ValC)),
        SIMDOps::Shl_u32<SFMTConsts::SL1>(ValD));
      *BufA = ValA;
      return ValA;
    }
    #endif

    #if (CFG_RANDPOOL_IMPL == CFG_RANDPOOL_IMPL_64BIT) || (CFG_RANDPOOL_IMPL == CFG_RANDPOOL_IMPL_SSE2)
    // -------------------------------------------------------------------------
    // This is the generic gen_rand for architectures where C and D are buffered
    // in registers.
    // -------------------------------------------------------------------------

    static const int PartLoops1 = (N - SFMTConsts::POS1) % 3;
    static const int Loops1 = (N - SFMTConsts::POS1) / 3;
    static const int Loops2 = SFMTConsts::POS1 / 3;
    static const int PartLoops2 = SFMTConsts::POS1 % 3;

    NOINLINE void gen_rand_all(void)
    {
      #ifndef CFG_TIMETRACK_DISABLE
      CTimedScope ScopeTimer(Metrics.gen_rand_all_time);
      Metrics.gen_rand_all_count++;
      #endif

      #if (CFG_RANDPOOL_IMPL == CFG_RANDPOOL_IMPL_SSE2)
      uint128_t Mask = SIMDOps::uint128_t_const<SFMTConsts::MSK1, SFMTConsts::MSK2, SFMTConsts::MSK3, SFMTConsts::MSK4>::Value();
      uint128_t AVal, CVal, DVal;
      #elif (CFG_RANDPOOL_IMPL == CFG_RANDPOOL_IMPL_64BIT)
      uint64_t ALow, AHigh, CLow, CHigh, DLow, DHigh;
      #endif

      uint128_t *APtr = FPool.template GetVarView<uint128_t>().GetPointer();
      uint128_t *BPtr;

      // Now would be a perfect time to use Duff's device. Except that both GCC
      // and MSVC choke badly on it and generate terrible code. So, we have to
      // manually unroll the partial loops. Additionally, it appears to be
      // impossible to express the functions in a way that makes everything work
      // well in both GCC and MSVC in both SSE2 and 64-bit mode. So, the code
      // has to be duplicated to coerce the compiler into not thrashing the
      // stack. Also, we should be able to use "APtr + 1" etc, except MSVC is
      // broken and emits C4328 on this construct.
      #define COMPOSE(x, y) x##y
      #if (CFG_RANDPOOL_IMPL == CFG_RANDPOOL_IMPL_SSE2)
        #define MM_RECURSION(A, AOffset, BOffset, C, D) COMPOSE(A, Val) = mm_recursion(&APtr[AOffset], &BPtr[BOffset], COMPOSE(C, Val), COMPOSE(D, Val), Mask);
        #define MM_LOAD(X, AOffset) COMPOSE(X, Val) = APtr[AOffset];
      #elif (CFG_RANDPOOL_IMPL == CFG_RANDPOOL_IMPL_64BIT)
        #define MM_RECURSION(A, AOffset, BOffset, C, D) mm_recursion(&APtr[AOffset], &BPtr[BOffset], COMPOSE(A, Low), COMPOSE(A, High), COMPOSE(C, Low), COMPOSE(C, High), COMPOSE(D, Low), COMPOSE(D, High));
        #define MM_LOAD(X, AOffset) COMPOSE(X, Low) = APtr[AOffset].GetU64<0>(); COMPOSE(X, High) = APtr[AOffset].GetU64<1>();
      #endif

      BPtr = APtr;
      if (PartLoops1 == 2)
      {
        MM_LOAD(D, N - 2)
        MM_LOAD(A, N - 1)
        MM_RECURSION(C, 0, SFMTConsts::POS1 + 0, D, A)
        MM_RECURSION(D, 1, SFMTConsts::POS1 + 1, A, C)
        APtr += 2;
      }
      if (PartLoops1 == 1)
      {
        MM_LOAD(A, N - 2)
        MM_LOAD(C, N - 1)
        MM_RECURSION(D, 0, SFMTConsts::POS1 + 0, A, C)
        APtr += 1;
      }

      APtr += 3 * Loops1;
      BPtr = APtr + SFMTConsts::POS1;
      int LoopCount = -3 * Loops1;

      for (;;)
      {
        for (; LoopCount < 0; LoopCount += 3)
        {
          MM_RECURSION(A, LoopCount + 0, LoopCount + 0, C, D)
          MM_RECURSION(C, LoopCount + 1, LoopCount + 1, D, A)
          MM_RECURSION(D, LoopCount + 2, LoopCount + 2, A, C)
        }
        if (BPtr == APtr + SFMTConsts::POS1)
        {
          // Handle BPtr wrapping around the end of the array.
          LoopCount = -Loops2 * 3;
          BPtr = APtr - N + 2 * SFMTConsts::POS1 - SFMTConsts::POS1 % 3;
          APtr += Loops2 * 3;
        }
        else
          break;
      }

      // Again, Duff's device would allow us to avoid this annoying manual
      // unrolling (not to mention this rather harder to follow logic).
      if (PartLoops2 >= 1) MM_RECURSION(A, LoopCount + 0, LoopCount + 0, C, D)
      if (PartLoops2 >= 2) MM_RECURSION(C, LoopCount + 1, LoopCount + 1, D, A)
    }
    #endif

    // Certifies the period (2^MEXP), potentially changing one of the bits to
    // make sure.
    void PeriodCertification(void)
    {
      CDataBuffer_VarView<uint128_t, N * 16> PoolU128 = FPool.template GetVarView<uint128_t>();
      uint128_t ParityCheck = SIMDOps::Parity(SIMDOP_and(
        SIMDOps::uint128_t_const<SFMTConsts::PARITY1, SFMTConsts::PARITY2, SFMTConsts::PARITY3, SFMTConsts::PARITY4>::Value(), PoolU128.Load(0)));
      PoolU128.Store(0, SIMDOP_xor(PoolU128.Load(0), SIMDOps::AndNot(SIMDOps::uint128_t_const<
        lowestbit_u128<SFMTConsts::PARITY1, SFMTConsts::PARITY2, SFMTConsts::PARITY3, SFMTConsts::PARITY4>::y0,
        lowestbit_u128<SFMTConsts::PARITY1, SFMTConsts::PARITY2, SFMTConsts::PARITY3, SFMTConsts::PARITY4>::y1,
        lowestbit_u128<SFMTConsts::PARITY1, SFMTConsts::PARITY2, SFMTConsts::PARITY3, SFMTConsts::PARITY4>::y2,
        lowestbit_u128<SFMTConsts::PARITY1, SFMTConsts::PARITY2, SFMTConsts::PARITY3, SFMTConsts::PARITY4>::y3>::Value(),
        ParityCheck)));
    }
  public:
    CRandPool(void)
    { 
      #ifndef CFG_TIMETRACK_DISABLE
      Metrics.ForceConstruction(); 
      #endif
    }
    /**
     * This function returns the identification string.
     * The string shows the word size, the Mersenne exponent,
     * and all parameters of this generator.
     */
    static std::string GetIDString(void)
    {
      std::ostringstream os;
      os << "SFMT" << '-' << SFMTConsts::MEXP << ':' << SFMTConsts::POS1 << '-' << SFMTConsts::SL1 << '-' << SFMTConsts::SL2 <<
        '-' << SFMTConsts::SR1 << '-' << SFMTConsts::SR2 << ':' << std::hex << std::setfill('0') <<
        std::setw(8) << SFMTConsts::MSK1 << '-' <<
        std::setw(8) << SFMTConsts::MSK2 << '-' <<
        std::setw(8) << SFMTConsts::MSK3 << '-' <<
        std::setw(8) << SFMTConsts::MSK4 << ':' << GetRandpoolImpl();
      return os.str();
    }
    
    /**
     * This function initializes the internal state array with a 32-bit
     * integer seed.
     *
     * @param seed a 32-bit integer used as the seed.
     */
     
    NOINLINE void init_gen_rand(uint32_t seed)
    {
      CDataBuffer_VarView<uint32_t, N * 16> PoolU32 = FPool.template GetVarView<uint32_t>();
      uint32_t x0 = seed;
      for (uint32_t i = 0; i < N; i++)
      {
        uint32_t x1 = func3(x0, i * 4 + 1);
        uint32_t x2 = func3(x1, i * 4 + 2);
        uint32_t x3 = func3(x2, i * 4 + 3);
        PoolU32.Store(i * 4 + EndianFix_static<2, 0>::Value, x0);
        PoolU32.Store(i * 4 + EndianFix_static<2, 1>::Value, x1);
        PoolU32.Store(i * 4 + EndianFix_static<2, 2>::Value, x2);
        PoolU32.Store(i * 4 + EndianFix_static<2, 3>::Value, x3);
        x0 = func3(x3, i * 4 + 4);
      }
      PeriodCertification();
      SIMDOps::EmptyForFP();
    }
    
    /**
     * This function initializes the internal state array,
     * with an array of 32-bit integers used as the seeds
     * @param init_key the array of 32-bit integers, used as a seed.
     * @param key_length the length of init_key.
     */
    NOINLINE void init_by_array(uint32_t *init_key, size_t key_length)
    {
      uint32_t *FPool32 = FPool.template GetVarView<uint32_t>().GetPointer();

      size_t lag;
      if (N32 >= 623)
	      lag = 11;
      else if (N32 >= 68)
	      lag = 7;
      else if (N32 >= 39)
	      lag = 5;
      else
	      lag = 3;
      size_t mid = (N32 - lag) / 2;

      memset(FPool32, 0x8b, N * 16);

      size_t count;
      if (key_length + 1 > N32)
        count = key_length + 1;
      else
	      count = N32;

      uint32_t r = func1(FPool32[IdxOf32(0)] ^ FPool32[IdxOf32(mid)]
        ^ FPool32[IdxOf32(N32 - 1)]);
      FPool32[IdxOf32(mid)] += r;
      r += key_length;
      FPool32[IdxOf32(mid + lag)] += r;
      FPool32[IdxOf32(0)] = r;

      size_t i, j;
      count--;
      for (i = 1, j = 0; (j < count) && (j < key_length); j++)
      {
	      r = func1(FPool32[IdxOf32(i)] ^ FPool32[IdxOf32((i + mid) % N32)]
          ^ FPool32[IdxOf32((i + N32 - 1) % N32)]);
	      FPool32[IdxOf32((i + mid) % N32)] += r;
	      r += init_key[j] + i;
	      FPool32[IdxOf32((i + mid + lag) % N32)] += r;
	      FPool32[IdxOf32(i)] = r;
	      i = (i + 1) % N32;
      }

      for (; j < count; j++)
      {
	      r = func1(FPool32[IdxOf32(i)] ^ FPool32[IdxOf32((i + mid) % N32)]
		      ^ FPool32[IdxOf32((i + N32 - 1) % N32)]);
	      FPool32[IdxOf32((i + mid) % N32)] += r;
	      r += i;
	      FPool32[IdxOf32((i + mid + lag) % N32)] += r;
	      FPool32[IdxOf32(i)] = r;
	      i = (i + 1) % N32;
      }
      for (j = 0; j < N32; j++)
      {
	      r = func2(FPool32[IdxOf32(i)] + FPool32[IdxOf32((i + mid) % N32)]
		      + FPool32[IdxOf32((i + N32 - 1) % N32)]);
	      FPool32[IdxOf32((i + mid) % N32)] ^= r;
	      r -= i;
	      FPool32[IdxOf32((i + mid + lag) % N32)] ^= r;
	      FPool32[IdxOf32(i)] = r;
	      i = (i + 1) % N32;
      }
      PeriodCertification();
      SIMDOps::EmptyForFP();
    }

    static const size_t BufSize = N;

    inline CRandomBlockPtr GetRandomBlock(void)
    {
      FPool.MakeUnique();
      gen_rand_all();
      return FPool;
    }
};

#ifndef CFG_TIMETRACK_DISABLE
template<class SFMTParams> typename CRandPool<SFMTParams>::TMetrics CRandPool<SFMTParams>::Metrics;
template<class SFMTParams> THREADVAR uint32_t CRandPool<SFMTParams>::TMetrics::poolmoves = 0;
template<class SFMTParams> THREADVAR uint32_t CRandPool<SFMTParams>::TMetrics::gen_rand_all_count = 0;
template<class SFMTParams> THREADVAR uint64_t CRandPool<SFMTParams>::TMetrics::gen_rand_all_time = 0;
#endif

#if CFG_COMPILER == CFG_COMPILER_MSVC
#pragma warning(pop)
#endif

#endif
