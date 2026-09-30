"""Knitting trajectories from a directional field (Chapter 6, Section 6.2.1).

The trajectories are the isolines of a stripe pattern aligned with the field.
Each trajectory is knitted out and back as two courses, so adjacent trajectories
are placed two stitch heights apart.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import collections
import os
import subprocess

import numpy as np
from scipy.spatial import cKDTree

from compas.datastructures import Mesh
from compas.geometry import Polyline

from compas_knit import HOME


__all__ = ["generate_stripes", "check_trajectories", "order_trajectories", "read_trajectories", "read_neighbours", "read_singularities", "read_mesh"]


STRIPES_EXE = os.environ.get("COMPAS_KNIT_STRIPES", os.path.join(HOME, "src", "cpp_stripes", "build", "stripes"))


def generate_stripes(mesh_path, field_path, stitch_height, stitch_width, stretch=1.0, out_dir=None, view=False, check=True):
    """Extract equally spaced knitting trajectories from a directional field, divided into stitches.

    Parameters
    ----------
    mesh_path : str
        Triangle mesh, ``<name>.obj``.
    field_path : str
        Per-vertex directional field, one ``x y z`` world-space vector per line, in mesh vertex order.
    stitch_height : float
        Stitch height st_h at theoretical zero stress, in the units of the mesh.
    stitch_width : float
        Stitch width st_w, in the units of the mesh. The trajectories are divided into stitches of this width,
        one point per stitch, as Grasshopper's DivideDistance, written to ``<name>_tri_path_recons.txt``.
    stretch : float, optional
        Pre-strain stretch factor along the wale. The spacing is divided by it, see Section 6.3.3.
    out_dir : str, optional
        Where to write ``<name>_remesh.obj``, ``<name>_tri_path.txt``, ``<name>_tri_path_recons.txt``,
        ``<name>_neighbours.txt`` (see :func:`read_neighbours`) and ``<name>_singularities.txt``.
        Defaults to the mesh directory.
    view : bool, optional
        Show the field and the trajectories in polyscope. Blocks until the window is closed.
    check : bool, optional
        Warn about segments running along the field, see :func:`check_trajectories`.

    Returns
    -------
    list[:class:`compas.geometry.Polyline`]
        The trajectories divided into stitches, one point per stitch, unordered, all running the same way along
        field x normal, in mesh coordinates. Trajectories shorter than one stitch are left out.

    """
    if not os.path.isfile(STRIPES_EXE):
        raise RuntimeError(
            "stripes executable not found at {}. Build it with\n"
            "  cmake -S src/cpp_stripes -B src/cpp_stripes/build && cmake --build src/cpp_stripes/build -j 8\n"
            "or point COMPAS_KNIT_STRIPES at it.".format(STRIPES_EXE)
        )

    spacing = 2 * stitch_height / stretch
    name = os.path.splitext(os.path.basename(mesh_path))[0]
    out_dir = out_dir or os.path.dirname(os.path.abspath(mesh_path))
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    cmd = [
        STRIPES_EXE,
        mesh_path,
        "--field", field_path,
        "--spacing", repr(spacing),
        "--size", "0",  # keep the mesh units, so the spacing is in the same units as the stitch height
        "--stitch-width", repr(stitch_width),
        "--out-dir", out_dir,
    ]
    if view:
        cmd.append("--view")
    subprocess.check_call(cmd)

    trajectories = read_trajectories(os.path.join(out_dir, name + "_tri_path.txt"))
    if check:
        for i, j, angle in check_trajectories(trajectories, mesh_path, field_path):
            print("warning: trajectory {} segment {} runs {:.0f} degrees from the field, it may join two trajectories".format(i, j, angle))
    return read_trajectories(os.path.join(out_dir, name + "_tri_path_recons.txt"))


def check_trajectories(trajectories, mesh, field, min_angle=60.0):
    """Find segments running along the field, which a trajectory should cross.

    Such a segment joins neighbouring trajectories, as the extraction used to do at stripe singularities.
    Next to a singularity, where two stripes merge into one, the remaining trajectory also shifts sideways
    by up to half a spacing, and such a segment is reported too.

    Parameters
    ----------
    trajectories : list[:class:`compas.geometry.Polyline`]
    mesh : str | :class:`compas.datastructures.Mesh`
        The mesh of the field, or the path to an ``.obj`` file.
    field : str | array-like
        Per-vertex directional field, or the path to its file, as for :func:`generate_stripes`.
    min_angle : float, optional
        Segments closer than this to the field direction, in degrees, are reported.

    Returns
    -------
    list[tuple[int, int, float]]
        Trajectory index, segment index and angle to the field in degrees, for each suspect segment.

    """
    field_at = _face_field(mesh, field)
    polylines = [np.array([list(point) for point in polyline.points]) for polyline in trajectories]
    # where an isoline passes (almost) through a mesh vertex, the crossings on the edges around it
    # (almost) coincide, and the direction of the segment between them means nothing
    min_length = 0.1 * np.median(np.concatenate([np.linalg.norm(p[1:] - p[:-1], axis=1) for p in polylines]))
    suspects = []
    for i, points in enumerate(polylines):
        vectors = points[1:] - points[:-1]
        lengths = np.linalg.norm(vectors, axis=1)
        cosines = np.abs((vectors * field_at((points[1:] + points[:-1]) / 2)).sum(axis=1)) / np.maximum(lengths, 1e-12)
        angles = np.degrees(np.arccos(np.clip(cosines, 0, 1)))
        for j in np.nonzero((angles < min_angle) & (lengths > min_length))[0]:
            suspects.append((i, int(j), float(angles[j])))
    return suspects


def read_mesh(path):
    """Read the vertices and triangles of an ``.obj``, in the order of the file, as the stripes executable does.

    Unlike :meth:`compas.datastructures.Mesh.from_obj`, it does not merge vertices at the same position, so the
    vertices stay in step with a per-vertex field.

    Returns
    -------
    tuple[np.ndarray, np.ndarray]
        The vertex coordinates, and the triangles as vertex indices.

    """
    vertices, faces = [], []
    with open(path, "r") as f:
        for line in f:
            if line.startswith("v "):
                vertices.append([float(c) for c in line.split()[1:4]])
            elif line.startswith("f "):
                faces.append([int(t.split("/")[0]) - 1 for t in line.split()[1:4]])
    return np.array(vertices), np.array(faces, dtype=int)


def _mesh_arrays(mesh):
    """Vertices and triangles of a mesh given as a path, read in file order, or as a compas mesh."""
    if isinstance(mesh, str):
        return read_mesh(mesh)
    index = {vertex: i for i, vertex in enumerate(mesh.vertices())}
    xyz = np.array([mesh.vertex_coordinates(vertex) for vertex in mesh.vertices()])
    faces = np.array([[index[vertex] for vertex in mesh.face_vertices(face)] for face in mesh.faces()])
    return xyz, faces


def _vertex_normals(xyz, faces):
    """Area-weighted vertex normals."""
    face_normals = np.cross(xyz[faces[:, 1]] - xyz[faces[:, 0]], xyz[faces[:, 2]] - xyz[faces[:, 0]])
    normals = np.zeros_like(xyz)
    for k in range(3):
        np.add.at(normals, faces[:, k], face_normals)
    return normals / np.maximum(np.linalg.norm(normals, axis=1), 1e-12)[:, None]


def _face_field(mesh, field):
    """Return a function giving the unit field, sign free, in the face nearest to each of some points."""
    xyz, faces = _mesh_arrays(mesh)
    if isinstance(field, str):
        field = np.loadtxt(field)
    field = np.asarray(field, dtype=float)[:, :3]
    if len(field) != len(xyz):
        raise ValueError("The field has {} vectors, the mesh {} vertices.".format(len(field), len(xyz)))
    corners = xyz[faces]
    normals = np.cross(corners[:, 1] - corners[:, 0], corners[:, 2] - corners[:, 0])
    normals /= np.linalg.norm(normals, axis=1)[:, None]

    # a line field: flip the corner vectors to agree with the first one before averaging
    first = field[faces[:, 0]]
    vectors = first.copy()
    for k in (1, 2):
        other = field[faces[:, k]]
        vectors += other * np.where((other * first).sum(axis=1) < 0, -1.0, 1.0)[:, None]
    vectors -= (vectors * normals).sum(axis=1)[:, None] * normals
    vectors /= np.maximum(np.linalg.norm(vectors, axis=1), 1e-12)[:, None]

    tree = cKDTree(corners.mean(axis=1))
    return lambda points: vectors[tree.query(points)[1]]


def read_trajectories(path):
    """Read a ``_tri_path.txt`` file, one polyline per line as ``x,y,z; x,y,z; ...``."""
    polylines = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            points = [[float(c) for c in point.split(",")] for point in line.split(";")]
            polylines.append(Polyline(points))
    return polylines


def read_neighbours(path):
    """Read a ``_neighbours.txt`` file: which trajectory comes after which along the field.

    Two trajectories are neighbours where they cross a mesh edge next to each other, and the one further
    along the field comes after the other. Indices refer to the trajectories in ``_tri_path.txt`` and, with
    a stitch width, ``_tri_path_recons.txt``, in the order of their lines.

    Returns
    -------
    list[tuple[int, int, int]]
        For each link, the trajectory before, the trajectory after, and the number of mesh edges on which
        they are adjacent, a measure of the length they share. Next to the end of a short row, the
        trajectories on either side of its tip are adjacent on only one or two edges.

    """
    links = []
    with open(path, "r") as f:
        for line in f:
            if line.strip():
                a, b, n = (int(v) for v in line.split())
                links.append((a, b, n))
    return links


def order_trajectories(links, n):
    """Position of each trajectory in the knitting order, from the links between neighbours.

    A trajectory's position is the length of the longest chain of links leading to it, so every trajectory
    comes after all the trajectories linked before it. Short rows share positions with the courses beside them.

    Parameters
    ----------
    links : list[tuple[int, int, int]]
        As returned by :func:`read_neighbours`.
    n : int
        The number of trajectories.

    Returns
    -------
    tuple[list[int], list[int]]
        The position of each trajectory, from 0, and the trajectories on a cycle of links, or after one.
        Where the links close on themselves, for instance where the courses run around a pole, there is no
        first or last and the knitting needs a seam; these trajectories get the position after the last
        one leading into them.

    """
    after = [[] for _ in range(n)]
    before = [[] for _ in range(n)]
    for a, b, _ in links:
        after[a].append(b)
        before[b].append(a)
    waiting = [len(before[i]) for i in range(n)]
    position = [0] * n
    queue = [i for i in range(n) if waiting[i] == 0]
    done = [False] * n
    while queue:
        a = queue.pop()
        done[a] = True
        for b in after[a]:
            position[b] = max(position[b], position[a] + 1)
            waiting[b] -= 1
            if waiting[b] == 0:
                queue.append(b)
    cyclic = [i for i in range(n) if not done[i]]
    # on a cycle, place each trajectory once, after the placed trajectories leading into it, in the order they are reached
    reached = collections.deque(i for i in cyclic if any(done[a] for a in before[i]))
    unreached = list(reversed(cyclic))
    while reached or unreached:
        if not reached:
            i = unreached.pop()
            if done[i]:
                continue
            reached.append(i)  # a cycle nothing leads into: start it anywhere
        i = reached.popleft()
        if done[i]:
            continue
        position[i] = max([position[a] + 1 for a in before[i] if done[a]] or [0])
        done[i] = True
        reached.extend(b for b in after[i] if not done[b])
    return position, cyclic


def read_singularities(path):
    """Read a ``_singularities.txt`` file: the singular triangles, at their centres.

    Returns
    -------
    list[tuple[str, list[float], int]]
        For each, its kind, its position and its index. ``"stripe"``: a singularity of the stripe pattern,
        where trajectories end, the index the number of stripes more on one side than on the other, with its sign.
        ``"field"``: a singularity of the directional field, the index in half turns, e.g. 1 for a
        half-turn, 2 for a pole.

    """
    singularities = []
    with open(path, "r") as f:
        for line in f:
            if line.strip():
                kind, x, y, z, index = line.split()
                singularities.append((kind, [float(x), float(y), float(z)], int(index)))
    return singularities

