#pragma once

#include <geometrycentral/utilities/vector3.h>

#include <functional>
#include <vector>

// Divide a polyline into stitches: from its first point, each next point is the first point further along the
// polyline at straight-line distance `width` from the previous one, as Grasshopper's DivideDistance does.
// The part of the polyline after the last full stitch is dropped.
std::vector<geometrycentral::Vector3> divideDistance(const std::vector<geometrycentral::Vector3>& polyline, double width);

// As above, with the stitch width a function of where the stitch starts, for a pre-strain that varies over the mesh.
std::vector<geometrycentral::Vector3> divideDistance(const std::vector<geometrycentral::Vector3>& polyline,
                                                     const std::function<double(const geometrycentral::Vector3&)>& width);

// Reverse the polylines that run against field x normal, so that all of them run the same way across the field.
// positions, normals and field are per mesh vertex; the field has to have consistent signs.
// Returns the number of polylines reversed.
size_t orientAcrossField(std::vector<std::vector<geometrycentral::Vector3>>& polylines,
                         const std::vector<geometrycentral::Vector3>& positions,
                         const std::vector<geometrycentral::Vector3>& normals,
                         const std::vector<geometrycentral::Vector3>& field);

