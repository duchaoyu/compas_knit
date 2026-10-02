# Fabrication steps: the pringle

The steps of the [fabrication workflow](fabrication-workflow.md), on an example: a pringle, a saddle 300 by 500 mm,
from the mesh to the knittable bitmap. Each step is a script in `scripts/fab/`, its inputs at the top, between the
`MODIFY` lines; they read and write in `data/pringle/`.

| Step | Script | Writes, in `data/pringle/` |
|---|---|---|
| 1.1 Direction field | `1.1_viewfield.py` | `pringle_vertex_directional_field.txt` |
| 1.2 Editing the field, optional | `1.2_edit_field.py` | `pringle_vertex_directional_field.txt` |
| 2. Trajectories and sequencing | `2_trajectories.py` | `out/pringle_tri_path*.txt`, `_neighbours.txt`, `_singularities.txt` |
| 3. Features, optional | `3_features.py` | `features/cable.obj` |
| 4. Bitmap and knittability | `4_pattern.py` | `out/pringle_bitmap.bmp`, `out/pringle_opt_bitmap.bmp`, and their pixel data |
| 5. Simulation | `scripts/sim/simulate_pringle.py` | `out/pringle_concrete_24_*`: the deformed knit, its stresses, a summary |

## Results

| | |
|---|---|
| Target surface | 300 × 500 × 328 mm, 1452 vertices, 2713 triangles |
| Direction field | per face, along y projected into each face; no singularity |
| Stitch | 2.297 mm high, 3.54 mm wide; stretch 1.05 along both, so the knit is pre-tensioned |
| Refined mesh | edges of at most 3.37 mm, the stitch width divided by 1.05 |
| Trajectories | 152, 11 965 stitches |
| Short rows | 24 trajectory ends inside the surface, at singularities of the stripes |
| Sequence | 164 links, no cycles, from y = −249 to 247 mm |
| Bitmap | 120 × 304 stitches, within 365 needles |
| Knittability | 128 black stitches moved down, 9 added at the boundary, 5 red rows turned; nothing left open |
| Simulation | boundary fixed, 10 mm of concrete, 41 N: in tension everywhere, 277 to 879 N/m; the concrete sags it 0.70 mm |

## The target surface

`data/pringle/pringle.obj`: the saddle as Rhino exported it, `data/pringle.obj`, scaled to millimetres, the units of
the stitch size, 300 by 500 mm and 328 mm high, and remeshed into a regular grid of triangles about 10 mm apart in plan,
the normals up: 1452 vertices, 2713 triangles. The rim rises at the ends along x and drops at the ends along y, so the
surface is longer along y, its long axis.

![The pringle, 300 by 500 mm](../.gitbook/assets/pringle-surface.png)

## 1.1 Direction field

The direction field is the knitting direction, the wale. `1.1_viewfield.py` takes two inputs, in `data/pringle/`:

| Input | |
|---|---|
| `pringle.obj` | the mesh, triangles |
| `pringle_face_directional_field.txt` | the direction field per face: one `x y z` per triangle, in the order of the faces of the mesh, e.g. from Grasshopper |

Here the field runs along the long axis of the pringle, y, projected into the plane of each triangle. The field per
face is averaged onto the vertices, the triangles around each weighted by their area, after turning their vectors to
agree, as a direction field has no sign; that is `pringle_vertex_directional_field.txt`, the field the next steps read.
A field given per vertex is used as it is.

```python
# scripts/fab/1.1_viewfield.py
folder = os.path.join(DATA, "pringle")
name = "pringle"
field_file = name + "_face_directional_field.txt"  # per face; or name + "_vertex_directional_field.txt", per vertex
```

```bash
python scripts/fab/1.1_viewfield.py
```

It shows the field as given, one segment per triangle, from the top.

![The pringle and its direction field, along y](../.gitbook/assets/pringle-field.png)

## 1.2 Editing the field, optional

`1.2_edit_field.py` makes the field per vertex instead, three ways: one direction projected into the surface
(`"direction"`), around an axis (`"axis"`), or the smoothest field held along a curve (`"hold"`). It writes
`pringle_vertex_directional_field.txt` too, in place of the one from 1.1.

## 2. Trajectories and sequencing

`2_trajectories.py` turns the field into the courses to knit. Its inputs are the mesh and the field per vertex from
step 1, and the stitch:

| Input | Here | |
|---|---|---|
| `stitch_height` | 2.297 mm | the height of a stitch, along the wale, at zero stress |
| `stitch_width` | 3.54 mm | the width of a stitch, along the course |
| `stretch_wale` | 1.05 | the pre-strain along the wale, the field: the stitch height is divided by it |
| `stretch_course` | 1.05 | the pre-strain along the course, across the field: the stitch width is divided by it |

A stretch factor above 1 makes the stitches smaller on the mesh, so the knit, smaller than the surface, is stretched
onto it. Here 1.05, 5 % along both: without it, the knit would be slack once fixed, and under a load would have to
carry compression, which a knit cannot; see the simulation, below.

