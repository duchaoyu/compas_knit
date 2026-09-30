#pragma once

#include <geometrycentral/utilities/vector3.h>

#include <array>
#include <vector>

// A link between two neighbouring trajectories: `next` lies after `prev` along the field.
// `hits` is the number of segments of either that see the other as their neighbour, a measure of the length they share.
struct Link
{
  size_t prev;
  size_t next;
  size_t hits;
};

// Find the neighbouring trajectories. From the middle of each segment, the line along the field is followed both ways,
// in the tangent plane, to the first trajectory it crosses within 1.5 spacings: the one ahead along the field comes
// next, the one behind before. This does not depend on the mesh, however fine or coarse.
//
// positions, normals and field are per mesh vertex; the field has to have consistent signs. Where two trajectories are
// found in both orders, the order found more often is kept.
std::vector<Link> findNeighbours(const std::vector<std::vector<geometrycentral::Vector3>>& polylines,
                                 const std::vector<geometrycentral::Vector3>& positions,
                                 const std::vector<geometrycentral::Vector3>& normals,
                                 const std::vector<geometrycentral::Vector3>& field, double spacing);
