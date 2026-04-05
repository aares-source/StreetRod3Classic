/*   ColDet - C++ 3D Collision Detection Library
 *   Copyright (C) 2000   Amir Geva
 *
 * Internal bounding box (OBB/AABB) definitions for the BVH tree.
 */
#ifndef COLDET_BOX_H
#define COLDET_BOX_H

#include "cdmath3d.h"
#include <vector>

namespace COLDET {

// A triangle stored in the model
struct Triangle
{
    Vector3f v[3];    // Vertices in model space

    Triangle() {}
    Triangle(const Vector3f& a, const Vector3f& b, const Vector3f& c)
    { v[0]=a; v[1]=b; v[2]=c; }

    bool intersect(const Triangle& other) const;

    // Ray-triangle intersection (Moller-Trumbore)
    bool rayIntersect(const Vector3f& origin, const Vector3f& dir,
                      float segmin, float segmax, float& t) const;

    Vector3f center() const
    { return (v[0]+v[1]+v[2])*(1.0f/3.0f); }
};

// An axis-aligned bounding box node in the BVH tree
struct BoxNode
{
    Vector3f      min, max;       // AABB in model space
    BoxNode*      left;
    BoxNode*      right;
    int           triIndex;       // -1 if not a leaf; index into model's triangle array otherwise
    int           numTris;        // number of triangles in this leaf (usually 1)

    BoxNode() : left(nullptr), right(nullptr), triIndex(-1), numTris(0) {}
    ~BoxNode()
    {
        delete left;
        delete right;
    }

    bool isLeaf() const { return left==nullptr && right==nullptr; }

    bool overlaps(const BoxNode& other,
                  const float myTransform[16],
                  const float otherTransform[16]) const;
};

// Build a BVH tree from a set of triangles
BoxNode* BuildBox(const std::vector<Triangle>& tris,
                  const std::vector<int>& indices);

} // namespace COLDET

#endif // COLDET_BOX_H
