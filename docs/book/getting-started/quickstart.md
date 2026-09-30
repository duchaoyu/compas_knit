# Quickstart

Knitting trajectories for a mesh and a directional field, and a look at them.

## 1. Prepare the inputs

In one folder under `data/`, e.g. `data/2part_remesh2/` (see `data/README.md` for the models included):

* `<name>.obj` — the triangle mesh
* `<name>_vertex_directional_field.txt` — one `x y z` vector per vertex, in mesh vertex order

See [File formats](../documentation/file-formats.md).

## 2. Edit and run the script

Open `scripts/knit.py` and set the inputs in the `MODIFY` block:

```python
folder = os.path.join(DATA, "2part_remesh2")
name = "2part_remesh2"

stitch_height = 2.297  # st_h at zero stress, in the units of the mesh
stretch = 1.0          # pre-strain stretch factor along the wale, 1.0 = none
stitch_width = 3.54    # st_w, in the units of the mesh: one point per stitch
view = True            # show the mesh and the trajectories, from the top
```

```bash
python scripts/knit.py
```

## 3. The result

The outputs are written to `<folder>/out/`, which git ignores: the trajectories, the stitches, the neighbours,
the singularities and the knitting pattern `<name>_export_wo_optim.bmp`. A viewer opens in top view.

<!-- TODO: screenshot of the viewer -->
<!-- ![](../.gitbook/assets/quickstart-viewer.png) -->

## Next

* [Your first trajectories](../tutorials/first-trajectories.md), the same step by step in Python
* [Stripe patterns and singularities](../documentation/stripe-patterns.md), what happens underneath
