#include "stitches.h"

#include <algorithm>
#include <cmath>
#include <array>
#include <limits>
#include <unordered_map>

using geometrycentral::Vector3;

std::vector<Vector3> divideDistance(const std::vector<Vector3>& polyline, double width)
{
  if(width <= 0)
    return {};
  return divideDistance(polyline, [width](const Vector3&) { return width; });
}

std::vector<Vector3> divideDistance(const std::vector<Vector3>& polyline, const std::function<double(const Vector3&)>& widthAt)
{
  std::vector<Vector3> stitches;
  if(polyline.empty())
    return stitches;

  Vector3 p = polyline[0];
  stitches.push_back(p);
  // the search for the next point starts at parameter t of segment i, where the previous one was found
  size_t i = 0;
  double t = 0;
  while(i + 1 < polyline.size())
  {
    Vector3 a = polyline[i], b = polyline[i + 1];
    Vector3 d = b - a;
    double width = widthAt(p);
    // |a + s d - p| = width, the larger root is where the segment leaves the sphere around p
    double A = dot(d, d), B = 2 * dot(d, a - p), C = dot(a - p, a - p) - width * width;
    double disc = B * B - 4 * A * C;
    if(A > 0 && disc >= 0)
    {
      double s = (-B + std::sqrt(disc)) / (2 * A);
      if(s >= t && s <= 1)
      {
        p = a + s * d;
        stitches.push_back(p);
        t = s;
        continue;
      }
    }
    ++i;
    t = 0;
  }
  return stitches;
}

size_t orientAcrossField(std::vector<std::vector<Vector3>>& polylines, const std::vector<Vector3>& positions,
                         const std::vector<Vector3>& normals, const std::vector<Vector3>& field)
{
  // the nearest vertex, exactly, from a uniform grid: rings of cells are searched outwards until no cell
  // further out can hold a closer vertex (a brute-force scan over all vertices per segment took minutes)
  struct CellHash { size_t operator()(const std::array<long, 3>& k) const { return (k[0] * 73856093) ^ (k[1] * 19349663) ^ (k[2] * 83492791); } };
  std::unordered_map<std::array<long, 3>, std::vector<size_t>, CellHash> cells;
  Vector3 lo{1e300, 1e300, 1e300}, hi{-1e300, -1e300, -1e300};
  for(const Vector3& p: positions)
    for(int c = 0; c < 3; ++c)
      lo[c] = std::min(lo[c], p[c]), hi[c] = std::max(hi[c], p[c]);
  double cell = std::max({hi.x - lo.x, hi.y - lo.y, hi.z - lo.z}) / std::max(1.0, std::cbrt((double)positions.size()));
  if(!(cell > 0))
    cell = 1.0;
  auto cellOf = [&](const Vector3& p) { return std::array<long, 3>{(long)std::floor(p.x / cell), (long)std::floor(p.y / cell), (long)std::floor(p.z / cell)}; };
  for(size_t v = 0; v < positions.size(); ++v)
    cells[cellOf(positions[v])].push_back(v);
  auto nearestTo = [&](const Vector3& p) {
    auto k = cellOf(p);
    size_t nearest = 0;
    double best = std::numeric_limits<double>::max();
    for(long r = 0;; ++r)
    {
      // a vertex in ring r is at least (r - 1) cells away
      if(r >= 1 && best < std::numeric_limits<double>::max() && (r - 1) * cell > std::sqrt(best))
        break;
      if(r > 0 && cells.size() > 0 && r * cell > 2 * (norm(hi - lo) + norm(p - lo)) + 2 * cell)
        break;
      for(long i = -r; i <= r; ++i)
        for(long j = -r; j <= r; ++j)
          for(long l = -r; l <= r; ++l)
          {
            if(std::max({std::abs(i), std::abs(j), std::abs(l)}) != r)
              continue;
            auto it = cells.find({k[0] + i, k[1] + j, k[2] + l});
            if(it == cells.end())
              continue;
            for(size_t v: it->second)
            {
              double d = norm2(positions[v] - p);
              if(d < best || (d == best && v < nearest))
                best = d, nearest = v;
            }
          }
    }
    return nearest;
  };

  size_t reversed = 0;
  for(auto& polyline: polylines)
  {
    // sum over the segments of their component along field x normal at the nearest vertex
    double along = 0;
    for(size_t i = 0; i + 1 < polyline.size(); ++i)
    {
      size_t nearest = nearestTo((polyline[i] + polyline[i + 1]) / 2);
      along += dot(polyline[i + 1] - polyline[i], cross(field[nearest], normals[nearest]));
    }
    if(along < 0)
    {
      std::reverse(polyline.begin(), polyline.end());
      ++reversed;
    }
  }
  return reversed;
}
