"""Step 1: mesh + directional field -> knitting trajectories.

Writes, to `<folder>/out/`, the trajectories, their stitches, which trajectory comes after which, and the
singularities, then `scripts/fab/4_pattern.py` turns them into the knitting pattern.

Edit the inputs below and run
    python scripts/fab/2_trajectories.py
"""
import os

from compas_knit import DATA
from compas_knit.stripes import generate_stripes
from compas_knit.stripes import read_neighbours
from compas_knit.stripes import read_singularities
from compas_knit.stripes import read_trajectories
from compas_knit.viewer import view_stripes

# MODIFY -----------------------------------------------------------------
folder = os.path.join(DATA, "pringle")  # or e.g. os.path.join(DATA, "2part_remesh2"), in mm
name = "pringle"  # 500 mm across, its field from scripts/fab/1.2_edit_field.py


stitch_height = 2.297  # st_h at zero stress, in the units of the mesh, here mm
stretch_wale = 1.05  # pre-strain stretch factor along the wale (the field): the stitch height is divided by it; 1.0 = none
stretch_course = 1.05  # pre-strain stretch factor along the course (across the field): the stitch width is divided by it
stitch_width = 3.54  # st_w, in the units of the mesh (Grasshopper's dis): one point per stitch
max_edge = None  # refine the mesh to edges no longer than this; None = the stitch width
recompute = True  # False: read the trajectories already in <folder>/out/, if there; True: after changing the inputs above
view = True  # show the mesh and the trajectories, from the top
# -------------------------------------------------------------------------

mesh_path = os.path.join(folder, name + ".obj")
field_path = os.path.join(folder, name + "_vertex_directional_field.txt")
out_dir = os.path.join(folder, "out")  # next to the inputs, ignored by git

stitches_path = os.path.join(out_dir, name + "_tri_path_recons.txt")
if recompute or not os.path.isfile(stitches_path):
    trajectories = generate_stripes(
        mesh_path,
        field_path,
        stitch_height,
        stitch_width,
        stretch_wale=stretch_wale,
        stretch_course=stretch_course,
        max_edge=max_edge,
        out_dir=out_dir,
    )
    print("{} trajectories, spacing {}, stitch width {}".format(len(trajectories), 2 * stitch_height / stretch_wale, stitch_width / stretch_course))
else:
    # as computed before: the inputs above are not read, set recompute = True after changing them
    trajectories = read_trajectories(stitches_path)
    print("{} trajectories read from {}".format(len(trajectories), stitches_path))

if view:
    # coloured from the first trajectory in the knitting order to the last,
    # and the singularities, where trajectories end
    links = read_neighbours(os.path.join(out_dir, name + "_neighbours.txt"))
    singularities = read_singularities(os.path.join(out_dir, name + "_singularities.txt"))
    # on the input mesh: the refined one has the same surface, only many more triangles to draw
    view_stripes(mesh_path, trajectories, links, singularities)
