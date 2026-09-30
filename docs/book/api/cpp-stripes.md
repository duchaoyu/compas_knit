# stripes (C++ executable)

```
stripes <mesh.obj> --spacing <s> [options]
```

Called by [`generate_stripes`](stripes.md#generate_stripes) with `--size 0 --spacing 2*stitch_height/stretch`.
Source in `src/cpp_stripes`, build instructions in [Installation](../getting-started/installation.md).

| Option | Description |
|---|---|
| `--spacing <s>` | distance between trajectories, in units of the rescaled mesh (required) |
| `--size <mm>` | rescale the mesh so its largest extent is `<mm>` (default 1000); `0` keeps the mesh units |
| `--field <file>` | per-vertex directional field (default `<name>_vertex_directional_field.txt`) |
| `--out-dir <dir>` | where to write the outputs (default: the mesh directory) |
| `--face-field <file>` | also write the field averaged onto each face |
| `--stitch-width <w>` | also write the trajectories divided into stitches of width `<w>`, one point per stitch, to `<name>_tri_path_recons.txt`; trajectories shorter than one stitch are left out of all outputs |
| `--view` | show the field and the trajectories in polyscope |

**Writes** `<name>_remesh.obj`, `<name>_tri_path.txt`, `<name>_neighbours.txt`, `<name>_singularities.txt` and, with `--stitch-width`, `<name>_tri_path_recons.txt`, see [File formats](../documentation/file-formats.md).

All trajectories run the same way across the field, along field × normal. The field needs consistent signs for this;
negate it to run them the other way.

**Prints** the number of stripe singularities and of trajectories ending at them, and how many trajectories were reversed.

## Source files

| File | What it does |
|---|---|
| `src/main.cpp` | reads the inputs, computes the stripe pattern, writes the outputs |
| `src/singularities.cpp` | links the isolines through singular triangles, see [Stripe patterns and singularities](../documentation/stripe-patterns.md#singularities) |
| `src/polyline.cpp` | chains the isoline segments into polylines |
| `src/stitches.cpp` | orients the trajectories along the field, divides them into stitches |
| `src/neighbours.cpp` | finds which trajectory comes after which |
