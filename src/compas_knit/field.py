"""Directional fields: the smoothest line field on a mesh, held at chosen vertices.

The field is a line field, a direction without a sign, as the knitting needs: the wale. Each vertex has a tangent
basis, and the field there is the complex number z = exp(2 i theta), the angle doubled so that theta and theta + pi are
the same. The smoothest field minimises the change of z along the edges, after transporting it from one vertex to the
next (Knoppel et al. 2013, "Globally optimal direction fields"), with cotan weights. With some vertices held, the
others follow from a sparse linear solve; with none, it is the smallest eigenvector.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np
import scipy.sparse
import scipy.sparse.linalg


__all__ = ["smoothest_field", "axis_field", "orient_field", "face_to_vertex_field", "read_field", "vertex_normals", "project_field"]


def vertex_normals(vertices, faces):
    """Unit normals per vertex, the area-weighted average of the face normals."""
    V = np.asarray(vertices, dtype=float)
    F = np.asarray(faces)
    n = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    normals = np.zeros_like(V)
    for k in range(3):
        np.add.at(normals, F[:, k], n)
    return normals / np.maximum(np.linalg.norm(normals, axis=1), 1e-300)[:, None]


def project_field(vertices, faces, field):
    """The field projected into the tangent plane at each vertex, unit length; zero where it is along the normal."""
    normals = vertex_normals(vertices, faces)
    field = np.broadcast_to(np.asarray(field, dtype=float), normals.shape)
    t = field - (field * normals).sum(axis=1)[:, None] * normals
    length = np.linalg.norm(t, axis=1)
    return np.where(length[:, None] > 1e-9, t / np.maximum(length, 1e-300)[:, None], 0.0)


def read_field(path, vertices, faces):
    """Read a directional field, one ``x y z`` per line, per vertex or per face, as the number of lines says.

    Returns
    -------
    tuple[np.ndarray, str]
        The vectors, and ``"vertices"`` or ``"faces"``.

    """
    field = np.loadtxt(path, delimiter="," if "," in open(path).readline() else None, ndmin=2)[:, :3]
    n, m = len(vertices), len(faces)
    if len(field) == n:
        return field, "vertices"
    if len(field) == m:
        return field, "faces"
    raise ValueError("The field has {} vectors; the mesh {} vertices and {} faces.".format(len(field), n, m))


def face_to_vertex_field(vertices, faces, field):
    """A field per face as a field per vertex: the faces around each vertex averaged, weighted by their area.

    A line field has no sign, so the face vectors are first turned to agree with each other; then each vertex average
    is projected into the tangent plane there, and the signs made consistent with :func:`orient_field`.

    Parameters
    ----------
    vertices, faces : array
        The mesh.
    field : array
        (m, 3) one vector per face.

    Returns
    -------
    np.ndarray
        (n, 3) unit vectors, one per vertex.

    """
    V = np.asarray(vertices, dtype=float)
    F = np.asarray(faces)
    D = np.asarray(field, dtype=float)[:, :3]
    D = D / np.maximum(np.linalg.norm(D, axis=1), 1e-300)[:, None]
    # the face vectors turned to agree, face to neighbouring face, as orient_field does for vertices
    D = orient_field(V[F].mean(axis=1), _face_adjacency(F), D)
    area = np.linalg.norm(np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]]), axis=1) / 2
    W = np.zeros_like(V)
    for k in range(3):
        np.add.at(W, F[:, k], area[:, None] * D)
    W = project_field(V, F, W)
    return orient_field(V, F, W)


def _face_adjacency(faces):
    """Triangles of the faces' adjacency, for orient_field: each pair of faces sharing an edge, as a degenerate triangle."""
    F = np.asarray(faces)
    edges = {}
    pairs = []
    for f, t in enumerate(F):
        for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            key = (min(a, b), max(a, b))
            if key in edges:
                pairs.append((edges[key], f, f))
            else:
                edges[key] = f
    return np.array(pairs, dtype=int).reshape(-1, 3)


def axis_field(vertices, faces, point, direction):
    """The field around an axis: the wale turning around the line, the courses in the planes through it.

    With the axis through the two points where the courses should meet, the courses are the meridians between
    them; moved off the surface, by a distance below the rim, the courses no longer meet in a point but end along a
    band of the boundary, about that wide. The field has no singularity on the surface then, and one sign.

    Parameters
    ----------
    vertices, faces : array
        The mesh.
    point : array
        A point on the axis.
    direction : array
        The direction of the axis; the field turns around it by the right-hand rule.

    Returns
    -------
    np.ndarray
        (n, 3) unit vectors in the tangent planes, zero where the field is along the normal.

    """
    V = np.asarray(vertices, dtype=float)
    around = np.cross(np.asarray(direction, dtype=float), V - np.asarray(point, dtype=float))
    return project_field(V, faces, around)


