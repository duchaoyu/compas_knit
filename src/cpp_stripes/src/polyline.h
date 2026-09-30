// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.
//
// Taken from shrink-morph (https://github.com/DavidJourdan/shrink-morph),
// src/path_extraction.h, Copyright (c) David Jourdan.

#pragma once

#include <geometrycentral/utilities/vector3.h>

#include <array>
#include <vector>

// chain the isoline segments returned by extractPolylinesFromStripePattern into polylines
std::vector<std::vector<geometrycentral::Vector3>> edgeToPolyline(const std::vector<geometrycentral::Vector3>& points,
                                                                  const std::vector<std::array<size_t, 2>>& edges);
