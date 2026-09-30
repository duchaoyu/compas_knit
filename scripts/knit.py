"""Master script: mesh + directional field -> knitting trajectories.

Edit the inputs below and run
    python scripts/knit.py
"""
import os

from compas_knit.stripes import generate_stripes
from compas_knit.stripes import read_neighbours
from compas_knit.stripes import read_singularities
from compas_knit.viewer import view_stripes

# MODIFY -----------------------------------------------------------------
folder = "/Users/duch/Documents/PhD/knit/2024_prototypes/2part/anisotropic"
name = "2part_remesh2"

stitch_height = 2.297  # st_h at zero stress, in the units of the mesh
stretch = 1.0  # pre-strain stretch factor along the wale, 1.0 = none
stitch_width = 3.54  # st_w, in the units of the mesh (Grasshopper's dis): one point per stitch, None = no division
view = True  # show the mesh and the trajectories, from the top
# -------------------------------------------------------------------------

mesh_path = os.path.join(folder, name + ".obj")
field_path = os.path.join(folder, name + "_vertex_directional_field.txt")
out_dir = os.path.join(folder, "out")  # keeps the files from earlier runs in `folder` untouched

trajectories = generate_stripes(mesh_path, field_path, stitch_height, stretch=stretch, stitch_width=stitch_width, out_dir=out_dir)
print("{} trajectories, spacing {}".format(len(trajectories), 2 * stitch_height / stretch))

if view:
    # coloured from the first trajectory in the knitting order to the last
    # and the singularities, where trajectories end
    links = read_neighbours(os.path.join(out_dir, name + "_neighbours.txt"))
    singularities = read_singularities(os.path.join(out_dir, name + "_singularities.txt"))
    view_stripes(os.path.join(out_dir, name + "_remesh.obj"), trajectories, links, singularities)
