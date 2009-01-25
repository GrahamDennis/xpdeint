#ifndef ZIGGURAT_H
#define ZIGGURAT_H

class CZigguratGaussian_FP32
{
  public:
    struct TBinData
    {
      uint32_t THold;
      float XScale, YOffset, YScale;
    };

    static const int NumBins = 256;
    static const TBinData Bins[NumBins];
};

class CZigguratGaussian_FP64
{
  public:
    struct TBinData
    {
      uint64_t THold;
      double XScale, YOffset, YScale;
    };

    static const int NumBins = 128;
    static const TBinData Bins[NumBins];
};

class CZigguratExponential_FP32
{
  public:
    struct TBinData
    {
      uint32_t THold;
      float XScale, YOffset, YScale;
    };

    static const int NumBins = 256;
    static const TBinData Bins[NumBins];
};

class CZigguratExponential_FP64
{
  public:
    struct TBinData
    {
      uint64_t THold;
      double XScale, YOffset, YScale;
    };

    static const int NumBins = 128;
    static const TBinData Bins[NumBins];
};

#endif
