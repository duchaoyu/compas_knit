// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.
//
// Taken from shrink-morph (https://github.com/DavidJourdan/shrink-morph),
// src/path_extraction.cpp, Copyright (c) David Jourdan.

#include "polyline.h"

#include <cassert>

using geometrycentral::Vector3;

std::vector<std::vector<Vector3>> edgeToPolyline(const std::vector<Vector3>& points,
                                                 const std::vector<std::array<size_t, 2>>& edges)
{
  // build up connectivity information (neighoring indices on polyline)
  std::vector<std::vector<size_t>> connectivity(points.size());

  for(auto& edge: edges)
  {
    connectivity[edge[0]].push_back(edge[1]);
    connectivity[edge[1]].push_back(edge[0]);
  }

  std::vector<std::vector<Vector3>> polylines;
  std::vector<bool> visited(points.size(), false);
  for(size_t i = 0; i < points.size(); ++i)
    if(!visited[i])
    {
      std::vector<Vector3> isoline;

      size_t nbOfPieces = connectivity[i].size();
      if(nbOfPieces == 0)
        continue; // ignore isolated points

      size_t currIdx = connectivity[i][0];
      size_t prevIdx = i;
      bool open = true;
      if(nbOfPieces == 2) // walk to the end of the line (if open)
      {
        while(connectivity[currIdx].size() == 2 && currIdx != i)
        {
          if(connectivity[currIdx][0] == prevIdx)
          {
            prevIdx = currIdx;
            currIdx = connectivity[currIdx][1];
          }
          else
          {
            prevIdx = currIdx;
            currIdx = connectivity[currIdx][0];
          }
        }
        open = currIdx != i;
        std::swap(prevIdx, currIdx); // revert the order to start from this end
      }

      isoline.push_back(points[prevIdx]);
      visited[prevIdx] = true;

      while((connectivity[currIdx].size() == 2 && open) || (currIdx != i && !open))
      {
        isoline.push_back(points[currIdx]);
        visited[currIdx] = true;

        if(connectivity[currIdx][0] == prevIdx)
        {
          prevIdx = currIdx;
          currIdx = connectivity[currIdx][1];
        }
        else
        {
          prevIdx = currIdx;
          currIdx = connectivity[currIdx][0];
        }
      }
      assert(connectivity[currIdx].size() == 1 || currIdx == i && !open);

      isoline.push_back(points[currIdx]);
      visited[currIdx] = true;

      polylines.push_back(isoline);
    }
  return polylines;
}
