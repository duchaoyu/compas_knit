"""Test the simulation on a flat circular membrane, clamped on its rim, under pressure.

1. An isotropic membrane against Hencky's solution for the centre deflection of a clamped circular membrane,
   w0 = C(nu) a (p a / E)^(1/3), with C = 0.662 for nu = 0.3, at two mesh sizes: within 2 %.
2. The knit, orthotropic with the moduli of Chapter 5, the wale along x: the crown height, and the shape along the wale
   and along the course.
3. The same, pre-strained by the stretch factors of the fabrication.
4. The circular flat mesh of the fabsim examples, data/circular_flat/circular_flat.obj, anchored on its boundary and
   inflated, E1 = 5000 N/m along the wale (x), E2 = 2500 N/m, nu = 0.198.

    python scripts/tests/simulate_disc.py

The results are written to data/tests/disc/out/.
"""
import os

import numpy as np
from scipy.spatial import Delaunay

from compas_knit import DATA
from compas_knit.simulation import simulate
from compas_knit.simulation import write_mesh
from compas_knit.stripes import read_mesh

# MODIFY -----------------------------------------------------------------
radius = 0.5  # m
edge = 0.02  # m, the target edge length of the mesh
pressure = 1000.0  # Pa

knit = {"E_wale": 10300.0, "E_course": 13400.0, "nu": 0.58}  # N/m, motif 1, calibrated in Chapter 5
stretch_wale, stretch_course = 1.1, 1.05
circular_flat = os.path.join(DATA, "circular_flat", "circular_flat.obj")
circular_flat_knit = {"E_wale": 5000.0, "E_course": 2500.0, "nu": 0.198}  # N/m, E1 along the field, E2 across
# -------------------------------------------------------------------------

out_dir = os.path.join(DATA, "tests", "disc", "out")


def disc_mesh(radius, edge):
    """A flat disc in the xy plane, triangulated from rings of points about edge apart, its normals along +z."""
    rings = max(int(np.ceil(radius / edge)), 1)
    points = [(0.0, 0.0)]
    for k in range(1, rings + 1):
        r = radius * k / rings
        n = max(6, int(round(2 * np.pi * r / edge)))
        a = np.linspace(0, 2 * np.pi, n, endpoint=False) + (k % 2) * np.pi / n
        points += list(zip(r * np.cos(a), r * np.sin(a)))
    points = np.array(points)
    faces = Delaunay(points).simplices
    # counter-clockwise, so the normals, and the pressure, point up
    e1 = points[faces[:, 1]] - points[faces[:, 0]]
    e2 = points[faces[:, 2]] - points[faces[:, 0]]
    flip = e1[:, 0] * e2[:, 1] - e1[:, 1] * e2[:, 0] < 0
    faces[flip] = faces[flip][:, ::-1]
    return np.c_[points, np.zeros(len(points))], faces


def boundary_vertices(faces):
    """The vertices on the boundary: those of the edges of one triangle only."""
    edges = np.sort(np.r_[faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]], axis=1)
    edges, count = np.unique(edges, axis=0, return_counts=True)
    return np.unique(edges[count == 1])


def height_along(vertices, rest, axis, r):
    """The height of the deformed membrane at distance r from the centre along the x (0) or y (1) axis."""
    d = np.abs(rest[:, axis] - r) + np.abs(rest[:, 1 - axis])
    return vertices[np.argmin(d), 2]


# 1. isotropic, against Hencky
print("1. isotropic membrane, E = 10000 N/m, nu = 0.3, against Hencky")
E = 10000.0
hencky = 0.662 * radius * (pressure * radius / E) ** (1 / 3)
for size in (2 * edge, edge):
    V, F = disc_mesh(radius, size)
    field = np.tile([1.0, 0.0, 0.0], (len(V), 1))
    r = simulate((V, F), field, os.path.join(out_dir, "iso_%g" % size), E, E, 0.3, pressure, mass=0.0)
    w0 = r["summary"]["crown_height"]
    print("   edge {:.3f} m, {:5d} triangles: w0 {:.4f} m, Hencky {:.4f} m, {:+.2f} %  ({})".format(
        size, len(F), w0, hencky, 100 * (w0 - hencky) / hencky, r["summary"]["status"]))
    assert abs(w0 - hencky) < 0.02 * hencky, "the crown height is off Hencky's solution"

# 2. and 3. the knit
V, F = disc_mesh(radius, edge)
write_mesh(os.path.join(out_dir, "disc.obj"), V, F)
field = np.tile([1.0, 0.0, 0.0], (len(V), 1))  # the wale along x
print("2. and 3. the knit, E_wale {E_wale:.0f} N/m, E_course {E_course:.0f} N/m, nu {nu}, wale along x".format(**knit))
for label, sw, sc in (("no pre-strain", 1.0, 1.0), ("pre-strained {}/{}".format(stretch_wale, stretch_course), stretch_wale, stretch_course)):
    r = simulate((V, F), field, os.path.join(out_dir, "knit_%g_%g" % (sw, sc)), pressure=pressure, stretch_wale=sw, stretch_course=sc, mass=0.0, **knit)
    s = r["summary"]
    wale, course = height_along(r["vertices"], V, 0, radius / 2), height_along(r["vertices"], V, 1, radius / 2)
    print("   {:22s} crown {:.4f} m; at r = a/2 along the wale {:.4f} m, along the course {:.4f} m; "
          "max stress {:.0f} N/m  ({})".format(label, s["crown_height"], wale, course, s["max_stress"], s["status"]))

# 4. the circular flat mesh, anchored on its boundary
V, F = read_mesh(circular_flat)
anchors = boundary_vertices(F)
a = np.linalg.norm(V[anchors, :2], axis=1).mean()
field = np.tile([1.0, 0.0, 0.0], (len(V), 1))
print("4. circular_flat.obj, {} vertices, {} triangles, radius {:.3f} m, {} anchors on the boundary, p = {:.0f} Pa".format(
    len(V), len(F), a, len(anchors), pressure))
print("   E_wale {E_wale:.0f} N/m, E_course {E_course:.0f} N/m, nu {nu}, wale along x".format(**circular_flat_knit))
r = simulate(circular_flat, field, os.path.join(out_dir, "circular_flat"), pressure=pressure, fixed_vertices=anchors,
             mass=0.0, **circular_flat_knit)
s = r["summary"]
wale, course = height_along(r["vertices"], V, 0, a / 2), height_along(r["vertices"], V, 1, a / 2)
print("   crown {:.4f} m; at r = a/2 along the wale {:.4f} m, along the course {:.4f} m; "
      "max stress {:.0f} N/m, mean {:.0f} N/m  ({})".format(s["crown_height"], wale, course, s["max_stress"], s["mean_stress"], s["status"]))
print("results in", out_dir)
