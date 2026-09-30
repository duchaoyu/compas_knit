# Comparing directional fields

**You will:** rotate the directional field in steps, compute the trajectories for each, and compare them
on a contact sheet. **Time:** 15 minutes, a few of them computing.

## 1. Set the inputs

Open `scripts/tests/field_rotation.py`:

```python
folder = "/path/to/your/model"
name = "2part_remesh2"

stitch_height = 2.297
step = 5  # degrees
```

Each vertex vector is rotated about the vertex normal. The field is a line field, so the angles run from 0 to 180°.

## 2. Run

```bash
python scripts/tests/field_rotation.py
```

## 3. Read the result

In `<folder>/out/field_rotation/`:

* `<angle>/` — the rotated field and its trajectories
* `summary.json` — per angle: trajectories, singularities, median gap and its 10–90 % range, suspect segments
* `field_rotation.png` — a top view per angle, red dots where a trajectory ends at a singularity, and the gap,
  singularities and trajectory count against the angle

<!-- TODO: the contact sheet -->
<!-- ![](../.gitbook/assets/field-rotation.png) -->

## 4. What to look for

* **Gap** — stays at `2 * stitch_height`, a little lower where there are many singularities.
* **Singularities** — fewer means a field the stripes can follow; on `2part_remesh2` the designed field (0°)
  has about 100, rotated by 90° about 270.

<!-- TODO: your conclusions -->
