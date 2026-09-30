# File formats

## Mesh — `<name>.obj`

A triangle mesh, manifold. The units are kept (`--size 0`), so the stitch height is in the same units.

## Directional field — `<name>_vertex_directional_field.txt`

One vector per line, `x y z`, in world coordinates, one line per mesh vertex, in the vertex order of the `.obj`.
The sign does not matter. The vectors are projected into the tangent plane of each vertex.

```
0.998 0.012 -0.061
0.997 0.015 -0.070
...
```

## Trajectories — `<name>_tri_path.txt`

One trajectory per line, its points as `x,y,z` separated by `; `. The trajectories are unordered, but all run
the same way across the field, along field × normal: negate the field to run them the other way.
Read and write it with [`read_trajectories`](../api/stripes.md#read_trajectories).

```
0.0,233.916,15.81; 0.080,233.917,15.873; 9.780,233.877,22.830
441.59,230.961,-166.448; 436.231,230.716,-166.448
```

## Stitches — `<name>_tri_path_recons.txt`

The trajectories divided into stitches, written with `--stitch-width` / `stitch_width`, in the same format as
`_tri_path.txt`. From the first point of each trajectory, each next point lies on the trajectory at straight-line
distance `stitch_width` from the previous one, as Grasshopper's DivideDistance does. The rest after the last full
stitch is dropped, and trajectories shorter than one stitch are left out.

## Neighbours — `<name>_neighbours.txt`

One link per line, `a b n`: trajectory `b` comes after trajectory `a` along the field, and they are adjacent on `n`
mesh edges. Indices are the line numbers, from 0, in `_tri_path.txt` and `_tri_path_recons.txt`.
Two trajectories are neighbours where they cross a mesh edge next to each other; the links form no cycles.

```
0 121 40
1 0 47
2 1 52
```

## Singularities — `<name>_singularities.txt`

One singular triangle per line, `kind x y z index`, at the triangle centre. `stripe`: a singularity of the stripe
pattern, where trajectories end; `field`: a singularity of the directional field, the index in half turns.

```
stripe 12.53 -470.1 -150.2 1
field 0.0012 0.0008 0.3104 1
```

## Rescaled mesh — `<name>_remesh.obj`

The mesh the trajectories live on, written by `stripes`. Unchanged from the input with `--size 0`.

## Face field — `--face-field <file>`

The input field averaged onto each face, one `x y z` per face, in face order.

<!-- TODO: the formats of the later steps (_tri_path_recons.txt, bitmaps, ...) -->
