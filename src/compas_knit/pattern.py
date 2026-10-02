"""Knitting pattern from the stitches: the order of the courses, and a bitmap for the machine.

Each trajectory is knitted out and back, as two rows of the bitmap, one pixel per stitch. A trajectory is
knitted after all the trajectories it sits on, its neighbours before it along the field, and each stitch
is placed in the column of the stitch below it.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import pickle

import numpy as np
from scipy.spatial import cKDTree

from compas_knit.stripes import break_cycles
from compas_knit.stripes import order_trajectories


__all__ = [
    "knitting_sequence",
    "course_directions",
    "stitch_columns",
    "boundary_polylines",
    "sample_polyline",
    "read_feature",
    "pattern_image",
    "write_feature",
    "knitting_pattern",
    "knittable",
    "write_pattern",
]


OUT = (0, 0, 0)  # the row knitting out, along the trajectory
BACK = (255, 0, 0)  # the row knitting back


def knitting_sequence(links, n):
    """The order to knit the trajectories in.

    A trajectory comes after all the trajectories it sits on. After a trajectory, the sequence continues with
    one it leads to, when that one is ready, so that a block of short rows is knitted in one go, straight after
    the course it starts from. Otherwise it continues with the ready trajectory earliest in the knitting order;
    one with nothing below it counts as due just before the first trajectory it leads to.

    Parameters
    ----------
    links : list[tuple[int, int, int]]
        As returned by :func:`compas_knit.stripes.read_neighbours`.
    n : int
        The number of trajectories.

    Returns
    -------
    tuple[list[int], int]
        The trajectories in knitting order, and how many links were cut where the links close on themselves, the
        weakest of each cycle, see :func:`compas_knit.stripes.break_cycles`: where the knitting needs a seam.

    """
    links, cut = break_cycles(links, n)
    position, _ = order_trajectories(links, n)
    before = [[] for _ in range(n)]
    after = [[] for _ in range(n)]
    for a, b, edges in links:
        before[b].append(a)
        after[a].append((edges, b))
    # a trajectory with nothing below it, a stray piece in the middle of the fabric or a bottom row, is due just
    # before the first trajectory it leads to, so that a stray piece is not knitted first, on its own
    due = [
        min(position[b] for _, b in after[i]) - 1 if not before[i] and after[i] else position[i]
        for i in range(n)
    ]
    waiting = [len(before[i]) for i in range(n)]
    placed = [False] * n
    sequence = []
    last = None
    while len(sequence) < n:
        # a trajectory the last one leads to, the longest shared first
        nxt = None
        if last is not None:
            ready = [(edges, b) for edges, b in after[last] if not placed[b] and waiting[b] == 0]
            if ready:
                nxt = max(ready)[1]
        if nxt is None:
            ready = [i for i in range(n) if not placed[i] and waiting[i] == 0]
            nxt = min(ready, key=lambda i: (due[i], i))
        placed[nxt] = True
        sequence.append(nxt)
        for _, b in after[nxt]:
            waiting[b] -= 1
        last = nxt
    return sequence, len(cut)


def course_directions(mesh, field):
    """A function giving the course direction, across the field in the surface, at points on the mesh.

    Parameters
    ----------
    mesh : str | :class:`compas.datastructures.Mesh`
        The mesh, or the path to an ``.obj`` file.
    field : str | array-like
        The directional field per vertex, or the path to its file.

    Returns
    -------
    callable
        ``directions(points)``: unit vectors, normal x field at the nearest vertex, in either sense.

    """
    from compas_knit.stripes import _mesh_arrays
    from compas_knit.stripes import _vertex_normals

    xyz, faces = _mesh_arrays(mesh)
    if isinstance(field, str):
        field = np.loadtxt(field)
    field = np.asarray(field, dtype=float)[:, :3]
    if len(field) != len(xyz):
        raise ValueError("The field has {} vectors, the mesh {} vertices.".format(len(field), len(xyz)))
    normals = _vertex_normals(xyz, faces)
    course = np.cross(normals, field)
    course /= np.maximum(np.linalg.norm(course, axis=1), 1e-12)[:, None]
    tree = cKDTree(xyz)
    return lambda points: course[tree.query(points)[1]]


def _below(above, below, tree, gap, across=None):
    """For each stitch of a trajectory, where it sits on the trajectory below, as a fractional stitch index.

    Following the wale, the stitch sits where the line through it along the field crosses the trajectory below:
    between the two stitches below on either side of that line, found among the stitches nearest to it. Without
    the course directions ``across``, it sits on the nearest stitch below. Stitches farther than 1.5 ``gap`` from
    the trajectory below, beyond its ends, sit on nothing and get NaN.
    """
    d, j = tree.query(above)
    index = j.astype(float)
    if across is not None:
        c = across(above)
        n = len(below)
        for k in range(len(above)):
            # the offset across the wale of the stitches below around the nearest one; the wale crosses where it
            # changes sign
            lo, hi = max(j[k] - 2, 0), min(j[k] + 2, n - 1)
            side = (below[lo:hi + 1] - above[k]) @ c[k]
            found = np.nan
            best = np.inf
            for m in range(len(side) - 1):
                if side[m] == 0 or side[m] * side[m + 1] < 0:
                    t = side[m] / (side[m] - side[m + 1]) if side[m] != side[m + 1] else 0.0
                    if abs(lo + m + t - j[k]) < best:
                        best, found = abs(lo + m + t - j[k]), lo + m + t
            index[k] = found
    index[d > 1.5 * gap] = np.nan
    return index


def stitch_columns(stitches, links, sequence=None, across=None, alignment=None, weight=100.0):
    """The column of the first stitch of each trajectory, the others following one column apart.

    A stitch belongs in the column of the stitch it sits on in the trajectory below: following the wale when the
    course directions ``across`` are given, see :func:`course_directions`, otherwise the nearest stitch. Each link so
    says how many columns the trajectory above starts from the one below, the median over its stitches, and the
    columns of all trajectories are solved together, by least squares over all links, which spreads the differences
    as smoothly as the links allow. With ``alignment``, the given stitches are moreover held in one column.

    Parameters
    ----------
    stitches : list[list[list[float]]]
        The stitches of each trajectory, as returned by :func:`compas_knit.stripes.generate_stripes`.
    links : list[tuple[int, int, int]]
        The links between neighbouring trajectories.
    sequence : list[int], optional
        The knitting order, see :func:`knitting_sequence`. Only the links it knits from below to above are used, so
        where the links close on themselves, the columns open up at the seam where the sequence broke the cycle.
    across : callable, optional
        The course directions, see :func:`course_directions`.
    alignment : list[tuple[int, int]], optional
        Stitches to hold in one column, as (trajectory, stitch index).
    weight : float, optional
        How strongly the alignment is held, against one stitch of a link.

    Returns
    -------
    tuple[list[int], dict[int, np.ndarray]]
        The column of the first stitch of each trajectory, the stitches running towards lower columns, and for each
        trajectory with trajectories below it, the column offset of each stitch from the stitch below it, 0 where they
        line up, NaN where there is none.

    """
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    from scipy.sparse.linalg import lsqr

    n = len(stitches)
    points = [np.asarray(s, dtype=float) for s in stitches]
    trees = [cKDTree(p) for p in points]
    if sequence is not None:
        rank = {i: r for r, i in enumerate(sequence)}
        links = [(a, b, e) for a, b, e in links if rank[a] < rank[b]]
    # stitches that sit on each other are about one course apart
    gap = np.median(np.concatenate([trees[a].query(points[b])[0] for a, b, _ in links])) if links else 0.0

    below = {}
    for a, b, _ in links:
        below[(a, b)] = _below(points[b], points[a], trees[a], gap, across)

    # unknowns: the start column of each trajectory, and the column of the alignment
    column = n
    rows, cols, vals, rhs, weights = [], [], [], [], []

    def equation(terms, value, w):
        for c, v in terms:
            rows.append(len(rhs))
            cols.append(c)
            vals.append(v)
        rhs.append(value)
        weights.append(w)

    for (a, b), index in below.items():
        on = ~np.isnan(index)
        if on.any():
            k = np.nonzero(on)[0]
            # stitch k of b in column start_b - k sits at index j of a, in column start_a - j
            equation([(b, 1.0), (a, -1.0)], float(np.median(k - index[k])), np.sqrt(len(k)))
    for i, k in alignment or []:
        equation([(i, 1.0), (column, -1.0)], float(k), weight)
    # one trajectory of each connected part at column 0
    m = len(rhs)
    graph = coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(max(m, 1), n + 1)).tocsr()
    parts, label = connected_components((graph.T @ graph).tocsr(), directed=False)
    for part in range(parts):
        equation([(int(np.nonzero(label == part)[0][0]), 1.0)], 0.0, 1.0)
    w = np.array(weights)
    A = coo_matrix((np.array(vals) * w[np.array(rows)], (rows, cols)), shape=(len(rhs), n + 1)).tocsr()
    solution = lsqr(A, np.array(rhs) * w, atol=1e-12, btol=1e-12, iter_lim=100000)[0]
    start = np.round(solution[:n] - (solution[column] if alignment else 0)).astype(int).tolist()

    offsets = {}
    for (a, b), index in below.items():
        # a stitch sits on the trajectory below it that it lies on, the first found
        wanted = start[a] - index + np.arange(len(points[b]))
        current = offsets.get(b)
        offset = start[b] - wanted
        offsets[b] = offset if current is None else np.where(np.isnan(current), offset, current)
    return start, offsets


def boundary_polylines(mesh, corner=60.0):
    """The boundary of a mesh, split into polylines at its corners.

    Parameters
    ----------
    mesh : str | :class:`compas.datastructures.Mesh`
        The mesh, or the path to an ``.obj``.
    corner : float, optional
        A boundary vertex where the boundary turns by more than this, in degrees, is a corner.

    Returns
    -------
    list[np.ndarray]
        The points of each piece of the boundary between two corners, or of a whole boundary loop without corners.

    """
    from compas_knit.stripes import _mesh_arrays

    xyz, faces = _mesh_arrays(mesh)
    count = {}
    for f in faces:
        for k in range(3):
            a, b = int(f[k]), int(f[(k + 1) % 3])
            key = (min(a, b), max(a, b))
            count[key] = count.get(key, 0) + 1
    # the boundary edges, in the direction of their face, so that they chain head to tail
    following = {}
    for f in faces:
        for k in range(3):
            a, b = int(f[k]), int(f[(k + 1) % 3])
            if count[(min(a, b), max(a, b))] == 1:
                following[a] = b
    pieces = []
    seen = set()
    for start in following:
        if start in seen:
            continue
        loop = [start]
        seen.add(start)
        while following[loop[-1]] != start:
            loop.append(following[loop[-1]])
            seen.add(loop[-1])
        p = xyz[loop]
        before = p - np.roll(p, 1, axis=0)
        after = np.roll(p, -1, axis=0) - p
        cos = (before * after).sum(1) / np.maximum(np.linalg.norm(before, axis=1) * np.linalg.norm(after, axis=1), 1e-12)
        corners = np.nonzero(cos < np.cos(np.radians(corner)))[0]
        if len(corners) == 0:
            pieces.append(np.vstack([p, p[:1]]))
            continue
        for i, c in enumerate(corners):
            d = corners[(i + 1) % len(corners)]
            idx = np.arange(c, d + 1) if d > c else np.concatenate([np.arange(c, len(p)), np.arange(0, d + 1)])
            pieces.append(p[idx])
    return pieces


def sample_polyline(points, step):
    """Points along a polyline, ``step`` apart along it, from its start to its end."""
    points = np.asarray(points, dtype=float)
    lengths = np.linalg.norm(np.diff(points, axis=0), axis=1)
    along = np.concatenate([[0], np.cumsum(lengths)])
    at = np.linspace(0, along[-1], max(int(np.ceil(along[-1] / step)), 1) + 1)
    return np.array([np.interp(at, along, points[:, k]) for k in range(3)]).T


def read_feature(path):
    """Read a feature: points and lines, from an ``.obj`` as Rhino exports it, or points from a ``.txt``.

    In an ``.obj``, the points are the vertices of the ``p`` records and the lines the polylines of the ``l`` records;
    a file with neither is read as points, all its vertices. A ``.txt`` is a feature file as the Grasshopper definition
    writes it, one ``x,y,z; r,g,b`` per line, read as points.

    Returns
    -------
    dict
        ``points``: an (n, 3) array, ``lines``: a list of (m, 3) arrays.

    """
    if path.endswith(".txt"):
        points = []
        with open(path, "r") as f:
            for line in f:
                if line.strip():
                    points.append([float(c) for c in line.split(";")[0].split(",")])
        return {"points": np.array(points).reshape(-1, 3), "lines": []}

    vertices, points, lines = [], [], []

    def index(token):
        i = int(token.split("/")[0])
        return i - 1 if i > 0 else len(vertices) + i

    with open(path, "r") as f:
        for line in f:
            parts = line.split()
            if not parts:
                continue
            if parts[0] == "v":
                vertices.append([float(c) for c in parts[1:4]])
            elif parts[0] == "p":
                points += [index(t) for t in parts[1:]]
            elif parts[0] == "l":
                lines.append([index(t) for t in parts[1:]])
    vertices = np.array(vertices).reshape(-1, 3)
    if not points and not lines:
        return {"points": vertices, "lines": []}
    return {"points": vertices[points].reshape(-1, 3), "lines": [vertices[line] for line in lines if len(line) > 1]}


def write_feature(path, points=(), lines=()):
    """Write a feature as an ``.obj``: the points as ``p`` records, the lines as ``l`` records, see :func:`read_feature`."""
    with open(path, "w") as f:
        n = 0
        for p in points:
            f.write("v {} {} {}\np {}\n".format(p[0], p[1], p[2], n + 1))
            n += 1
        for line in lines:
            for p in line:
                f.write("v {} {} {}\n".format(p[0], p[1], p[2]))
            f.write("l {}\n".format(" ".join(str(n + 1 + k) for k in range(len(line)))))
            n += len(line)


def knitting_pattern(stitches, links, mesh=None, field=None, alignment=None, features=None, reach=1.5):
    """The bitmap of the knitting pattern, one pixel per stitch, two rows per trajectory.

    The stitches are placed in the column of the stitch they sit on, following the wale when the mesh and its field
    are given, the nearest stitch below otherwise, solved over all the trajectories together. With ``alignment``,
    the stitches at the given points are held in one column, and the others follow.

    Parameters
    ----------
    stitches : list[list[list[float]]] | list[:class:`compas.geometry.Polyline`]
        The stitches of each trajectory, in the order of ``_tri_path_recons.txt``.
    links : list[tuple[int, int, int]]
        The links between neighbouring trajectories, see :func:`compas_knit.stripes.read_neighbours`.
    mesh : str | :class:`compas.datastructures.Mesh`, optional
        The mesh of the field, or the path to its ``.obj``.
    field : str | array-like, optional
        The directional field per vertex, or the path to its file.
    alignment : dict | list[list[float]], optional
        A feature, see :func:`read_feature`, or points, whose stitches are held in one column: of a line, in each course
        it passes, the stitch closest to it.
    features : list[tuple[dict, tuple[int, int, int]]], optional
        Stitches to colour, as (feature, colour): each point of a feature takes the stitch nearest to it, and each line
        every stitch it passes over, within ``reach``. The stitches take the colour in both rows of their trajectory;
        where features share a stitch, the later one wins.
    reach : float, optional
        How far a feature reaches for its stitches, in stitch widths. On the boundary, the nearest stitch is the end of
        a course, up to one stitch short of the boundary and half a course spacing to the side.

    Raises
    ------
    ValueError
        If trajectories are closed rings, courses knitted in the round, which need a seam.

    Returns
    -------
    dict
        ``pixels``: ``{(x, y): (r, g, b)}``, from (0, 0), the row knitting out of each trajectory black at even y,
        the row knitting back red at y + 1, the stitches running towards lower x, as the pixel data of the
        earlier scripts. ``sequence``: the trajectories in knitting order, ``rows[i]``: the first row of
        trajectory i, ``offsets[i]``: the column offset of each of its stitches from the stitch below it,
        ``aligned``: the aligned stitches, as (trajectory, stitch index), ``colored``: the coloured stitches of each
        feature, ``breaks``: the number of links cut where they closed on themselves, the weakest of each cycle.

    """
    stitches = [[list(p) for p in (s.points if hasattr(s, "points") else s)] for s in stitches]
    # a trajectory closing on itself is a course knitted in the round, which needs a seam to lie in a flat bitmap
    width = np.median(np.concatenate([np.linalg.norm(np.diff(s, axis=0), axis=1) for s in stitches if len(s) > 1]))
    rings = [i for i, s in enumerate(stitches) if len(s) > 2 and np.linalg.norm(np.subtract(s[0], s[-1])) < 1.5 * width]
    if rings:
        raise ValueError(
            "{} trajectories are closed rings, courses knitted in the round, e.g. around a pole: {}. "
            "They need a seam to be knitted flat.".format(len(rings), rings[:10])
        )
    sequence, breaks = knitting_sequence(links, len(stitches))
    if breaks:
        print("warning: the links close on themselves; {} links cut, the weakest of each cycle, "
              "which is where the knitting needs a seam".format(breaks))

    # the stitches of the features: nearest to each point, and to the samples of each line, finer than a stitch
    owner = np.concatenate([np.full(len(s), i) for i, s in enumerate(stitches)])
    index = np.concatenate([np.arange(len(s)) for s in stitches])
    tree = cKDTree(np.vstack(stitches))

    def feature_stitches(feature, what):
        if not isinstance(feature, dict):
            feature = {"points": np.asarray(feature, dtype=float).reshape(-1, 3), "lines": []}
        found = {}
        groups = [("point", feature["points"])] if len(feature["points"]) else []
        groups += [("line", sample_polyline(line, width / 4)) for line in feature["lines"]]
        points_out, lines_out = 0, 0
        for kind, points in groups:
            d, nearest = tree.query(np.asarray(points, dtype=float)[:, :3])
            on = d <= reach * width
            for dist, k in zip(d[on], nearest[on]):
                stitch = (int(owner[k]), int(index[k]))
                found[stitch] = min(dist, found.get(stitch, np.inf))
            if kind == "point":
                points_out += int((~on).sum())
            elif not on.any():
                lines_out += 1
        if points_out:
            print("warning: {} points of {} are out of reach of any stitch".format(points_out, what))
        if lines_out:
            print("warning: {} lines of {} are out of reach of any stitch".format(lines_out, what))
        return found

    aligned = []
    if alignment is not None:
        # of a line, one stitch in each course, the closest
        closest = {}
        for (i, k), dist in feature_stitches(alignment, "the alignment").items():
            if dist < closest.get(i, (np.inf, None))[0]:
                closest[i] = (dist, k)
        aligned = sorted((i, k) for i, (_, k) in closest.items())
    colors, colored = {}, []
    for n, (feature, color) in enumerate(features or []):
        colored.append(sorted(feature_stitches(feature, "feature {}".format(n))))
        for stitch in colored[-1]:
            colors[stitch] = tuple(color)

    across = course_directions(mesh, field) if mesh is not None and field is not None else None
    start, offsets = stitch_columns(stitches, links, sequence, across, aligned)
    lowest = min(start[i] - len(stitches[i]) + 1 for i in sequence)
    pixels = {}
    rows = {}
    for row, i in enumerate(sequence):
        y = 2 * row
        rows[i] = y
        for k in range(len(stitches[i])):
            x = start[i] - k - lowest
            color = colors.get((i, k))
            pixels[(x, y)] = color or OUT
            pixels[(x, y + 1)] = color or BACK
    return {
        "pixels": pixels,
        "sequence": sequence,
        "rows": rows,
        "offsets": offsets,
        "aligned": aligned,
        "colored": colored,
        "breaks": breaks,
    }


ADDED = (0, 0, 200)  # the stitches added at the boundary to carry the yarn, as the earlier post-processing coloured them


def knittable(pixels, gap=3, reach=50, added=ADDED):
    """Make the pattern knittable from one yarn carrier, row after row from the bottom right corner (Section 6.2.4).

    In the bitmap the first row is at the bottom. The carrier knits a black row from right to left, the red row above it
    back from left to right, then the next black row from right to left, and so on. So a black row and its red row
    turn at their left end, and consecutive trajectories meet at the right end:

    * where the next black row starts further right than the red row ended, the red row is continued to it, if there
      are no stitches beneath: the addition is at the boundary, so it hardly changes the geometry; where there are, the
      red row turns late instead: it takes over the end of the next red row, over those needles;
    * where it starts more than ``gap`` needles further left, the black stitches above those needles are moved down
      into it, from the nearest black row above, keeping every column in order; where there is nothing above, it is at
      the boundary, and stitches are added;
    * where that cannot be done, a short row ending inside the fabric on the right, the red row before it turns early,
      where the black row starts, and the rest of it is knitted by the short row's red row on its way back to the
      right. Turned early or late, every needle keeps its number of rows, only their order changes.

    The added stitches take the colour ``added``.

    Parameters
    ----------
    pixels : dict
        ``{(x, y): (r, g, b)}``, see :func:`knitting_pattern`: black rows at even y, red rows at odd y, from y = 0 at the
        bottom of the bitmap, x growing to the right.
    gap : int, optional
        A black row starting this many needles or fewer from where the yarn is is left as it is.
    reach : int, optional
        How many rows up the black rows are searched.
    added : tuple[int, int, int], optional
        The colour of the stitches added at the boundary.

    Returns
    -------
    tuple[dict, dict]
        The pixels, and a report: ``moved`` stitches, stitches ``added``, and the transitions left open: red rows that
        could not be continued because of stitches beneath, ``red_open``, black rows that could not be connected,
        ``black_open``, and red rows not starting where their black row ended, ``turn_open``; and the red rows that
        ``turned`` early for a short row on the right.

    """
    rows = {}
    for (x, y), color in pixels.items():
        rows.setdefault(y, {})[x] = color
    top = max(rows)
    report = {"moved": 0, "added": 0, "turned": 0, "red_open": 0, "black_open": 0, "turn_open": 0}

    for y in range(1, top + 1):
        if not rows.get(y) or not rows.get(y - 1):
            continue
        if y % 2:
            # a red row: it goes back from where its black row ended, on the left
            if min(rows[y]) != min(rows[y - 1]):
                report["turn_open"] += 1
            continue

        end, start = max(rows[y - 1]), max(rows[y])  # the red row ends at its right, the black row starts at its right
        if start - end > gap:
            # continue the red row to the start, if there is nothing beneath
            needles = range(end + 1, start + 1)
            if any(x in rows.get(q, {}) for q in range(y - 1) for x in needles):
                # the red row turns late instead: it takes the end of the next red row, the black row's own, over
                # these needles, which keeps the number of rows on each of them
                red = rows.get(y + 1, {})
                if all(x in red for x in needles) and max(red) == start and not any(x in rows[y - 1] for x in needles):
                    for x in needles:
                        rows[y - 1][x] = red.pop(x)
                    report["turned"] += 1
                else:
                    report["red_open"] += 1
            else:
                for x in needles:
                    rows[y - 1][x] = added
                    report["added"] += 1
        elif end - start > gap:
            # move down the black stitches above those needles, or add stitches where there are none
            moved, made, failed = [], [], False
            x = start + 1
            while x <= end:
                above = next((q for q in range(y + 2, min(y + reach, top + 1), 2) if x in rows.get(q, {})), None)
                if above is None:
                    if any(x in rows.get(q, {}) for q in range(y + 1, top + 1)):
                        failed = True  # stitches above, but no black one within reach
                        break
                    for c in range(x, end + 1):  # nothing above: the boundary
                        rows[y][c] = added
                        made.append(c)
                    break
                run = [c for c in sorted(rows[above]) if c >= x]
                # moved down, a stitch passes the rows in between: none of them may have a stitch in its column, and the
                # row it leaves has to stay in one piece, so its part beyond where the yarn is cannot be left behind
                if run[-1] > end or any(c in rows.get(q, {}) for q in range(y + 1, above) for c in run):
                    failed = True
                    break
                for c in run:
                    rows[y][c] = rows[above].pop(c)
                    moved.append((c, above))
                x = run[-1] + 1
            if failed:
                # undo, and turn the red row early instead, if the short row's red row can take the rest of it
                for c, above in moved:
                    rows[above][c] = rows[y].pop(c)
                for c in made:
                    del rows[y][c]
                moved, made = [], []
                red, tail = rows.get(y + 1), [c for c in rows[y - 1] if c > start]
                if red and max(red) == start and not any(c in red or c in rows[y] for c in tail):
                    for c in tail:
                        red[c] = rows[y - 1].pop(c)
                    report["turned"] += 1
                else:
                    report["black_open"] += 1
            report["moved"] += len(moved)
            report["added"] += len(made)

    out = {(x, y): c for y, row in rows.items() for x, c in row.items()}
    return out, report


VIEW_COLORS = {BACK: (160, 160, 160)}  # to look at the pattern: the rows knitting back grey, the others as they are


def pattern_image(pixels, scale=1, colors=None):
    """The pattern as an image, one pixel per stitch, the first row at the bottom, as the bitmap for the machine.

    Parameters
    ----------
    pixels : dict
        ``{(x, y): (r, g, b)}``, see :func:`knitting_pattern`.
    scale : int, optional
        Pixels per stitch, to look at it.
    colors : dict, optional
        Colours to show in place of others, e.g. :data:`VIEW_COLORS`, the rows knitting back grey; the bitmap for the
        machine keeps its colours, which code the operations.

    Returns
    -------
    :class:`PIL.Image.Image`

    """
    from PIL import Image

    xs = [x for x, _ in pixels]
    ys = [y for _, y in pixels]
    x0, y0 = min(xs), min(ys)
    image = Image.new("RGB", (max(xs) - x0 + 1, max(ys) - y0 + 1), "white")
    colors = colors or {}
    for (x, y), color in pixels.items():
        image.putpixel((x - x0, y - y0), colors.get(color, color))
    image = image.transpose(Image.FLIP_TOP_BOTTOM)
    if scale > 1:
        image = image.resize((image.width * scale, image.height * scale), Image.NEAREST)
    return image


def write_pattern(pixels, bitmap_path, pickle_path=None, bed_width=None):
    """Write the pattern as a bitmap, flipped top to bottom for the machine software, and the pixel data.

    Parameters
    ----------
    pixels : dict
        ``{(x, y): (r, g, b)}``, see :func:`knitting_pattern`.
    bitmap_path : str
        The ``.bmp`` to write.
    pickle_path : str, optional
        Also write the pixel data, as ``_pixel_data_dict.pkl`` for the post-processing scripts.
    bed_width : int, optional
        Raise an error if the pattern is wider than the needle bed.

    Returns
    -------
    tuple[int, int]
        The width and height of the bitmap.

    """
    image = pattern_image(pixels)
    width, height = image.size
    if bed_width and width > bed_width:
        raise ValueError("The pattern is {} stitches wide, more than the needle bed of {}.".format(width, bed_width))
    image.save(bitmap_path)
    if pickle_path:
        with open(pickle_path, "wb") as f:
            pickle.dump(pixels, f)
    return width, height
