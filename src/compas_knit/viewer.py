"""View the mesh, the directional field, the knitting trajectories and the simulated shape in compas_viewer."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np
from scipy.spatial import cKDTree

from compas.colors import Color
from compas.datastructures import Mesh
from compas.geometry import Line
from compas.geometry import Point
from compas.geometry import Polyline
from compas.geometry import bounding_box


__all__ = ["view_stripes", "view_field", "view_simulation"]


def view_stripes(
    mesh,
    trajectories,
    links=None,
    singularities=None,
    view="top",
    show_mesh=True,
    colors=("#fb8500", "#1a7431"),
):
    """Show the mesh and the trajectories. Blocks until the window is closed.

    Parameters
    ----------
    mesh : str | :class:`compas.datastructures.Mesh`
        The mesh, or the path to an ``.obj`` file.
    trajectories : list[:class:`compas.geometry.Polyline`]
        The trajectories, as returned by :func:`compas_knit.stripes.generate_stripes`.
    links : list[tuple[int, int, int]], optional
        The links between neighbouring trajectories, as returned by :func:`compas_knit.stripes.read_neighbours`.
        The trajectories are then coloured by their position in the knitting order, see
        :func:`compas_knit.stripes.order_trajectories`, from the first colour to the second; without, black.
    singularities : list[tuple[str, list[float], int]], optional
        As returned by :func:`compas_knit.stripes.read_singularities`, shown as points: stripe singularities,
        where a trajectory ends, blue, field singularities black.
        Those with an index beyond one are drawn larger.
    view : {"top", "perspective", "front", "right"}, optional
        The initial view. Switch views in the viewer under View.
    show_mesh : bool, optional
        Show the mesh under the trajectories.
    colors : tuple[str, str], optional
        Hex colours of the first and the last trajectories in the order, by default orange to green.

    """
    from compas_viewer import Viewer  # optional dependency
    from compas_viewer.scene import Collection

    from compas_knit.stripes import order_trajectories

    if isinstance(mesh, str):
        mesh = Mesh.from_obj(mesh)

    line_colors = [Color.black()] * len(trajectories)
    if links is not None:
        position, cyclic = order_trajectories(links, len(trajectories))
        if cyclic:
            print("warning: {} trajectories are on a cycle of links, the knitting needs a seam there".format(len(cyclic)))
        top = max(max(position), 1)
        line_colors = [_blend(colors[0], colors[1], p / top) for p in position]

    viewer = Viewer()
    viewer.renderer.view = view
    viewer.config.renderer.show_grid = False

    if show_mesh:
        viewer.scene.add(mesh, name="mesh", facecolor=Color.grey().lightened(70), show_lines=False, opacity=0.8)

    # lift the trajectories a little off the surface, along the normal at the nearest vertex,
    # so the faces do not draw over them and tint their colours
    from compas_knit.stripes import _mesh_arrays
    from compas_knit.stripes import _vertex_normals

    xyz, faces = _mesh_arrays(mesh)
    normals = _vertex_normals(xyz, faces)
    lift = 0.02 * np.mean(np.linalg.norm(xyz[faces] - xyz[np.roll(faces, 1, axis=1)], axis=2))
    tree = cKDTree(xyz)

    group = viewer.scene.add_group(name="trajectories")
    for i, (polyline, color) in enumerate(zip(trajectories, line_colors)):
        points = np.array([list(point) for point in polyline.points])
        points = points + lift * normals[tree.query(points)[1]]
        group.add(Polyline(points.tolist()), name="trajectory {}".format(i), linecolor=color, linewidth=2)

    if singularities:
        # one scene object per kind, so each can be switched on and off in the scene panel
        styles = {
            "stripe": ("stripe singularities", "#2b6cb0"),
            "field": ("field singularities", "#000000"),
        }
        points = {}
        for kind, point, index in singularities:
            name, color = styles[kind]
            p = np.array(point)
            p = p + 3 * lift * normals[tree.query(p)[1]]
            points.setdefault((name, color, abs(index) > 1), []).append(Point(*p))
        for (name, color, large), pts in sorted(points.items()):
            viewer.scene.add(
                Collection(pts),
                name=name + (" (index beyond 1)" if large else ""),
                show_points=True,
                pointcolor=Color.from_hex(color),
                pointsize=16 if large else 9,
            )

    _frame(viewer, mesh.vertices_attributes("xyz"), view)
    viewer.show()


def view_field(mesh, field, view="top", length=None, points=None):
    """Show the mesh and the directional field. Blocks until the window is closed.

    The field is a line field, so each vertex, or each face for a field per face, gets a segment centred on it, without
    an arrowhead. The vectors are projected into the tangent plane there, as the stripes executable does.

    Parameters
    ----------
    mesh : str | :class:`compas.datastructures.Mesh`
        The mesh, or the path to an ``.obj`` file.
    field : str | array-like
        The directional field, one ``x y z`` vector per vertex, or per face, in the order of the mesh, or the path to
        its file.
    view : {"top", "perspective", "front", "right"}, optional
        The initial view. Switch views in the viewer under View.
    length : float, optional
        Length of the segments. Defaults to 0.8 times the mean edge length.
    points : array, optional
        Points to mark in red, e.g. the vertices where the field is held.

    """
    from compas_viewer import Viewer  # optional dependency
    from compas_viewer.scene import Collection

    from compas_knit.stripes import _mesh_arrays
    from compas_knit.stripes import _vertex_normals

    # the vertices in the order of the file, in step with the field, which Mesh.from_obj would merge
    xyz, faces = _mesh_arrays(mesh)
    if isinstance(mesh, str):
        mesh = Mesh.from_vertices_and_faces(xyz.tolist(), faces.tolist())
    from compas_knit.field import read_field

    if isinstance(field, str):
        field, on = read_field(field, xyz, faces)
    else:
        field = np.asarray(field, dtype=float)[:, :3]
        on = "faces" if len(field) == len(faces) and len(field) != len(xyz) else "vertices"
        if len(field) != len(xyz) and on == "vertices":
            raise ValueError("The field has {} vectors; the mesh {} vertices and {} faces.".format(len(field), len(xyz), len(faces)))

    if on == "faces":
        normals = np.cross(xyz[faces[:, 1]] - xyz[faces[:, 0]], xyz[faces[:, 2]] - xyz[faces[:, 0]])
        normals /= np.maximum(np.linalg.norm(normals, axis=1), 1e-300)[:, None]
        at = xyz[faces].mean(axis=1)
    else:
        normals = _vertex_normals(xyz, faces)
        at = xyz
    tangent = field - (field * normals).sum(axis=1)[:, None] * normals
    tangent /= np.maximum(np.linalg.norm(tangent, axis=1), 1e-12)[:, None]
    mean_edge = np.mean([mesh.edge_length(edge) for edge in mesh.edges()])
    half = (length or (0.5 if on == "faces" else 0.8) * mean_edge) / 2
    # lift the segments a little off the surface, so the faces do not draw over them
    centres = at + 0.02 * mean_edge * normals
    lines = [Line(p - half * t, p + half * t) for p, t in zip(centres, tangent)]

    viewer = Viewer()
    viewer.renderer.view = view
    viewer.config.renderer.show_grid = False

    viewer.scene.add(mesh, name="mesh", facecolor=Color.grey().lightened(70), linecolor=Color.grey().lightened(40), opacity=0.8)
    viewer.scene.add(Collection(lines), name="field", linecolor=Color.from_hex("#1f4e79"), linewidth=2)
    if points is not None and len(points):
        viewer.scene.add(Collection([Point(*p) for p in np.asarray(points)]), name="points", show_points=True, pointcolor=Color.red(), pointsize=10)

    _frame(viewer, xyz, view)
    viewer.show()


def view_simulation(
    original,
    deformed,
    stress=None,
    quantity="von_mises",
    field=None,
    show_field=False,
    loads=None,
    view="top",
    colors=("#dbeafe", "#1e3a8a"),
):
    """Show the original mesh and the simulated, deformed one. Blocks until the window is closed.

    The original is drawn as its edges in black, the deformed mesh as faces, shaded by the stress from the first colour,
    the lowest, to the second, the highest, or plain without the stress. Each can be switched off in the scene panel.
    With the field, a checkbox in the side panel shows the wale direction on the deformed mesh.

    Parameters
    ----------
    original : str | tuple[array, array]
        The mesh before the simulation, the path to an ``.obj`` or its vertices and triangles.
    deformed : str | tuple[array, array]
        The deformed mesh, ``<out_prefix>_deformed.obj`` of :func:`compas_knit.simulation.simulate`, with the vertices
        in the same order.
    stress : str | array, optional
        The stress per face, ``<out_prefix>_stress.csv``, or the ``stress`` that ``simulate`` returns.
    quantity : str, optional
        The column of the stress to shade by: ``von_mises``, ``principal_1``, ``principal_2``, ``T_wale_Nm``,
        ``T_course_Nm``, ``S11``, ``S22`` or ``S12``.
    field : str | array, optional
        The directional field of the original mesh, the wale per vertex, or the path to its file. It is carried onto
        the deformed mesh by the deformation of the triangles around each vertex.
    show_field : bool, optional
        Start with the field shown.
    loads : list[tuple[int, tuple[float, float, float]]], optional
        Point loads, ``(vertex, (fx, fy, fz))`` as given to :func:`compas_knit.simulation.simulate`, each drawn as a red
        line along its force, ending at the vertex, on the original and on the deformed mesh; the largest a fifth of
        the size of the mesh.
    view : {"top", "perspective", "front", "right"}, optional
        The initial view. ``"top"`` is a perspective view looking straight down, so it can be rotated with the right
        mouse button. Switch views in the viewer under View.
    colors : tuple[str, str], optional
        Hex colours of the lowest and the highest stress.

    """
    from compas_viewer import Viewer  # optional dependency
    from compas_viewer.components.booleantoggle import BooleanToggle
    from compas_viewer.scene import Collection

    from compas_knit.stripes import _vertex_normals
    from compas_knit.stripes import read_mesh

    xyz0, faces0 = read_mesh(original) if isinstance(original, str) else map(np.asarray, original)
    xyz, faces = read_mesh(deformed) if isinstance(deformed, str) else map(np.asarray, deformed)
    if len(xyz0) != len(xyz):
        raise ValueError("The original has {} vertices, the deformed mesh {}.".format(len(xyz0), len(xyz)))
    before = Mesh.from_vertices_and_faces(xyz0.tolist(), faces0.tolist())
    after = Mesh.from_vertices_and_faces(xyz.tolist(), faces.tolist())

    facecolor = Color.from_hex(colors[1]).lightened(50)
    if stress is not None:
        columns = ["face", "S11", "S22", "S12", "von_mises", "principal_1", "principal_2", "T_wale_Nm", "T_course_Nm"]
        if isinstance(stress, str):
            with open(stress) as f:
                columns = f.readline().strip().split(",")
            stress = np.loadtxt(stress, delimiter=",", skiprows=1, ndmin=2)
        values = np.asarray(stress)[:, columns.index(quantity)]
        low, high = values.min(), values.max()
        t = (values - low) / ((high - low) or 1.0)
        facecolor = {face: _blend(colors[0], colors[1], t[i]) for i, face in enumerate(after.faces())}
        print("{}: {:.4g} to {:.4g} N/m, {} to {}".format(quantity, low, high, colors[0], colors[1]))
    print("largest displacement {:.4g} m".format(np.linalg.norm(xyz - xyz0, axis=1).max()))

    viewer = Viewer()
    viewer.renderer.view = view
    viewer.config.renderer.show_grid = False

    viewer.scene.add(before, name="original", show_faces=False, linecolor=Color.black(), linewidth=1)
    viewer.scene.add(after, name="simulated", facecolor=facecolor, linecolor=Color.grey().darkened(30), linewidth=1, opacity=0.7)

    if field is not None:
        if isinstance(field, str):
            field = np.loadtxt(field)
        field = np.asarray(field, dtype=float)[:, :3]
        if len(field) != len(xyz0):
            raise ValueError("The field has {} vectors, the mesh {} vertices.".format(len(field), len(xyz0)))
        # the deformation gradient of each triangle, from its edges before and after, applied to the field at its
        # corners and averaged per vertex
        edges0 = np.stack([xyz0[faces0[:, 1]] - xyz0[faces0[:, 0]], xyz0[faces0[:, 2]] - xyz0[faces0[:, 0]]], axis=2)
        edges = np.stack([xyz[faces[:, 1]] - xyz[faces[:, 0]], xyz[faces[:, 2]] - xyz[faces[:, 0]]], axis=2)
        grad = edges @ np.linalg.pinv(edges0)
        moved = np.zeros_like(field)
        for corner in range(3):
            v = faces0[:, corner]
            d = np.einsum("fij,fj->fi", grad, field[v])
            # the field is a line field: keep the signs at a vertex together
            sign = np.sign(np.einsum("fi,fi->f", d, moved[v]) + 1e-12)
            np.add.at(moved, v, sign[:, None] * d)
        normals = _vertex_normals(xyz, faces)
        moved -= (moved * normals).sum(axis=1)[:, None] * normals
        moved /= np.maximum(np.linalg.norm(moved, axis=1), 1e-12)[:, None]
        mean_edge = np.linalg.norm(edges[:, :, 0], axis=1).mean()
        half = 0.4 * mean_edge
        centres = xyz + 0.05 * mean_edge * normals
        lines = [Line(p - half * t, p + half * t) for p, t in zip(centres, moved)]
        segments = viewer.scene.add(Collection(lines), name="field", linecolor=Color.from_hex("#fb8500"), linewidth=2, show=show_field)

        state = {"show_field": bool(show_field)}

        def toggle(component, checked):
            segments.show = checked
            viewer.renderer.update()

        viewer.ui.sidedock.show = True
        viewer.ui.sidedock.add(BooleanToggle(state, "show_field", title="Show field", action=toggle))

    if loads:
        forces = np.array([np.asarray(f, dtype=float) for _, f in loads])
        span = (np.r_[xyz0, xyz].max(axis=0) - np.r_[xyz0, xyz].min(axis=0)).max()
        scale = 0.2 * span / max(np.linalg.norm(forces, axis=1).max(), 1e-12)
        for label, surface in (("load (original)", xyz0), ("load", xyz)):
            lines = [Line(surface[v] - scale * f, surface[v]) for (v, _), f in zip(loads, forces)]
            viewer.scene.add(Collection(lines), name=label, linecolor=Color.from_hex("#c0392b"), linewidth=4)

    _frame(viewer, np.r_[xyz0, xyz], view)
    viewer.show()


def _blend(first, last, t):
    """The colour a fraction t of the way from the hex colour first to last, blended in OKLab,
    so that the colours in between stay as clear as the ends instead of turning grey."""

    def to_linear(c):
        return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)

    def to_srgb(c):
        return np.where(c <= 0.0031308, 12.92 * c, 1.055 * np.power(np.maximum(c, 0), 1 / 2.4) - 0.055)

    M1 = np.array([[0.4122214708, 0.5363325363, 0.0514459929],
                   [0.2119034982, 0.6806995451, 0.1073969566],
                   [0.0883024619, 0.2817188376, 0.6299787005]])
    M2 = np.array([[0.2104542553, 0.7936177850, -0.0040720468],
                   [1.9779984951, -2.4285922050, 0.4505937099],
                   [0.0259040371, 0.7827717662, -0.8086757660]])
    lab = [M2 @ np.cbrt(M1 @ to_linear(np.array(Color.from_hex(c).rgb))) for c in (first, last)]
    mixed = lab[0] + (lab[1] - lab[0]) * t
    rgb = to_srgb(np.linalg.inv(M1) @ (np.linalg.inv(M2) @ mixed) ** 3)
    return Color(*np.clip(rgb, 0, 1))


def _frame(viewer, points, view):
    """Point the camera at the centre of the points and zoom so they fill the window.

    The top view is a perspective view looking straight down, so that it can still be rotated with the right mouse
    button; the other orthographic views of compas_viewer cannot.
    """
    box = bounding_box(points)
    xmin, ymin, zmin = box[0]
    xmax, ymax, zmax = box[6]
    centre = [(xmin + xmax) / 2, (ymin + ymax) / 2, (zmin + zmax) / 2]
    size = max(xmax - xmin, ymax - ymin, zmax - zmin) or 1.0
    # in the orthographic views the camera distance is half the visible width
    window = viewer.config.window
    aspect = (window.width - 300) / window.height  # minus the sidebar
    width = {"top": (xmax - xmin, ymax - ymin), "front": (xmax - xmin, zmax - zmin), "right": (ymax - ymin, zmax - zmin)}
    w, h = width.get(view, (size, size))
    distance = 0.55 * max(w, h * aspect) if view in width else 1.5 * size

    camera = viewer.renderer.camera
    camera.scale = size / 10  # near/far planes and panning scale with the model, the defaults suit a 10 unit model
    camera.reset_position(view)
    camera.target.set(*centre)
    camera.distance = distance
    if view == "top":
        # looking straight down, far enough for the perspective to show the whole plan
        viewer.renderer.view = "perspective"
        camera.rotation.set(0, 0, 0)
        camera.distance = 0.55 * max(w / aspect, h) / np.tan(np.radians(camera.fov) / 2) + (zmax - zmin)