def smoothest_field(vertices, faces, fixed=None, directions=None, target=None, weight=0.0):
    """The smoothest line field on a mesh, held at some vertices, or pulled towards a target field.

    Parameters
    ----------
    vertices : array
        (n, 3) vertex coordinates.
    faces : array
        (m, 3) triangles.
    fixed : list[int], optional
        The vertices where the field is held. None: free everywhere, the smoothest field of all.
    directions : array, optional
        The field at the fixed vertices, one 3D vector each, projected into the tangent plane there.
    target : array, optional
        A field to stay close to, one 3D vector per vertex, zero where it does not matter: a small modification of
        it, smoothed. Each vertex is pulled towards it by ``weight`` times its area.
    weight : float, optional
        How strongly, 1 / l^2: the field follows the target over lengths longer than l, and is smoothed over shorter
        ones. Large: the target; small: the smoothest field.

    Returns
    -------
    np.ndarray
        (n, 3) unit vectors in the tangent planes, one per vertex, their signs made consistent with
        :func:`orient_field`, from the first fixed vertex, along its direction.

    """
    V = np.asarray(vertices, dtype=float)
    F = np.asarray(faces)
    n = len(V)
    normals = vertex_normals(V, F)

    # a tangent basis per vertex: any direction not along the normal, made orthogonal
    a = np.where(np.abs(normals[:, :1]) < 0.9, [[1.0, 0.0, 0.0]], [[0.0, 1.0, 0.0]])
    bx = a - (a * normals).sum(axis=1)[:, None] * normals
    bx /= np.linalg.norm(bx, axis=1)[:, None]
    by = np.cross(normals, bx)

    def angle(v, d):
        return np.arctan2((d * by[v]).sum(axis=1), (d * bx[v]).sum(axis=1))

    # the edges, with cotan weights
    i, j, w = [], [], []
    for k in range(3):
        p, q, r = F[:, k], F[:, (k + 1) % 3], F[:, (k + 2) % 3]
        u, v = V[p] - V[r], V[q] - V[r]
        cot = (u * v).sum(axis=1) / np.maximum(np.linalg.norm(np.cross(u, v), axis=1), 1e-300)
        i.append(p)
        j.append(q)
        w.append(0.5 * cot)
    i, j, w = np.concatenate(i), np.concatenate(j), np.concatenate(w)
    key = np.minimum(i, j) * n + np.maximum(i, j)
    key, inverse = np.unique(key, return_inverse=True)
    w = np.bincount(inverse, weights=w)
    w = np.maximum(w, 1e-12)  # obtuse triangles can make a cotan weight negative; keep the energy positive
    i, j = key // n, key % n

    # the transport from j to i: the edge's angle in the basis of i minus its angle in the basis of j, doubled
    e = V[j] - V[i]
    rho = np.exp(2j * (angle(i, e) - angle(j, e)))

    # the energy sum w |z_i - rho z_j|^2 as z^H L z
    rows = np.r_[i, j, i, j]
    cols = np.r_[i, j, j, i]
    vals = np.r_[w, w, -w * rho, -w * np.conj(rho)]
    L = scipy.sparse.csr_matrix((vals.astype(complex), (rows, cols)), shape=(n, n))

    area = np.zeros(n)
    A = np.linalg.norm(np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]]), axis=1) / 6
    for k in range(3):
        np.add.at(area, F[:, k], A)
    M = scipy.sparse.diags(area.astype(complex))

    # the pull towards the target: weight sum area |z - t|^2, t the target's doubled angle, zero where it has none
    t = np.zeros(n, dtype=complex)
    if target is not None and weight > 0:
        target = np.asarray(target, dtype=float)
        has = np.linalg.norm(target, axis=1) > 0
        t[has] = np.exp(2j * angle(np.flatnonzero(has), target[has]))
        L = L + weight * scipy.sparse.diags(area * has).astype(complex)

    if fixed is None or len(fixed) == 0:
        if not t.any():
            # the smallest eigenvector, against the vertex areas
            _, vectors = scipy.sparse.linalg.eigsh(L, k=1, M=M, sigma=-1e-8, which="LM")
            z = vectors[:, 0]
        else:
            z = scipy.sparse.linalg.spsolve(L.tocsc(), weight * area * t)
    else:
        fixed = np.asarray(fixed)
        d = np.asarray(directions, dtype=float)
        z = np.zeros(n, dtype=complex)
        z[fixed] = np.exp(2j * angle(fixed, d))
        free = np.setdiff1d(np.arange(n), fixed)
        L = L.tocsc()
        b = weight * area[free] * t[free] - L[free][:, fixed] @ z[fixed]
        z[free] = scipy.sparse.linalg.spsolve(L[free][:, free], b)

    theta = np.angle(z) / 2
    field = np.cos(theta)[:, None] * bx + np.sin(theta)[:, None] * by
    if fixed is not None and len(fixed):
        return orient_field(V, F, field, start=fixed[0], direction=d[0])
    if t.any():
        start = int(np.argmax(np.abs(t)))
        return orient_field(V, F, field, start=start, direction=target[start])
    return orient_field(V, F, field)


def orient_field(vertices, faces, field, start=0, direction=None):
    """Give a line field consistent signs: each vertex along its neighbour, from the start vertex outwards.

    The stripes take the sign of the field for which course is above the other, so it has to be consistent. Around
    a half-turn singularity it cannot be: the sign flips somewhere on a line from it.

    Parameters
    ----------
    vertices, faces : array
        The mesh.
    field : array
        (n, 3) the field, one vector per vertex.
    start : int, optional
        The vertex to start from.
    direction : array, optional
        The sign at the start vertex: along this direction.

    Returns
    -------
    np.ndarray
        The field, some vectors reversed.

    """
    import collections

    F = np.asarray(faces)
    field = np.array(field, dtype=float)
    n = len(field)
    neighbours = [[] for _ in range(n)]
    for k in range(3):
        for a, b in zip(F[:, k], F[:, (k + 1) % 3]):
            neighbours[a].append(b)
            neighbours[b].append(a)
    if direction is not None and np.dot(field[start], direction) < 0:
        field[start] *= -1
    done = np.zeros(n, dtype=bool)
    done[start] = True
    queue = collections.deque([start])
    while queue:
        a = queue.popleft()
        for b in neighbours[a]:
            if not done[b]:
                if np.dot(field[a], field[b]) < 0:
                    field[b] *= -1
                done[b] = True
                queue.append(b)
    return field
