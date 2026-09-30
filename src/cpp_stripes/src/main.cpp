// Stripe pattern trajectories from a user-defined directional field.
//
// Reads a triangle mesh and a per-vertex directional field (one "x y z" world-space
// vector per line, in mesh vertex order), and extracts equally spaced knitting
// trajectories as the isolines of a stripe pattern [Knoppel et al. 2015] aligned
// with the field. Ported from shrink-morph src/main2.cpp.
//
// usage: stripes <mesh.obj> --spacing <s> --stitch-width <w> [options]
//
// outputs, written next to the mesh unless --out-dir is given:
//   <name>_remesh.obj   the mesh rescaled to --size (unchanged with --size 0), which the trajectories live on
//   <name>_tri_path.txt one polyline per line, "x,y,z; x,y,z; ...", all running the same way, field x normal
//   <name>_tri_path_recons.txt  the trajectories divided into stitches, one point per stitch
//   <name>_neighbours.txt  one link per line, "a b n": trajectory b comes after a along the field, adjacent on n mesh edges
//   <name>_singularities.txt  one singular triangle per line, "stripe|field x y z index", at the triangle centre

#include "polyline.h"
#include "singularities.h"
#include "neighbours.h"
#include "stitches.h"

#include <geometrycentral/surface/manifold_surface_mesh.h>
#include <geometrycentral/surface/meshio.h>
#include <geometrycentral/surface/stripe_patterns.h>
#include <geometrycentral/surface/vertex_position_geometry.h>

#include <polyscope/curve_network.h>
#include <polyscope/polyscope.h>
#include <polyscope/surface_mesh.h>

#include <igl/readOBJ.h>
#include <igl/writeOBJ.h>

#include <complex>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

using namespace geometrycentral;
using namespace geometrycentral::surface;

namespace fs = std::filesystem;

const char* USAGE = R"(usage: stripes <mesh.obj> --spacing <s> --stitch-width <w> [options]

  --spacing <s>        distance between trajectories, in units of the rescaled mesh (required)
  --stitch-width <w>   width of a stitch, in units of the rescaled mesh (required): the trajectories are divided into
                       stitches, one point per stitch, written to <name>_tri_path_recons.txt
  --size <mm>          rescale the mesh so its largest extent is <mm> (default 1000), 0 keeps the mesh units
  --field <file>       per-vertex directional field (default <name>_vertex_directional_field.txt)
  --out-dir <dir>      where to write the outputs (default: the mesh directory)
  --face-field <file>  also write the field averaged onto each face, one "x y z" per face
  --view               show the field and the trajectories in polyscope
)";

Eigen::MatrixXd loadMatrixFromFile(const std::string& filePath)
{
  std::ifstream file(filePath);

  if(!file.is_open())
  {
    std::cerr << "Could not open the file - '" << filePath << "'" << std::endl;
    return Eigen::MatrixXd();
  }

  std::vector<double> matrixEntries;
  int numRows = 0;
  std::string line;

  while(getline(file, line))
  {
    std::istringstream iss(line);
    double num;
    while(iss >> num)
      matrixEntries.push_back(num);
    ++numRows;
  }

  if(numRows == 0)
  {
    std::cerr << "Matrix is empty or not properly formatted" << std::endl;
    return Eigen::MatrixXd();
  }
  int numCols = matrixEntries.size() / numRows;

  Eigen::MatrixXd mat(numRows, numCols);
  for(int i = 0; i < numRows; ++i)
    for(int j = 0; j < numCols; ++j)
      mat(i, j) = matrixEntries[i * numCols + j];

  return mat;
}

