# compas\_knit.viewer

```python
from compas_knit.viewer import view_field, view_stripes
```

## view\_stripes

```python
view_stripes(mesh, trajectories, links=None, singularities=None, view="top", show_mesh=True, colors=("#ffba08", "#9d0208"))
```

Show the mesh and the trajectories in compas\_viewer. Blocks until the window is closed.
The camera is centred on the mesh and zoomed to fit it.

| Parameter | Type | Description |
|---|---|---|
| `mesh` | `str` or `Mesh` | the mesh, or the path to an `.obj` |
| `trajectories` | `list[Polyline]` | as returned by [`generate_stripes`](stripes.md#generate_stripes) |
| `links` | `list[tuple]` | the links from [`read_neighbours`](stripes.md#read_neighbours); the trajectories are then coloured by their position in the knitting order, see [`order_trajectories`](stripes.md#order_trajectories) |
| `singularities` | `list[tuple]` | from [`read_singularities`](stripes.md#read_singularities), shown as points: stripe singularities, where a trajectory ends, blue; field singularities black; larger where the index is beyond one. Each group can be hidden in the scene panel |
| `view` | `str` | the initial view: `"top"`, `"perspective"`, `"front"` or `"right"` |
| `show_mesh` | `bool` | show the mesh under the trajectories |
| `colors` | `tuple[str, str]` | hex colours of the first and the last trajectories in the order, blended in OKLab; default amber to dark red |

```python
view_stripes("out/model_remesh.obj", trajectories,
             read_neighbours("out/model_neighbours.txt"), read_singularities("out/model_singularities.txt"))
```

## view\_field

```python
view_field(mesh, field, view="top", length=None)
```

Show the mesh and the directional field in compas\_viewer. Blocks until the window is closed.
The field is a line field, so each vertex gets a segment centred on it, without an arrowhead,
projected into the tangent plane as the `stripes` executable does. `scripts/view_field.py` runs it.

| Parameter | Type | Description |
|---|---|---|
| `mesh` | `str` or `Mesh` | the mesh, or the path to an `.obj` |
| `field` | `str` or array | per-vertex directional field, or the path to its file, see [File formats](../documentation/file-formats.md) |
| `view` | `str` | the initial view: `"top"`, `"perspective"`, `"front"` or `"right"` |
| `length` | `float` | length of the segments; defaults to 0.8 times the mean edge length |

**Raises** `ValueError` if the field and the mesh have a different number of vertices.

```python
view_field("model.obj", "model_vertex_directional_field.txt")
```

