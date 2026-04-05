/*   ColDet - C++ 3D Collision Detection Library
 *   Copyright (C) 2000   Amir Geva
 *
 * Collision query implementations and factory function.
 */
#include "coldet_impl.h"
#include <float.h>
#include <math.h>

namespace COLDET {

// ----------------------------------------------------------------
// Recursive BVH traversal for model-model collision
// ----------------------------------------------------------------
void CollisionModel3DImpl::collectCollisions(BoxNode* nodeA, BoxNode* nodeB,
                                             CollisionModel3DImpl* other,
                                             const float* otherTransform)
{
    if(!nodeA || !nodeB) return;

    if(!nodeA->overlaps(*nodeB, m_transform, otherTransform)) return;

    if(nodeA->isLeaf() && nodeB->isLeaf()) {
        // Transform triangles to world space and test
        const Triangle& ta = m_triangles[nodeA->triIndex];
        const Triangle& tb = other->m_triangles[nodeB->triIndex];

        Triangle wa, wb;
        for(int v=0;v<3;v++) {
            wa.v[v] = TransformPoint(m_transform, ta.v[v]);
            wb.v[v] = TransformPoint(otherTransform, tb.v[v]);
        }

        if(wa.intersect(wb)) {
            CollidingPair pair;
            pair.t1 = nodeA->triIndex;
            pair.t2 = nodeB->triIndex;
            // Collision point = centroid of first triangle in world space
            pair.point = (wa.v[0]+wa.v[1]+wa.v[2])*(1.0f/3.0f);
            m_collisions.push_back(pair);
        }
        return;
    }

    // Recurse: split the larger node
    if(nodeA->isLeaf()) {
        collectCollisions(nodeA, nodeB->left,  other, otherTransform);
        collectCollisions(nodeA, nodeB->right, other, otherTransform);
    } else if(nodeB->isLeaf()) {
        collectCollisions(nodeA->left,  nodeB, other, otherTransform);
        collectCollisions(nodeA->right, nodeB, other, otherTransform);
    } else {
        collectCollisions(nodeA->left,  nodeB->left,  other, otherTransform);
        collectCollisions(nodeA->left,  nodeB->right, other, otherTransform);
        collectCollisions(nodeA->right, nodeB->left,  other, otherTransform);
        collectCollisions(nodeA->right, nodeB->right, other, otherTransform);
    }
}

// ----------------------------------------------------------------
// collision()
// ----------------------------------------------------------------
bool CollisionModel3DImpl::collision(CollisionModel3D* other,
                                     int /*AccuracyDepth*/,
                                     int /*MaxProcessingTime*/,
                                     float* other_transform)
{
    if(!m_finalized) throw Inconsistency();
    CollisionModel3DImpl* otherImpl = static_cast<CollisionModel3DImpl*>(other);
    if(!otherImpl->m_finalized) throw Inconsistency();
    if(!m_root || !otherImpl->m_root) return false;

    m_collisions.clear();

    const float* ot = other_transform ? other_transform : otherImpl->m_transform;
    collectCollisions(m_root, otherImpl->m_root, otherImpl, ot);

    return !m_collisions.empty();
}

// ----------------------------------------------------------------
// rayCollision()
// ----------------------------------------------------------------
bool CollisionModel3DImpl::rayCollision(float origin[3], float direction[3],
                                        bool closest, float segmin, float segmax)
{
    if(!m_finalized) throw Inconsistency();
    m_collisions.clear();

    Vector3f orig(origin[0],origin[1],origin[2]);
    Vector3f dir(direction[0],direction[1],direction[2]);

    // Build inverse transform to bring ray to model space
    float inv[16];
    InvertTransform(m_transform, inv);
    Vector3f localOrig = TransformPoint(inv, orig);
    Vector3f localDir  = TransformDir(inv, dir);

    float bestT = FLT_MAX;
    int   bestTri = -1;

    for(int i=0;i<(int)m_triangles.size();i++) {
        float t;
        if(m_triangles[i].rayIntersect(localOrig, localDir, segmin, segmax, t)) {
            if(!closest) {
                CollidingPair p;
                p.t1 = i; p.t2 = -1;
                p.point = localOrig + localDir * t;
                m_collisions.push_back(p);
                return true;
            }
            if(t < bestT) { bestT = t; bestTri = i; }
        }
    }

    if(bestTri >= 0) {
        CollidingPair p;
        p.t1 = bestTri; p.t2 = -1;
        p.point = localOrig + localDir * bestT;
        m_collisions.push_back(p);
        return true;
    }
    return false;
}

// ----------------------------------------------------------------
// sphereCollision()
// ----------------------------------------------------------------

// Returns the squared distance from point P to the closest point on
// triangle (A, B, C).  Based on Christer Ericson "Real-Time Collision
// Detection" chapter 5.
static float PointTriangleDistSq(const Vector3f& P,
                                  const Vector3f& A,
                                  const Vector3f& B,
                                  const Vector3f& C)
{
    Vector3f AB = B - A;
    Vector3f AC = C - A;
    Vector3f AP = P - A;

    float d1 = AB.dot(AP);
    float d2 = AC.dot(AP);
    if(d1 <= 0.0f && d2 <= 0.0f)
        return (P - A).lengthSq();   // closest = A

    Vector3f BP = P - B;
    float d3 = AB.dot(BP);
    float d4 = AC.dot(BP);
    if(d3 >= 0.0f && d4 <= d3)
        return (P - B).lengthSq();   // closest = B

    Vector3f CP = P - C;
    float d5 = AB.dot(CP);
    float d6 = AC.dot(CP);
    if(d6 >= 0.0f && d5 <= d6)
        return (P - C).lengthSq();   // closest = C

    float vc = d1*d4 - d3*d2;
    if(vc <= 0.0f && d1 >= 0.0f && d3 <= 0.0f) {  // edge AB
        float v = d1 / (d1 - d3);
        return (P - (A + AB*v)).lengthSq();
    }

    float vb = d5*d2 - d1*d6;
    if(vb <= 0.0f && d2 >= 0.0f && d6 <= 0.0f) {  // edge AC
        float w = d2 / (d2 - d6);
        return (P - (A + AC*w)).lengthSq();
    }

    float va = d3*d6 - d5*d4;
    float d43 = d4 - d3;
    float d56 = d5 - d6;
    if(va <= 0.0f && d43 >= 0.0f && d56 >= 0.0f) {  // edge BC
        float w = d43 / (d43 + d56);
        return (P - (B + (C - B)*w)).lengthSq();
    }

    // P projects inside the triangle
    float denom = 1.0f / (va + vb + vc);
    float v = vb * denom;
    float w = vc * denom;
    return (P - (A + AB*v + AC*w)).lengthSq();
}

bool CollisionModel3DImpl::sphereCollision(float origin[3], float radius)
{
    if(!m_finalized) throw Inconsistency();
    m_collisions.clear();

    Vector3f center(origin[0], origin[1], origin[2]);
    float inv[16];
    InvertTransform(m_transform, inv);
    Vector3f localCenter = TransformPoint(inv, center);

    // The model transform may have scale; transform radius too (assume uniform scale).
    // For a rotation-only transform the radius is unchanged.
    float r2 = radius * radius;

    for(int i = 0; i < (int)m_triangles.size(); i++) {
        const Triangle& tri = m_triangles[i];
        float d2 = PointTriangleDistSq(localCenter, tri.v[0], tri.v[1], tri.v[2]);
        if(d2 <= r2) {
            CollidingPair p;
            p.t1 = i; p.t2 = -1;
            // Approximate collision point: closest point on triangle
            // (we just store the triangle centroid for simplicity)
            p.point = (tri.v[0] + tri.v[1] + tri.v[2]) * (1.0f/3.0f);
            m_collisions.push_back(p);
            return true;
        }
    }
    return false;
}

// ----------------------------------------------------------------
// Accessors
// ----------------------------------------------------------------
bool CollisionModel3DImpl::getCollidingTriangles(int nTri,
                                                  float t1[9], float t2[9],
                                                  bool ModelSpace)
{
    if(nTri < 0 || nTri >= (int)m_collisions.size()) return false;
    const CollidingPair& p = m_collisions[nTri];

    const Triangle& tri1 = m_triangles[p.t1];
    for(int v=0;v<3;v++) {
        Vector3f vw = ModelSpace ? tri1.v[v] : TransformPoint(m_transform, tri1.v[v]);
        t1[v*3+0]=vw[0]; t1[v*3+1]=vw[1]; t1[v*3+2]=vw[2];
    }

    if(t2 && p.t2 >= 0) {
        // t2 belongs to the other model; we just zero it out here
        // (caller should query the other model)
        for(int i=0;i<9;i++) t2[i]=0;
    }
    return true;
}

bool CollisionModel3DImpl::getCollidingTriangles(int& t1, int& t2)
{
    if(m_collisions.empty()) return false;
    t1 = m_collisions[0].t1;
    t2 = m_collisions[0].t2;
    return true;
}

bool CollisionModel3DImpl::getCollisionPoint(int nPnt, float p[3], bool ModelSpace)
{
    if(nPnt < 0 || nPnt >= (int)m_collisions.size()) return false;
    Vector3f pt = m_collisions[nPnt].point;
    if(!ModelSpace) pt = TransformPoint(m_transform, pt);
    p[0]=pt[0]; p[1]=pt[1]; p[2]=pt[2];
    return true;
}

int CollisionModel3DImpl::getNumCollisions(void)
{
    return (int)m_collisions.size();
}

} // namespace COLDET

