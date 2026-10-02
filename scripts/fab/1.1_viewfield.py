"""Step 1.1: the input mesh and its directional field: look at it, and make it the field per vertex of the next steps.

Inputs, in <folder>:
    <name>.obj                          the mesh, triangles
    <field_file>                        the directional field, the knitting direction (the wale): one "x y z" per
                                        face, as the faces of the mesh, e.g. from Grasshopper, or one per vertex

A field per face is averaged onto the vertices, the faces around each weighted by their area, their signs made to
agree, and written as <name>_vertex_directional_field.txt, which scripts/fab/2_trajectories.py reads. A field per vertex
is that file already. Shows the field, from the top.

Edit the inputs below and run
    python scripts/fab/1.1_viewfield.py
"""
import os

import numpy as np

from compas_knit import DATA
from compas_knit.field import face_to_vertex_field
from compas_knit.field import read_field
from compas_knit.stripes import read_mesh
from compas_knit.viewer import view_field

# MODIFY -----------------------------------------------------------------
folder = os.path.join(DATA, "pringle")  # or e.g. os.path.join(DATA, "2part_remesh2"), in mm
name = "pringle"
field_file = name + "_face_directional_field.txt"  # per face; or name + "_vertex_directional_field.txt", per vertex
view = True  # show the field as given
# -------------------------------------------------------------------------

mesh_path = os.path.join(folder, name + ".obj")
field_path = os.path.join(folder, field_file)
vertex_field_path = os.path.join(folder, name + "_vertex_directional_field.txt")

V, F = read_mesh(mesh_path)
field, on = read_field(field_path, V, F)
print("{}: {} vertices, {} faces; the field {}, one per {}".format(name, len(V), len(F), field_file, on[:-1]))

if on == "faces":
    np.savetxt(vertex_field_path, face_to_vertex_field(V, F, field), fmt="%12.6f")
    print("wrote", vertex_field_path)

if view:
    view_field(mesh_path, field_path)
