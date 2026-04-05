/*   ColDet - C++ 3D Collision Detection Library
 *   Copyright (C) 2000   Amir Geva
 *
 * Internal implementation class.
 */
#ifndef COLDET_IMPL_H
#define COLDET_IMPL_H

#include "../include/coldet.h"
#include "box.h"
#include <vector>

namespace COLDET {

struct CollidingPair
{
    int t1, t2;
    Vector3f point;
};

class CollisionModel3DImpl : public CollisionModel3D
{
public:
    explicit CollisionModel3DImpl(bool isStatic);
    virtual ~CollisionModel3DImpl();

    // CollisionModel3D interface
    virtual void setTriangleNumber(int num) override;
    virtual void addTriangle(float x1,float y1,float z1,
                             float x2,float y2,float z2,
                             float x3,float y3,float z3) override;
    virtual void addTriangle(float v1[3], float v2[3], float v3[3]) override;
    virtual void finalize() override;
    virtual void setTransform(float m[16]) override;

    virtual bool collision(CollisionModel3D* other,
                           int AccuracyDepth,
                           int MaxProcessingTime,
                           float* other_transform) override;

    virtual bool rayCollision(float origin[3], float direction[3],
                              bool closest, float segmin, float segmax) override;

    virtual bool sphereCollision(float origin[3], float radius) override;

    virtual bool getCollidingTriangles(int nTri,
                                       float t1[9], float t2[9],
                                       bool ModelSpace) override;
    virtual bool getCollidingTriangles(int& t1, int& t2) override;
    virtual bool getCollisionPoint(int nPnt, float p[3], bool ModelSpace) override;
    virtual int  getNumCollisions(void) override;

    // Internal helpers
    void collectCollisions(BoxNode* nodeA, BoxNode* nodeB,
                           CollisionModel3DImpl* other,
                           const float* otherTransform);

    bool m_static;
    bool m_finalized;
    float m_transform[16];

    std::vector<Triangle>     m_triangles;
    BoxNode*                  m_root;
    std::vector<CollidingPair> m_collisions;
};

} // namespace COLDET

#endif // COLDET_IMPL_H