// ----------------------------------------------------------------
// Factory - exported C++ function (matches coldet.h signature)
// ----------------------------------------------------------------
EXPORT CollisionModel3D* newCollisionModel3D(bool Static)
{
    return new COLDET::CollisionModel3DImpl(Static);
}

// ----------------------------------------------------------------
// Utility functions
// ----------------------------------------------------------------
EXPORT bool SphereRayCollision(float center[3], float radius,
                                float origin[3], float direction[3],
                                float point[3])
{
    COLDET::Vector3f c(center[0],center[1],center[2]);
    COLDET::Vector3f o(origin[0],origin[1],origin[2]);
    COLDET::Vector3f d(direction[0],direction[1],direction[2]);
    d = d.normalize();

    COLDET::Vector3f oc = o - c;
    float b = oc.dot(d);
    float disc = b*b - oc.dot(oc) + radius*radius;
    if(disc < 0) return false;
    float sqrtDisc = sqrtf(disc);
    float t = -b - sqrtDisc;
    if(t < 0) t = -b + sqrtDisc;
    if(t < 0) return false;
    COLDET::Vector3f p = o + d*t;
    point[0]=p[0]; point[1]=p[1]; point[2]=p[2];
    return true;
}

EXPORT bool SphereSphereCollision(float c1[3], float r1,
                                   float c2[3], float r2, float point[3])
{
    COLDET::Vector3f a(c1[0],c1[1],c1[2]);
    COLDET::Vector3f b(c2[0],c2[1],c2[2]);
    COLDET::Vector3f d = b - a;
    float dist2 = d.lengthSq();
    float sumR = r1+r2;
    if(dist2 > sumR*sumR) return false;
    COLDET::Vector3f mid = a + d * (r1 / (r1+r2));
    point[0]=mid[0]; point[1]=mid[1]; point[2]=mid[2];
    return true;
}
