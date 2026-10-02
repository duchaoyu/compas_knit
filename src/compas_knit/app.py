"""A window to simulate a knit interactively, and export the settings of the simulation for the fabrication.

The window shows the mesh, ``<folder>/<name>.obj``. *Run simulation* runs ``knit_sim``, the boundary fixed, under the
concrete and the pressure, and shows the knit under them, shaded by the von Mises stress, over the mesh as it was; the
status bar gives the displacements, the stresses, and how many faces are in compression. *Export settings* writes the
parameters of that run, the stitch, the stretch factors, the material and the loads, with what it gave, to
``<folder>/<name>_settings.json``; ``scripts/fab/5_pattern_from_settings.py`` makes the knitting pattern of that knit
from it.

The parameters are kept in ``<folder>/<name>_params.json``, saved on every change, so the window opens with them again.
``scripts/sim/sim_window.py`` opens it.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import datetime
import json
import os

import numpy as np

__all__ = ["DEFAULTS", "load_params", "save_params", "export_settings", "read_settings", "sim_window"]


DEFAULTS = {
    # the stitch and the pre-strain, of the knit simulated and of its pattern
    "stitch_height": 2.297,  # in the units of the mesh
    "stitch_width": 3.54,
    "stretch_wale": 1.05,  # the stitches are divided by it
    "stretch_course": 1.05,
    # the simulation
    "units": 0.001,  # metres per unit of the mesh
    "E_wale": 12500.0,  # N/m
    "E_course": 5000.0,
    "nu": 0.198,
    "concrete_thickness": 10.0,  # mm
    "concrete_density": 2400.0,  # kg/m3
    "pressure": 0.0,  # Pa
}


def params_path(folder, name):
    return os.path.join(folder, name + "_params.json")


def load_params(folder, name):
    """The parameters of an example, the defaults where the file has none."""
    params = dict(DEFAULTS)
    path = params_path(folder, name)
    if os.path.isfile(path):
        with open(path) as f:
            params.update(json.load(f))
    return params


def save_params(folder, name, params):
    """Write the parameters, so the window opens with them again."""
    with open(params_path(folder, name), "w") as f:
        json.dump(params, f, indent=1)


def settings_path(folder, name):
    """Where the settings of an example are: ``<folder>/<name>_settings.json``."""
    return os.path.join(folder, name + "_settings.json")


def export_settings(folder, name, params, results=None):
    """Write the parameters of a simulation, and what it gave, to ``<folder>/<name>_settings.json``.

    Returns
    -------
    str
        The path.

    """
    path = settings_path(folder, name)
    with open(path, "w") as f:
        json.dump({"geometry": name, "exported": datetime.datetime.now().isoformat(timespec="seconds"),
                   "parameters": dict(params), "results": results or {}}, f, indent=1)
    return path


def read_settings(path):
    """The settings exported by the window, or None where there is no file.

    Returns
    -------
    dict | None
        ``geometry``, ``exported``, ``parameters`` as :data:`DEFAULTS`, ``results``.

    """
    if not path or not os.path.isfile(path):
        return None
    with open(path) as f:
        return json.load(f)


def _status(viewer, text):
    """Show a message in the status bar, and repaint, before a long computation."""
    from PySide6.QtWidgets import QApplication

    print(text)
    viewer.ui.window.widget.statusBar().showMessage(text)
    QApplication.processEvents()


def sim_window(folder, name):
    """The window: ``<folder>/<name>.obj``, its boundary fixed, under concrete and pressure; its settings exported."""
    from compas.colors import Color
    from compas.datastructures import Mesh
    from compas_viewer import Viewer
    from compas_viewer.components.button import Button
    from compas_viewer.components.numberedit import NumberEdit

    from compas_knit.simulation import simulate
    from compas_knit.stripes import read_mesh
    from compas_knit.viewer import _blend
    from compas_knit.viewer import _frame

    V0, F = read_mesh(os.path.join(folder, name + ".obj"))
    field = os.path.join(folder, name + "_vertex_directional_field.txt")
    edges = np.sort(np.r_[F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]], axis=1)
    edges, count = np.unique(edges, axis=0, return_counts=True)
    boundary = np.unique(edges[count == 1])

    p = load_params(folder, name)
    save_params(folder, name, p)

    viewer = Viewer()
    viewer.config.renderer.show_grid = False
    viewer.ui.sidedock.show = True
    viewer.scene.add(Mesh.from_vertices_and_faces(V0.tolist(), F.tolist()), name="mesh", show_faces=False,
                     linecolor=Color.grey(), linewidth=1)
    shown = []
    last = {}

    def run():
        _status(viewer, "Running the simulation...")
        V = V0 * p["units"]
        added = p["concrete_density"] * p["concrete_thickness"] / 1000.0  # kg/m2
        out = os.path.join(folder, "out", name + "_window")
        r = simulate((V, F), field, out, p["E_wale"], p["E_course"], p["nu"], p["pressure"], stretch_wale=p["stretch_wale"],
                     stretch_course=p["stretch_course"], fixed_vertices=boundary, mass=0.0, added_mass=added)
        s = r["summary"]
        columns = open(out + "_stress.csv").readline().strip().split(",")
        vm = r["stress"][:, columns.index("von_mises")]
        p2 = r["stress"][:, columns.index("principal_2")]
        t = (vm - vm.min()) / ((vm.max() - vm.min()) or 1.0)
        deformed = Mesh.from_vertices_and_faces((r["vertices"] / p["units"]).tolist(), F.tolist())
        colors = {f: _blend("#dbeafe", "#1e3a8a", t[i]) for i, f in enumerate(deformed.faces())}
        # the simulated knit in place of the one before
        for obj in shown:
            viewer.scene.remove(obj, rebuild_buffers=False)
        shown[:] = [viewer.scene.add(deformed, name="simulated", facecolor=colors, linecolor=Color.grey().darkened(30),
                                     linewidth=1, opacity=0.8)]
        viewer.renderer.makeCurrent()
        viewer.renderer.rebuild_buffers()
        viewer.renderer.update()
        viewer.ui.sidebar.update()
        d = (r["vertices"] - V) * 1000.0
        last.clear()
        last["parameters"] = dict(p)
        last["results"] = {"status": s["status"], "largest_displacement_mm": round(float(np.linalg.norm(d, axis=1).max()), 3),
                           "down_mm": round(float(-d[:, 2].min()), 3), "von_mises_min": round(float(vm.min()), 1),
                           "von_mises_max": round(float(vm.max()), 1), "faces_in_compression": int((p2 < 0).sum()),
                           "concrete_N": round(float(s.get("added_weight", 0.0)), 2)}
        _status(viewer, "{}: largest displacement {:.2f} mm, down {:.2f} mm; von Mises {:.0f} to {:.0f} N/m; "
                        "{} faces in compression; concrete {:.0f} N; stretch {} / {}".format(
                            s["status"], np.linalg.norm(d, axis=1).max(), -d[:, 2].min(), vm.min(), vm.max(),
                            int((p2 < 0).sum()), s.get("added_weight", 0.0), p["stretch_wale"], p["stretch_course"]))

    def export():
        if not last:
            _status(viewer, "Run the simulation first: the settings are those of the last run.")
            return
        path = export_settings(folder, name, last["parameters"], last["results"])
        warning = ", but {} faces were in compression".format(last["results"]["faces_in_compression"]) \
            if last["results"]["faces_in_compression"] else ""
        _status(viewer, "Exported the settings of the last run, stretch {} / {}{}, to {}".format(
            last["parameters"]["stretch_wale"], last["parameters"]["stretch_course"], warning, path))

    def changed(component, value):
        save_params(folder, name, p)

    def edit(key, title, step, decimals, min_val=0.0, max_val=1e9):
        viewer.ui.sidedock.add(NumberEdit(p, key, title=title, min_val=min_val, max_val=max_val, step=step,
                                          decimals=decimals, action=changed))

    viewer.ui.sidedock.add(Button(text="Run simulation", action=run))
    edit("stretch_wale", "stretch, wale", 0.01, 3, 0.5, 2.0)
    edit("stretch_course", "stretch, course", 0.01, 3, 0.5, 2.0)
    edit("E_wale", "E wale, N/m", 100, 0)
    edit("E_course", "E course, N/m", 100, 0)
    edit("nu", "Poisson's ratio", 0.01, 3, 0.0, 0.99)
    edit("concrete_thickness", "concrete, mm", 1, 1)
    edit("concrete_density", "concrete, kg/m3", 100, 0)
    edit("pressure", "pressure, Pa", 100, 0, -1e6, 1e6)
    edit("units", "units, m per unit", 0.001, 4, 1e-6, 1e3)
    viewer.ui.sidedock.add(Button(text="Export settings", action=export))
    edit("stitch_height", "stitch height", 0.01, 3)
    edit("stitch_width", "stitch width", 0.01, 3)

    _frame(viewer, V0, "top")
    viewer.show()
