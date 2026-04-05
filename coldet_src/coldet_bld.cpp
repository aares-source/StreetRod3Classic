/*   ColDet - C++ 3D Collision Detection Library
 *   Copyright (C) 2000   Amir Geva
 *
 * CollisionModel3D implementation - model building and storage.
 */
#include "coldet_impl.h"

namespace COLDET {

CollisionModel3DImpl::CollisionModel3DImpl(bool isStatic)
    : m_static(isStatic)
    , m_finalized(false)
    , m_root(nullptr)
{
    // Identity transform
    for(int i=0;i<16;i++) m_transform[i]=0;
    m_transform[0]=m_transform[5]=m_transform[10]=m_transform[15]=1.0f;
}

CollisionModel3DImpl::~CollisionModel3DImpl()
{
    delete m_root;
}

void CollisionModel3DImpl::setTriangleNumber(int num)
{
    m_triangles.reserve(num);
}

void CollisionModel3DImpl::addTriangle(float x1,float y1,float z1,
                                       float x2,float y2,float z2,
                                       float x3,float y3,float z3)
{
    if(m_finalized) throw Inconsistency();
    m_triangles.push_back(Triangle(
        Vector3f(x1,y1,z1),
        Vector3f(x2,y2,z2),
        Vector3f(x3,y3,z3)));
}

void CollisionModel3DImpl::addTriangle(float v1[3], float v2[3], float v3[3])
{
    addTriangle(v1[0],v1[1],v1[2], v2[0],v2[1],v2[2], v3[0],v3[1],v3[2]);
}

void CollisionModel3DImpl::finalize()
{
    if(m_triangles.empty()) { m_finalized=true; return; }
    std::vector<int> idx;
    idx.reserve(m_triangles.size());
    for(int i=0;i<(int)m_triangles.size();i++) idx.push_back(i);
    delete m_root;
    m_root = BuildBox(m_triangles, idx);
    m_finalized = true;
}

void CollisionModel3DImpl::setTransform(float m[16])
{
    for(int i=0;i<16;i++) m_transform[i]=m[i];
}

} // namespace COLDET
