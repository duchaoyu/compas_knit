"""View the mesh, the directional field and the knitting trajectories in compas_viewer."""
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


__all__ = ["view_stripes", "view_field"]


def view_stripes(
    mesh,
    trajectories,
    links=None,
    singularities=None,
    show_sequence=True,
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
        :func:`compas_knit.stripes.order_trajectories`, from the first colour to the second, and a checkbox
        in the side panel switches between that and black.
    singularities : list[tuple[str, list[float], int]], optional
        As returned by :func:`compas_knit.stripes.read_singularities`, shown as points: stripe singularities,
        where a trajectory ends, blue, field singularities black.
        Those with an index beyond one are drawn larger.
    show_sequence : bool, optional
        Start with the trajectories coloured by their position in the knitting order, needs ``links``.
        Otherwise, and without ``links``, they are all black.
    view : {"top", "perspective", "front", "right"}, optional
        The initial view. Switch views in the viewer under View.
    show_mesh : bool, optional
        Show the mesh under the trajectories.
    colors : tuple[str, str], optional
        Hex colours of the first and the last trajectories in the order, by default orange to green.

    """
    from compas_viewer import Viewer  # optional dependency

    from compas_viewer.components.booleantoggle import BooleanToggle
    from compas_viewer.scene import Collection

    from compas_knit.stripes import order_trajectories

    if isinstance(mesh, str):
        mesh = Mesh.from_obj(mesh)

    plain_colors = [Color.black()] * len(trajectories)
    sequence_colors = None
    if links is not None:
        position, cyclic = order_trajectories(links, len(trajectories))
        if cyclic:
            print("warning: {} trajectories are on a cycle of links, the knitting needs a seam there".format(len(cyclic)))
        top = max(max(position), 1)
        sequence_colors = [_blend(colors[0], colors[1], p / top) for p in position]
    line_colors = sequence_colors if (show_sequence and sequence_colors) else plain_colors

    viewer = Viewer()
    viewer.renderer.view = view
    viewer.config.renderer.show_grid = False

    if show_mesh:
        viewer.scene.add(mesh, name="mesh", facecolor=Color.grey().lightened(70), show_lines=False, opacity=0.8)

    # lift the trajectories a little off the surface, along the normal at the nearest vertex,
    # so the faces do not draw over them and tint their colours
    xyz = np.array(mesh.vertices_attributes("xyz"))
    normals = np.array([mesh.vertex_normal(vertex) for vertex in mesh.vertices()])
    lift = 0.02 * np.mean([mesh.edge_length(edge) for edge in mesh.edges()])
    tree = cKDTree(xyz)

    group = viewer.scene.add_group(name="trajectories")
    objects = []
    for i, (polyline, color) in enumerate(zip(trajectories, line_colors)):
        points = np.array([list(point) for point in polyline.points])
        points = points + lift * normals[tree.query(points)[1]]
        objects.append(group.add(Polyline(points.tolist()), name="trajectory {}".format(i), linecolor=color, linewidth=2))

    if sequence_colors:
        # a checkbox in the side panel switches between the knitting order and one colour
        state = {"show_sequence": bool(show_sequence)}

        def recolor(component, checked):
            for obj, color in zip(objects, sequence_colors if checked else plain_colors):
                obj.linecolor = color
                obj.update(update_data=True)
            viewer.renderer.update()

        viewer.ui.sidedock.show = True  # the config is read when the viewer is made, so show the panel directly
        viewer.ui.sidedock.add(BooleanToggle(state, "show_sequence", title="Show sequence", action=recolor))

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


def view_field(mesh, field, view="top", length=None):
    """Show the mesh and the directional field. Blocks until the window is closed.

    The field is a line field, so each vertex gets a segment centred on it, without an arrowhead.
    The vectors are projected into the tangent plane at each vertex, as the stripes executable does.

    Parameters
    ----------
    mesh : str | :class:`compas.datastructures.Mesh`
        The mesh, or the path to an ``.obj`` file.
    field : str | array-like
        Per-vertex directional field, one ``x y z`` vector per vertex in mesh vertex order, or the path to its file.
    view : {"top", "perspective", "front", "right"}, optional
        The initial view. Switch views in the viewer under View.
    length : float, optional
        Length of the segments. Defaults to 0.8 times the mean edge length.

    """
    from compas_viewer import Viewer  # optional dependency
    from compas_viewer.scene import Collection

    from compas_knit.stripes import _mesh_arrays
    from compas_knit.stripes import _vertex_normals

    # the vertices in the order of the file, in step with the field, which Mesh.from_obj would merge
    xyz, faces = _mesh_arrays(mesh)
    if isinstance(mesh, str):
        mesh = Mesh.from_vertices_and_faces(xyz.tolist(), faces.tolist())
    if isinstance(field, str):
        field = np.loadtxt(field)
    field = np.asarray(field, dtype=float)[:, :3]
    if len(field) != len(xyz):
        raise ValueError("The field has {} vectors, the mesh {} vertices.".format(len(field), len(xyz)))

    normals = _vertex_normals(xyz, faces)
    tangent = field - (field * normals).sum(axis=1)[:, None] * normals
    tangent /= np.maximum(np.linalg.norm(tangent, axis=1), 1e-12)[:, None]
    mean_edge = np.mean([mesh.edge_length(edge) for edge in mesh.edges()])
    half = (length or 0.8 * mean_edge) / 2
    # lift the segments a little off the surface, so the faces do not draw over them
    centres = xyz + 0.02 * mean_edge * normals
    lines = [Line(p - half * t, p + half * t) for p, t in zip(centres, tangent)]

    viewer = Viewer()
    viewer.renderer.view = view
    viewer.config.renderer.show_grid = False

    viewer.scene.add(mesh, name="mesh", facecolor=Color.grey().lightened(70), linecolor=Color.grey().lightened(40), opacity=0.8)
    viewer.scene.add(Collection(lines), name="field", linecolor=Color.from_hex("#1f4e79"), linewidth=2)

    _frame(viewer, xyz, view)
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
    """Point the camera at the centre of the points and zoom so they fill the window."""
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
