// smooth_field: the smoothest line field on a mesh (Knoppel et al. 2013, "Globally optimal direction fields"), as a
// per-vertex directional field for stripes.
//
// usage: smooth_field <mesh.obj> <out_field.txt> [--boundary | --along-boundary]
//
//   --boundary         aligned with the boundary, across it, as geometry-central aligns it
//   --along-boundary   the same turned by 90 degrees in the surface, along the boundary: as smooth, the wales along
//                      the boundary
//   otherwise free at the boundary, the smoothest of all
//
// Writes one "x y z" unit vector per vertex, in the order of the .obj, a line field: the sign is arbitrary.

#include "geometrycentral/surface/direction_fields.h"
#include "geometrycentral/surface/manifold_surface_mesh.h"
#include "geometrycentral/surface/surface_mesh_factories.h"
#include "geometrycentral/surface/vertex_position_geometry.h"

#include <igl/readOBJ.h>

#include <complex>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <string>

using namespace geometrycentral;
using namespace geometrycentral::surface;

int main(int argc, char* argv[])
{
  std::string meshPath, outPath;
  bool boundary = false, along = false;
  for(int i = 1; i < argc; ++i)
  {
    std::string arg = argv[i];
    if(arg == "--boundary")
      boundary = true;
    else if(arg == "--along-boundary")
      boundary = along = true;
    else if(meshPath.empty())
      meshPath = arg;
    else
      outPath = arg;
  }
  if(meshPath.empty() || outPath.empty())
  {
    std::cerr << "usage: smooth_field <mesh.obj> <out_field.txt> [--boundary | --along-boundary]\n";
    return EXIT_FAILURE;
  }

  Eigen::MatrixXd V;
  Eigen::MatrixXi F;
  if(!igl::readOBJ(meshPath, V, F))
  {
    std::cerr << "Could not read the mesh - '" << meshPath << "'\n";
    return EXIT_FAILURE;
  }
  std::unique_ptr<ManifoldSurfaceMesh> mesh;
  std::unique_ptr<VertexPositionGeometry> geometry;
  std::tie(mesh, geometry) = makeManifoldSurfaceMeshAndGeometry(V, F);

  // a line field: the complex number squared, theta and theta + pi the same
  VertexData<Vector2> field = boundary ? computeSmoothestBoundaryAlignedVertexDirectionField(*geometry, 2)
                                       : computeSmoothestVertexDirectionField(*geometry, 2);

  geometry->requireVertexTangentBasis();
  std::ofstream out(outPath);
  out << std::setprecision(10);
  for(Vertex v: mesh->vertices())
  {
    std::complex<double> z(field[v].x, field[v].y);
    double angle = std::arg(z) / 2 + (along ? M_PI / 2 : 0.0);
    Vector3 d = std::cos(angle) * geometry->vertexTangentBasis[v][0] + std::sin(angle) * geometry->vertexTangentBasis[v][1];
    out << d.x << " " << d.y << " " << d.z << "\n";
  }
  std::cout << "Wrote the smoothest line field" << (along ? " along the boundary" : boundary ? " across the boundary" : "")
            << ", " << mesh->nVertices() << " vertices, to " << outPath << "\n";
  return EXIT_SUCCESS;
}
