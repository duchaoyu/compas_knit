# compas\_knit.stripes

Knitting trajectories from a directional field (Chapter 6, Section 6.2.1).

```python
from compas_knit.stripes import generate_stripes, check_trajectories, read_trajectories
```

## generate\_stripes

```python
generate_stripes(mesh_path, field_path, stitch_height, stitch_width, stretch_wale=1.0, stretch_course=1.0,
                 max_edge=None, out_dir=None, view=False, check=True)
```

Extract equally spaced knitting trajectories from a directional field, by running the [`stripes`](cpp-stripes.md) executable.

| Parameter | Type | Description |
|---|---|---|
| `mesh_path` | `str` | triangle mesh, `<name>.obj` |
| `field_path` | `str` | per-vertex directional field, see [File formats](../documentation/file-formats.md) |
| `stitch_height` | `float` | stitch height st\_h at theoretical zero stress, in the units of the mesh |
| `stitch_width` | `float` | stitch width st\_w, in the units of the mesh; the trajectories are divided into stitches of this width, one point per stitch, written to `<name>_tri_path_recons.txt` |
| `stretch_wale` | `float` | pre-strain stretch factor along the wale, the direction of the field; the stitch height, and so the spacing, is divided by it (Section 6.3.3) |
| `stretch_course` | `float` | pre-strain stretch factor along the course, across the field; the stitch width is divided by it |
| `max_edge` | `float` | refine the mesh until no edge is longer, by default the stitch width on the mesh, `stitch_width / stretch_course`; a trajectory ending at a singularity stops about half an edge from it, so this sets the gap in the knit there |
| `out_dir` | `str` | where to write `<name>_remesh.obj` and `<name>_tri_path.txt`; defaults to the mesh directory |
| `view` | `bool` | show the field and the trajectories in polyscope; blocks until the window is closed |
| `check` | `bool` | warn about segments running along the field, see [`check_trajectories`](#check_trajectories) |

**Returns** `list[compas.geometry.Polyline]` — the trajectories, unordered, all running the same way along field × normal, in mesh coordinates.
Divided into stitches, one point per stitch; trajectories shorter than one stitch are left out.

**Raises** `RuntimeError` if the executable is not found.

```python
trajectories = generate_stripes("model.obj", "model_vertex_directional_field.txt", 2.297, 3.54, out_dir="out")
```

## check\_trajectories

```python
check_trajectories(trajectories, mesh, field, min_angle=60.0)
```

Find segments running along the field, which a trajectory should cross. Segments shorter than a tenth of the
median segment length are skipped.

| Parameter | Type | Description |
|---|---|---|
| `trajectories` | `list[Polyline]` | |
| `mesh` | `str` or `Mesh` | the mesh of the field, or the path to an `.obj` |
| `field` | `str` or array | per-vertex directional field, or the path to its file |
| `min_angle` | `float` | segments closer than this to the field, in degrees, are reported |

**Returns** `list[tuple[int, int, float]]` — trajectory index, segment index and angle to the field in degrees.

{% hint style="info" %}
Next to a singularity, where two stripes merge into one, the remaining trajectory shifts sideways by up to half a
spacing. Such a segment is reported too, and is correct.
{% endhint %}

## order\_trajectories

```python
order_trajectories(links, n)
```

Position of each trajectory in the knitting order: the length of the longest chain of links leading to it.
**Returns** `(position, cyclic)` — the position of each of the `n` trajectories, from 0, and the trajectories on or
after a cycle of links. Where the links close on themselves, for instance where the courses run around a pole,
there is no first or last and the knitting needs a seam.

## read\_mesh

```python
read_mesh(path)
```

The vertices and triangles of an `.obj` in the order of the file, as the `stripes` executable reads it. Unlike
`Mesh.from_obj`, it does not merge vertices at the same position, so the vertices stay in step with a per-vertex field.

## read\_neighbours

```python
read_neighbours(path)
```

Read a `_neighbours.txt` file: which trajectory comes after which along the field.
**Returns** `list[tuple[int, int, int]]` — for each link, the trajectory before, the trajectory after, and how many
segments of either found the other, a measure of the length they share.

## read\_singularities

```python
read_singularities(path)
```

Read a `_singularities.txt` file. **Returns** `list[tuple[str, list[float], int]]` — for each singular triangle,
its kind, its centre and its index. `"stripe"`: a singularity of the stripe pattern, where trajectories end.
`"field"`: a singularity of the directional field, the index in half turns (1 for a half-turn, 2 for a pole).

## read\_trajectories

```python
read_trajectories(path)
```

Read a `_tri_path.txt` file. **Returns** `list[Polyline]`.
