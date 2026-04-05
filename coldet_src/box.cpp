/*   ColDet - C++ 3D Collision Detection Library
 *   Copyright (C) 2000   Amir Geva
 */
#include "box.h"
#include <float.h>

extern "C" int tri_tri_intersect(float V0[3], float V1[3], float V2[3],
                                 float U0[3], float U1[3], float U2[3]);

namespace COLDET {

// ----------------------------------------------------------------
// Triangle::intersect
// ----------------------------------------------------------------
bool Triangle::intersect(const Triangle& other) const
{
    float v0[3]={ v[0][0], v[0][1], v[0][2] };
    float v1[3]={ v[1][0], v[1][1], v[1][2] };
    float v2[3]={ v[2][0], v[2][1], v[2][2] };
    float u0[3]={ other.v[0][0], other.v[0][1], other.v[0][2] };
    float u1[3]={ other.v[1][0], other.v[1][1], other.v[1][2] };
    float u2[3]={ other.v[2][0], other.v[2][1], other.v[2][2] };
    return tri_tri_intersect(v0,v1,v2,u0,u1,u2) != 0;
}

// ----------------------------------------------------------------
// Triangle::rayIntersect  (Moller-Trumbore)
// ----------------------------------------------------------------
bool Triangle::rayIntersect(const Vector3f& origin, const Vector3f& dir,
                            float segmin, float segmax, float& t) const
{
    const float EPSILON = 1e-6f;
    Vector3f e1 = v[1] - v[0];
    Vector3f e2 = v[2] - v[0];
    Vector3f h  = dir.cross(e2);
    float    a  = e1.dot(h);
    if(a > -EPSILON && a < EPSILON) return false;
    float    f  = 1.0f / a;
    Vector3f s  = origin - v[0];
    float    u  = f * s.dot(h);
    if(u < 0.0f || u > 1.0f) return false;
    Vector3f q  = s.cross(e1);
    float    vv = f * dir.dot(q);
    if(vv < 0.0f || u+vv > 1.0f) return false;
    t = f * e2.dot(q);
    return (t >= segmin && t <= segmax);
}

// ----------------------------------------------------------------
// BoxNode::overlaps
// Transform both boxes to world space and do AABB overlap test.
// For correctness with OBBs this is an approximation, but matches
// the original coldet 2.0 approach for tree traversal.
// ----------------------------------------------------------------
bool BoxNode::overlaps(const BoxNode& other,
                       const float myT[16],
                       const float otherT[16]) const
{
    // Transform our AABB corners to world space and compute world AABB
    Vector3f myCorners[8];
    myCorners[0]=Vector3f(min[0],min[1],min[2]);
    myCorners[1]=Vector3f(max[0],min[1],min[2]);
    myCorners[2]=Vector3f(min[0],max[1],min[2]);
    myCorners[3]=Vector3f(max[0],max[1],min[2]);
    myCorners[4]=Vector3f(min[0],min[1],max[2]);
    myCorners[5]=Vector3f(max[0],min[1],max[2]);
    myCorners[6]=Vector3f(min[0],max[1],max[2]);
    myCorners[7]=Vector3f(max[0],max[1],max[2]);

    Vector3f myWMin(FLT_MAX,FLT_MAX,FLT_MAX);
    Vector3f myWMax(-FLT_MAX,-FLT_MAX,-FLT_MAX);
    for(int i=0;i<8;i++) {
        Vector3f wp = TransformPoint(myT, myCorners[i]);
        for(int k=0;k<3;k++) {
            if(wp[k]<myWMin[k]) myWMin[k]=wp[k];
            if(wp[k]>myWMax[k]) myWMax[k]=wp[k];
        }
    }

    Vector3f otherCorners[8];
    otherCorners[0]=Vector3f(other.min[0],other.min[1],other.min[2]);
    otherCorners[1]=Vector3f(other.max[0],other.min[1],other.min[2]);
    otherCorners[2]=Vector3f(other.min[0],other.max[1],other.min[2]);
    otherCorners[3]=Vector3f(other.max[0],other.max[1],other.min[2]);
    otherCorners[4]=Vector3f(other.min[0],other.min[1],other.max[2]);
    otherCorners[5]=Vector3f(other.max[0],other.min[1],other.max[2]);
    otherCorners[6]=Vector3f(other.min[0],other.max[1],other.max[2]);
    otherCorners[7]=Vector3f(other.max[0],other.max[1],other.max[2]);

    Vector3f otherWMin(FLT_MAX,FLT_MAX,FLT_MAX);
    Vector3f otherWMax(-FLT_MAX,-FLT_MAX,-FLT_MAX);
    for(int i=0;i<8;i++) {
        Vector3f wp = TransformPoint(otherT, otherCorners[i]);
        for(int k=0;k<3;k++) {
            if(wp[k]<otherWMin[k]) otherWMin[k]=wp[k];
            if(wp[k]>otherWMax[k]) otherWMax[k]=wp[k];
        }
    }

    // AABB overlap test
    for(int k=0;k<3;k++) {
        if(myWMax[k] < otherWMin[k]) return false;
        if(myWMin[k] > otherWMax[k]) return false;
    }
    return true;
}

} // namespace COLDET
