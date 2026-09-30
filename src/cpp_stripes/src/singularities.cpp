#include "singularities.h"

#include <cmath>
#include <limits>
#include <map>

using namespace geometrycentral;
using namespace geometrycentral::surface;

namespace
{
struct Crossing
{
  size_t point; // index into points
  int level;    // the stripe, as the multiple of 2*pi the stripe value crosses
  int edge;     // 0, 1 or 2, from f.halfedge()
};

// index of the point at position p, adding it if there is none within tol
size_t findOrAddPoint(std::vector<Vector3>& points, const Vector3& p, double tol)
{
  for(size_t i = 0; i < points.size(); ++i)
    if(norm(points[i] - p) < tol)
      return i;
  points.push_back(p);
  return points.size() - 1;
}
} // namespace

size_t connectOnStripeSingularities(VertexPositionGeometry& geometry, const CornerData<double>& stripeValues,
                                    const FaceData<int>& stripeIndices, const FaceData<Vector3>& faceField,
                                    std::vector<Vector3>& points, std::vector<std::array<size_t, 2>>& edges)
{
  SurfaceMesh& mesh = geometry.mesh;
  size_t looseEnds = 0;

  for(Face f: mesh.faces())
  {
    int n = stripeIndices[f];
    if(n == 0)
      continue;

    // the crossings on the edges, labelled with the edge from corner 2 to corner 0 as the seam,
    // the same lifting as geometry-central's connectIsolinesOnSingularities
    std::vector<Crossing> crossings;
    double tol = 0;
    for(Halfedge he: f.adjacentHalfedges())
      tol = std::max(tol, 1e-6 * norm(geometry.vertexPositions[he.tipVertex()] - geometry.vertexPositions[he.tailVertex()]));
    int k = 0;
    for(Halfedge he: f.adjacentHalfedges())
    {
      double a = stripeValues[he.corner()];
      double b = stripeValues[he.next().corner()] + (he.next() == f.halfedge() ? 2 * PI * n : 0);
      double lo = std::min(a, b), hi = std::max(a, b);
      Vector3 tail = geometry.vertexPositions[he.tailVertex()];
      Vector3 tip = geometry.vertexPositions[he.tipVertex()];
      for(int m = std::ceil(lo / (2 * PI)); 2 * PI * m < hi; ++m)
      {
        double t = (2 * PI * m - a) / (b - a);
        crossings.push_back({findOrAddPoint(points, tail + t * (tip - tail), tol), m, k});
      }
      ++k;
    }

    // taking edge s - 1 as the seam instead shifts the labels of the edges before it by n
    auto offset = [&](const Crossing& c1, const Crossing& c2) {
      return std::abs(dot(points[c1.point] - points[c2.point], faceField[f]));
    };
    double bestScore = std::numeric_limits<double>::max();
    std::vector<std::array<size_t, 2>> bestPairs;
    size_t bestLoose = 0;
    for(int s = 0; s < 3; ++s)
    {
      std::map<int, std::vector<Crossing>> stripes;
      for(const Crossing& c: crossings)
        stripes[c.level + (c.edge < s ? n : 0)].push_back(c);

      double score = 0;
      std::vector<std::array<size_t, 2>> pairs;
      size_t loose = 0;
      for(auto& [level, cs]: stripes)
      {
        if(cs.size() == 1)
        {
          ++loose;
          continue;
        }
        // two crossings are joined; of three, the two closest along the field, and the third ends
        size_t i = 0, j = 1;
        for(size_t p = 0; p < cs.size(); ++p)
          for(size_t q = p + 1; q < cs.size(); ++q)
            if(offset(cs[p], cs[q]) < offset(cs[i], cs[j]))
              i = p, j = q;
        score += offset(cs[i], cs[j]);
        pairs.push_back({cs[i].point, cs[j].point});
        loose += cs.size() - 2;
      }
      if(score < bestScore)
      {
        bestScore = score;
        bestPairs = pairs;
        bestLoose = loose;
      }
    }
    edges.insert(edges.end(), bestPairs.begin(), bestPairs.end());
    looseEnds += bestLoose;
  }
  return looseEnds;
}
