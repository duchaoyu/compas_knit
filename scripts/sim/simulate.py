"""Simulation: inflate a knit membrane (Section 6.3).

The circular flat mesh, anchored on its boundary, inflated by a pressure. The knit is an orthotropic membrane, E_wale
along the knitting direction, read per vertex from `<field_name>_vertex_directional_field.txt` as for the
trajectories, and E_course across it. Two fields come with the mesh: `circular_flat`, the wale along y, and
`circular_flat_2part`, the two-pattern disc, turning from about 40 to 90 degrees from x. Writes
`<field_name>_deformed.obj`, `_stress.csv` and `_summary.json` to `<folder>/out/`, then shows the simulated geometry over the original one, shaded by the stress, with a checkbox for
the field.

Edit the inputs below and run
    python scripts/sim/simulate.py
"""
import os

import numpy as np

from compas_knit import DATA
from compas_knit.simulation import simulate
from compas_knit.stripes import read_mesh
from compas_knit.viewer import view_simulation

# MODIFY -----------------------------------------------------------------
folder = os.path.join(DATA, "circular_flat")
name = "circular_flat"
field_name = "circular_flat_2part"  # the field <field_name>_vertex_directional_field.txt; circular_flat: along y

E_course = 5000.0  # N/m, along the course, across the directional field
E_wale = 12500.0  # N/m, along the wale, the knitting direction of the directional field
nu = 0.198
pressure = 1000.0  # Pa
stretch_wale, stretch_course = 1.1, 1.1  # pre-strain of the fabrication, 1: none

quantity = "von_mises"  # the stress to shade by: principal_1, principal_2, T_wale_Nm, T_course_Nm, S11, S22, S12
show_field = False  # start the viewer with the directional field shown
# -------------------------------------------------------------------------


def boundary_vertices(faces):
    """The vertices on the boundary: those of the edges of one triangle only."""
    edges = np.sort(np.r_[faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]], axis=1)
    edges, count = np.unique(edges, axis=0, return_counts=True)
    return np.unique(edges[count == 1])


mesh = os.path.join(folder, name + ".obj")
field = os.path.join(folder, field_name + "_vertex_directional_field.txt")  # the knitting direction, the wale, per vertex
V, F = read_mesh(mesh)
anchors = boundary_vertices(F)

out = os.path.join(folder, "out", field_name)
result = simulate(mesh, field, out, E_wale, E_course, nu, pressure,
                  stretch_wale=stretch_wale, stretch_course=stretch_course, fixed_vertices=anchors, mass=0.0)

s = result["summary"]
print("{} vertices, {} triangles, {} anchors on the boundary, p = {:.0f} Pa".format(len(V), len(F), len(anchors), pressure))
print("E_wale {:.0f} N/m, E_course {:.0f} N/m, nu {}, field {}".format(E_wale, E_course, nu, field_name))
print("crown height {:.4f} m, max stress {:.0f} N/m, mean stress {:.0f} N/m ({})".format(
    s["crown_height"], s["max_stress"], s["mean_stress"], s["status"]))
print("results in", os.path.join(folder, "out"))

view_simulation(mesh, out + "_deformed.obj", out + "_stress.csv", quantity=quantity, field=field, show_field=show_field)
