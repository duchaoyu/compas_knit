#pragma once

#include <geometrycentral/surface/vertex_position_geometry.h>

#include <array>
#include <vector>

// Connect the isolines through the triangles holding a singularity of the stripe pattern,
// which extractPolylinesFromStripePattern(..., false) leaves empty.
//
// Going around such a triangle the stripe value comes back shifted by 2*pi*index, so the crossings
// on its edges can be labelled by stripe level in three ways, one per edge taken as the seam.
// Crossings with the same label are on the same stripe and are joined. Of the three labellings,
// the one whose joins run most across the field is kept. The crossings left without a partner
// are where a stripe ends.
//
// faceField is the direction field in each face, in world coordinates, any sign.
// points and edges are the output of extractPolylinesFromStripePattern and are added to.
// Returns the number of stripe ends left in the singular triangles.
size_t connectOnStripeSingularities(geometrycentral::surface::VertexPositionGeometry& geometry,
                                    const geometrycentral::surface::CornerData<double>& stripeValues,
                                    const geometrycentral::surface::FaceData<int>& stripeIndices,
                                    const geometrycentral::surface::FaceData<geometrycentral::Vector3>& faceField,
                                    std::vector<geometrycentral::Vector3>& points,
                                    std::vector<std::array<size_t, 2>>& edges);
