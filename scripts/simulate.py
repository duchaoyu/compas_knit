"""Simulation: inflate a knit membrane (Section 6.3).

The circular flat mesh, anchored on its boundary, inflated by a pressure. The knit is an orthotropic membrane, E1 along
the wale, the directional field, and E2 along the course, across it; here the wale runs along x. Writes
`<name>_deformed.obj`, `_stress.csv` and `_summary.json` to `<folder>/out/`.

Edit the inputs below and run
    python scripts/simulate.py
"""
import os

import numpy as np

from compas_knit import DATA
from compas_knit.simulation import simulate
from compas_knit.stripes import read_mesh

# MODIFY -----------------------------------------------------------------
folder = os.path.join(DATA, "circular_flat")
name = "circular_flat"

E_wale, E_course = 5000.0, 2500.0  # N/m, E1 along the wale, E2 along the course
nu = 0.198
pressure = 1000.0  # Pa
stretch_wale, stretch_course = 1.0, 1.0  # pre-strain of the fabrication, 1: none
wale = [1.0, 0.0, 0.0]  # the wale direction, the same at every vertex
# -------------------------------------------------------------------------


def boundary_vertices(faces):
    """The vertices on the boundary: those of the edges of one triangle only."""
    edges = np.sort(np.r_[faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]], axis=1)
    edges, count = np.unique(edges, axis=0, return_counts=True)
    return np.unique(edges[count == 1])


mesh = os.path.join(folder, name + ".obj")
V, F = read_mesh(mesh)
anchors = boundary_vertices(F)
field = np.tile(wale, (len(V), 1))

result = simulate(mesh, field, os.path.join(folder, "out", name), E_wale, E_course, nu, pressure,
                  stretch_wale=stretch_wale, stretch_course=stretch_course, fixed_vertices=anchors, mass=0.0)

s = result["summary"]
print("{} vertices, {} triangles, {} anchors on the boundary, p = {:.0f} Pa".format(len(V), len(F), len(anchors), pressure))
print("crown height {:.4f} m, max stress {:.0f} N/m, mean stress {:.0f} N/m ({})".format(
    s["crown_height"], s["max_stress"], s["mean_stress"], s["status"]))
print("results in", os.path.join(folder, "out"))
