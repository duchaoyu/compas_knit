"""Master script: mesh + directional field -> knitting trajectories.

Edit the inputs below and run
    python scripts/knit.py
"""
import os

from compas_knit import DATA
from compas_knit.stripes import generate_stripes
from compas_knit.stripes import read_neighbours
from compas_knit.stripes import read_singularities
from compas_knit.pattern import knitting_pattern
from compas_knit.pattern import read_features
from compas_knit.pattern import write_pattern
from compas_knit.viewer import view_stripes

# MODIFY -----------------------------------------------------------------
folder = os.path.join(DATA, "2part_remesh2")  # or e.g. os.path.join(DATA, "fabsim", "D5"), in metres
name = "2part_remesh2"

stitch_height = 2.297  # st_h at zero stress, in the units of the mesh
stretch = 1.0  # pre-strain stretch factor along the wale, 1.0 = none
stitch_width = 3.54  # st_w, in the units of the mesh (Grasshopper's dis): one point per stitch
view = False  # show the mesh and the trajectories, from the top
bed_width = 365  # needles on the bed; the knitting pattern has to fit
alignment = None  # a feature file, "x,y,z; r,g,b" per line, of stitches to hold in one column; None = follow the wales
# -------------------------------------------------------------------------

mesh_path = os.path.join(folder, name + ".obj")
field_path = os.path.join(folder, name + "_vertex_directional_field.txt")
out_dir = os.path.join(folder, "out")  # next to the inputs, ignored by git

trajectories = generate_stripes(mesh_path, field_path, stitch_height, stitch_width, stretch=stretch, out_dir=out_dir)
print("{} trajectories, spacing {}".format(len(trajectories), 2 * stitch_height / stretch))

links = read_neighbours(os.path.join(out_dir, name + "_neighbours.txt"))

# the knitting pattern: one pixel per stitch, two rows per trajectory, for the post-processing scripts
features = read_features(alignment) if alignment else None
pattern = knitting_pattern(trajectories, links, mesh_path, field_path, features)
bitmap_path = os.path.join(out_dir, name + "_export_wo_optim.bmp")
width, height = write_pattern(pattern["pixels"], bitmap_path, os.path.join(out_dir, name + "_pixel_data_dict.pkl"), bed_width)
print("knitting pattern {} x {} stitches, {}".format(width, height, bitmap_path))

if view:
    # coloured from the first trajectory in the knitting order to the last
    # and the singularities, where trajectories end
    singularities = read_singularities(os.path.join(out_dir, name + "_singularities.txt"))
    view_stripes(os.path.join(out_dir, name + "_remesh.obj"), trajectories, links, singularities)
