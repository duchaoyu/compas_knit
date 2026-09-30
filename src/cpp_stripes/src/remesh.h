#pragma once

#include <Eigen/Core>

// Split the edges longer than maxEdge at their midpoints until none is left, the triangles around them cut into
// two, three or four. The surface stays the same, the original vertices keep their indices, and each new vertex
// gets the mean of the field at the ends of its edge, flipped to agree first. Returns the number of passes.
//
// At a singularity of the stripe pattern a trajectory ends at the edge of the singular triangle, about half an
// edge from the singularity, so the edge length sets the gap left in the knit there.
int refine(Eigen::MatrixXd& V, Eigen::MatrixXi& F, Eigen::MatrixXd& field, double maxEdge);
