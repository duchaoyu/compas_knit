# stripes

Knitting trajectories from a user-defined directional field (Chapter 6, Section 6.2.1).
The trajectories are the isolines of a stripe pattern [Knöppel et al. 2015] aligned with the field,
spaced `--spacing` apart. Ported from `src/main2*.cpp` in the
[shrink-morph fork](https://github.com/duchaoyu/shrink-morph).

At a singularity of the stripe pattern the trajectories are linked by stripe level, in
`src/singularities.cpp`, instead of geometry-central's `connectIsolinesOnSingularities`, which
could join a trajectory to its neighbour (a U-turn). One trajectory ends at each singularity.

## Build

```
cmake -S src/cpp_stripes -B src/cpp_stripes/build
cmake --build src/cpp_stripes/build -j 8
```

CMake downloads libigl, polyscope and geometry-central at the same revisions as shrink-morph.

## Run

From Python, `compas_knit.stripes.generate_stripes(mesh, field, stitch_height, stitch_width)` calls this with
`--size 0 --spacing 2*stitch_height --stitch-width stitch_width`, see `scripts/fab/2_trajectories.py`.


```
src/cpp_stripes/build/stripes <folder>/<name>.obj --spacing <s> --stitch-width <w> [--size 1000] [--view]
```

Inputs, in `<folder>`:
- `<name>.obj`, the triangle mesh
- `<name>_vertex_directional_field.txt`, one `x y z` world-space vector per vertex, in mesh vertex order
  (or pass another file with `--field`)

Outputs, in `<folder>` (or `--out-dir`):
- `<name>_remesh.obj`, the mesh rescaled so its largest extent is `--size` (`--size 0` keeps the mesh units) and refined
  until no edge is longer than `--max-edge` (default: the stitch width), and its field,
  `<name>_remesh_vertex_directional_field.txt`
- `<name>_tri_path.txt`, one trajectory per line, `x,y,z; x,y,z; ...`, all running the same way along field × normal
- `<name>_tri_path_recons.txt`, the trajectories divided into stitches of width `<w>`,
  one point per stitch, as Grasshopper's DivideDistance
- `<name>_neighbours.txt`, one link per line, `a b n`: trajectory `b` comes after `a` along the field,
  found `n` times
- `<name>_singularities.txt`, one singular triangle per line, `stripe|field x y z index`, at its centre
- with `--face-field <file>`, the field averaged onto each face, one `x y z` per face

`--spacing` is in the units of the rescaled mesh, and is the course spacing 2·st_h
(divided by the wale stretch factor where the knit is pre-strained; `--stitch-width` by the course one). Values used before:

| model | command |
|---|---|
| 2part/anisotropic/2part_remesh2 | `--spacing 4.594098288282881` (= 4.532151655555558 · 1.218 / 1201.576538 · 1000) |
| iass_2024/barrel_vault | `--size 1200 --spacing <4.532151655555558 / W · 1000>`, W = original largest extent (printed as "The coefficiency is") |
| iass_2024/barrel_vault_1200mm, boundary field | `--size 1200 --spacing 8 --field barrel_vault_boundary_vertex_directional_field.txt` |
