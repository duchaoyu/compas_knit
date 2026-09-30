"""View the mesh and the knitting trajectories in compas_viewer."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from compas.colors import Color
from compas.datastructures import Mesh
from compas.geometry import bounding_box


__all__ = ["view_stripes"]


def view_stripes(mesh, trajectories, view="top", show_mesh=True):
    """Show the mesh and the trajectories. Blocks until the window is closed.

    Parameters
    ----------
    mesh : str | :class:`compas.datastructures.Mesh`
        The mesh, or the path to an ``.obj`` file.
    trajectories : list[:class:`compas.geometry.Polyline`]
        The trajectories, as returned by :func:`compas_knit.stripes.generate_stripes`.
    view : {"top", "perspective", "front", "right"}, optional
        The initial view. Switch views in the viewer under View.
    show_mesh : bool, optional
        Show the mesh under the trajectories.

    """
    from compas_viewer import Viewer  # optional dependency

    if isinstance(mesh, str):
        mesh = Mesh.from_obj(mesh)

    viewer = Viewer()
    viewer.renderer.view = view
    viewer.config.renderer.show_grid = False

    if show_mesh:
        viewer.scene.add(mesh, name="mesh", facecolor=Color.grey().lightened(70), show_lines=False, opacity=0.8)

    group = viewer.scene.add_group(name="trajectories")
    for i, polyline in enumerate(trajectories):
        group.add(polyline, name="trajectory {}".format(i), linecolor=Color.from_hex("#1f4e79"), linewidth=1)

    _frame(viewer, mesh.vertices_attributes("xyz"), view)
    viewer.show()


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
