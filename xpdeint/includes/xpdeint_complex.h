/*
  Copyright (C) 2000-2007

  Code contributed by Greg Collecutt, Joseph Hope and the xmds-devel team

  This file is part of xpdeint.

  This program is free software; you can redistribute it and/or
  modify it under the terms of the GNU General Public License
  as published by the Free Software Foundation; either version 2
  of the License, or (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this program; if not, write to the Free Software
  Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
*/

/*! @file xpdeint_complex.h
  @brief Functions and overloads for fftw_complex types
*/
#include <math.h>

extern "C++" {

#include <iomanip>

#ifdef FFTW3_H
  typedef struct {
    double re;
    double im;
  } fftw_complex3;

#define fftw_complex fftw_complex3

#define xmds_malloc fftw_malloc
#define xmds_free   fftw_free
#else
#define xmds_malloc(n) _aligned_malloc(n, sizeof(double))
#define xmds_free   _aligned_free

typedef struct {
  double re;
  double im;
} fftw_complex;
#endif //FFTW3_H

  // **********************************************
  // rectangular complex and polar complex creation
  // **********************************************

  //! Rectangular complex object creation
  inline fftw_complex rcomplex(const double& re, const double& im) {
    fftw_complex z;
    z.re = re;
    z.im = im;
    return z;
  }

  //! Polar complex object creation
  inline fftw_complex pcomplex(const double& mag, const double& phase) {
    fftw_complex z;
    z.re = mag*cos(phase);
    z.im = mag*sin(phase);
    return z;
  }

  // **********************************************
  //     external fftw_complex overloads
  // **********************************************

  //! Overloaded complex addition operator
  inline fftw_complex operator + (fftw_complex z) {
    return z;
  }

  //! Overloaded complex addition operator
  inline fftw_complex operator + (fftw_complex z1, const fftw_complex& z2) {
    z1.re += z2.re;
    z1.im += z2.im;
    return z1;
  }

  //! Overloaded complex addition operator
  inline fftw_complex operator + (fftw_complex z, const double& d) {
    z.re += d;
    return z;
  }

  //! Overloaded complex addition operator
  inline fftw_complex operator + (const double& d, fftw_complex z) {
    z.re += d;
    return z;
  }

  //! Overloaded complex addition operator
  inline fftw_complex operator + (fftw_complex z, const int& j) {
    z.re += j;
    return z;
  }

  //! Overloaded complex addition operator
  inline fftw_complex operator + (const int& j, fftw_complex z) {
    z.re += j;
    return z;
  }

  //! Overloaded complex negation operator
  inline fftw_complex operator - (fftw_complex z) {
    z.im = -z.im;
    z.re = -z.re;
    return z;
  }

  //! Overloaded complex subtraction operator
  inline fftw_complex operator - (fftw_complex z1, const fftw_complex& z2) {
    z1.re -= z2.re;
    z1.im -= z2.im;
    return z1;
  }

  //! Overloaded complex subtraction operator
  inline fftw_complex operator - (fftw_complex z, const double& d) {
    z.re -= d;
    return z;
  }

  //! Overloaded complex subtraction operator
  inline fftw_complex operator - (const double& d, fftw_complex z) {
    z.re = d-z.re;
    z.im =  -z.im;
    return z;
  }

  //! Overloaded complex subtraction operator
  inline fftw_complex operator - (fftw_complex z, const int& j) {
    z.re -= j;
    return z;
  }

  //! Overloaded complex subtraction operator
  inline fftw_complex operator - (const int& j, fftw_complex z) {
    z.re = j-z.re;
    z.im =  -z.im;
    return z;
  }

  //! Overloaded complex multiplication operator
  inline fftw_complex operator * (const fftw_complex& z1, const fftw_complex&  z2) {
    fftw_complex z;
    z.re = z1.re*z2.re - z1.im*z2.im;
    z.im = z1.im*z2.re + z1.re*z2.im;
    return z;
  }

  //! Overloaded complex multiplication operator
  inline fftw_complex operator * (fftw_complex z, const double& d) {
    z.re *= d;
    z.im *= d;
    return z;
  }

  //! Overloaded complex multiplication operator
  inline fftw_complex operator * (const double& d, fftw_complex z) {
    z.re *= d;
    z.im *= d;
    return z;
  }

  //! Overloaded complex multiplication operator
  inline fftw_complex operator * (fftw_complex z, const int& j) {
    z.re *= j;
    z.im *= j;
    return z;
  }
  
  //! Overloaded complex multiplication operator
  inline fftw_complex operator * (fftw_complex z, const long& j) {
    z.re *= j;
    z.im *= j;
    return z;
  }

  //! Overloaded complex multiplication operator
  inline fftw_complex operator * (const int& j, fftw_complex z) {
    z.re *= j;
    z.im *= j;
    return z;
  }

  //! Overloaded complex multiplication operator
  inline fftw_complex operator * (const long& j, fftw_complex z) {
    z.re *= j;
    z.im *= j;
    return z;
  }

  //! Overloaded complex division operator
  inline fftw_complex operator / (fftw_complex z1, const fftw_complex&  z2) {
    const double c = z2.re*z2.re + z2.im*z2.im;
    const double temp = (z1.re*z2.re + z1.im*z2.im)/c;
    z1.im = (z1.im*z2.re - z1.re*z2.im)/c;
    z1.re = temp;
    return z1;
  }

  //! Overloaded complex division operator
  inline fftw_complex operator / (fftw_complex z, const double& d) {
    z.re /= d;
    z.im /= d;
    return z;
  }

  //! Overloaded complex division operator
  inline fftw_complex operator / (const double& d, fftw_complex z) {
    double c = z.re*z.re + z.im*z.im;
    z.re *=  d/c;
    z.im *= -d/c;
    return z;
  }

  //! Overloaded complex division operator
  inline fftw_complex operator / (fftw_complex z, const int& j) {
    z.re /= j;
    z.im /= j;
    return z;
  }

  //! Overloaded complex division operator
  inline fftw_complex operator / (const int& j, fftw_complex z) {
    double c = z.re*z.re + z.im*z.im;
    z.re *=  j/c;
    z.im *= -j/c;
    return z;
  }

  //! Overloaded complex division operator
  inline fftw_complex operator / (fftw_complex z, const long& j) {
    z.re /= j;
    z.im /= j;
    return z;
  }

  //! Overloaded complex division operator
  inline fftw_complex operator / (const long& j, fftw_complex z) {
    double c = z.re*z.re + z.im*z.im;
    z.re *=  j/c;
    z.im *= -j/c;
    return z;
  }

  //! Overloaded complex less than operator
  inline bool operator < (const double& d, const fftw_complex& z) {
    return d < z.re*z.re+z.im*z.im;
  }

  //! Overloaded complex greater than operator
  inline bool operator > (const double& d, const fftw_complex& z) {
    return d > z.re*z.re+z.im*z.im;
  }

  //! Overloaded complex less than or equal to operator
  inline bool operator <= (const double& d, const fftw_complex& z) {
    return d <= z.re*z.re+z.im*z.im;
  }

  //! Overloaded complex greater than or equal to operator
  inline bool operator >= (const double& d, const fftw_complex& z) {
    return d >= z.re*z.re+z.im*z.im;
  }

  //! Overloaded complex equality operator
  inline bool operator == (const double& d, const fftw_complex& z) {
    return d == z.re*z.re+z.im*z.im;
  }

  //! Overloaded complex inequality operator
  inline bool operator != (const double& d, const fftw_complex& z) {
    return d != z.re*z.re+z.im*z.im;
  }

  // **********************************************
  //         some unary complex functions
  // **********************************************

  //! Returns real part of a complex number
  inline double real(const fftw_complex& z) {
    return z.re;
  }

  //! Returns imaginary part of a complex number
  inline double imag(const fftw_complex& z) {
    return z.im;
  }

  //! Returns modulus squared of a complex number
  inline double mod2(const fftw_complex& z) {
    return z.re*z.re + z.im*z.im;
  }
  
  //! Returns modulus squared of a real number
  inline double mod2(const double& x) {
    return x*x;
  }

  //! Returns modulus of a complex number
  inline double mod(const fftw_complex& z) {
    return sqrt(z.re*z.re + z.im*z.im);
  }
  
  //! Returns modulus of a real number
  inline double mod(const double& x) {
    return fabs(x);
  }

  //! Returns arg of a complex number
  inline double arg(const fftw_complex& z) {
    return atan2(z.im, z.re);
  }

  //! Returns the complex conjugate
  inline fftw_complex conj(fftw_complex z) {
    z.im = -z.im;
    return z;
  }

  //! Returns the complex exponential
  inline fftw_complex c_exp(const fftw_complex& z1) {
    fftw_complex z;
    z.re = exp(z1.re)*cos(z1.im);
    z.im = exp(z1.re)*sin(z1.im);
    return z;
  }

  //! Returns the complex natural logarithm
  inline fftw_complex c_log(const fftw_complex& z1) {

    fftw_complex z;

    double _m = mod(z1);

    if (fabs(_m)>1e-100)
      z.re = log(_m);
    else
      z.re = -46;

    z.im = arg(z1);

    return z;
  }

  //! Returns the complex square root
  inline fftw_complex c_sqrt(const fftw_complex z1) {

    const double _m = sqrt(mod(z1));
    const double _a = arg(z1)/2;

    return pcomplex(_m, _a);
  }

  // **********************************************
  //             a nice complex class
  // **********************************************

  //! A nice complex class
  class complex : public fftw_complex {

  public:

    //Constructors

    //! Constructor of complex object
    complex() {
      re = 0;
      im = 0;
    }

    //! Constructor of complex object
    /*!
      This could be "explicit", providing extra warnings
    */
    complex(const fftw_complex& z) {
      re = z.re;
      im = z.im;
    }

    //! Constructor of complex object
    /*!
      This could be "explicit", providing extra warnings
    */
    complex(const double& d) {
      re = d;
      im = 0;
    }

    //! Constructor of complex object
    complex(const double& real, const double& imag, const bool& polar=false) {
      if (polar) {
  re = real*cos(imag);
  im = real*sin(imag);
      }
      else {
  re = real;
  im = imag;
      }
    }

    //! Addition operator
    inline complex& operator + () {
      return *this;
    }

    //! Negation operator
    inline complex operator - () {
      return complex(-re, -im);
    }

    //! Assignment operator
    inline complex& operator = (const fftw_complex& z) {
      re = z.re;
      im = z.im;
      return *this;
    }

    //! Assignment operator
    inline complex& operator = (const double& d) {
      re = d;
      im = 0;
      return *this;
    }

    //! Conversion to double operator
    inline operator double () const {
      return re;
    }

    //! += operator
    inline complex& operator += (const fftw_complex& z) {
      re += z.re;
      im += z.im;
      return *this;
    }

    //! += operator
    inline complex& operator += (const double& d) {
      re += d;
      return *this;
    }

    //! -= operator
    inline complex& operator -= (const fftw_complex& z) {
      re -= z.re;
      im -= z.im;
      return *this;
    }

    //! -= operator
    inline complex& operator -= (const double& d) {
      re -= d;
      return *this;
    }

    //! *= operator
    inline complex& operator *= (const fftw_complex& z) {
      const double temp = re*z.re - im*z.im;
      im = im*z.re + re*z.im;
      re = temp;
      return *this;
    }

    //! *= operator
    inline complex& operator *= (const double& d) {
      re *= d;
      im *= d;
      return *this;
    }

    //! /= operator
    inline complex& operator /= (const fftw_complex& z) {
      const double c = z.re*z.re + z.im*z.im;
      const double temp = (re*z.re + im*z.im)/c;
      im = (im*z.re - re*z.im)/c;
      re=temp;
      return *this;
    }

    //! /= operator
    inline complex& operator /= (const double& d) {
      re /= d;
      im /= d;
      return *this;
    }

    //! /= operator
    inline complex& operator /= (const int& j) {
      re /= j;
      im /= j;
      return *this;
    }

    //! /= operator
    inline complex& operator /= (const long& j) {
      re /= j;
      im /= j;
      return *this;
    }

    //! Less than comparison operator
    inline bool operator < (const fftw_complex& z) const {
      return re*re+im*im < z.re*z.re+z.im*z.im;
    }

    //! Less than comparison operator
    inline bool operator < (const double& d) const {
      return re*re+im*im < d;
    }

    //! Greater than comparison operator
    inline bool operator > (const fftw_complex& z) const {
      return re*re+im*im > z.re*z.re+z.im*z.im;
    }

    //! Greater than comparison operator
    inline bool operator > (const double& d) const {
      return re*re+im*im > d;
    }

    //! Less than or equal to comparison operator
    inline bool operator <= (const fftw_complex& z) const {
      return re*re+im*im <= z.re*z.re+z.im*z.im;
    }

    //! Less than or equal to comparison operator
    inline bool operator <= (const double& d) const {
      return re*re+im*im <= d;
    }

    //! Greater than or equal to comparison operator
    inline bool operator >= (const fftw_complex& z) const {
      return re*re+im*im >= z.re*z.re+z.im*z.im;
    }

    //! Greater than or equal to comparison operator
    inline bool operator >= (const double& d) const {
      return re*re+im*im >= d;
    }

    //! Equality comparison operator
    inline bool operator == (const complex& z) const {
      return re == z.re && im == z.im;
    }

    //! Equality comparison operator
    inline bool operator == (const double& d) const {
      return re == d && im == 0;
    }

    //! Inequality comparison operator
    inline bool operator != (const complex& z) const {
      return re!=z.re || im!=z.im;
    }

    //! Inequality comparison operator
    inline bool operator != (const double& d) const {
      return re!=d || im!=0;
    }

    //! Complex conjugate operator
    /*!
      We define operator ~ to be the complex conjugate
    */
    inline complex operator ~ () const {
      complex z = *this;
      z.im = -z.im;
      return z;
    }
  };

  //! Define the complex number i
  const complex i = complex(0, 1);

#ifdef FFTW3_H
#undef fftw_complex
#endif //FFTW3_H

} // extern "C++"

