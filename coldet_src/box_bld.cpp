/*   ColDet - C++ 3D Collision Detection Library
 *   Copyright (C) 2000   Amir Geva
 *
 * BVH tree construction.
 */
#include "box.h"
#include <vector>
#include <algorithm>
#include <float.h>

namespace COLDET {

// Build a BVH node from a set of triangles
BoxNode* BuildBox(const std::vector<Triangle>& tris,
                  const std::vector<int>& indices)
{
    BoxNode* node = new BoxNode();

    // Compute AABB
    node->min = Vector3f( FLT_MAX, FLT_MAX, FLT_MAX);
    node->max = Vector3f(-FLT_MAX,-FLT_MAX,-FLT_MAX);
    for(int idx : indices) {
        const Triangle& t = tris[idx];
        for(int v=0; v<3; v++) {
            for(int k=0; k<3; k++) {
                if(t.v[v][k] < node->min[k]) node->min[k] = t.v[v][k];
                if(t.v[v][k] > node->max[k]) node->max[k] = t.v[v][k];
            }
        }
    }

    if(indices.size() == 1) {
        // Leaf node
        node->triIndex = indices[0];
        node->numTris  = 1;
        return node;
    }

    // Find longest axis
    float dx = node->max[0]-node->min[0];
    float dy = node->max[1]-node->min[1];
    float dz = node->max[2]-node->min[2];
    int axis = 0;
    if(dy>dx && dy>dz) axis=1;
    else if(dz>dx && dz>dy) axis=2;

    // Sort by centroid along axis
    std::vector<int> sorted = indices;
    std::sort(sorted.begin(), sorted.end(), [&](int a, int b){
        return tris[a].center()[axis] < tris[b].center()[axis];
    });

    size_t mid = sorted.size()/2;
    std::vector<int> leftIdx(sorted.begin(), sorted.begin()+mid);
    std::vector<int> rightIdx(sorted.begin()+mid, sorted.end());

    node->left  = BuildBox(tris, leftIdx);
    node->right = BuildBox(tris, rightIdx);
    node->triIndex = -1;

    return node;
}

} // namespace COLDET
