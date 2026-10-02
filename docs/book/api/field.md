# compas\_knit.field

Directional fields: the smoothest line field on a mesh, held at chosen vertices.

```python
from compas_knit.field import smoothest_field, project_field
```

The field is a line field, the wale, a direction without a sign. The smoothest field minimises the change of the field
along the edges, after transporting it from one vertex to the next, with cotan weights (Knöppel et al. 2013,
"Globally optimal direction fields"). `scripts/fab/1.2_edit_field.py` holds the field along a curve, e.g. y = 0 on the
hemisphere, and writes the result as a new example for `scripts/fab/2_trajectories.py`.

## smoothest\_field

```python
smoothest_field(vertices, faces, fixed=None, directions=None)
```

| Parameter | Type | Description |
|---|---|---|
| `vertices`, `faces` | array | the mesh |
| `fixed` | `list[int]` | the vertices where the field is held; none: free everywhere, the smoothest field of all |
| `directions` | array | the field at the fixed vertices, one 3D vector each, projected into the surface |

**Returns** an (n, 3) array, a unit vector in the tangent plane at each vertex; the sign is arbitrary.

## read\_field

```python
read_field(path, vertices, faces)
```

Read a direction field, one `x y z` per line, spaces or commas. **Returns** `(field, on)`: the vectors, and `"vertices"`
or `"faces"`, as the number of lines matches the vertices or the faces of the mesh.

## face\_to\_vertex\_field

```python
face_to_vertex_field(vertices, faces, field)
```

A field per face as a field per vertex, as `2_trajectories.py` reads it: the faces around each vertex averaged, weighted
by their area, after turning the face vectors to agree, a direction field having no sign; projected into the tangent
plane, with consistent signs. `scripts/fab/1.1_viewfield.py` writes it for a field given per face.

## project\_field

```python
project_field(vertices, faces, field)
```

A field, one vector or one per vertex, projected into the tangent plane at each vertex, unit length; zero where it
is along the normal.

## vertex\_normals

```python
vertex_normals(vertices, faces)
```

Unit normals per vertex, the area-weighted average of the face normals.
