"""Step 5: the knitting pattern of a simulated knit, from the settings exported by the simulation window.

Reads `<folder>/<name>_settings.json`, written by *Export settings* in `scripts/sim/sim_window.py`: the stitch and the
stretch factors of the knit simulated. With them, it generates the trajectories, as `scripts/fab/2_trajectories.py`,
and the knitting pattern, as `scripts/fab/4_pattern.py`: the bitmap and the knittable bitmap, `<name>_bitmap.bmp` and
`<name>_opt_bitmap.bmp` in `<folder>/out/`, and a copy of the settings next to them, `<name>_pattern_settings.json`, so
the pattern says which simulation it is the knit of. Shows the bitmaps before and after, and, with `view`, the stripes.

Edit the inputs below and run
    python scripts/fab/5_pattern_from_settings.py
"""
import json
import os

from compas_knit import DATA
from compas_knit.app import read_settings
from compas_knit.pattern import VIEW_COLORS
from compas_knit.pattern import knittable
from compas_knit.pattern import knitting_pattern
from compas_knit.pattern import pattern_image
from compas_knit.pattern import write_pattern
from compas_knit.stripes import generate_stripes
from compas_knit.stripes import read_neighbours
from compas_knit.stripes import read_singularities
from compas_knit.stripes import read_trajectories

# MODIFY -----------------------------------------------------------------
folder = os.path.join(DATA, "pringle")  # the mesh <name>.obj and its field <name>_vertex_directional_field.txt, step 1
name = "pringle"
settings = os.path.join(folder, name + "_settings.json")  # exported by scripts/sim/sim_window.py

bed_width = 365  # needles on the bed, the knitting pattern has to fit; None: no limit
gap = 3  # a black row starting this many needles or fewer from where the yarn is is left as it is
show = True  # show the pattern before and after the knittability optimisation
view = True  # show the stripes: the trajectories in the knitting order, and the short rows
# -------------------------------------------------------------------------

exported = read_settings(settings)
if exported is None:
    raise SystemExit("No settings at {}: run the simulation window, scripts/sim/sim_window.py, and Export settings".format(settings))
q = exported["parameters"]
results = exported.get("results", {})
print("the settings of {}, exported {}: stitch {} x {}, stretch {} / {}".format(
    exported["geometry"], exported["exported"], q["stitch_height"], q["stitch_width"], q["stretch_wale"], q["stretch_course"]))
if results.get("faces_in_compression"):
    print("warning: the simulation had {} faces in compression; a knit cannot carry it".format(results["faces_in_compression"]))

mesh_path = os.path.join(folder, name + ".obj")
field_path = os.path.join(folder, name + "_vertex_directional_field.txt")
out_dir = os.path.join(folder, "out")

# the trajectories, step 2
stitches = generate_stripes(mesh_path, field_path, q["stitch_height"], q["stitch_width"], stretch_wale=q["stretch_wale"],
                            stretch_course=q["stretch_course"], out_dir=out_dir)
links = read_neighbours(os.path.join(out_dir, name + "_neighbours.txt"))
singularities = read_singularities(os.path.join(out_dir, name + "_singularities.txt"))
print("{} trajectories, {} short rows".format(len(stitches), sum(kind == "stripe" for kind, _, _ in singularities)))

# the knitting pattern, step 4
pattern = knitting_pattern(stitches, links, os.path.join(out_dir, name + "_remesh.obj"),
                           os.path.join(out_dir, name + "_remesh_vertex_directional_field.txt"))
write_pattern(pattern["pixels"], os.path.join(out_dir, name + "_bitmap.bmp"), os.path.join(out_dir, name + "_pixel_data_dict.pkl"), bed_width)
pixels, report = knittable(pattern["pixels"], gap=gap)
print("{moved} black stitches moved down, {added} stitches added at the boundary, {turned} red rows turned for a short row "
      "on the right; left open: {red_open} red rows with stitches beneath, {black_open} black rows, "
      "{turn_open} turns".format(**report))
bitmap_path = os.path.join(out_dir, name + "_opt_bitmap.bmp")
width, height = write_pattern(pixels, bitmap_path, os.path.join(out_dir, name + "_pixel_data_dict_knittable.pkl"), bed_width)
print("knittable pattern {} x {} stitches, {}".format(width, height, bitmap_path))

# the settings it was made with, next to it
exported["pattern"] = dict(width=width, height=height, trajectories=len(stitches), **report)
with open(os.path.join(out_dir, name + "_pattern_settings.json"), "w") as f:
    json.dump(exported, f, indent=1)

if show:
    scale = max(1, 800 // height)
    pattern_image(pattern["pixels"], scale, VIEW_COLORS).show(title=name + " before the optimisation")
    pattern_image(pixels, scale, VIEW_COLORS).show(title=name + " knittable")

if view:
    from compas_knit.viewer import view_stripes

    view_stripes(mesh_path, read_trajectories(os.path.join(out_dir, name + "_tri_path.txt")), links, singularities)
