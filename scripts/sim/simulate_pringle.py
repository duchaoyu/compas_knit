"""Simulation: the pringle, its whole boundary fixed, under a thin layer of concrete (Section 6.3).

The pringle of the fabrication steps, `data/pringle/`, its mesh and its direction field, the knitting direction: the
knit with the stitches of the fabrication, stretched by the same factors, its boundary fixed, and a layer of concrete
cast on it, its weight G = area x density x thickness x g, the area of each triangle of the knit, straight down, put on
in steps of 10, 50 and 100 %. The mesh is in millimetres, knit_sim in metres. Writes `pringle_concrete_*` to
`<folder>/out/`, and shows the knit under the concrete over the knit as it was, shaded by the stress.

Edit the inputs below and run
    python scripts/sim/simulate_pringle.py
"""
import os

import numpy as np

from compas_knit import DATA
from compas_knit.simulation import simulate
from compas_knit.stripes import read_mesh
from compas_knit.viewer import view_simulation

# MODIFY -----------------------------------------------------------------
folder = os.path.join(DATA, "pringle")
name = "pringle"
units = 0.001  # the mesh in mm, knit_sim in m

E_course = 5000.0  # N/m, along the course, across the directional field
E_wale = 12500.0  # N/m, along the wale, the knitting direction of the directional field
nu = 0.198
stretch_wale, stretch_course = 1.05, 1.05  # pre-strain of the fabrication, as in scripts/fab/2_trajectories.py

concrete_density = 2400.0  # kg/m3
concrete_thickness = 0.01  # m

quantity = "von_mises"  # the stress to shade by: principal_1, principal_2, T_wale_Nm, T_course_Nm, S11, S22, S12
show_field = False  # start the viewer with the directional field shown
# -------------------------------------------------------------------------


def boundary_vertices(faces):
    """The vertices on the boundary: those of the edges of one triangle only."""
    edges = np.sort(np.r_[faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]], axis=1)
    edges, count = np.unique(edges, axis=0, return_counts=True)
    return np.unique(edges[count == 1])


V, F = read_mesh(os.path.join(folder, name + ".obj"))
V = V * units
field = os.path.join(folder, name + "_vertex_directional_field.txt")  # the knitting direction, the wale, per vertex
anchors = boundary_vertices(F)
concrete = concrete_density * concrete_thickness  # kg/m2

print("{}: {} vertices, {} triangles, {} fixed on the boundary; {:.0f} x {:.0f} x {:.0f} mm".format(
    name, len(V), len(F), len(anchors), *(1000 * np.ptp(V, axis=0))))
print("E_wale {:.0f} N/m, E_course {:.0f} N/m, nu {}, stretch {} / {}".format(E_wale, E_course, nu, stretch_wale, stretch_course))
print("concrete {:.0f} mm, {:.1f} kg/m2, {:.0f} Pa".format(1000 * concrete_thickness, concrete, 9.8 * concrete))

out = os.path.join(folder, "out", "{}_concrete_{:g}".format(name, concrete))
result = simulate((V, F), field, out, E_wale, E_course, nu, 0.0, stretch_wale=stretch_wale,
                  stretch_course=stretch_course, fixed_vertices=anchors, mass=0.0, added_mass=concrete)
s = result["summary"]
d = result["vertices"] - V
print("concrete {:.0f} N; largest displacement {:.2f} mm, down {:.2f} mm; von Mises stress max {:.0f} N/m, mean {:.0f} N/m ({}, residual {:.1e})".format(
    s["added_weight"], 1000 * np.linalg.norm(d, axis=1).max(), -1000 * d[:, 2].min(), s["max_stress"], s["mean_stress"],
    s["status"], s["residual"]))
print("results in", os.path.join(folder, "out"))

view_simulation((V, F), out + "_deformed.obj", out + "_stress.csv", quantity=quantity, field=field, show_field=show_field)
