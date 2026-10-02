"""Step 1.2: make or edit the directional field, three ways.

"direction": one direction, e.g. y, projected into the surface at every vertex: the wale along it.

"axis": the wale turns around an axis, the courses lie in the planes through it. For the hemisphere, the axis along
y, the courses are the meridians from one end to the other; lowered below the rim, by `axis_offset`, the courses no
longer meet in a point at each end but end along a band of the rim, so the short rows do not all end in one point.

"hold": the field is held along a curve, e.g. the middle curve y = 0, at a direction, and is the smoothest line field
everywhere else, free at the rim.

Writes the mesh and the field as a new example, `<folder_out>/<name_out>.obj` and
`<name_out>_vertex_directional_field.txt`, for `scripts/fab/2_trajectories.py`, and shows it, held vertices in red.

Edit the inputs below and run
    python scripts/fab/1.2_edit_field.py
"""
import os
import shutil

import numpy as np

from compas_knit import DATA
from compas_knit.field import axis_field
from compas_knit.field import project_field
from compas_knit.field import smoothest_field
from compas_knit.stripes import read_mesh

# MODIFY -----------------------------------------------------------------
folder = os.path.join(DATA, "pringle")  # the mesh <folder>/<name>.obj
name = "pringle"

mode = "direction"  # "direction", "axis" or "hold"

# direction: the wale along it, projected into the surface; for the pringle, its long axis, y
direction = (0.0, 1.0, 0.0)

# axis: along y, through the centre, lowered by axis_offset below the rim; 0: the courses meet in the two end points
axis_offset = 0.2  # m, about the width of the band at each end where the courses end
axis_direction = (0.0, 1.0, 0.0)

# hold
held_axis, held_value = 1, 0.0  # the curve where the field is held: y (axis 1) = 0
held_direction = (0.0, 1.0, 0.0)  # the field there, projected into the surface: the knitting direction along y

name_out = "pringle"  # the example to write, in DATA/<name_out>/; the same as name: the field next to the mesh
view = True  # show the field
# -------------------------------------------------------------------------

V, F = read_mesh(os.path.join(folder, name + ".obj"))

held = np.zeros(0, dtype=int)
if mode == "direction":
    field = project_field(V, F, direction)
    print("{} vertices, the field along {} projected into the surface, zero at {}".format(
        len(V), direction, int((np.linalg.norm(field, axis=1) == 0).sum())))
elif mode == "axis":
    field = axis_field(V, F, (0.0, 0.0, -axis_offset), axis_direction)
    print("{} vertices, the field around the axis {} through (0, 0, {})".format(len(V), axis_direction, -axis_offset))
else:
    # the curve: the vertices within half an edge of it
    edges = np.linalg.norm(V[F] - V[np.roll(F, 1, axis=1)], axis=2)
    held = np.flatnonzero(np.abs(V[:, held_axis] - held_value) < 0.5 * edges.mean())
    directions = project_field(V, F, held_direction)[held]
    ok = np.linalg.norm(directions, axis=1) > 0  # not where the direction is along the normal
    held, directions = held[ok], directions[ok]
    field = smoothest_field(V, F, held, directions)
    print("{} vertices, the field held at {} on the curve, the smoothest elsewhere".format(len(V), len(held)))

folder_out = os.path.join(DATA, name_out)
os.makedirs(folder_out, exist_ok=True)
mesh_out = os.path.join(folder_out, name_out + ".obj")
if os.path.abspath(mesh_out) != os.path.abspath(os.path.join(folder, name + ".obj")):
    shutil.copyfile(os.path.join(folder, name + ".obj"), mesh_out)
field_path = os.path.join(folder_out, name_out + "_vertex_directional_field.txt")
np.savetxt(field_path, field, fmt="%12.6f")
print("wrote", field_path)

if view:
    from compas_knit.viewer import view_field

    view_field(os.path.join(folder_out, name_out + ".obj"), field_path, points=V[held])
