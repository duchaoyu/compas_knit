#include "neighbours.h"

#include <algorithm>
#include <cmath>
#include <map>
#include <unordered_map>

using namespace geometrycentral;
using namespace geometrycentral::surface;

namespace
{
// finds which trajectory a point belongs to, by position
class PointLocator
{
public:
  PointLocator(double tol) : tol(tol), cell(100 * tol) {}

  void add(const Vector3& p, size_t id) { cells[key(p)].push_back({p, id}); }

  // the trajectory of the point within tol of p, or -1
  long find(const Vector3& p) const
  {
    auto [i, j, k] = key(p);
    for(long di = -1; di <= 1; ++di)
      for(long dj = -1; dj <= 1; ++dj)
        for(long dk = -1; dk <= 1; ++dk)
        {
          auto it = cells.find({i + di, j + dj, k + dk});
          if(it == cells.end())
            continue;
          for(const auto& [q, id]: it->second)
            if(norm(q - p) < tol)
              return id;
        }
    return -1;
  }

private:
  using Key = std::array<long, 3>;
  struct Hash
  {
    size_t operator()(const Key& k) const { return (k[0] * 73856093) ^ (k[1] * 19349663) ^ (k[2] * 83492791); }
  };
  Key key(const Vector3& p) const
  {
    return {(long)std::floor(p.x / cell), (long)std::floor(p.y / cell), (long)std::floor(p.z / cell)};
  }

  double tol, cell;
  std::unordered_map<Key, std::vector<std::pair<Vector3, size_t>>, Hash> cells;
};
} // namespace

std::vector<Link> findNeighbours(VertexPositionGeometry& geometry, const CornerData<double>& stripeValues,
                                 const FaceData<int>& stripeIndices, const std::vector<std::vector<Vector3>>& polylines,
                                 const std::vector<Vector3>& vertexField)
{
  SurfaceMesh& mesh = geometry.mesh;
  geometry.requireEdgeLengths();
  double meanEdge = 0;
  for(Edge e: mesh.edges())
    meanEdge += geometry.edgeLengths[e];
  meanEdge /= mesh.nEdges();

  PointLocator locator(1e-6 * meanEdge);
  for(size_t i = 0; i < polylines.size(); ++i)
    for(const Vector3& p: polylines[i])
      locator.add(p, i);

  // the trajectories crossing each edge, with the position of the crossing along the edge
  EdgeData<std::vector<std::pair<double, size_t>>> crossings(mesh);
  for(Face f: mesh.faces())
    for(Halfedge he: f.adjacentHalfedges())
    {
      // the same stripe values as the extraction, with the seam of a singular triangle on its last edge
      double a = stripeValues[he.corner()];
      double b = stripeValues[he.next().corner()] + (he.next() == f.halfedge() ? 2 * PI * stripeIndices[f] : 0);
      double lo = std::min(a, b), hi = std::max(a, b);
      Vector3 tail = geometry.vertexPositions[he.tailVertex()];
      Vector3 tip = geometry.vertexPositions[he.tipVertex()];
      Edge e = he.edge();
      Vector3 origin = geometry.vertexPositions[e.halfedge().tailVertex()];
      Vector3 axis = geometry.vertexPositions[e.halfedge().tipVertex()] - origin;
      for(int m = std::ceil(lo / (2 * PI)); 2 * PI * m < hi; ++m)
      {
        double t = (2 * PI * m - a) / (b - a);
        Vector3 p = tail + t * (tip - tail);
        long id = locator.find(p);
        if(id < 0)
          continue;
        double s = dot(p - origin, axis) / dot(axis, axis);
        auto& list = crossings[e];
        bool seen = false;
        for(const auto& [s2, id2]: list)
          seen = seen || (id2 == (size_t)id && std::abs(s2 - s) < 1e-9);
        if(!seen)
          list.push_back({s, (size_t)id});
      }
    }

  // consecutive crossings on an edge: the one further along the field comes next
  std::map<std::pair<size_t, size_t>, size_t> votes;
  for(Edge e: mesh.edges())
  {
    auto& list = crossings[e];
    std::sort(list.begin(), list.end());
    Vertex v0 = e.halfedge().tailVertex(), v1 = e.halfedge().tipVertex();
    Vector3 field = vertexField[v0.getIndex()] + vertexField[v1.getIndex()];
    Vector3 axis = geometry.vertexPositions[v1] - geometry.vertexPositions[v0];
    // along the edge, s grows towards v1: the later crossing is further along the field if the edge points with it
    bool forward = dot(axis, field) > 0;
    for(size_t k = 0; k + 1 < list.size(); ++k)
    {
      size_t first = list[k].second, second = list[k + 1].second;
      if(first == second)
        continue;
      if(forward)
        ++votes[{first, second}];
      else
        ++votes[{second, first}];
    }
  }

  std::vector<Link> links;
  for(const auto& [pair, n]: votes)
  {
    auto reverse = votes.find({pair.second, pair.first});
    size_t against = reverse == votes.end() ? 0 : reverse->second;
    if(n > against || (n == against && pair.first < pair.second))
      links.push_back({pair.first, pair.second, n});
  }
  return links;
}
