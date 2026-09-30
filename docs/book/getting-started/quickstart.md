# Quickstart

Knitting trajectories and a knitting pattern for a mesh and a directional field, in two steps.

## 1. Prepare the inputs

In one folder under `data/`, e.g. `data/2part_remesh2/` (see `data/README.md` for the models included):

* `<name>.obj` — the triangle mesh
* `<name>_vertex_directional_field.txt` — one `x y z` vector per vertex, in mesh vertex order

See [File formats](../documentation/file-formats.md).

## 2. Trajectories

Open `scripts/trajectories.py` and set the inputs in the `MODIFY` block:

```python
folder = os.path.join(DATA, "2part_remesh2")
name = "2part_remesh2"

stitch_height = 2.297  # st_h at zero stress, in the units of the mesh
stretch_wale = 1.0     # pre-strain stretch factor along the wale (the field): the stitch height is divided by it
stretch_course = 1.0   # pre-strain stretch factor along the course (across the field): the stitch width is divided by it
stitch_width = 3.54    # st_w, in the units of the mesh: one point per stitch
view = True            # show the mesh and the trajectories, from the top
```

```bash
python scripts/trajectories.py
```

It writes to `<folder>/out/`, which git ignores: the trajectories, their stitches, which trajectory comes after which,
and the singularities. With `view = True`, a viewer opens in top view, the trajectories coloured by their knitting order.

## 3. Knitting pattern

Open `scripts/pattern.py`, set the same `folder` and `name`, and the needle bed:

```python
bed_width = 365      # needles on the bed; the knitting pattern has to fit
alignment = "cable"  # the feature whose stitches are held in one column; None = follow the wales
features = [         # (feature, colour): the stitches of each feature take its colour
    ("cable", (0, 255, 255)),
    ("bdr_anchors", (255, 0, 255)),
]
```

The features are `.obj` files in `<folder>/features/`, as Rhino exports them: points (`p` records), each taking the
stitch nearest to it, and lines (`l` records), taking every stitch they pass over. `python scripts/features.py` writes
the cable, the boundary piece furthest to the left, as a line, for when none is drawn in Rhino.

```bash
python scripts/pattern.py
```

It writes the bitmap `<name>_export_wo_optim.bmp` and the pixel data `<name>_pixel_data_dict.pkl` for the
post-processing scripts.

<!-- TODO: screenshot of the viewer -->
<!-- ![](../.gitbook/assets/quickstart-viewer.png) -->

## Next

* [Your first trajectories](../tutorials/first-trajectories.md), the same step by step in Python
* [Stripe patterns and singularities](../documentation/stripe-patterns.md), what happens underneath
