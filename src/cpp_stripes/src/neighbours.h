#pragma once

#include <geometrycentral/surface/vertex_position_geometry.h>

#include <array>
#include <vector>

// A link between two neighbouring trajectories: `next` lies after `prev` along the field.
// `edges` is the number of mesh edges on which they are adjacent, a measure of the length they share.
struct Link
{
  size_t prev;
  size_t next;
  size_t edges;
};

// Find the neighbouring trajectories. Along a mesh edge, the isolines cross in stripe order, so two trajectories
// with consecutive crossings on an edge are neighbours, and the one further along the field comes next.
//
// polylines are the trajectories as extracted, their points on the mesh edges; vertexField is the field per vertex,
// with consistent signs. Where two trajectories are found in both orders, the order found on more edges is kept.
std::vector<Link> findNeighbours(geometrycentral::surface::VertexPositionGeometry& geometry,
                                 const geometrycentral::surface::CornerData<double>& stripeValues,
                                 const geometrycentral::surface::FaceData<int>& stripeIndices,
                                 const std::vector<std::vector<geometrycentral::Vector3>>& polylines,
                                 const std::vector<geometrycentral::Vector3>& vertexField);
