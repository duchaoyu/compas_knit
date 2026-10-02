"""Step 3: trajectories -> knitting pattern -> knittable pattern (Section 6.2.4).

Reads what `scripts/fab/2_trajectories.py` wrote to `<folder>/out/`. The knitting pattern, one pixel per stitch, two
rows per trajectory, black knitting out, red back: the bitmap `<name>_bitmap.bmp` and the pixel data
`<name>_pixel_data_dict.pkl`. Then made knittable from one yarn carrier, row after row from the bottom right corner,
moving black stitches down, adding stitches at the boundary, and turning red rows early or late for short rows on the
right: `<name>_opt_bitmap.bmp` and `<name>_pixel_data_dict_knittable.pkl`. Shows both, before and after.

Edit the inputs below and run
    python scripts/fab/4_pattern.py
"""
import os

from compas_knit import DATA
from compas_knit.pattern import knittable
from compas_knit.pattern import knitting_pattern
from compas_knit.pattern import VIEW_COLORS
from compas_knit.pattern import pattern_image
from compas_knit.pattern import read_feature
from compas_knit.pattern import write_pattern
from compas_knit.stripes import read_neighbours
from compas_knit.stripes import read_trajectories

# MODIFY -----------------------------------------------------------------
folder = os.path.join(DATA, "pringle")  # the same as in scripts/fab/2_trajectories.py
name = "pringle"

bed_width = 365  # needles on the bed, the knitting pattern has to fit; None: no limit
# features are read from <folder>/features/<feature>.obj, points (p) and lines (l), as Rhino exports them
alignment = None  # the feature whose stitches are held in one column, e.g. "cable"; None = follow the wales
features = [  # (feature, colour): the stitches of each feature take its colour; a later one wins where they share one
    # ("cable", (0, 255, 255)),
    # ("bdr_anchors", (255, 0, 255)),
]
gap = 3  # a black row starting this many needles or fewer from where the yarn is is left as it is
show = True  # show the pattern before and after the knittability optimisation
# -------------------------------------------------------------------------

out_dir = os.path.join(folder, "out")
# the refined mesh and its field, as the trajectories were made on, to follow the wales
mesh_path = os.path.join(out_dir, name + "_remesh.obj")
field_path = os.path.join(out_dir, name + "_remesh_vertex_directional_field.txt")

stitches = read_trajectories(os.path.join(out_dir, name + "_tri_path_recons.txt"))
links = read_neighbours(os.path.join(out_dir, name + "_neighbours.txt"))


def feature(name):
    return read_feature(os.path.join(folder, "features", name + ".obj"))


# the knitting pattern
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
bitmap_path = os.path.join(out_dir, name + "_bitmap.bmp")
width, height = write_pattern(pattern["pixels"], bitmap_path, os.path.join(out_dir, name + "_pixel_data_dict.pkl"), bed_width)
print("knitting pattern {} x {} stitches, {}".format(width, height, bitmap_path))

# knittable from one yarn carrier
pixels, report = knittable(pattern["pixels"], gap=gap)
print("{moved} black stitches moved down, {added} stitches added at the boundary, {turned} red rows turned for a short row "
      "on the right; left open: {red_open} red rows with stitches beneath, {black_open} black rows, "
      "{turn_open} turns".format(**report))
bitmap_path = os.path.join(out_dir, name + "_opt_bitmap.bmp")
width, height = write_pattern(pixels, bitmap_path, os.path.join(out_dir, name + "_pixel_data_dict_knittable.pkl"), bed_width)
print("knittable pattern {} x {} stitches, {}".format(width, height, bitmap_path))

if show:
    # enlarged to about 800 pixels high, each in its own window
    scale = max(1, 800 // height)
    # the rows knitting back in grey, to look at; the bitmaps keep the machine's colours
    pattern_image(pattern["pixels"], scale, VIEW_COLORS).show(title=name + " before the optimisation")
    pattern_image(pixels, scale, VIEW_COLORS).show(title=name + " knittable")
