"""Step 2: trajectories -> knitting pattern, one pixel per stitch, two rows per trajectory.

Reads what `scripts/trajectories.py` wrote to `<folder>/out/`, and writes the bitmap `<name>_export_wo_optim.bmp`
and the pixel data `<name>_pixel_data_dict.pkl` for the post-processing scripts.

Edit the inputs below and run
    python scripts/pattern.py
"""
import os

from compas_knit import DATA
from compas_knit.pattern import knitting_pattern
from compas_knit.pattern import read_feature
from compas_knit.pattern import write_pattern
from compas_knit.stripes import read_neighbours
from compas_knit.stripes import read_trajectories

# MODIFY -----------------------------------------------------------------
folder = os.path.join(DATA, "2part_remesh2")  # the same as in scripts/trajectories.py
name = "2part_remesh2"

bed_width = 365  # needles on the bed; the knitting pattern has to fit
# features are read from <folder>/features/<feature>.obj, points (p) and lines (l), as Rhino exports them
alignment = "cable"  # the feature whose stitches are held in one column; None = follow the wales
features = [  # (feature, colour): the stitches of each feature take its colour; a later one wins where they share one
    ("cable", (0, 255, 255)),
    ("bdr_anchors", (255, 0, 255)),
]
# -------------------------------------------------------------------------

out_dir = os.path.join(folder, "out")
# the refined mesh and its field, as the trajectories were made on, to follow the wales
mesh_path = os.path.join(out_dir, name + "_remesh.obj")
field_path = os.path.join(out_dir, name + "_remesh_vertex_directional_field.txt")

stitches = read_trajectories(os.path.join(out_dir, name + "_tri_path_recons.txt"))
links = read_neighbours(os.path.join(out_dir, name + "_neighbours.txt"))


def feature(name):
    return read_feature(os.path.join(folder, "features", name + ".obj"))


pattern = knitting_pattern(
    stitches,
    links,
    mesh_path,
    field_path,
    alignment=feature(alignment) if alignment else None,
    features=[(feature(f), color) for f, color in features],
)
for (f, color), colored in zip(features, pattern["colored"]):
    print("{}: {} stitches in {}".format(f, len(colored), color))
bitmap_path = os.path.join(out_dir, name + "_export_wo_optim.bmp")
width, height = write_pattern(pattern["pixels"], bitmap_path, os.path.join(out_dir, name + "_pixel_data_dict.pkl"), bed_width)
print("knitting pattern {} x {} stitches, {}".format(width, height, bitmap_path))
