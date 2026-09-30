# Your first trajectories

**You will:** compute knitting trajectories in Python, check them, and view them.
**Time:** 10 minutes. **Needs:** [Installation](../getting-started/installation.md).

## 1. Compute the trajectories

```python
import os
from compas_knit.stripes import generate_stripes

folder = "/path/to/your/model"
name = "2part_remesh2"
mesh_path = os.path.join(folder, name + ".obj")
field_path = os.path.join(folder, name + "_vertex_directional_field.txt")

trajectories = generate_stripes(mesh_path, field_path, stitch_height=2.297, out_dir=os.path.join(folder, "out"))
print(len(trajectories), "trajectories")
```

`stripes` prints how many singularities it found; one trajectory ends at each.

## 2. Check them

```python
from compas_knit.stripes import check_trajectories

for i, j, angle in check_trajectories(trajectories, mesh_path, field_path):
    print("trajectory", i, "segment", j, "is", round(angle), "degrees from the field")
```

An empty list means every segment runs across the field.

## 3. View them

```python
from compas_knit.viewer import view_stripes

view_stripes(os.path.join(folder, "out", name + "_remesh.obj"), trajectories)
```

The viewer opens in top view. Switch views under **View**, and hide the mesh in the scene panel.

<!-- TODO: screenshot -->

## 4. Try another stitch height

<!-- TODO: exercise — halve the stitch height, compare the number of trajectories -->

## What's next

* [Comparing directional fields](field-rotation.md)
