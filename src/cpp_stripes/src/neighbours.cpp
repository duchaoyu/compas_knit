#include "neighbours.h"

#include <cmath>
#include <limits>
#include <map>
#include <unordered_map>

using geometrycentral::Vector3;

namespace
{
using Key = std::array<long, 3>;
struct Hash
{
  size_t operator()(const Key& k) const { return (k[0] * 73856093) ^ (k[1] * 19349663) ^ (k[2] * 83492791); }
};

// items at points, found by position, in cells of a given size
template <typename T>
class Grid
{
public:
  Grid(double cell) : cell(cell) {}
  void add(const Vector3& p, const T& item) { cells[key(p)].push_back(item); }
  template <typename F>
  void around(const Vector3& p, int reach, F visit) const
  {
    Key k = key(p);
    for(long i = -reach; i <= reach; ++i)
      for(long j = -reach; j <= reach; ++j)
        for(long l = -reach; l <= reach; ++l)
        {
          auto it = cells.find({k[0] + i, k[1] + j, k[2] + l});
          if(it != cells.end())
            for(const T& item: it->second)
              visit(item);
        }
  }

private:
  Key key(const Vector3& p) const
  {
    return {(long)std::floor(p.x / cell), (long)std::floor(p.y / cell), (long)std::floor(p.z / cell)};
  }
  double cell;
  std::unordered_map<Key, std::vector<T>, Hash> cells;
};
} // namespace

std::vector<Link> findNeighbours(const std::vector<std::vector<Vector3>>& polylines,
                                 const std::vector<Vector3>& positions, const std::vector<Vector3>& normals,
                                 const std::vector<Vector3>& field, double spacing)
{
  // the nearest vertex, for the normal and the field at a point
  double meanStep = 0;
  size_t nSteps = 0;
  for(const auto& p: polylines)
    for(size_t i = 0; i + 1 < p.size(); ++i, ++nSteps)
      meanStep += norm(p[i + 1] - p[i]);
  meanStep /= std::max<size_t>(nSteps, 1);
  Grid<size_t> vertices(spacing);
  for(size_t v = 0; v < positions.size(); ++v)
    vertices.add(positions[v], v);
  auto nearestVertex = [&](const Vector3& p) {
    size_t best = 0;
    double d = std::numeric_limits<double>::max();
    for(int reach = 1; reach < 64 && d == std::numeric_limits<double>::max(); reach *= 2)
      vertices.around(p, reach, [&](size_t v) {
        double dv = norm2(positions[v] - p);
        if(dv < d)
          d = dv, best = v;
      });
    return best;
  };

  // the segments of all trajectories, by their middle
  struct Segment
  {
    size_t trajectory, index;
  };
  Grid<Segment> segments(spacing);
  for(size_t t = 0; t < polylines.size(); ++t)
    for(size_t i = 0; i + 1 < polylines[t].size(); ++i)
      segments.add((polylines[t][i] + polylines[t][i + 1]) / 2, {t, i});
  // segments longer than a spacing reach further than their middle: widen the search
  int reach = 1 + (int)std::ceil(2 * meanStep / spacing);

  std::map<std::pair<size_t, size_t>, size_t> votes;
  for(size_t t = 0; t < polylines.size(); ++t)
    for(size_t i = 0; i + 1 < polylines[t].size(); ++i)
    {
      Vector3 p = (polylines[t][i] + polylines[t][i + 1]) / 2;
      size_t v = nearestVertex(p);
      Vector3 n = normals[v];
      Vector3 f = field[v] - dot(field[v], n) * n;
      if(norm(f) == 0)
        continue;
      f = normalize(f);
      Vector3 c = cross(n, f); // across the field, in the tangent plane

      // the first trajectory crossed ahead along the field, and behind
      double ahead = 1.5 * spacing, behind = -1.5 * spacing;
      long next = -1, prev = -1;
      segments.around(p, reach, [&](const Segment& s) {
        if(s.trajectory == t)
          return;
        const Vector3& q0 = polylines[s.trajectory][s.index];
        const Vector3& q1 = polylines[s.trajectory][s.index + 1];
        double u0 = dot(q0 - p, c), u1 = dot(q1 - p, c);
        if(u0 * u1 > 0 || u0 == u1)
          return;
        double w = u0 / (u0 - u1);
        Vector3 q = q0 + w * (q1 - q0);
        // off the tangent plane by less than the distance along the field: the same sheet of the surface
        double along = dot(q - p, f);
        if(std::abs(dot(q - p, n)) > std::abs(along))
          return;
        if(along > 0 && along < ahead)
          ahead = along, next = s.trajectory;
        if(along < 0 && along > behind)
          behind = along, prev = s.trajectory;
      });
      if(next >= 0)
        ++votes[{t, (size_t)next}];
      if(prev >= 0)
        ++votes[{(size_t)prev, t}];
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
