#include "remesh.h"

#include <algorithm>
#include <map>
#include <utility>
#include <vector>

int refine(Eigen::MatrixXd& V, Eigen::MatrixXi& F, Eigen::MatrixXd& field, double maxEdge)
{
  int passes = 0;
  for(; passes < 30; ++passes)
  {
    std::vector<Eigen::RowVectorXd> newV, newField;
    std::map<std::pair<int, int>, int> midpoints;
    auto midpoint = [&](int a, int b) -> int {
      auto key = std::minmax(a, b);
      auto it = midpoints.find(key);
      return it == midpoints.end() ? -1 : it->second;
    };

    // the midpoints of the edges too long
    for(int f = 0; f < F.rows(); ++f)
      for(int k = 0; k < 3; ++k)
      {
        int a = F(f, k), b = F(f, (k + 1) % 3);
        if((V.row(a) - V.row(b)).norm() <= maxEdge || midpoint(a, b) >= 0)
          continue;
        midpoints[std::minmax(a, b)] = V.rows() + newV.size();
        newV.push_back((V.row(a) + V.row(b)) / 2);
        Eigen::RowVectorXd fa = field.row(a), fb = field.row(b);
        if(fa.head(3).dot(fb.head(3)) < 0)
          fb = -fb;
        Eigen::RowVectorXd mean = (fa + fb) / 2;
        double length = (fa.head(3).norm() + fb.head(3).norm()) / 2;
        if(mean.head(3).norm() > 0)
          mean.head(3) *= length / mean.head(3).norm();
        newField.push_back(mean);
      }
    if(newV.empty())
      break;

    // cut the triangles around them, keeping their orientation
    std::vector<Eigen::RowVector3i> faces;
    for(int f = 0; f < F.rows(); ++f)
    {
      int t[3] = {F(f, 0), F(f, 1), F(f, 2)};
      int m[3], n = 0;
      for(int k = 0; k < 3; ++k)
        n += (m[k] = midpoint(t[k], t[(k + 1) % 3])) >= 0;
      if(n == 0)
        faces.push_back({t[0], t[1], t[2]});
      else if(n == 3)
      {
        faces.push_back({t[0], m[0], m[2]});
        faces.push_back({m[0], t[1], m[1]});
        faces.push_back({m[2], m[1], t[2]});
        faces.push_back({m[0], m[1], m[2]});
      }
      else if(n == 1)
      {
        int i = m[0] >= 0 ? 0 : m[1] >= 0 ? 1 : 2;
        int a = t[i], b = t[(i + 1) % 3], c = t[(i + 2) % 3];
        faces.push_back({a, m[i], c});
        faces.push_back({m[i], b, c});
      }
      else
      {
        // the edge (c, a) is whole, (a, b) and (b, c) are split
        int i = m[0] < 0 ? 0 : m[1] < 0 ? 1 : 2;
        int c = t[i], a = t[(i + 1) % 3], b = t[(i + 2) % 3];
        int mab = m[(i + 1) % 3], mbc = m[(i + 2) % 3];
        faces.push_back({mab, b, mbc});
        auto position = [&](int v) -> Eigen::RowVectorXd {
          return v < V.rows() ? Eigen::RowVectorXd(V.row(v)) : newV[v - V.rows()];
        };
        // the quad a, mab, mbc, c, cut along its shorter diagonal
        if((position(a) - position(mbc)).norm() < (position(mab) - position(c)).norm())
        {
          faces.push_back({a, mab, mbc});
          faces.push_back({a, mbc, c});
        }
        else
        {
          faces.push_back({a, mab, c});
          faces.push_back({mab, mbc, c});
        }
      }
    }

    int nV = V.rows();
    V.conservativeResize(nV + newV.size(), Eigen::NoChange);
    field.conservativeResize(nV + newField.size(), Eigen::NoChange);
    for(size_t i = 0; i < newV.size(); ++i)
    {
      V.row(nV + i) = newV[i];
      field.row(nV + i) = newField[i];
    }
    F.resize(faces.size(), 3);
    for(size_t f = 0; f < faces.size(); ++f)
      F.row(f) = faces[f];
  }
  return passes;
}