```python
# scripts/fab/2_trajectories.py
folder = os.path.join(DATA, "pringle")
name = "pringle"
stitch_height = 2.297  # mm
stretch_wale = 1.05
stretch_course = 1.05
stitch_width = 3.54  # mm
recompute = True  # False: read the trajectories already in out/, to look at them again
view = True
```

```bash
python scripts/fab/2_trajectories.py
```

It does three things:

1. **The stripes.** The mesh is refined to edges no longer than a stitch width, here to edges of 3.37 mm,
   and a stripe pattern is computed along the field. Its stripes are the trajectories, the courses: across the field,
   `2 × stitch_height / stretch_wale` apart, as each is knitted out and back, two rows, and divided into stitches
   `stitch_width / stretch_course` apart. Here 152 trajectories, 2 to 120 stitches long, 11 965 stitches in all
   (`out/pringle_tri_path.txt`, and the stitches in `out/pringle_tri_path_recons.txt`).
2. **The singularities, the short rows.** Where the courses spread apart, towards the two low ends of the saddle, the
   stripe pattern starts a new one between two others: a trajectory ends inside the surface, at a singularity of the
   stripes. Each is a short row. Here 24, in two bands across the pringle, 112 to 228 mm from the middle along y; the
   field itself has no singularity (`out/pringle_singularities.txt`).
3. **The sequence.** Each trajectory is linked to the ones beside it, which gives the order to knit them in, every one
   after those it sits on (`out/pringle_neighbours.txt`, 164 links). Here the links have no cycles, and the sequence
   runs from one end of the long axis to the other, y = −249 to 247 mm.

The viewer shows the trajectories in the sequence, from the first (orange) to the last (green), and the short rows
(blue), from the top; turn it with the right mouse button.

![The trajectories in sequence, and the short rows](../.gitbook/assets/pringle-trajectories.png)

## 3. Features, optional

Features mark stitches in the bitmap: lines and points as `.obj` files in `data/pringle/features/`, as Rhino exports
them, e.g. where a cable runs or where the knit is anchored. `3_features.py` writes one when none is drawn: the piece of
the boundary furthest to the left, as `features/cable.obj`. `4_pattern.py` can hold the stitches of a feature in one
column, a straight selvedge, and colour the stitches of each. The pringle has none.

## 4. Bitmap and knittability

Each trajectory becomes two rows of the bitmap, one pixel per stitch: knitted out (black) and back (red in the bitmap for the machine, grey in the images here), each stitch
in the column of the stitch it sits on. The bitmap is then made knittable from one yarn carrier, row after row from the
bottom right corner: where the next row does not start where the yarn is, black stitches are moved down from the rows
above, stitches are added at the boundary (blue), or, for a short row ending inside the fabric on the right, the red
row turns early or late.

```python
# scripts/fab/4_pattern.py
folder = os.path.join(DATA, "pringle")
name = "pringle"
bed_width = 365  # needles
alignment = None  # follow the wales
features = []
```

```bash
python scripts/fab/4_pattern.py
```

The pattern is 120 stitches wide and 304 rows high, within the 365 needles of the bed. Making it knittable moved 128
black stitches down, added 9 at the boundary and turned 5 red rows, and left nothing open. It shows both, before and
after; the white notches are the short rows.

| Before | After |
|---|---|
| ![Before the knittability optimisation](../.gitbook/assets/pringle-bitmap-before.png) | ![Knittable](../.gitbook/assets/pringle-bitmap-after.png) |

## 5. Simulation

The knit, knitted with the stitches of the pattern, fixed on its whole boundary, and a layer of concrete cast on it,
10 mm at 2400 kg/m³, 24 kg/m²: `scripts/sim/simulate_pringle.py`, an orthotropic membrane with E_wale 12 500 N/m,
E_course 5000 N/m and nu 0.198, its frame the direction field, its rest shape the surface with the stitches made smaller
by the stretch factors of step 2, so that, fixed, it is pre-tensioned.

```bash
python scripts/sim/simulate_pringle.py
```

The concrete weighs 41 N. The pre-tension alone pulls the surface up to 6.2 mm as the knit tightens on its supports; the
concrete sags it by 0.70 mm more. The knit is in tension everywhere, 470 to 879 N/m along the wale, 277 to 526 N/m along
the course. Without the pre-tension, at 1.0, three quarters of it would be in compression, down to −47 N/m, and
CalculiX, with the same mesh, supports and loads, stops at half the load. With it, CalculiX carries the load too: the
sag from the concrete agrees, 0.76 against 0.70 mm; the change of shape from the pre-tension less, up to 6.9 against
6.2 mm and 1.9 mm apart per vertex on average, a difference that grows with the stretch and whose cause is still open.

![The knit under the concrete, shaded by the von Mises stress, 426 to 766 N/m](../.gitbook/assets/pringle-simulation.png)

## Knitting pattern

<!-- TODO: from the knittable bitmap to the machine file -->
