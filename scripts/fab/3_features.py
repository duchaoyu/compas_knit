"""A line feature along the boundary of the mesh, for when there is none drawn in Rhino.

Splits the boundary of the mesh at its corners and writes the piece furthest to the left (the lowest x), where the
cable runs, as a line to `<folder>/features/cable.obj`. `scripts/fab/4_pattern.py` reads the features in that folder, points
and lines, e.g. also `bdr_anchors.obj` exported from Rhino.

Edit the inputs below and run
    python scripts/fab/3_features.py
"""
import os

import numpy as np

from compas_knit import DATA
from compas_knit.pattern import boundary_polylines
from compas_knit.pattern import write_feature

# MODIFY -----------------------------------------------------------------
folder = os.path.join(DATA, "2part_remesh2")
name = "2part_remesh2"
# -------------------------------------------------------------------------

pieces = boundary_polylines(os.path.join(folder, name + ".obj"))
cable = min(pieces, key=lambda p: p[:, 0].mean())

os.makedirs(os.path.join(folder, "features"), exist_ok=True)
path = os.path.join(folder, "features", "cable.obj")
write_feature(path, lines=[cable])
print("cable: a line of {} points, {:.1f} long, {}".format(len(cable), np.linalg.norm(np.diff(cable, axis=0), axis=1).sum(), path))
