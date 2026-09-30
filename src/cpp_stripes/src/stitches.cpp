#include "stitches.h"

#include <algorithm>
#include <cmath>
#include <limits>

using geometrycentral::Vector3;

std::vector<Vector3> divideDistance(const std::vector<Vector3>& polyline, double width)
{
  std::vector<Vector3> stitches;
  if(polyline.empty() || width <= 0)
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
  size_t reversed = 0;
  for(auto& polyline: polylines)
  {
    // sum over the segments of their component along field x normal at the nearest vertex
    double along = 0;
    for(size_t i = 0; i + 1 < polyline.size(); ++i)
    {
      Vector3 mid = (polyline[i] + polyline[i + 1]) / 2;
      size_t nearest = 0;
      double best = std::numeric_limits<double>::max();
      for(size_t v = 0; v < positions.size(); ++v)
      {
        double d = norm2(positions[v] - mid);
        if(d < best)
          best = d, nearest = v;
      }
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

