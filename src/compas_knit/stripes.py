"""Knitting trajectories from a directional field (Chapter 6, Section 6.2.1).

The trajectories are the isolines of a stripe pattern aligned with the field.
Each trajectory is knitted out and back as two courses, so adjacent trajectories
are placed two stitch heights apart.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import subprocess

import numpy as np
from scipy.spatial import cKDTree

from compas.datastructures import Mesh
from compas.geometry import Polyline

from compas_knit import HOME


__all__ = ["generate_stripes", "check_trajectories", "read_trajectories"]


STRIPES_EXE = os.environ.get("COMPAS_KNIT_STRIPES", os.path.join(HOME, "src", "cpp_stripes", "build", "stripes"))


def generate_stripes(mesh_path, field_path, stitch_height, stretch=1.0, out_dir=None, view=False, check=True):
    """Extract equally spaced knitting trajectories from a directional field.

    Parameters
    ----------
    mesh_path : str
        Triangle mesh, ``<name>.obj``.
    field_path : str
        Per-vertex directional field, one ``x y z`` world-space vector per line, in mesh vertex order.
    stitch_height : float
        Stitch height st_h at theoretical zero stress, in the units of the mesh.
    stretch : float, optional
        Pre-strain stretch factor along the wale. The spacing is divided by it, see Section 6.3.3.
    out_dir : str, optional
        Where to write ``<name>_remesh.obj`` and ``<name>_tri_path.txt``. Defaults to the mesh directory.
    view : bool, optional
        Show the field and the trajectories in polyscope. Blocks until the window is closed.
    check : bool, optional
        Warn about segments running along the field, see :func:`check_trajectories`.

    Returns
    -------
    list[:class:`compas.geometry.Polyline`]
        The trajectories, unordered, in mesh coordinates.

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
        "--out-dir", out_dir,
    ]
    if view:
        cmd.append("--view")
    subprocess.check_call(cmd)

    trajectories = read_trajectories(os.path.join(out_dir, name + "_tri_path.txt"))
    if check:
        for i, j, angle in check_trajectories(trajectories, mesh_path, field_path):
            print("warning: trajectory {} segment {} runs {:.0f} degrees from the field, it may join two trajectories".format(i, j, angle))
    return trajectories


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


def _face_field(mesh, field):
    """Return a function giving the unit field, sign free, in the face nearest to each of some points."""
    if isinstance(mesh, str):
        mesh = Mesh.from_obj(mesh)
    if isinstance(field, str):
        field = np.loadtxt(field)
    field = np.asarray(field, dtype=float)[:, :3]

    xyz = np.array(mesh.vertices_attributes("xyz"))
    index = {vertex: i for i, vertex in enumerate(mesh.vertices())}
    faces = np.array([[index[vertex] for vertex in mesh.face_vertices(face)] for face in mesh.faces()])
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
