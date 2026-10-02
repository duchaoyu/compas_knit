# compas\_knit.pattern

The knitting pattern from the stitches: the order of the courses, and a bitmap for the machine.

```python
from compas_knit.pattern import knitting_pattern, write_pattern
```

Each trajectory is knitted out and back, as two rows of the bitmap, one pixel per stitch. A trajectory is knitted
after all the trajectories it sits on, and each stitch is placed in the column of the stitch below it.

## knitting\_pattern

```python
knitting_pattern(stitches, links, mesh=None, field=None, alignment=None, features=None, reach=1.5)
```

The stitches are placed in the column of the stitch they sit on: following the wale when the mesh and its field are
given, where the line through the stitch along the field crosses the course below; the nearest stitch below otherwise.
The columns of all courses are solved together by least squares, which spreads the differences as smoothly as the
links allow. With `alignment`, the stitches at the given points are held in one column, e.g. a straight selvedge or
a wale line, and the rest follow.

| Parameter | Type | Description |
|---|---|---|
| `stitches` | `list[Polyline]` | the stitches of each trajectory, as returned by [`generate_stripes`](stripes.md#generate_stripes) |
| `links` | `list[tuple]` | from [`read_neighbours`](stripes.md#read_neighbours) |
| `mesh`, `field` | `str` or `Mesh`, `str` or array | the mesh and its directional field, to follow the wales |
| `alignment` | `dict` or points | a feature from [`read_feature`](#read_feature), or points, whose stitches are held in one column; of a line, one stitch per course, the closest |
| `features` | `list[tuple]` | `(feature, colour)`: the stitches of each feature take the colour in both rows of their course; a later feature wins where they share a stitch |
| `reach` | `float` | how far a feature reaches for its stitches, in stitch widths |

**Returns** `dict`:
* `pixels` — `{(x, y): (r, g, b)}` from (0, 0): the row knitting out black at even `y`, the row knitting back red at
  `y + 1`, the stitches running towards lower `x`; the pixel data of the post-processing scripts
* `sequence` — the trajectories in knitting order; `rows[i]` — the first row of trajectory `i`
* `offsets[i]` — the column offset of each stitch of trajectory `i` from the stitch below it, 0 where they line up
* `aligned` — the aligned stitches, as (trajectory, stitch index); `colored` — the coloured stitches of each feature
* `breaks` — how many links were cut where they closed on themselves, the weakest of each cycle, where the knitting needs a seam

**Raises** `ValueError` if trajectories are closed rings, courses knitted in the round, which need a seam.

## knittable

```python
knittable(pixels, gap=3, reach=50, added=(0, 0, 200))
```

Make the pattern knittable from one yarn carrier, row after row from the bottom right corner (Section 6.2.4). In the
bitmap the first row is at the bottom; the carrier knits a black row from right to left, the red row above it back from
left to right, then the next black row from right to left. A black row and its red row turn at their left end, and
consecutive trajectories meet at the right end:

* where the next black row starts further right than the red row ended, the red row is continued to it, if there are no
  stitches beneath — the addition is at the boundary, so it hardly changes the geometry;
* where it starts more than `gap` needles further left, the black stitches above those needles are moved down into it,
  from the nearest black row above, every column keeping its stitches in order; where there is nothing above, it is at
  the boundary, and stitches are added.

Where neither works, a short row ending inside the fabric on the right, the red row turns there instead: early, the
short row's own red row knitting the rest of it on the way back to the right, or late, taking over the end of the
next red row. Every needle keeps its number of rows; only their order changes, and the yarn is continuous.

Added stitches take the colour `added`. `scripts/fab/4_pattern.py` runs it after `knitting_pattern`.

**Returns** `(pixels, report)`, the report giving the `moved` and `added` stitches, the red rows `turned` early or
late, and the transitions left open.

## knitting\_sequence

```python
knitting_sequence(links, n)
```

The order to knit the trajectories in. After a trajectory, the sequence continues with one it leads to when that one
is ready, so a block of short rows is knitted in one go, straight after the course it starts from; otherwise with the
ready trajectory earliest in the knitting order. **Returns** `(sequence, breaks)`.

## stitch\_columns

```python
stitch_columns(stitches, links, sequence=None, across=None, alignment=None, weight=100.0)
```

The column of the first stitch of each trajectory. Each link gives how many columns the trajectory above starts from
the one below, the median over the stitches that sit on each other, following the wale with the course directions
`across`; all columns are solved together by least squares, the `alignment` stitches held in one column.
**Returns** `(start, offsets)`.

## read\_feature

```python
read_feature(path)
```

Read a feature: points and lines, from an `.obj` as Rhino exports it — the vertices of the `p` records as points, the
polylines of the `l` records as lines — or points from a `.txt` feature file of the Grasshopper definition, one
`x,y,z; r,g,b` per line. **Returns** `dict` — `points`, an (n, 3) array, and `lines`, a list of (m, 3) arrays.

A point takes the stitch nearest to it; a line every stitch it passes over, in each course it crosses the stitch at
the crossing, and along a course the stitches it runs along.

## write\_feature

```python
write_feature(path, points=(), lines=())
```

Write a feature as an `.obj`, the points as `p` records and the lines as `l` records.

## boundary\_polylines

```python
boundary_polylines(mesh, corner=60.0)
```

The boundary of a mesh, split at its corners, where it turns by more than `corner` degrees.
**Returns** `list[np.ndarray]` — the points of each piece. `scripts/fab/3_features.py` takes the piece furthest to the
left as the cable and writes it as a line to `features/cable.obj`, for when there is none drawn in Rhino.
`scripts/fab/4_pattern.py` aligns the stitches at the cable, a straight selvedge along it.

## sample\_polyline

```python
sample_polyline(points, step)
```

Points along a polyline, `step` apart along it.

## course\_directions

```python
course_directions(mesh, field)
```

A function giving the course direction, normal × field at the nearest vertex, at points on the mesh.

## write\_pattern

```python
write_pattern(pixels, bitmap_path, pickle_path=None, bed_width=None)
```

Write the bitmap, flipped top to bottom for the machine software, and optionally the pixel data as
`_pixel_data_dict.pkl`. **Raises** `ValueError` if wider than `bed_width`. **Returns** `(width, height)`.
