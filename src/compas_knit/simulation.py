"""Finite element simulation of the knit, with the ``knit_sim`` executable (Chapter 6, Section 6.3).

The knit is an orthotropic membrane whose material frame comes from the same directional field the trajectories are
extracted from, pre-strained by the stretch factors of the fabrication, with sliding cables and rods, under pressure.
Units are those of ``knit_sim``: metres, moduli in N/m (Young's modulus times thickness), pressure in Pa.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import os
import subprocess

import numpy as np

from compas_knit import HOME
from compas_knit.stripes import read_mesh


__all__ = ["simulate", "write_mesh"]


SIM_EXE = os.environ.get("COMPAS_KNIT_SIM", os.path.join(HOME, "src", "cpp_sim", "build", "knit_sim"))


def write_mesh(path, vertices, faces):
    """Write a triangle mesh as an ``.obj``, the vertices in the given order."""
    with open(path, "w") as f:
        for v in vertices:
            f.write("v {:.10g} {:.10g} {:.10g}\n".format(*v))
        for t in faces:
            f.write("f {} {} {}\n".format(*(int(i) + 1 for i in t)))


def simulate(
    mesh,
    field,
    out_prefix,
    E_wale,
    E_course,
    nu,
    pressure,
    stretch_wale=1.0,
    stretch_course=1.0,
    fixed_vertices=None,
    cables=(),
    rods=(),
    thickness=1.0,
    mass=0.001,
    load_steps=0,
):
    """Simulate the knit under pressure.

    Parameters
    ----------
    mesh : str | tuple[array, array]
        The mesh M, in metres: the path to an ``.obj`` or ``.off``, or its vertices and triangles.
    field : str | array
        The wale direction per vertex, as read by ``stripes``: the path to its file, or an (n, 3) array.
    out_prefix : str
        Where to write the inputs and the results, ``<out_prefix>_deformed.obj``, ``_stress.csv``, ``_summary.json``.
    E_wale, E_course : float
        Membrane moduli along the wale and the course, in N/m.
    nu : float
        Poisson's ratio.
    pressure : float
        In Pa, along the face normals.
    stretch_wale, stretch_course : float | list[float], optional
        Pre-strain stretch factors, one value or one per face: the stitches are divided by them, as in the fabrication.
    fixed_vertices : list[int], optional
        The supports; by default the whole boundary.
    cables : list[dict], optional
        ``{"path": [vertex, ...], "EA": N, "rest_scale": 1.0}``: sliding cables through these vertices.
    rods : list[dict], optional
        ``{"path": [vertex, ...], "E": Pa, "thickness": m, "width": m}``.
    thickness : float, optional
        Thickness of the membrane, 1 when the moduli are per unit length.
    mass : float, optional
        Mass per unit area, for the self-weight.
    load_steps : int, optional
        Number of pressure steps from 1 % to 100 %; 0: 1, 10, 50 and 100 %.

    Returns
    -------
    dict
        ``vertices``: the deformed vertices, ``faces``, ``stress``: the stress per face as in the ``_stress.csv``
        columns, and ``summary``: solver status and residual, crown height, stresses, cable tensions.

    """
    if not os.path.isfile(SIM_EXE):
        raise RuntimeError(
            "knit_sim executable not found at {}. Build it with\n"
            "  cmake -S src/cpp_sim -B src/cpp_sim/build && cmake --build src/cpp_sim/build -j 8\n"
            "or point COMPAS_KNIT_SIM at it.".format(SIM_EXE)
        )
    folder = os.path.dirname(os.path.abspath(out_prefix))
    if not os.path.isdir(folder):
        os.makedirs(folder)

    if not isinstance(mesh, str):
        vertices, faces = mesh
        mesh = out_prefix + "_mesh.obj"
        write_mesh(mesh, vertices, faces)
    if not isinstance(field, str):
        path = out_prefix + "_field.txt"
        np.savetxt(path, np.asarray(field, dtype=float)[:, :3], fmt="%.10g")
        field = path

    params = {
        "E_wale": E_wale,
        "E_course": E_course,
        "nu": nu,
        "pressure": pressure,
        "thickness": thickness,
        "mass": mass,
        "stretch_wale": list(stretch_wale) if np.ndim(stretch_wale) else stretch_wale,
        "stretch_course": list(stretch_course) if np.ndim(stretch_course) else stretch_course,
        "cables": [dict(c, path=[int(v) for v in c["path"]]) for c in cables],
        "rods": [dict(r, path=[int(v) for v in r["path"]]) for r in rods],
        "load_steps": load_steps,
    }
    if fixed_vertices is not None:
        params["fixed_vertices"] = [int(v) for v in fixed_vertices]
    params_path = out_prefix + "_params.json"
    with open(params_path, "w") as f:
        json.dump(params, f, indent=1)

    run = subprocess.run([SIM_EXE, mesh, field, params_path, out_prefix], capture_output=True, text=True)
    if run.returncode == 1:
        raise RuntimeError("knit_sim failed:\n" + run.stderr)
    with open(out_prefix + "_summary.json") as f:
        summary = json.load(f)
    if summary["status"] != "success":
        print("warning: knit_sim did not converge: {} (residual {:.2e})".format(summary["status"], summary["residual"]))
    vertices, faces = read_mesh(out_prefix + "_deformed.obj")
    stress = np.loadtxt(out_prefix + "_stress.csv", delimiter=",", skiprows=1, ndmin=2)
    return {"vertices": vertices, "faces": faces, "stress": stress, "summary": summary}
