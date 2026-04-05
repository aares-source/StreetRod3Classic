/*   ColDet - C++ 3D Collision Detection Library
 *   Copyright (C) 2000   Amir Geva
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Library General Public
 * License as published by the Free Software Foundation; either
 * version 2 of the License, or (at your option) any later version.
 */
#ifndef COLDET_CDMATH3D_H
#define COLDET_CDMATH3D_H

#include <math.h>
#include <float.h>
#include <string.h>

namespace COLDET {

class Vector3f
{
public:
    float v[3];

    Vector3f() { v[0]=0; v[1]=0; v[2]=0; }
    Vector3f(float x, float y, float z) { v[0]=x; v[1]=y; v[2]=z; }

    float& operator[](int i) { return v[i]; }
    const float& operator[](int i) const { return v[i]; }

    Vector3f operator+(const Vector3f& o) const { return Vector3f(v[0]+o[0],v[1]+o[1],v[2]+o[2]); }
    Vector3f operator-(const Vector3f& o) const { return Vector3f(v[0]-o[0],v[1]-o[1],v[2]-o[2]); }
    Vector3f operator*(float s) const { return Vector3f(v[0]*s,v[1]*s,v[2]*s); }
    Vector3f operator-() const { return Vector3f(-v[0],-v[1],-v[2]); }

    float dot(const Vector3f& o) const { return v[0]*o[0]+v[1]*o[1]+v[2]*o[2]; }
    Vector3f cross(const Vector3f& o) const {
        return Vector3f(v[1]*o[2]-v[2]*o[1], v[2]*o[0]-v[0]*o[2], v[0]*o[1]-v[1]*o[0]);
    }
    float lengthSq() const { return v[0]*v[0]+v[1]*v[1]+v[2]*v[2]; }
    float length() const { return sqrtf(lengthSq()); }
    Vector3f normalize() const { float l=length(); if(l>1e-10f) return *this*(1.0f/l); return *this; }
    bool operator==(const Vector3f& o) const { return v[0]==o[0]&&v[1]==o[1]&&v[2]==o[2]; }
};

// Transform a point by a 4x4 column-major matrix (OpenGL style)
inline Vector3f TransformPoint(const float m[16], const Vector3f& p)
{
    return Vector3f(
        m[0]*p[0]+m[4]*p[1]+m[8] *p[2]+m[12],
        m[1]*p[0]+m[5]*p[1]+m[9] *p[2]+m[13],
        m[2]*p[0]+m[6]*p[1]+m[10]*p[2]+m[14]);
}

// Transform a direction (no translation) by a 4x4 column-major matrix
inline Vector3f TransformDir(const float m[16], const Vector3f& p)
{
    return Vector3f(
        m[0]*p[0]+m[4]*p[1]+m[8] *p[2],
        m[1]*p[0]+m[5]*p[1]+m[9] *p[2],
        m[2]*p[0]+m[6]*p[1]+m[10]*p[2]);
}

// Invert a 4x4 matrix (assumes only rotation+translation, no scale)
inline void InvertTransform(const float m[16], float inv[16])
{
    // Transpose the 3x3 rotation part
    inv[0]=m[0]; inv[4]=m[1]; inv[8] =m[2];  inv[12]=0;
    inv[1]=m[4]; inv[5]=m[5]; inv[9] =m[6];  inv[13]=0;
    inv[2]=m[8]; inv[6]=m[9]; inv[10]=m[10]; inv[14]=0;
    inv[3]=0;    inv[7]=0;    inv[11]=0;      inv[15]=1;
    // Compute new translation: -R^T * t
    float tx=m[12], ty=m[13], tz=m[14];
    inv[12]=-(inv[0]*tx+inv[4]*ty+inv[8] *tz);
    inv[13]=-(inv[1]*tx+inv[5]*ty+inv[9] *tz);
    inv[14]=-(inv[2]*tx+inv[6]*ty+inv[10]*tz);
}

} // namespace COLDET

#endif // COLDET_CDMATH3D_H
