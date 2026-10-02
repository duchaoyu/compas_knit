# Data

Input models, one folder each, with the mesh and its directional field:

* `<name>.obj` — the triangle mesh
* `<name>_vertex_directional_field.txt` — one `x y z` wale direction per vertex, in mesh vertex order, with consistent signs

The scripts write their outputs to an `out/` folder next to the inputs, which git ignores.

## 2part_remesh2

Copied from `PhD/knit/2024_prototypes/2part/anisotropic`, unchanged. Millimetres; `scripts/fab/2_trajectories.py` uses
stitch height 2.297 and stitch width 3.54.

## fabsim

From `fabsim-example-project`, converted to the format above. Metres: use stitch height 0.002297 and stitch width
0.00354.

The fields there are per face (`d1`, the wale direction) and only fix a line, their sign flipping between faces.
Each was converted by walking across the faces and flipping each vector to agree with the face it was reached from,
averaging the faces around each vertex, and splitting every triangle into four, the field on the new vertices the
mean of the edge ends, until the edges are at most about three course spacings long; coarser, the stripe pattern
breaks down into clusters of singularities.

| model | mesh | field | faces | subdivided | sign conflicts |
|---|---|---|---|---|---|
| circle | `data/circular_flat.off` | `FDM/data/2part/circle_face_directional_field.txt` | 735 → 11760 | twice | 0 |
| 2part | `FDM/data/2part/2parts_smooth_tri_m.off` | `FDM/data/2part/directional_field_2part.json` | 1100 → 17600 | twice | 14 |
| 4part | `FDM/data/4part/4part_tri_m.off` | `FDM/data/4part/directional_field_4part.json` | 1000 → 16000 | twice | 0 |
| D5 | `FDM/data/D5/D5_remeshed.obj` | `FDM/data/D5/directional_field_D5.json` | 1563 → 25008 | twice | 15 |
| C5 | `FDM/data/C5/C5_remeshed.obj` | `FDM/data/C5/directional_field_C5.json` | 2137 → 34192 | twice | 0 |
| pattern | `FDM/data/pattern/pattern_smooth_tri_m.off` | `FDM/data/pattern/directional_field_pattern_smooth.json` | 1720 → 27520 | twice | 31 |
| pattern_rm2 | `FDM/data/pattern/remesh2/pattern_smooth_rm2.obj` | `FDM/data/pattern/remesh2/directional_field_pattern_smooth_rm2.json` | 2320 → 9280 | once | 0 |

Sign conflicts are neighbouring faces whose directions could not be made to agree: the field turns by a half turn
around a point there, or jumps between regions, and the order of the courses breaks down locally.

What to expect:

* circle, C5, D5, pattern\_rm2 — clean patterns
* 2part, pattern\_rm2 — wider than a 365-needle bed
* pattern — the sign conflicts break the order in a few places
* 4part — closed rings around the pole: knitted in the round, it needs a seam
* C5 — the mesh has 735 duplicate vertices, an unwelded seam that the stripes treat as a boundary; read it with
  `compas_knit.stripes.read_mesh`, which keeps them, as `Mesh.from_obj` would merge them out of step with the field
