"""Simulation: inflate a knit membrane, then cast a thin layer of concrete on it (Section 6.3).

The circular flat mesh, anchored on its boundary, inflated by a pressure as in `scripts/simulate.py`; then, the pressure
held, a layer of concrete cast on the inflated surface: its weight G = area x density x thickness x g, the area of each
triangle on the inflated surface, acting straight down, put on in steps of 10, 50 and 100 %. The knit is simulated with and without the concrete, and the one with is shown, shaded by the stress.
Writes `<field_name>_concrete_*` to `<folder>/out/`.

Edit the inputs below and run
    python scripts/simulate_inf_concrete.py
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


mesh = os.path.join(folder, name + ".obj")
field = os.path.join(folder, field_name + "_vertex_directional_field.txt")  # the knitting direction, the wale, per vertex
V, F = read_mesh(mesh)
anchors = boundary_vertices(F)
concrete = concrete_density * concrete_thickness  # kg/m2

print("{} vertices, {} triangles, {} anchors on the boundary, p = {:.0f} Pa".format(len(V), len(F), len(anchors), pressure))
print("E_wale {:.0f} N/m, E_course {:.0f} N/m, nu {}, field {}".format(E_wale, E_course, nu, field_name))
print("concrete {:.0f} mm, {:.1f} kg/m2, {:.0f} Pa".format(1000 * concrete_thickness, concrete, 9.8 * concrete))
results = {}
for label, added in (("inflated", 0.0), ("with concrete", concrete)):
    out = os.path.join(folder, "out", "{}_concrete_{:g}".format(field_name, added))
    r = simulate(mesh, field, out, E_wale, E_course, nu, pressure, stretch_wale=stretch_wale, stretch_course=stretch_course,
                 fixed_vertices=anchors, mass=0.0, added_mass=added)
    s = r["summary"]
    print("{:14s} crown height {:.4f} m, max stress {:.0f} N/m, mean stress {:.0f} N/m, concrete {:.0f} N ({})".format(
        label, s["crown_height"], s["max_stress"], s["mean_stress"], s["added_weight"], s["status"]))
    results[label] = (out, r)

drop = results["inflated"][1]["vertices"][:, 2] - results["with concrete"][1]["vertices"][:, 2]
print("the concrete lowers the crown by {:.1f} mm, the surface by up to {:.1f} mm".format(
    1000 * (results["inflated"][1]["summary"]["crown_height"] - results["with concrete"][1]["summary"]["crown_height"]),
    1000 * drop.max()))
print("results in", os.path.join(folder, "out"))

out = results["with concrete"][0]
view_simulation(mesh, out + "_deformed.obj", out + "_stress.csv", quantity=quantity, field=field, show_field=show_field)
