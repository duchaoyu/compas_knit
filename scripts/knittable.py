"""Step 3: knitting pattern -> knittable pattern (Section 6.2.4).

Reads the pixel data `scripts/pattern.py` wrote to `<folder>/out/`, makes it knittable from one yarn carrier, row
after row from the bottom right corner, moving black stitches down and adding stitches at the boundary, and writes the
bitmap `<name>_export_knittable.bmp` and the pixel data `<name>_pixel_data_dict_knittable.pkl`.

Edit the inputs below and run
    python scripts/knittable.py
"""
import os
import pickle

from compas_knit import DATA
from compas_knit.pattern import knittable
from compas_knit.pattern import write_pattern

# MODIFY -----------------------------------------------------------------
folder = os.path.join(DATA, "2part_remesh2")  # the same as in scripts/pattern.py
name = "2part_remesh2"

gap = 3  # a black row starting this many needles or fewer from where the yarn is is left as it is
bed_width = 365  # needles on the bed
# -------------------------------------------------------------------------

out_dir = os.path.join(folder, "out")
with open(os.path.join(out_dir, name + "_pixel_data_dict.pkl"), "rb") as f:
    pixels = pickle.load(f)

pixels, report = knittable(pixels, gap=gap)
print("{moved} black stitches moved down, {added} stitches added at the boundary; left open: {red_open} red rows with "
      "stitches beneath, {black_open} black rows, {turn_open} turns".format(**report))

bitmap_path = os.path.join(out_dir, name + "_export_knittable.bmp")
width, height = write_pattern(pixels, bitmap_path, os.path.join(out_dir, name + "_pixel_data_dict_knittable.pkl"), bed_width)
print("knittable pattern {} x {} stitches, {}".format(width, height, bitmap_path))