int main(int argc, char** argv)
{
  std::string meshPath, fieldPath, outDir, faceFieldPath;
  double spacing = -1;
  double stitchWidth = 0;
  double size = 1000;
  bool view = false;

  for(int i = 1; i < argc; ++i)
  {
    std::string arg = argv[i];
    auto value = [&]() -> std::string {
      if(i + 1 >= argc)
      {
        std::cerr << arg << " needs a value\n" << USAGE;
        std::exit(EXIT_FAILURE);
      }
      return argv[++i];
    };
    if(arg == "--spacing")
      spacing = std::stod(value());
    else if(arg == "--size")
      size = std::stod(value());
    else if(arg == "--field")
      fieldPath = value();
    else if(arg == "--out-dir")
      outDir = value();
    else if(arg == "--face-field")
      faceFieldPath = value();
    else if(arg == "--stitch-width")
      stitchWidth = std::stod(value());
    else if(arg == "--view")
      view = true;
    else if(arg == "-h" || arg == "--help")
    {
      std::cout << USAGE;
      return EXIT_SUCCESS;
    }
    else if(meshPath.empty() && arg[0] != '-')
      meshPath = arg;
    else
    {
      std::cerr << "unknown argument " << arg << "\n" << USAGE;
      return EXIT_FAILURE;
    }
  }
  if(meshPath.empty() || spacing <= 0 || stitchWidth <= 0)
  {
    std::cerr << USAGE;
    return EXIT_FAILURE;
  }

  fs::path mesh_file(meshPath);
  std::string name = mesh_file.stem().string();
  fs::path dir = outDir.empty() ? mesh_file.parent_path() : fs::path(outDir);
  if(fieldPath.empty())
    fieldPath = (mesh_file.parent_path() / (name + "_vertex_directional_field.txt")).string();
  std::string remeshPath = (dir / (name + "_remesh.obj")).string();
  std::string polylinePath = (dir / (name + "_tri_path.txt")).string();
  std::string stitchPath = (dir / (name + "_tri_path_recons.txt")).string();
  std::string neighbourPath = (dir / (name + "_neighbours.txt")).string();
  std::string singularityPath = (dir / (name + "_singularities.txt")).string();

  Eigen::MatrixXd V;
  Eigen::MatrixXi F;
  if(!igl::readOBJ(meshPath, V, F))
  {
    std::cerr << "Could not read the mesh - '" << meshPath << "'" << std::endl;
    return EXIT_FAILURE;
  }

  // resize mesh so that its largest extent is `size`
  double scale_factor = (V.colwise().maxCoeff() - V.colwise().minCoeff()).maxCoeff();
  if(size > 0)
    V *= size / scale_factor;
  std::cout << "The coefficiency is: " << scale_factor << std::endl;

  igl::writeOBJ(remeshPath, V, F);

  std::unique_ptr<ManifoldSurfaceMesh> mesh;
  std::unique_ptr<VertexPositionGeometry> geometry;
  std::tie(mesh, geometry) = readManifoldSurfaceMesh(remeshPath);

  VertexData<double> frequencies(*mesh, 1.0 / spacing);

  geometry->requireVertexTangentBasis();
  VertexData<Vector3> vBasisX(*mesh);
  VertexData<Vector3> vBasisY(*mesh);
  for(Vertex v: mesh->vertices())
  {
    vBasisX[v] = geometry->vertexTangentBasis[v][0];
    vBasisY[v] = geometry->vertexTangentBasis[v][1];
  }

  auto VD = loadMatrixFromFile(fieldPath);
  std::cout << VD.rows() << "," << VD.cols() << std::endl;
  std::cout << mesh->nVertices() << std::endl;
  if(VD.rows() != (long)mesh->nVertices() || VD.cols() < 3)
  {
    std::cerr << "The field needs one \"x y z\" row per mesh vertex - '" << fieldPath << "'" << std::endl;
    return EXIT_FAILURE;
  }

  // project the world-space field into each vertex tangent plane
  VertexData<Vector2> originalField(*mesh);
  for(Vertex v: mesh->vertices())
  {
    int index = v.getIndex();
    Vector3 refVec{VD(index, 0), VD(index, 1), VD(index, 2)};
    Vector2 dir = {dot(refVec, vBasisX[v]), dot(refVec, vBasisY[v])};
    originalField[v] = unit(dir);
  }

  // square the complex representation to get a line field (2-RoSy): theta and theta + pi are the same axis
  VertexData<Vector2> directionField(*mesh);
  for(Vertex v: mesh->vertices())
  {
    size_t i = v.getIndex();
    std::complex<double> z(originalField[i].x, originalField[i].y);
    std::complex<double> zRoot = std::pow(z, 2);
    directionField[v] = {real(zRoot), imag(zRoot)};
  }

  CornerData<double> stripeValues;
  FaceData<int> stripeIndices, fieldIndices;
  std::tie(stripeValues, stripeIndices, fieldIndices) = computeStripePattern(*geometry, frequencies, directionField);

  // the input field in each face, with the corner vectors flipped to agree before averaging (it is a line field)
  FaceData<Vector3> lineField(*mesh);
  for(Face f: mesh->faces())
  {
    Vector3 first{0.0, 0.0, 0.0}, sum{0.0, 0.0, 0.0};
    for(Vertex v: f.adjacentVertices())
    {
      Vector3 u{VD(v.getIndex(), 0), VD(v.getIndex(), 1), VD(v.getIndex(), 2)};
      if(norm(first) == 0)
        first = u;
      sum += dot(u, first) < 0 ? -u : u;
    }
    lineField[f] = normalize(sum);
  }

  // geometry-central's own linking through the singular triangles joins neighbouring trajectories, see singularities.h
  auto [points, edges] =
      extractPolylinesFromStripePattern(*geometry, stripeValues, stripeIndices, fieldIndices, directionField, false);
  size_t nSingular = 0;
  for(Face f: mesh->faces())
    nSingular += stripeIndices[f] != 0;
  size_t looseEnds = connectOnStripeSingularities(*geometry, stripeValues, stripeIndices, lineField, points, edges);
  std::cout << nSingular << " stripe singularities, " << looseEnds << " trajectories end at one" << std::endl;
  auto polylines = edgeToPolyline(points, edges);

  // make all the trajectories run the same way, field x normal, as the Grasshopper definition did by flipping
  // the curves that did not start at a hand-placed plane
  geometry->requireVertexNormals();
  std::vector<Vector3> positions, normals, field;
  for(Vertex v: mesh->vertices())
  {
    positions.push_back(geometry->vertexPositions[v]);
    normals.push_back(geometry->vertexNormals[v]);
    field.push_back({VD(v.getIndex(), 0), VD(v.getIndex(), 1), VD(v.getIndex(), 2)});
  }
  size_t nReversed = orientAcrossField(polylines, positions, normals, field);
  std::cout << "Reversed " << nReversed << " trajectories to run the same way across the field" << std::endl;

  auto writePolylines = [](const std::string& path, const std::vector<std::vector<Vector3>>& polylines) {
    std::ofstream file(path);
    file << std::setprecision(10);
    for(const auto& polyline: polylines)
    {
      for(size_t i = 0; i < polyline.size(); ++i)
      {
        const auto& point = polyline[i];
        file << point[0] << "," << point[1] << "," << point[2];
        if(i < polyline.size() - 1)
          file << "; ";
      }
      file << "\n";
    }
  };
  // divide the trajectories into stitches; those shorter than one stitch are left out of all the outputs,
  // so that a trajectory has the same index in each of them
  std::vector<std::vector<Vector3>> stitches, kept;
  size_t nStitches = 0;
  for(const auto& polyline: polylines)
  {
    auto divided = divideDistance(polyline, stitchWidth);
    if(divided.size() < 2)
      continue;
    nStitches += divided.size();
    stitches.push_back(divided);
    kept.push_back(polyline);
  }
  std::cout << polylines.size() - kept.size() << " trajectories shorter than a stitch left out" << std::endl;
  polylines = kept;

  writePolylines(polylinePath, polylines);
  std::cout << "Wrote " << polylines.size() << " trajectories to " << polylinePath << std::endl;
  writePolylines(stitchPath, stitches);
  std::cout << "Wrote " << nStitches << " stitches to " << stitchPath << std::endl;

  // which trajectory comes after which along the field
  auto links = findNeighbours(*geometry, stripeValues, stripeIndices, polylines, field);
  {
    std::ofstream file(neighbourPath);
    for(const Link& link: links)
      file << link.prev << " " << link.next << " " << link.edges << "\n";
  }
  std::cout << "Wrote " << links.size() << " links between neighbouring trajectories to " << neighbourPath << std::endl;

  // the singular triangles, at their centres: of the stripe pattern, where a trajectory ends, and of the field
  {
    std::ofstream file(singularityPath);
    file << std::setprecision(10);
    size_t nField = 0;
    for(Face f: mesh->faces())
    {
      Vector3 c{0.0, 0.0, 0.0};
      for(Vertex v: f.adjacentVertices())
        c += geometry->vertexPositions[v] / 3.0;
      if(stripeIndices[f] != 0)
        file << "stripe " << c.x << " " << c.y << " " << c.z << " " << stripeIndices[f] << "\n";
      if(fieldIndices[f] != 0)
      {
        file << "field " << c.x << " " << c.y << " " << c.z << " " << fieldIndices[f] << "\n";
        ++nField;
      }
    }
    std::cout << "Wrote " << nSingular << " stripe and " << nField << " field singularities to " << singularityPath
              << std::endl;
  }

  // the input field averaged onto each face, in world coordinates
  FaceData<Vector3> faceField(*mesh);
  for(Face f: mesh->faces())
  {
    Vector3 sum{0.0, 0.0, 0.0};
    for(Vertex v: f.adjacentVertices())
    {
      int index = v.getIndex();
      sum += Vector3{VD(index, 0), VD(index, 1), VD(index, 2)};
    }
    faceField[f] = sum / 3.0;
  }

  if(!faceFieldPath.empty())
  {
    std::ofstream faceFieldFile(faceFieldPath);
    faceFieldFile << std::fixed << std::setprecision(6);
    for(Face f: mesh->faces())
    {
      Vector3 v = faceField[f];
      faceFieldFile << v.x << " " << v.y << " " << v.z << "\n";
    }
    std::cout << "Wrote face directional field to " << faceFieldPath << std::endl;
  }

  if(!view)
    return EXIT_SUCCESS;

  polyscope::init();

  auto* psMesh = polyscope::registerSurfaceMesh("my_mesh", geometry->inputVertexPositions,
                                                mesh->getFaceVertexList(), polyscopePermutations(*mesh));
  psMesh->addVertexTangentVectorQuantity("VF", directionField, vBasisX, vBasisY, 1);
  psMesh->addVertexTangentVectorQuantity("OF", originalField, vBasisX, vBasisY, 2);
  psMesh->addFaceVectorQuantity("Face field", faceField);

  for(size_t i = 0; i < polylines.size(); ++i)
  {
    std::vector<std::vector<size_t>> polylineIndices;
    for(size_t k = 0; k + 1 < polylines[i].size(); k++)
      polylineIndices.push_back({k, k + 1});
    auto curveNet = polyscope::registerCurveNetwork("Polyline " + std::to_string(i), polylines[i], polylineIndices);
    curveNet->setRadius(0.001);
  }

  polyscope::show();

  return EXIT_SUCCESS;
}
