# Quickstart

Knitting trajectories for a mesh and a directional field, and a look at them.

## 1. Prepare the inputs

In one folder:

* `<name>.obj` — the triangle mesh
* `<name>_vertex_directional_field.txt` — one `x y z` vector per vertex, in mesh vertex order

See [File formats](../documentation/file-formats.md).

## 2. Edit and run the script

Open `scripts/knit.py` and set the inputs in the `MODIFY` block:

```python
folder = "/path/to/your/model"
name = "2part_remesh2"

stitch_height = 2.297  # st_h at zero stress, in the units of the mesh
stretch = 1.0          # pre-strain stretch factor along the wale, 1.0 = none
view = True            # show the mesh and the trajectories, from the top
```

```bash
python scripts/knit.py
```

## 3. The result

The trajectories are written to `<folder>/out/<name>_tri_path.txt`, and a viewer opens in top view.

<!-- TODO: screenshot of the viewer -->
<!-- ![](../.gitbook/assets/quickstart-viewer.png) -->

## Next

* [Your first trajectories](../tutorials/first-trajectories.md), the same step by step in Python
* [Stripe patterns and singularities](../documentation/stripe-patterns.md), what happens underneath
