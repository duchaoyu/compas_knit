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

from compas_knit.stripes import order_trajectories


__all__ = ["knitting_sequence", "course_directions", "stitch_columns", "read_features", "knitting_pattern", "write_pattern"]


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
        The trajectories in knitting order, and how many times a cycle of links had to be broken: where the links
        close on themselves, the sequence continues with the trajectory with the most of its neighbours below it
        already knitted, which is where the knitting needs a seam.

    """
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
    breaks = 0
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
            if ready:
                nxt = min(ready, key=lambda i: (due[i], i))
            else:
                # a cycle: continue where the most of the neighbours below are knitted
                rest = [i for i in range(n) if not placed[i]]
                nxt = max(rest, key=lambda i: (len(before[i]) - waiting[i], -position[i], -i))
                breaks += 1
        placed[nxt] = True
        sequence.append(nxt)
        for _, b in after[nxt]:
            waiting[b] -= 1
        last = nxt
    return sequence, breaks


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


def read_features(path):
    """Read a feature file, as written by the Grasshopper definition: one ``x,y,z; r,g,b`` per line.

    Returns
    -------
    list[tuple[list[float], tuple[int, int, int]]]
        The points and their colours.

    """
    features = []
    with open(path, "r") as f:
        for line in f:
            if line.strip():
                point, color = line.strip().split(";")
                features.append(([float(c) for c in point.split(",")], tuple(int(c) for c in color.split(","))))
    return features


def knitting_pattern(stitches, links, mesh=None, field=None, alignment=None):
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
    alignment : list[tuple[list[float], tuple[int, int, int]]], optional
        Points to align the stitches at, with their colours, as returned by :func:`read_features`. Each point takes
        the stitch nearest to it, within one stitch width; these stitches are held in one column and keep the colour
        of their point in the pattern.

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
        ``aligned``: the aligned stitches, as (trajectory, stitch index), ``breaks``: the number of cycles broken.

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
        print("warning: the links close on themselves in {} places; the sequence breaks them there, "
              "which is where the knitting needs a seam".format(breaks))

    # the stitches at the alignment points
    aligned, colors = [], {}
    if alignment:
        owner = np.concatenate([np.full(len(s), i) for i, s in enumerate(stitches)])
        index = np.concatenate([np.arange(len(s)) for s in stitches])
        d, nearest = cKDTree(np.vstack(stitches)).query([p for p, _ in alignment])
        for (point, color), dist, k in zip(alignment, d, nearest):
            if dist <= width:
                aligned.append((int(owner[k]), int(index[k])))
                colors[aligned[-1]] = color
        if len(aligned) < len(alignment):
            print("warning: {} alignment points are farther than a stitch from any stitch".format(len(alignment) - len(aligned)))

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
    return {"pixels": pixels, "sequence": sequence, "rows": rows, "offsets": offsets, "aligned": aligned, "breaks": breaks}


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
    from PIL import Image

    xs = [x for x, _ in pixels]
    ys = [y for _, y in pixels]
    width = max(xs) - min(xs) + 1
    height = max(ys) - min(ys) + 1
    if bed_width and width > bed_width:
        raise ValueError("The pattern is {} stitches wide, more than the needle bed of {}.".format(width, bed_width))
    x0, y0 = min(xs), min(ys)
    image = Image.new("RGB", (width, height), "white")
    for (x, y), color in pixels.items():
        image.putpixel((x - x0, y - y0), color)
    image.transpose(Image.FLIP_TOP_BOTTOM).save(bitmap_path)
    if pickle_path:
        with open(pickle_path, "wb") as f:
            pickle.dump(pixels, f)
    return width, height
