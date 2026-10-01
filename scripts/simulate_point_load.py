"""Simulation: a point load on a knit membrane (Section 6.3).

The circular flat mesh, anchored on its boundary, pre-strained by the stretch factors, without pressure, and a force at
a point, fixed in size and direction, put on in steps of 10, 50 and 100 %. The force goes to the vertex nearest the
point, or is shared equally by the vertices within `load_radius` of it. A membrane has no bending
stiffness, so under a load on a single vertex the dent depends on the size of the mesh; a radius, the size of what
pushes on the knit, makes it independent of it. Writes `<field_name>_point_load_*` to `<folder>/out/`, and shows the
result, the load drawn as a red line on the flat and on the simulated knit.

Edit the inputs below and run
    python scripts/simulate_point_load.py
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
stretch_wale, stretch_course = 1.1, 1.1  # pre-strain of the fabrication; above 1, so the flat knit is taut

load_point = (0.0, 0.0)  # m, where the load is, in plan
load_force = (0.0, 0.0, -100.0)  # N, fixed in size and direction; -z: down
load_radius = 0.0  # m, shared by the vertices within it; 0: the nearest vertex only

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

distance = np.linalg.norm(V[:, :2] - load_point, axis=1)
loaded = np.flatnonzero(distance <= load_radius) if load_radius > 0 else []
if not len(loaded):
    loaded = [int(np.argmin(distance))]
point_loads = [(v, np.array(load_force) / len(loaded)) for v in loaded]

print("{} vertices, {} triangles, {} anchors on the boundary".format(len(V), len(F), len(anchors)))
print("E_wale {:.0f} N/m, E_course {:.0f} N/m, nu {}, field {}".format(E_wale, E_course, nu, field_name))
print("point load {} N at {} m, on {} vertices".format(tuple(load_force), tuple(load_point), len(loaded)))

out = os.path.join(folder, "out", "{}_point_load_{:g}".format(field_name, np.linalg.norm(load_force)))
result = simulate(mesh, field, out, E_wale, E_course, nu, 0.0, stretch_wale=stretch_wale, stretch_course=stretch_course,
                  fixed_vertices=anchors, mass=0.0, point_loads=point_loads)
s = result["summary"]
print("height at the load {:.4f} m, lowest point {:.4f} m, max stress {:.0f} N/m, mean stress {:.0f} N/m ({})".format(
    result["vertices"][loaded, 2].mean(), result["vertices"][:, 2].min(), s["max_stress"], s["mean_stress"], s["status"]))
print("results in", os.path.join(folder, "out"))

view_simulation(mesh, out + "_deformed.obj", out + "_stress.csv", quantity=quantity, field=field, show_field=show_field,
                loads=point_loads)
